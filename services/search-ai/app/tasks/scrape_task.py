import asyncio
import uuid
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.models import ScrapedPackage
from app.services.async_scraper import AsyncPackageScraper
from app.services.scraper import PackageScraper
from app.services.search_engine import reset_search_engine


@dataclass
class TaskRegistry:
    scraper: PackageScraper
    async_scraper: AsyncPackageScraper = field(default_factory=AsyncPackageScraper)
    tasks: dict[str, dict] = field(default_factory=dict)

    def start(self, source: str | None) -> str:
        task_id = str(uuid.uuid4())[:8]
        self.tasks[task_id] = {"status": "running", "detail": "scraping en curso"}
        return task_id

    def get(self, task_id: str) -> dict | None:
        return self.tasks.get(task_id)

    def run(self, db: Session, task_id: str, source: str | None) -> None:
        try:
            records = self.scraper.scrape(source)
            self._finish(db, task_id, records, source=source or "fixture")
        except Exception as exc:  # noqa: BLE001
            self._fail(db, task_id, exc)

    def run_async(self, db: Session, task_id: str, urls: list[str] | None) -> None:
        try:
            records = asyncio.run(self.async_scraper.scrape(urls))
            self._finish(db, task_id, records, source="async" if urls else "fixtures")
        except Exception as exc:  # noqa: BLE001
            self._fail(db, task_id, exc)

    def _finish(self, db: Session, task_id: str, records: list[dict], source: str) -> None:
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
                        destination=package["destination"][:256]
                        if package["destination"]
                        else None,
                        price=package["price"],
                        currency=package["currency"],
                        url=package["url"],
                    )
                )
                count += 1
        db.commit()
        reset_search_engine()
        self.tasks[task_id] = {
            "status": "done",
            "detail": f"{count} paquetes nuevos guardados de {len(records)} extraídos",
        }

    def _fail(self, db: Session, task_id: str, exc: Exception) -> None:
        db.rollback()
        self.tasks[task_id] = {"status": "error", "detail": str(exc)}
