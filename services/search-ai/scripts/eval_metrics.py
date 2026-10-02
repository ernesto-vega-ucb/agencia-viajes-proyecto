import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
from sklearn.metrics import f1_score  # noqa: E402
from sklearn.model_selection import KFold  # noqa: E402

from app.services.assistant import (  # noqa: E402
    ChatAssistant,
    EntityExtractor,
    IntentClassifier,
    load_synthetic_samples,
)
from app.services.catalog import BASE_CATALOG, CatalogClient  # noqa: E402
from app.services.embeddings import EmbeddingsProvider  # noqa: E402
from app.services.scraper import PackageScraper  # noqa: E402
from app.services.search_engine import SearchEngine  # noqa: E402

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


def evaluate_all() -> dict:
    engine = build_engine()
    samples = load_synthetic_samples()
    extractor = EntityExtractor(engine.docs)

    classifier = IntentClassifier()
    classifier.fit([s["message"] for s in samples], [s["intent"] for s in samples])
    assistant = ChatAssistant(engine, classifier, extractor)

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
    }


def main() -> None:
    report = evaluate_all()
    dataset = report["datos"]
    print("========== Métricas formales del asistente y buscador ==========")
    print(
        f"Dataset fusionado: {dataset['total_fusion']} paquetes indexados "
        f"({dataset['paquetes_sinteticos']} sintéticos, "
        f"{dataset['scrapeados']} externos scrapeados; "
        f"{dataset['interacciones_sinteticas']} interacciones). "
        f"Embeddings: {dataset['embeddings']}"
    )
    print(
        "Asistente  -> Macro-F1 intenciones (CV 5): "
        f"{report['asistente']['macro_f1_intenciones']}"
    )
    print(
        "             Booking success rate (top-1): "
        f"{report['asistente']['booking_success_rate']}"
    )
    print(
        "             F1 exacto por entidad: "
        + ", ".join(f"{key}={value}" for key, value in report["entidades"].items())
    )
    print(f"Buscador   -> nDCG@5: {report['buscador']['ndcg_at_5']}")
    print("=================================================================")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
