import asyncio

import httpx

from app.services.scraper import DEFAULT_FIXTURE, FIXTURE_GLOB, PackageScraper

DEFAULT_MIN_RECORDS = 15
DEFAULT_MAX_RECORDS = 20


class AsyncPackageScraper:
    """
    Extractor asíncrono de paquetes turísticos externos.

    Descarga varias páginas con `httpx.AsyncClient` de forma concurrente no
    bloqueante (semáforo de límite), parsea el HTML con BeautifulSoup en un
    hilo de trabajo y normaliza cada resultado a la estructura común. Si no se
    pasan URLs, lee los fixtures locales (modo demo sin red), acumulando todas
    las páginas (mock_booking*.html).
    """

    def __init__(
        self,
        concurrent_limit: int = 8,
        timeout: float = 15.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._concurrent_limit = concurrent_limit
        self._timeout = timeout
        self._transport = transport
        self._parser = PackageScraper()

    async def scrape(
        self,
        urls: list[str] | None = None,
        *,
        require_range: bool = False,
    ) -> list[dict]:
        pages = await self._fetch_pages(urls)
        records: list[dict] = []
        for html in pages:
            raw_items = await asyncio.to_thread(self._parser._parse, html)
            records.extend(
                PackageScraper.normalize(raw, index) for index, raw in enumerate(raw_items)
            )
        records = records[:DEFAULT_MAX_RECORDS]
        if require_range and not (DEFAULT_MIN_RECORDS <= len(records) <= DEFAULT_MAX_RECORDS):
            raise ValueError(
                f"Se esperaban entre {DEFAULT_MIN_RECORDS} y {DEFAULT_MAX_RECORDS} "
                f"registros, se obtuvieron {len(records)}"
            )
        return records

    async def _fetch_pages(self, urls: list[str] | None) -> list[str]:
        if urls:
            return await self._fetch_remote(urls)
        return await asyncio.to_thread(self._read_local_fixtures)

    async def _fetch_remote(self, urls: list[str]) -> list[str]:
        semaphore = asyncio.Semaphore(self._concurrent_limit)

        async def fetch(client: httpx.AsyncClient, url: str) -> str:
            async with semaphore:
                response = await client.get(
                    url,
                    headers={"User-Agent": "agencia-search-ai/0.3"},
                )
                response.raise_for_status()
                return response.text

        async with httpx.AsyncClient(
            timeout=self._timeout,
            follow_redirects=True,
            transport=self._transport,
        ) as client:
            return await asyncio.gather(*(fetch(client, url) for url in urls))

    @staticmethod
    def _read_local_fixtures() -> list[str]:
        fixture_dir = DEFAULT_FIXTURE.parent
        files = sorted(fixture_dir.glob(FIXTURE_GLOB))
        if not files:
            raise FileNotFoundError("No se encontraron fixtures de scraping locales")
        return [path.read_text(encoding="utf-8") for path in files]
