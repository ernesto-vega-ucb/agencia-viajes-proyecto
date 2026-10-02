import re
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

from app.services.text_prep import CATEGORY_SYNONYMS, normalize_es

DEFAULT_FIXTURE = Path(__file__).resolve().parents[1] / "data" / "mock_booking.html"
FIXTURE_GLOB = "mock_booking*.html"

DESTINATION_COUNTRIES = {
    "cancun": "México",
    "marrakech": "Marruecos",
    "serengeti": "Tanzania",
    "costa brava": "España",
    "barcelona": "España",
    "paris": "Francia",
    "roma": "Italia",
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
    "san sebastian": "España",
}

DURATION_RE = re.compile(r"(?i)(\d{1,2})\s*(?:dias|días|noches)")


class PackageScraper:
    """
    Extractor de paquetes turísticos desde HTML estilo Booking.com.

    Por defecto lee el fixture local (sin red). Pasa una URL http(s) para
    scrapear fuentes externas en producción. Normaliza cada resultado a la
    estructura común usada por el motor de recomendación.
    """

    def scrape(self, source: str | None = None) -> list[dict]:
        html = self._fetch_html(source)
        return [self.normalize(raw, index) for index, raw in enumerate(self._parse(html))]

    def scrape_all(self) -> list[dict]:
        fixture_dir = DEFAULT_FIXTURE.parent
        files = sorted(fixture_dir.glob(FIXTURE_GLOB))
        if not files:
            raise FileNotFoundError("No hay fixtures de scraping locales")
        records: list[dict] = []
        for path in files:
            raw_items = self._parse(path.read_text(encoding="utf-8"))
            records.extend(self.normalize(raw, index) for index, raw in enumerate(raw_items))
        return records

    @staticmethod
    def normalize(raw: dict, index: int) -> dict:
        title = raw.get("title") or ""
        destination = raw.get("destination") or title
        region = raw.get("region") or ""
        normalized = dict(raw)
        normalized["destination"] = destination.strip() or None
        normalized["country"] = PackageScraper._country_for(destination, region)
        normalized["category"] = PackageScraper._category_for(f"{title} {destination}")
        normalized["durationDays"] = PackageScraper._duration_of(f"{title} {destination}")
        normalized["rating"] = 4.0
        normalized["description"] = f"{title} en {destination}".strip()
        normalized["source"] = "external"
        if normalized["destination"] is None:
            normalized["destination"] = title
        return normalized

    def _fetch_html(self, source: str | None) -> str:
        if not source:
            if not DEFAULT_FIXTURE.exists():
                raise FileNotFoundError("Fixture de scraping no encontrado")
            return DEFAULT_FIXTURE.read_text(encoding="utf-8")

        if source.startswith(("http://", "https://")):
            with httpx.Client(timeout=15.0, follow_redirects=True) as client:
                response = client.get(
                    source,
                    headers={"User-Agent": "agencia-search-ai/0.2"},
                )
                response.raise_for_status()
                return response.text

        path = Path(source)
        if not path.exists():
            raise FileNotFoundError(f"Archivo fuente no encontrado: {source}")
        return path.read_text(encoding="utf-8")

    def _parse(self, html: str) -> list[dict]:
        soup = BeautifulSoup(html, "html.parser")
        packages: list[dict] = []

        for card in soup.select(".sr_item"):
            name_el = card.select_one(".sr-hotel__name")
            destination_el = card.select_one(".sr_card_address_line")
            region_el = card.select_one(".sr_card_address_region")
            price_el = card.select_one(
                ".bui-price-display__value, .availprice, .prco-valign-middle-helper"
            )
            link_el = card.select_one("a.hotel_name_link_url, a[href*='hotel']")
            source_id_el = card.select_one(".hotel_id, [data-hotelid]")

            title = name_el.get_text(strip=True) if name_el else "Sin título"
            if not title:
                continue

            packages.append(
                {
                    "source_id": (
                        source_id_el["data-hotelid"]
                        if source_id_el and source_id_el.has_attr("data-hotelid")
                        else link_el.get("href")
                        if link_el
                        else None
                    ),
                    "title": title,
                    "destination": (destination_el.get_text(strip=True) if destination_el else ""),
                    "region": (region_el.get_text(strip=True) if region_el else ""),
                    "price": self._parse_price(price_el.get_text(strip=True)) if price_el else None,
                    "currency": "EUR",
                    "url": link_el.get("href") if link_el else None,
                }
            )
        return packages

    @staticmethod
    def _parse_price(text: str) -> float | None:
        cleaned = text.replace(".", "").replace(",", ".")
        match = re.search(r"\d+(?:\.\d+)?", cleaned)
        if not match:
            return None
        try:
            return float(match.group(0))
        except ValueError:
            return None

    @staticmethod
    def _country_for(destination: str, region: str = "") -> str | None:
        key = normalize_es(destination, keep_stopwords=True)
        for name, country in DESTINATION_COUNTRIES.items():
            if name == key or name in key or key in name:
                return country
        region_tail = region.rsplit(",", 1)[-1].strip()
        if region_tail:
            return region_tail
        return None

    @staticmethod
    def _category_for(text: str) -> str | None:
        normalized = normalize_es(text, keep_stopwords=True)
        for category, synonyms in CATEGORY_SYNONYMS.items():
            if any(synonym in normalized for synonym in synonyms):
                return category
        return None

    @staticmethod
    def _duration_of(text: str) -> int:
        match = DURATION_RE.search(text)
        if match:
            return int(match.group(1))
        return 5
