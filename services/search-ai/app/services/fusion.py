"""
Fusión del dataset unificado: scraping asíncrono + persistencia en la BD
temporal del servicio (scraped_package) + reconstrucción del índice.

El arranque del servicio (lifespan) y el endpoint POST /api/v1/scrape/refresh
invocan refresh_scraped_packages() para mantener el buscador indexando los
paquetes externos dinámicos junto a los locales y sintéticos.
"""

from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import SessionLocal
from app.models import ScrapedPackage
from app.services.async_scraper import AsyncPackageScraper
from app.services.search_engine import reset_search_engine


def _persist(db: Session, records: list[dict], source: str) -> int:
    count = 0
    for package in records:
        existing = (
            db.query(ScrapedPackage)
            .filter(ScrapedPackage.source_id == package["source_id"])
            .first()
        )
        if not package["source_id"] or not existing:
            db.add(
                ScrapedPackage(
                    source=source,
                    source_id=str(package["source_id"])[:128] if package["source_id"] else None,
                    title=package["title"][:512],
                    destination=package["destination"][:256] if package["destination"] else None,
                    price=package["price"],
                    currency=package["currency"],
                    url=package["url"],
                )
            )
            count += 1
    db.commit()
    return count


async def refresh_scraped_packages() -> dict:
    settings = get_settings()
    records = await AsyncPackageScraper().scrape(settings.scrape_url_list or None)
    try:
        db = SessionLocal()
        try:
            new = _persist(db, records, source="async" if settings.scrape_url_list else "fixtures")
        finally:
            db.close()
    except Exception:  # noqa: BLE001 (BD temporal no disponible -> memoria)
        new = 0
    reset_search_engine()
    return {
        "funcion": "refresh_scraped_packages",
        "extraidos": len(records),
        "nuevos_guardados": new,
        "fuente": "async" if settings.scrape_url_list else "fixtures",
    }
