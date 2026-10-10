from __future__ import annotations

import json
import math
import re
from datetime import date
from pathlib import Path
from typing import Protocol

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline

from app.config import get_settings
from app.services.search_engine import PackageDoc, SearchEngine
from app.services.text_prep import CATEGORY_SYNONYMS, TOKEN_RE, normalize_es

SYNTHETIC_PATH = Path(__file__).resolve().parents[1] / "data" / "synthetic_interactions.json"

INTENTS = (
    "saludo",
    "despedida",
    "buscar_paquetes",
    "reservar_paquete",
    "presupuesto",
    "recomendar",
)

RULE_KEYWORDS = {
    "saludo": {
        "hola",
        "buenos dias",
        "buenas tardes",
        "buenas noches",
        "buen dia",
        "hey",
        "saludos",
        "que tal",
    },
    "despedida": {
        "adios",
        "hasta luego",
        "hasta pronto",
        "nos vemos",
        "chao",
        "gracias por todo",
        "fue todo",
    },
    "buscar_paquetes": {
        "buscar",
        "busco",
        "busqueda",
        "opciones",
        "quiero ver",
        "ofertas",
        "oferta",
        "viajar a",
        "tour",
        "destino",
        "destinos",
        "vacaciones",
        "encontrar",
        "ultimo momento",
    },
    "reservar_paquete": {
        "reservar",
        "reserva",
        "reservacion",
        "quiero reservar",
        "apartar",
        "contratar",
        "comprar",
        "hacer una reserva",
        "confirmar",
        "boletos",
        "gestiona",
    },
    "presupuesto": {
        "precio",
        "presupuesto",
        "cuanto cuesta",
        "cuanto vale",
        "tarifa",
        "barato",
        "economico",
        "coste",
        "costo",
        "dinero",
        "cuanto sale",
    },
    "recomendar": {
        "recomienda",
        "recomiendame",
        "recomiendas",
        "sugiere",
        "sugieres",
        "sugerencia",
        "ideas",
        "que me recomiendas",
        "ayuda",
        "donde ir",
        "aconseja",
        "decidir",
    },
}

DESTINATION_ALIASES = {
    "machu picchu": "Cusco",
    "machupicchu": "Cusco",
    "riviera maya": "Cancún",
    "caribe": "Cancún",
    "tulum": "Cancún",
}

_MONTHS = {
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "septiembre": 9,
    "octubre": 10,
    "noviembre": 11,
    "diciembre": 12,
}

_TRAVELER_WORDS = {
    "uno": 1,
    "una": 1,
    "dos": 2,
    "tres": 3,
    "cuatro": 4,
    "cinco": 5,
    "seis": 6,
    "siete": 7,
    "ocho": 8,
    "nueve": 9,
    "diez": 10,
    "once": 11,
    "doce": 12,
}

_BUDGET_RE = re.compile(r"(?i)(\d{2,6}(?:[.,]\d{1,2})?)\s*(?:euros?|eur|usd|\$|€)")
_PRESUPUESTO_RE = re.compile(
    r"(?i)presupuesto(?:\s+de|\s+maximo|\s+máximo)?\s+(\d{2,6}(?:[.,]\d{1,2})?)"
)
_MAXIMO_RE = re.compile(
    r"(?i)(?:menos\s+de|por\s+menos\s+de|maximo|máximo)\s+(\d{2,6}(?:[.,]\d{1,2})?)"
)
_TRAVELERS_RE = re.compile(
    r"(?i)\b(?:para|somos|viajamos|van|serian|iban)\s+(?:solo\s+)?"
    r"(uno|una|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|once|doce|\d{1,2})"
    r"\s*(?:personas?|adultos?|ninos?|ninas?|viajeros?|huespedes?|pax)?\b"
)
_COUNT_RE = re.compile(r"(?i)\b(\d{1,2})\s*(?:adultos?|personas?|viajeros?|pax)\b")
_DURATION_RE = re.compile(r"(?i)(\d{1,2})\s*(?:dias|noches)")
_DURATION_WORDS = {"una semana": 7, "una quincena": 15, "un mes": 30, "fin de semana": 2}


class IntentBackbone(Protocol):
    def fit(self, texts: list[str], labels: list[str]) -> None: ...

    def predict_proba(self, texts: list[str]) -> np.ndarray: ...

    @property
    def classes(self) -> list[str]: ...


class TfidfLogisticBackbone:
    """Línea base obligatoria: TF-IDF + Regresión Logística multinomial."""

    def __init__(self) -> None:
        self._pipeline = None
        self._classes: list[str] = []
        self._label_index: dict[str, int] = {}

    def fit(self, texts: list[str], labels: list[str]) -> None:
        self._classes = sorted(set(labels))
        self._label_index = {label: index for index, label in enumerate(self._classes)}
        if len(self._classes) < 2:
            return
        targets = [self._label_index[label] for label in labels]
        self._pipeline = make_pipeline(
            TfidfVectorizer(token_pattern=TOKEN_RE, ngram_range=(1, 2), min_df=1),
            LogisticRegression(max_iter=2000, C=10.0),
        )
        self._pipeline.fit(texts, targets)

    def predict_proba(self, texts: list[str]) -> np.ndarray:
        if self._pipeline is None or len(self._classes) < 2:
            return np.full((len(texts), len(self._classes)), 1.0 / max(len(self._classes), 1))
        outcome = np.zeros((len(texts), len(self._classes)))
        proba = self._pipeline.predict_proba(texts)
        model_classes = sorted(int(value) for value in self._pipeline.classes_)
        for row, values in enumerate(proba):
            for number, value in zip(model_classes, values, strict=True):
                outcome[row][number] = value
        return outcome

    @property
    def classes(self) -> list[str]:
        return self._classes


class BetoBackbone:
    """
    Opción estructurada para integrar Beto (Spanish BERT, dccuchile) en
    fases posteriores. Solo se activa si BETO_ENABLED=true y `transformers`
    está instalada; de lo contrario, la línea base TF-IDF cubre la tarea.
    """

    def __init__(self, model_name: str = "dccuchile/bert-base-spanish-wwm-uncased") -> None:
        self.model_name = model_name
        self.enabled = get_settings().beto_enabled
        self._tokenizer = None
        self._model = None
        self._classes: list[str] = []

    def fit(self, texts: list[str], labels: list[str]) -> None:
        if not self.enabled:
            raise RuntimeError(
                "Beto deshabilitado (BETO_ENABLED=false o 'transformers' no instalada)"
            )
        try:
            from transformers import BertForSequenceClassification, BertTokenizer

            self._classes = sorted(set(labels))
            self._tokenizer = BertTokenizer.from_pretrained(self.model_name)
            self._model = BertForSequenceClassification.from_pretrained(
                self.model_name, num_labels=len(self._classes)
            )
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("Instala el extra [ml] y 'transformers' para usar Beto") from exc

    def predict_proba(self, texts: list[str]) -> np.ndarray:  # pragma: no cover
        import torch

        if self._model is None or self._tokenizer is None:
            raise RuntimeError("Beto aún no entrenado")
        inputs = self._tokenizer(texts, padding=True, truncation=True, return_tensors="pt")
        self._model.eval()
        with torch.no_grad():
            logits = self._model(**inputs).logits
        return torch.softmax(logits, dim=-1).numpy()

    @property
    def classes(self) -> list[str]:
        return self._classes


class IntentClassifier:
    def __init__(self, backbone: IntentBackbone | None = None) -> None:
        self.backbone = backbone or TfidfLogisticBackbone()
        self._fitted = False

    def fit(self, texts: list[str], labels: list[str]) -> None:
        self.backbone.fit(texts, labels)
        self._fitted = True

    def predict(self, text: str) -> tuple[str, float, dict[str, float]]:
        scores = self._rule_scores(text)
        if self._fitted and self.backbone.classes:
            proba = self.backbone.predict_proba([text])[0]
            model_scores = dict(zip(self.backbone.classes, proba, strict=True))
            confidence = max(model_scores.values()) if model_scores else 0.0
            if confidence >= 0.7:
                model_weight = 0.75
            elif confidence >= 0.5:
                model_weight = 0.4
            else:
                model_weight = 0.0
            scores = {
                intent: model_weight * model_scores.get(intent, 0.0)
                + (1.0 - model_weight) * scores.get(intent, 0.0)
                for intent in INTENTS
            }
        best = max(scores, key=lambda intent: (scores[intent], -INTENTS.index(intent)))
        return best, scores[best], scores

    def _rule_scores(self, text: str) -> dict[str, float]:
        raw = normalize_es(text, keep_stopwords=True)
        counts = {}
        for intent, keywords in RULE_KEYWORDS.items():
            hits = sum(1 for keyword in keywords if keyword in raw)
            counts[intent] = 1.0 - 0.6 * math.exp(-hits)
        return counts


class EntityExtractor:
    def __init__(self, docs: list[PackageDoc]) -> None:
        self._destinations = sorted(
            {(doc.destination, normalize_es(doc.destination, keep_stopwords=True)) for doc in docs},
            key=lambda pair: pair[0],
        )
        self._country_map: dict[str, list[str]] = {}
        for doc in docs:
            if not doc.country:
                continue
            key = normalize_es(doc.country, keep_stopwords=True)
            destinations = self._country_map.setdefault(key, [])
            if doc.destination not in destinations:
                destinations.append(doc.destination)

    def extract(self, message: str) -> dict[str, list]:
        return {
            "destination": self._destinations_from(message),
            "category": self._categories_from(message),
            "budget": self._budget_from(message),
            "travelers": self._travelers_from(message),
            "start_date": self._start_date_from(message),
            "duration": self._duration_from(message),
        }

    def _destinations_from(self, message: str) -> list[str]:
        raw = normalize_es(message, keep_stopwords=True)
        found: list[str] = []
        for destination, normalized in self._destinations:
            if normalized and (normalized in raw or raw in normalized):
                if destination not in found:
                    found.append(destination)
        for alias, destination in DESTINATION_ALIASES.items():
            if normalize_es(alias, keep_stopwords=True) in raw and destination not in found:
                found.append(destination)
        for country, destinations in self._country_map.items():
            if country in raw:
                for destination in destinations:
                    if destination not in found:
                        found.append(destination)
        return found

    def _categories_from(self, message: str) -> list[str]:
        raw = normalize_es(message, keep_stopwords=True)
        found: list[str] = []
        for category, synonyms in CATEGORY_SYNONYMS.items():
            if any(synonym in raw for synonym in synonyms) and category not in found:
                found.append(category)
        return found

    def _budget_from(self, message: str) -> list[float]:
        values: list[float] = []
        for pattern in (_BUDGET_RE, _PRESUPUESTO_RE, _MAXIMO_RE):
            for match in pattern.finditer(message):
                value = float(match.group(1).replace(",", "."))
                if value not in values:
                    values.append(value)
        return values

    def _travelers_from(self, message: str) -> list[int]:
        values: list[int] = []
        for match in _TRAVELERS_RE.finditer(message):
            raw = match.group(1).lower()
            value = int(raw) if raw.isdigit() else _TRAVELER_WORDS.get(raw)
            if value is None:
                continue
            if value not in values:
                values.append(value)
        for match in _COUNT_RE.finditer(message):
            value = int(match.group(1))
            if value not in values:
                values.append(value)
        return values

    def _start_date_from(self, message: str) -> list[str]:
        raw = normalize_es(message, keep_stopwords=True)
        tokens = set(raw.split())
        year = self._year_from(message)
        dates: list[str] = []
        for month, number in _MONTHS.items():
            if month in tokens:
                dates.append(f"{year:04d}-{number:02d}")
                break
        if "proximo mes" in raw:
            year, number = self._shift_month(year or date.today().year, date.today().month, 1)
            dates.append(f"{year:04d}-{number:02d}")
        elif "este mes" in raw:
            year, number = date.today().year, date.today().month
            dates.append(f"{year:04d}-{number:02d}")
        return list(dict.fromkeys(dates))

    def _year_from(self, message: str) -> int | None:
        match = re.search(r"(?i)\b(20\d{2})\b", message)
        if match:
            return int(match.group(1))
        return date.today().year

    def _duration_from(self, message: str) -> list[int]:
        raw = normalize_es(message, keep_stopwords=True)
        durations: list[int] = []
        for match in _DURATION_RE.finditer(raw):
            value = int(match.group(1))
            if value not in durations:
                durations.append(value)
        for word, value in _DURATION_WORDS.items():
            if word in raw and value not in durations:
                durations.append(value)
        return durations

    @staticmethod
    def _shift_month(year: int, month: int, offset: int) -> tuple[int, int]:
        total = year * 12 + (month - 1) + offset
        return total // 12, total % 12 + 1


class ChatAssistant:
    def __init__(
        self,
        engine: SearchEngine,
        classifier: IntentClassifier,
        extractor: EntityExtractor,
    ) -> None:
        self.engine = engine
        self.classifier = classifier
        self.extractor = extractor

    def handle(self, message: str) -> dict:
        intent, confidence, scores = self.classifier.predict(message)
        entities = self.extractor.extract(message)
        context = {
            "category": entities["category"][0] if entities["category"] else None,
            "destination": entities["destination"][0] if entities["destination"] else None,
            "max_budget": max(entities["budget"]) if entities["budget"] else None,
        }
        suggestions: list[dict] = []
        if intent in {"buscar_paquetes", "reservar_paquete", "recomendar", "presupuesto"}:
            docs = self.engine.search(
                " ".join(chunk for chunk in [message, context["destination"] or ""] if chunk),
                category=context["category"],
                destination=context["destination"],
                max_budget=context["max_budget"],
                limit=4,
            )
            suggestions = [doc.to_dict() for doc in docs]
        rounded_scores = {
            key: round(value, 3)
            for key, value in sorted(scores.items(), key=lambda item: -item[1])
        }
        confidence = round(float(confidence), 3)
        return {
            "intent": intent,
            "confidence": confidence,
            "scores": rounded_scores,
            "entities": entities,
            "context": context,
            "suggestions": suggestions,
            "message": self._reply(intent, suggestions, context),
            "nlp_debug": {
                "intent": intent,
                "confidence": confidence,
                "entities": entities,
                "scores": rounded_scores,
                "model": "TF-IDF + Regresión Logística",
            },
        }

    def _reply(self, intent: str, suggestions: list[dict], context: dict) -> str:
        if intent == "saludo":
            return "¡Hola! Soy tu asistente de reservas. Cuéntame destino, fechas o presupuesto y te sugeriré paquetes para reservar."
        if intent == "despedida":
            return "¡Hasta pronto! Que tengas un gran viaje. Aquí estaré si necesitas algo más."
        if not suggestions:
            return (
                "Aún no encuentro paquetes con esos datos. Refuerza destino, fechas o presupuesto "
                'por ejemplo: "playa en Cancún para dos personas por 1200 €".'
            )
        listing = " | ".join(
            f"{item['title']} ({item['destination']}, desde {item['basePrice']:.0f} €)"
            for item in suggestions[:3]
        )
        if intent == "presupuesto":
            return f"He encontrado {len(suggestions)} opciones dentro de tu presupuesto:\n{listing}"
        if intent == "reservar_paquete":
            first = suggestions[0]
            return (
                f"Claro, te propongo reservar \"{first['title']}\""
                f" (desde {first['basePrice']:.0f} €). Confírmame y tramito la reserva con el servicio central."
            )
        return f"He encontrado {len(suggestions)} opciones que encajan contigo:\n{listing}"


def load_synthetic_samples() -> list[dict]:
    if not SYNTHETIC_PATH.exists():
        return []
    with SYNTHETIC_PATH.open(encoding="utf-8") as handler:
        return json.load(handler)


def build_assistant() -> ChatAssistant:
    from app.services.search_engine import get_search_engine

    engine = get_search_engine()
    classifier = IntentClassifier()
    samples = load_synthetic_samples()
    if samples:
        classifier.fit(
            [sample["message"] for sample in samples], [sample["intent"] for sample in samples]
        )
    return ChatAssistant(engine, classifier, EntityExtractor(engine.docs))
