import httpx

from app.config import get_settings

_FALLBACK_COUNTRY = "Internacional"


def _sync_source(doc_source: str) -> str:
    if doc_source == "sintetico":
        return "SINTETICO"
    if doc_source == "external":
        return "SCRAPED"
    return "MANUAL"


def build_sync_payload(doc) -> dict:
    payload = doc.to_dict()
    payload["source"] = _sync_source(doc.source)
    if not payload.get("country"):
        payload["country"] = _FALLBACK_COUNTRY
    return payload


def sync_package(doc) -> dict:
    settings = get_settings()
    payload = build_sync_payload(doc)
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(
                f"{settings.booking_core_url}/packages/sync",
                json=payload,
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError:
        return payload