import time

import httpx

from app.config import get_settings
from app.services.synthetic import load_synthetic_packages
from app.services.text_prep import normalize_es

BASE_CATALOG = [
    {
        "id": 1,
        "code": "PVP-CUN-001",
        "title": "Todo incluido en la Riviera Maya",
        "destination": "Cancún",
        "country": "México",
        "description": "7 días todo incluido en hotel 5 estrellas frente al Caribe, tours a Tulum y snorkel.",
        "category": "playa",
        "durationDays": 7,
        "basePrice": 1250.0,
        "currency": "EUR",
        "rating": 4.8,
        "startDates": [],
        "images": [],
        "maxTravelers": 4,
        "cancelDaysBefore": 14,
        "cancelRefundPercent": 100,
        "active": True,
    },
    {
        "id": 2,
        "code": "PVP-LIS-001",
        "title": "Escapada urbana a Lisboa",
        "destination": "Lisboa",
        "country": "Portugal",
        "description": "Fin de semana en Lisboa: city tour, fado y degustación de vinos.",
        "category": "ciudad",
        "durationDays": 3,
        "basePrice": 420.0,
        "currency": "EUR",
        "rating": 4.6,
        "startDates": [],
        "images": [],
        "maxTravelers": 6,
        "cancelDaysBefore": 7,
        "cancelRefundPercent": 50,
        "active": True,
    },
    {
        "id": 3,
        "code": "PVP-AND-001",
        "title": "Aventura en los Andes",
        "destination": "Cusco",
        "country": "Perú",
        "description": "Trekking a Machu Picchu con guías certificados y camping.",
        "category": "aventura",
        "durationDays": 6,
        "basePrice": 980.0,
        "currency": "EUR",
        "rating": 4.9,
        "startDates": [],
        "images": [],
        "maxTravelers": 8,
        "cancelDaysBefore": 21,
        "cancelRefundPercent": 100,
        "active": True,
    },
    {
        "id": 4,
        "code": "PVP-BCN-001",
        "title": "Costa Brava en familia",
        "destination": "Costa Brava",
        "country": "España",
        "description": "Semana en la Costa Brava con actividades familiares y media pensión.",
        "category": "familiar",
        "durationDays": 7,
        "basePrice": 780.0,
        "currency": "EUR",
        "rating": 4.4,
        "startDates": [],
        "images": [],
        "maxTravelers": 6,
        "cancelDaysBefore": 10,
        "cancelRefundPercent": 75,
        "active": True,
    },
]


def _to_catalog_payload(package: dict, package_id: int) -> dict:
    return {
        "id": int(package.get("id", package_id)),
        "code": package["code"],
        "title": package["title"],
        "destination": package["destination"],
        "country": package["country"],
        "description": package["description"],
        "category": package["category"],
        "durationDays": package["durationDays"],
        "basePrice": package["basePrice"],
        "currency": package["currency"],
        "rating": package["rating"],
        "startDates": package.get("startDates", []),
        "images": [],
        "maxTravelers": 8,
        "cancelDaysBefore": 15,
        "cancelRefundPercent": 100,
        "active": True,
    }


class CatalogClient:
    def __init__(self) -> None:
        self._catalog: list[dict] = []
        self._last_fetch: float = 0.0

    def packages(self, force: bool = False) -> list[dict]:
        settings = get_settings()
        if (
            not force
            and self._catalog
            and time.time() - self._last_fetch < settings.catalog_cache_ttl_seconds
        ):
            return self._catalog

        try:
            with httpx.Client(timeout=5.0) as client:
                for attempt in range(3):
                    try:
                        response = client.get(settings.packages_endpoint)
                        response.raise_for_status()
                        self._catalog = response.json()
                        self._last_fetch = time.time()
                        return self._catalog
                    except httpx.HTTPError:
                        if attempt == 2:
                            raise
                        time.sleep(1.0)
        except httpx.HTTPError:
            self._catalog = self._fallback_catalog()
            self._last_fetch = time.time()

        return self._catalog

    def refresh(self) -> None:
        self.packages(force=True)

    @staticmethod
    def _fallback_catalog() -> list[dict]:
        merged = [dict(package) for package in BASE_CATALOG]
        seen = {normalize_es(package["destination"]) for package in merged}
        for index, package in enumerate(load_synthetic_packages(), start=len(BASE_CATALOG) + 1):
            key = normalize_es(package["destination"])
            if key in seen:
                continue
            seen.add(key)
            merged.append(_to_catalog_payload(package, index))
        return merged
