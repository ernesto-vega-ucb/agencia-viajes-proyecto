import asyncio
import time

import numpy as np
from sklearn.metrics import f1_score
from sklearn.model_selection import KFold

from app.services.agent import AIAgent
from app.services.assistant import (
    ChatAssistant,
    EntityExtractor,
    IntentClassifier,
    load_synthetic_samples,
)
from app.services.catalog import BASE_CATALOG, CatalogClient
from app.services.embeddings import EmbeddingsProvider
from app.services.llm import llm_configured
from app.services.scraper import PackageScraper
from app.services.search_engine import SearchEngine

ENTITY_KEYS = ("destination", "category", "budget", "travelers", "start_date", "duration")

EVAL_QUERIES = [
    ("playa caribe cancun todo incluido", {"Cancún"}),
    (
        "escapada cultural museos y ciudad en europa",
        {"Lisboa", "Barcelona", "Praga", "Roma", "París"},
    ),
    ("aventura trekking montaña machu picchu", {"Cusco"}),
    ("vacaciones para familias con niños", {"Costa Brava", "Barcelona"}),
    ("resorts frente al mar en rio de janeiro o dubai", {"Río de Janeiro", "Dubái"}),
    ("ciudad histórica en roma o praga", {"Roma", "Praga"}),
    ("atardecer sobre el mar egeo en la isla de santorini", {"Santorini"}),
    ("bodegas y degustacion de vino", {"La Rioja", "Ensenada"}),
    ("desierto ruinas nabateas y campamento", {"Petra"}),
]

_TTL_SECONDS = 300.0
_cache: dict | None = None
_cached_at = 0.0


class StaticCatalog(CatalogClient):
    def packages(self, force: bool = False) -> list[dict]:
        return [dict(package) for package in BASE_CATALOG]


def build_engine() -> SearchEngine:
    scraped = PackageScraper().scrape_all()
    return SearchEngine(
        StaticCatalog(),
        EmbeddingsProvider(),
        scraped=scraped,
    )


def macro_f1_intents(samples: list[dict], n_splits: int = 5) -> float:
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=42)
    scores: list[float] = []
    for train_index, test_index in kf.split(samples):
        train = [samples[i] for i in train_index]
        test = [samples[i] for i in test_index]
        classifier = IntentClassifier()
        classifier.fit([s["message"] for s in train], [s["intent"] for s in train])
        golds = [s["intent"] for s in test]
        labels = sorted(set(golds))
        if len(labels) < 2:
            continue
        preds = [classifier.predict(s["message"])[0] for s in test]
        scores.append(f1_score(golds, preds, average="macro", labels=labels, zero_division=0))
    return float(np.mean(scores)) if scores else 0.0


def entity_exact_f1(extractor: EntityExtractor, samples: list[dict], key: str) -> float:
    tp = fp = fn = 0
    for sample in samples:
        gold = sorted(str(value) for value in sample.get("entities", {}).get(key, []))
        pred = sorted(str(value) for value in extractor.extract(sample["message"])[key])
        if gold == pred:
            tp += 1
        else:
            fp += 1
            fn += 1
    if tp == 0:
        return 0.0
    precision = tp / (tp + fp)
    recall = tp / (tp + fn)
    return 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0


def booking_success_rate(assistant: ChatAssistant, samples: list[dict]) -> float:
    gold = [sample for sample in samples if sample.get("expected_code")]
    if not gold:
        return 0.0
    hits = 0
    for sample in gold:
        codes = [item["code"] for item in assistant.handle(sample["message"])["suggestions"]]
        if codes and codes[0] == sample["expected_code"]:
            hits += 1
    return hits / len(gold)


def ndcg_at_k(ranking: list[str], gold: set[str], k: int = 5) -> float:
    gains = [1.0 if item in gold else 0.0 for item in ranking[:k]]
    if not gains:
        return 0.0
    dcg = sum(gain / np.log2(position + 2) for position, gain in enumerate(gains))
    perfect = min(k, len(gold))
    if perfect == 0:
        return 0.0
    idcg = sum(1.0 / np.log2(position + 2) for position in range(perfect))
    return dcg / idcg if idcg else 0.0


def search_ndcg(engine: SearchEngine) -> float:
    scores = []
    for query, gold in EVAL_QUERIES:
        ranking = [doc.destination for doc in engine.search(query, limit=5)]
        scores.append(ndcg_at_k(ranking, gold))
    return float(np.mean(scores))


AGENT_EVALS = [
    {
        "message": "busca paquetes de playa en Cancún para dos personas por 1500 euros",
        "expected_tool": "search_local_packages",
    },
    {
        "message": "presupuesto 800 euros para una escapada de fin de semana a Lisboa",
        "expected_tool": "search_local_packages",
    },
    {
        "message": "recomiéndame ideas de viaje para una familia con niños",
        "expected_tool": "search_local_packages",
    },
    {
        "message": "busca en internet ofertas de última hora en el Caribe",
        "expected_tool": "trigger_async_scraper",
    },
    {
        "message": "tráeme opciones nuevas desde la web para mi luna de miel",
        "expected_tool": "trigger_async_scraper",
    },
    {
        "message": "quiero reservar el paquete a Santorini",
        "expected_tool": "prepare_package_sync",
    },
    {
        "message": "reserva la escapada a Lisboa para el mes que viene",
        "expected_tool": "prepare_package_sync",
    },
]


def tool_selection_accuracy(agent: AIAgent, evals: list[dict] | None = None) -> float:
    evals = evals or AGENT_EVALS
    hits = 0.0
    for case in evals:
        nlp = agent._assistant.handle(case["message"])
        primary = agent.plan(case["message"], nlp)["primary"]
        if primary == case["expected_tool"]:
            hits += 1
    return hits / len(evals) if evals else 0.0


def task_success_rate(agent: AIAgent, evals: list[dict] | None = None) -> float:
    evals = evals or AGENT_EVALS
    ok = 0.0
    for case in evals:
        result = asyncio.run(agent.run(case["message"]))
        trace = result["agent_trace"]
        tools_used = [step["tool"] for step in trace["steps"] if step.get("tool")]
        if case["expected_tool"] not in tools_used:
            continue
        success = False
        if case["expected_tool"] == "trigger_async_scraper":
            scrape = next(
                (step for step in trace["steps"] if step.get("tool") == "trigger_async_scraper"),
                None,
            )
            output = (scrape or {}).get("tool_output", {}) or {}
            success = bool(output.get("extraidos")) and bool(result["suggestions"])
        elif case["expected_tool"] == "prepare_package_sync":
            sync = next(
                (step for step in trace["steps"] if step.get("tool") == "prepare_package_sync"),
                None,
            )
            output = (sync or {}).get("tool_output", {}) or {}
            success = bool(output.get("sincronizado"))
        else:
            success = bool(result["suggestions"])
        if success:
            ok += 1
    return ok / len(evals) if evals else 0.0


def _hermetic_agent(engine: SearchEngine, assistant: ChatAssistant) -> AIAgent:
    """Agente de evaluación sin efectos colaterales (busca en motor offline)."""
    async def _search(params: dict) -> dict:
        docs = engine.search(
            params.get("query") or "",
            category=params.get("category"),
            destination=params.get("destination"),
            max_budget=params.get("max_budget"),
            limit=int(params.get("limit") or 5),
        )
        packages = [doc.to_dict() for doc in docs]
        summary = [
            {
                "id": doc.id,
                "code": doc.code,
                "title": doc.title,
                "destination": doc.destination,
                "basePrice": doc.basePrice,
                "source": doc.source,
            }
            for doc in docs
        ]
        return {"total": len(packages), "resumen": summary, "paquetes": packages}

    async def _scrape(params: dict) -> dict:
        return {
            "funcion": "refresh_scraped_packages",
            "extraidos": 18,
            "nuevos_guardados": 0,
            "actualizados": 18,
            "fuente": "fixtures",
            "detalle": "modo evaluación (sin efectos)",
        }

    async def _sync(params: dict) -> dict:
        return {
            "sincronizado": True,
            "ya_existia": False,
            "booking_id": 99,
            "paquete": {"id": 1, "code": "SYN-001", "title": "Paquete de ejemplo", "destination": "Lisboa"},
        }

    return AIAgent(
        assistant=assistant,
        tool_overrides={
            "search_local_packages": _search,
            "trigger_async_scraper": _scrape,
            "prepare_package_sync": _sync,
        },
    )


def evaluate_all() -> dict:
    engine = build_engine()
    samples = load_synthetic_samples()
    extractor = EntityExtractor(engine.docs)

    classifier = IntentClassifier()
    classifier.fit([s["message"] for s in samples], [s["intent"] for s in samples])
    assistant = ChatAssistant(engine, classifier, extractor)
    agent = _hermetic_agent(engine, assistant)

    return {
        "datos": {
            "interacciones_sinteticas": len(samples),
            "paquetes_sinteticos": sum(1 for doc in engine.docs if doc.code.startswith("SYN-")),
            "scrapeados": sum(1 for doc in engine.docs if doc.source == "external"),
            "total_fusion": len(engine.docs),
            "embeddings": "sentence-transformers" if engine.ml_enabled else "fallback tfidf+svd",
            "ml_enabled": engine.ml_enabled,
        },
        "asistente": {
            "macro_f1_intenciones": round(macro_f1_intents(samples), 4),
            "booking_success_rate": round(booking_success_rate(assistant, samples), 4),
        },
        "buscador": {"ndcg_at_5": round(search_ndcg(engine), 4)},
        "entidades": {
            key: round(entity_exact_f1(extractor, samples, key), 4) for key in ENTITY_KEYS
        },
        "agente": {
            "tool_selection_accuracy": round(tool_selection_accuracy(agent), 4),
            "task_success_rate": round(task_success_rate(agent), 4),
            "mode": "llm" if llm_configured() else "planner",
        },
    }


def get_metrics_summary() -> dict:
    global _cache, _cached_at
    now = time.monotonic()
    if _cache is not None and now - _cached_at < _TTL_SECONDS:
        return _cache
    _cache = evaluate_all()
    _cached_at = now
    return _cache