import asyncio
import uuid
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.services.async_scraper import AsyncPackageScraper
from app.services.fusion import upsert_scraped
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
        inserted, updated = upsert_scraped(db, records, source)
        reset_search_engine()
        self.tasks[task_id] = {
            "status": "done",
            "detail": f"{inserted} nuevos, {updated} actualizados de {len(records)} extraídos",
        }

    def _fail(self, db: Session, task_id: str, exc: Exception) -> None:
        db.rollback()
        self.tasks[task_id] = {"status": "error", "detail": str(exc)}
