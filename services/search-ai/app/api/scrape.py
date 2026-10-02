import asyncio

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import ScrapedPackage
from app.schemas import ScrapeRequest, ScrapeTaskOut, ScrapedPackageOut
from app.services.async_scraper import AsyncPackageScraper
from app.services.fusion import refresh_scraped_packages
from app.services.scraper import PackageScraper
from app.tasks.scrape_task import TaskRegistry

router = APIRouter(prefix="/api/v1/scrape", tags=["scraping"])

_registry = TaskRegistry(scraper=PackageScraper(), async_scraper=AsyncPackageScraper())


@router.post("/run", response_model=ScrapeTaskOut, status_code=202)
async def run_scrape(
    payload: ScrapeRequest,
    db: Session = Depends(get_db),
) -> ScrapeTaskOut:
    task_id = _registry.start(payload.source)

    def background() -> None:
        _registry.run(db, task_id, payload.source)

    asyncio.create_task(asyncio.to_thread(background))

    return ScrapeTaskOut(
        task_id=task_id,
        status="running",
        detail="tarea de scraping programada",
    )


@router.post("/run-async", response_model=ScrapeTaskOut, status_code=202)
async def run_scrape_async(
    payload: ScrapeRequest,
    db: Session = Depends(get_db),
) -> ScrapeTaskOut:
    task_id = _registry.start(payload.source or ",".join(payload.urls or []))

    def background() -> None:
        _registry.run_async(db, task_id, payload.urls)

    asyncio.create_task(asyncio.to_thread(background))

    return ScrapeTaskOut(
        task_id=task_id,
        status="running",
        detail="worker asíncrono de scraping programado",
    )


@router.post("/refresh")
async def refresh_index() -> dict:
    summary = await refresh_scraped_packages()
    return {
        "status": "ok",
        "indice_reconstruido": True,
        **summary,
    }


@router.get("/tasks/{task_id}", response_model=ScrapeTaskOut)
def scrape_status(task_id: str) -> ScrapeTaskOut:
    task = _registry.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    return ScrapeTaskOut(task_id=task_id, status=task["status"], detail=task["detail"])


@router.get("/packages", response_model=list[ScrapedPackageOut])
def list_scraped_packages(
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[ScrapedPackage]:
    return list(
        db.scalars(select(ScrapedPackage).order_by(ScrapedPackage.scraped_at.desc()).limit(limit))
    )
