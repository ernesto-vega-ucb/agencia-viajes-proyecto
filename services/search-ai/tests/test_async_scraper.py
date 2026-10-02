import asyncio
from pathlib import Path

import httpx
import pytest

from app.services.async_scraper import AsyncPackageScraper

FIXTURE_DIR = Path(__file__).resolve().parents[1] / "app" / "data"

PAGES = {
    "https://pkg.test/list?page=1": (FIXTURE_DIR / "mock_booking.html"),
    "https://pkg.test/list?page=2": (FIXTURE_DIR / "mock_booking_2.html"),
}


def _transport(fixtures: dict[str, Path], counter: list[int] | None = None):
    def handler(request: httpx.Request) -> httpx.Response:
        if counter is not None:
            counter.append(request.url)
        path = fixtures.get(str(request.url))
        if path is None:
            return httpx.Response(404, request=request)
        return httpx.Response(200, text=path.read_text(encoding="utf-8"), request=request)

    return httpx.MockTransport(handler)


def test_async_scraper_returns_15_to_20_normalized_records() -> None:
    scraper = AsyncPackageScraper(transport=_transport(PAGES))
    records = asyncio.run(scraper.scrape(list(PAGES), require_range=True))
    assert 15 <= len(records) <= 20
    first = records[0]
    for key in ("source_id", "title", "destination", "price", "currency", "source"):
        assert key in first
    sources = {record["source_id"] for record in records}
    assert len(sources) == len(records)


def test_async_scraper_fetches_pages_concurrently() -> None:
    calls: list[str] = []
    scraper = AsyncPackageScraper(transport=_transport(PAGES, calls), concurrent_limit=2)
    records = asyncio.run(scraper.scrape(list(PAGES)))
    assert len(calls) == len(PAGES)
    assert len(records) == 18


def test_async_scraper_reads_local_fixtures_offline() -> None:
    scraper = AsyncPackageScraper()
    records = asyncio.run(scraper.scrape())
    assert 15 <= len(records) <= 20
    assert asyncio.run(scraper.scrape(require_range=True)) == records


def test_async_scraper_raises_when_range_not_met() -> None:
    single = {"https://pkg.test/only": FIXTURE_DIR / "mock_booking_2.html"}
    scraper = AsyncPackageScraper(transport=_transport(single))
    with pytest.raises(ValueError):
        asyncio.run(scraper.scrape(list(single), require_range=True))
