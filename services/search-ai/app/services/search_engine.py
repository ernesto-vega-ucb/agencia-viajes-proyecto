from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from datetime import date, timedelta

import numpy as np

from app.db import SessionLocal
from app.models import ScrapedPackage
from app.services.catalog import CatalogClient
from app.services.embeddings import EmbeddingsProvider
from app.services.scraper import PackageScraper
from app.services.synthetic import load_synthetic_packages
from app.services.text_prep import CATEGORY_SYNONYMS, normalize_es

_DURATION_RE = re.compile(r"(?i)(\d{1,2})\s*(?:dias|días|noches)")
_EXT_CODE_RE = re.compile(r"(?i)EXT[-_]?(\d+)")

_COUNTRY_BY_DESTINATION = {
    "cancun": "México",
    "lisboa": "Portugal",
    "cusco": "Perú",
    "costa brava": "España",
    "marrakech": "Marruecos",
    "serengeti": "Tanzania",
    "barcelona": "España",
    "paris": "Francia",
    "roma": "Italia",
    "cartagena de indias": "Colombia",
    "cartagena": "Colombia",
    "rio de janeiro": "Brasil",
    "tokio": "Japón",
    "praga": "Chequia",
    "dubai": "Emiratos Árabes",
    "venecia": "Italia",
    "atenas": "Grecia",
    "nueva york": "Estados Unidos",
    "bangkok": "Tailandia",
    "malta": "Malta",
    "la valeta": "Malta",
    "san sebastian": "España",
}


@dataclass
class PackageDoc:
    id: int
    code: str
    title: str
    destination: str
    country: str
    description: str
    category: str
    durationDays: int
    basePrice: float
    currency: str
    rating: float
    source: str
    text: str
    startDates: list[str] = field(default_factory=list)
    images: list[str] = field(default_factory=list)
    maxTravelers: int = 8
    cancelDaysBefore: int = 15
    cancelRefundPercent: int = 100
    active: bool = True

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "code": self.code,
            "title": self.title,
            "destination": self.destination,
            "country": self.country,
            "description": self.description,
            "category": self.category,
            "durationDays": self.durationDays,
            "basePrice": self.basePrice,
            "currency": self.currency,
            "rating": self.rating,
            "source": self.source,
            "startDates": list(self.startDates),
            "images": list(self.images),
            "maxTravelers": self.maxTravelers,
            "cancelDaysBefore": self.cancelDaysBefore,
            "cancelRefundPercent": self.cancelRefundPercent,
            "active": self.active,
        }


class SearchEngine:
    """
    Motor de búsqueda y recomendación sobre el dataset fusionado de tres
    fuentes normalizadas: catálogo interno (booking-core), paquetes sintéticos
    y paquetes externos scrapeados; con embeddings y filtros estructurados
    (precio, destino, categoría).
    """

    def __init__(
        self,
        catalog: CatalogClient,
        embeddings: EmbeddingsProvider,
        scraped: list[dict] | None = None,
        synthetic: list[dict] | None = None,
    ) -> None:
        self._catalog = catalog
        self.embeddings = embeddings
        docs = self._merge_documents(scraped, synthetic)
        self.docs = docs
        self._docs_by_id = {doc.id: doc for doc in docs}
        self._docs_by_code = {doc.code: doc for doc in docs}
        embeddings.fit([doc.text for doc in docs])
        self._matrix = embeddings.embed([doc.text for doc in docs])
        self._popular_ids = [doc.id for doc in sorted(docs, key=lambda d: d.rating, reverse=True)]

    @property
    def ml_enabled(self) -> bool:
        return self.embeddings.ml_enabled

    def search(
        self,
        query: str,
        *,
        category: str | list[str] | None = None,
        destination: str | None = None,
        max_budget: float | None = None,
        limit: int = 5,
        return_scores: bool = False,
    ) -> list[PackageDoc] | list[tuple[PackageDoc, float]]:
        categories = _as_list(category)
        indices = [
            index
            for index, doc in enumerate(self.docs)
            if self._matches(doc, categories, destination, max_budget)
        ]
        if not indices:
            return [] if not return_scores else []

        query_vector = self.embeddings.embed_one(query)
        scores = self._matrix[indices] @ query_vector
        ranked = sorted(zip(indices, scores, strict=True), key=lambda pair: pair[1], reverse=True)
        ranked = ranked[:limit]

        if return_scores:
            return [(self.docs[index], float(score)) for index, score in ranked]
        return [self.docs[index] for index, _ in ranked]

    def search_multi(self, queries: list[str], limit: int = 5) -> list[PackageDoc]:
        if not queries:
            return self.popular(limit)
        vectors = np.mean(self.embeddings.embed(queries), axis=0)
        scores = self._matrix @ vectors
        return [self.docs[index] for index in np.argsort(scores)[::-1][:limit]]

    def doc(self, doc_id: int) -> PackageDoc | None:
        return self._docs_by_id.get(doc_id)

    def doc_by_code(self, code: str) -> PackageDoc | None:
        return self._docs_by_code.get(code)

    def popular(self, limit: int = 5) -> list[PackageDoc]:
        return [self._docs_by_id[doc_id] for doc_id in self._popular_ids[:limit]]

    def destinations(self) -> list[str]:
        seen: list[str] = []
        for doc in self.docs:
            if doc.destination and doc.destination not in seen:
                seen.append(doc.destination)
        return seen

    def _matches(
        self,
        doc: PackageDoc,
        categories: list[str],
        destination: str | None,
        max_budget: float | None,
    ) -> bool:
        if categories and doc.category not in categories:
            return False
        if destination and normalize_es(destination) not in normalize_es(doc.destination):
            return False
        if max_budget is not None and doc.basePrice > max_budget:
            return False
        return True

    def _merge_documents(
        self,
        scraped: list[dict] | None,
        synthetic: list[dict] | None,
    ) -> list[PackageDoc]:
        docs = [self._from_catalog(package) for package in self._catalog.packages()]
        seen_destinations = {normalize_es(doc.destination) for doc in docs}
        seen_codes = {doc.code for doc in docs}
        seen_titles = {normalize_es(doc.title) for doc in docs}

        synthetic = load_synthetic_packages() if synthetic is None else synthetic
        for index, item in enumerate(synthetic):
            destination = item.get("destination") or item.get("title", "")
            key = normalize_es(destination)
            if not key or key in seen_destinations:
                continue
            seen_destinations.add(key)
            docs.append(self._from_synthetic(index, item))

        scraped = self._default_scraped() if scraped is None else scraped
        for index, item in enumerate(scraped):
            if not item.get("title") or item.get("price") is None:
                continue
            code = _scraped_code(item)
            if code and code in seen_codes:
                continue
            title = normalize_es(item["title"])
            if title and title in seen_titles:
                continue
            destination = item.get("destination") or item["title"]
            key = normalize_es(destination)
            if key in seen_destinations:
                continue
            seen_destinations.add(key)
            seen_titles.add(title)
            if code:
                seen_codes.add(code)
            docs.append(self._from_scraped(index, item))
        return docs

    def _default_scraped(self) -> list[dict]:
        records = self._db_scraped_records()
        if records:
            return records
        try:
            return PackageScraper().scrape_all()
        except FileNotFoundError:
            return []

    def _db_scraped_records(self) -> list[dict]:
        try:
            rows = SessionLocal().query(ScrapedPackage).all()
        except Exception:  # noqa: BLE001 (BD temporal no disponible)
            return []
        return [
            {
                "db_id": row.id,
                "source_id": row.source_id,
                "title": row.title,
                "destination": row.destination or row.title,
                "price": row.price,
                "currency": row.currency or "EUR",
                "url": row.url,
            }
            for row in rows
        ]

    def _from_synthetic(self, index: int, item: dict) -> PackageDoc:
        fields = {
            "id": int(item.get("id", 8000 + index)),
            "code": item.get("code", f"SYN-{index + 1:03d}"),
            "title": item.get("title", "Sin título"),
            "destination": item.get("destination", ""),
            "country": item.get("country", ""),
            "description": item.get("description", ""),
            "category": item.get("category") or "otros",
            "durationDays": int(item.get("durationDays", 5)),
            "basePrice": float(item.get("basePrice", 0.0)),
            "currency": item.get("currency", "EUR"),
            "rating": float(item.get("rating", 4.0)),
            "startDates": item.get("startDates") or _default_start_dates(),
            "images": item.get("images", []),
            "maxTravelers": int(item.get("maxTravelers", 8)),
            "cancelDaysBefore": int(item.get("cancelDaysBefore", 15)),
            "cancelRefundPercent": int(item.get("cancelRefundPercent", 100)),
        }
        return self._build_doc(source="sintetico", **fields)

    def _from_catalog(self, package: dict) -> PackageDoc:
        upstream = str(package.get("source", "")).upper()
        source = {"SCRAPED": "external", "SINTETICO": "sintetico"}.get(upstream, "catalogo")
        fields = {
            "id": int(package.get("id", 0)),
            "code": package.get("code", f"INT-{package.get('id', 0):03d}"),
            "title": package.get("title", "Sin título"),
            "destination": package.get("destination", ""),
            "country": package.get("country", ""),
            "description": package.get("description", ""),
            "category": package.get("category", ""),
            "durationDays": int(package.get("durationDays", 5)),
            "basePrice": float(package.get("basePrice", 0.0)),
            "currency": package.get("currency", "EUR"),
            "rating": float(package.get("rating", 4.0)),
            "startDates": package.get("startDates") or _default_start_dates(),
            "images": package.get("images", []),
            "maxTravelers": int(package.get("maxTravelers", 8)),
            "cancelDaysBefore": int(package.get("cancelDaysBefore", 15)),
            "cancelRefundPercent": int(package.get("cancelRefundPercent", 100)),
            "active": bool(package.get("active", True)),
        }
        return self._build_doc(source=source, **fields)

    def _from_scraped(self, index: int, item: dict) -> PackageDoc:
        destination = item.get("destination") or item["title"]
        duration = _duration(item.get("title", "") + " " + destination)
        code = _scraped_code(item)
        if code is None and item.get("db_id"):
            code = f"EXT-{int(item['db_id']):03d}"
        if code is None:
            code = f"EXT-{index + 1:03d}"
        ext_number = _ext_number(code)
        stable_id = 9000 + ext_number if ext_number is not None else 9000 + index
        fields = {
            "id": stable_id,
            "code": code,
            "title": item.get("title", "Sin título"),
            "destination": destination,
            "country": item.get("country")
            or _COUNTRY_BY_DESTINATION.get(normalize_es(destination), ""),
            "description": f"{item.get('title', '')} en {destination}",
            "category": item.get("category") or _category(destination) or "otros",
            "durationDays": duration,
            "basePrice": float(item["price"]),
            "currency": item.get("currency", "EUR"),
            "rating": float(item.get("rating", 4.0)),
            "startDates": _default_start_dates(),
            "images": [],
        }
        return self._build_doc(source="external", **fields)

    @staticmethod
    def _build_doc(
        *,
        id: int,
        code: str,
        title: str,
        destination: str,
        country: str,
        description: str,
        category: str,
        durationDays: int,
        basePrice: float,
        currency: str,
        rating: float,
        source: str,
        startDates: list[str] | None = None,
        images: list[str] | None = None,
        maxTravelers: int = 8,
        cancelDaysBefore: int = 15,
        cancelRefundPercent: int = 100,
        active: bool = True,
    ) -> PackageDoc:
        text = normalize_es(
            " ".join(
                [
                    title or "",
                    destination or "",
                    country or "",
                    category or "",
                    description or "",
                ]
            ),
            keep_stopwords=True,
        )
        return PackageDoc(
            id=id,
            code=code,
            title=title,
            destination=destination,
            country=country,
            description=description,
            category=category,
            durationDays=durationDays,
            basePrice=basePrice,
            currency=currency,
            rating=rating,
            source=source,
            text=text,
            startDates=startDates or [],
            images=images or [],
            maxTravelers=maxTravelers,
            cancelDaysBefore=cancelDaysBefore,
            cancelRefundPercent=cancelRefundPercent,
            active=active,
        )


def _as_list(value: str | list[str] | None) -> list[str]:
    if value is None:
        return []
    return [value] if isinstance(value, str) else list(value)


def _default_start_dates(count: int = 4) -> list[str]:
    today = date.today()
    offset = (5 - today.weekday()) % 7
    return [(today + timedelta(days=offset + step * 7)).isoformat() for step in range(count)]


def _category(text: str) -> str | None:
    normalized = normalize_es(text, keep_stopwords=True)
    for category, synonyms in CATEGORY_SYNONYMS.items():
        if any(synonym in normalized for synonym in synonyms):
            return category
    return None


def _duration(text: str) -> int:
    match = _DURATION_RE.search(text)
    if match:
        return int(match.group(1))
    if "fin de semana" in normalize_es(text, keep_stopwords=True):
        return 2
    return 5


def _scraped_code(item: dict) -> str | None:
    match = _EXT_CODE_RE.search(item.get("source_id") or "")
    if match:
        return f"EXT-{int(match.group(1)):03d}"
    return None


def _ext_number(code: str | None) -> int | None:
    if not code:
        return None
    match = _EXT_CODE_RE.search(code)
    if not match:
        return None
    return int(match.group(1))


_ENGINE_CACHE: tuple[SearchEngine, float] | None = None
_TTL = 60.0


def get_search_engine(force: bool = False) -> SearchEngine:
    global _ENGINE_CACHE
    if _ENGINE_CACHE is None or force or time.time() - _ENGINE_CACHE[1] > _TTL:
        _ENGINE_CACHE = (SearchEngine(CatalogClient(), EmbeddingsProvider()), time.time())
    return _ENGINE_CACHE[0]


def reset_search_engine() -> None:
    global _ENGINE_CACHE
    _ENGINE_CACHE = None
