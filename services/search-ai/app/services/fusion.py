"""
Fusión del dataset unificado: scraping asíncrono + persistencia en la BD
temporal del servicio (scraped_package) + reconstrucción del índice.

El arranque del servicio (lifespan) y el endpoint POST /api/v1/scrape/refresh
invocan refresh_scraped_packages() para mantener el buscador indexando los
paquetes externos dinámicos junto a los locales y sintéticos.
"""

from datetime import datetime

from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import SessionLocal
from app.models import ScrapedPackage
from app.services.async_scraper import AsyncPackageScraper
from app.services.search_engine import reset_search_engine


def upsert_scraped(db: Session, records: list[dict], source: str) -> tuple[int, int]:
    inserted = updated = 0
    for package in records:
        source_id = str(package["source_id"])[:128] if package["source_id"] else None
        if not source_id:
            continue
        values = {
            "source": source,
            "title": package["title"][:512],
            "destination": package["destination"][:256] if package["destination"] else None,
            "price": package["price"],
            "currency": package["currency"],
            "url": package["url"],
        }
        existing = db.query(ScrapedPackage).filter(ScrapedPackage.source_id == source_id).first()
        if existing is not None:
            for key, value in values.items():
                setattr(existing, key, value)
            existing.scraped_at = datetime.utcnow()
            updated += 1
        else:
            db.add(ScrapedPackage(scraped_at=datetime.utcnow(), source_id=source_id, **values))
            inserted += 1
    db.commit()
    return inserted, updated


async def refresh_scraped_packages() -> dict:
    settings = get_settings()
    records = await AsyncPackageScraper().scrape(settings.scrape_url_list or None)
    source = "async" if settings.scrape_url_list else "fixtures"
    try:
        db = SessionLocal()
        try:
            inserted, updated = upsert_scraped(db, records, source)
        finally:
            db.close()
    except Exception:  # noqa: BLE001 (BD temporal no disponible -> memoria)
        inserted = updated = 0
    reset_search_engine()
    return {
        "funcion": "refresh_scraped_packages",
        "extraidos": len(records),
        "nuevos_guardados": inserted,
        "actualizados": updated,
        "fuente": source,
    }