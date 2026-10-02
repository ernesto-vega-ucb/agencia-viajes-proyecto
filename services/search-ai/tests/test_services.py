from app.services.catalog import CatalogClient
from app.services.nlp import NlpService
from app.services.scraper import PackageScraper


def test_scraper_fixture_returns_packages() -> None:
    scraper = PackageScraper()
    packages = scraper.scrape(source=None)
    assert len(packages) >= 4
    first = packages[0]
    assert first["title"]
    assert first["price"] is not None
    assert first["source_id"]


def _catalog_no_network(monkeypatch):
    monkeypatch.setattr(CatalogClient, "packages", lambda self, force=False: [
        {
            "id": 1,
            "code": "PVP-CUN-001",
            "title": "Todo incluido en la Riviera Maya",
            "destination": "Cancún",
            "country": "México",
            "description": "playa y caribe todo incluido",
            "category": "playa",
            "durationDays": 7,
            "basePrice": 1250.0,
            "currency": "EUR",
            "rating": 4.8,
        },
        {
            "id": 2,
            "code": "PVP-LIS-001",
            "title": "Escapada urbana a Lisboa",
            "destination": "Lisboa",
            "country": "Portugal",
            "description": "cultura y ciudad",
            "category": "ciudad",
            "durationDays": 3,
            "basePrice": 420.0,
            "currency": "EUR",
            "rating": 4.6,
        },
    ])
    return NlpService(CatalogClient())


def test_nlp_analyze_detects_category(monkeypatch) -> None:
    nlp = _catalog_no_network(monkeypatch)
    analysis = nlp.analyze("quiero una playa en el caribe")
    assert "playa" in analysis.categories


def test_nlp_rank_returns_relevant_first(monkeypatch) -> None:
    nlp = _catalog_no_network(monkeypatch)
    ranked = nlp.rank("caribe playa")
    assert ranked
    assert ranked[0]["id"] == 1


def test_nlp_normalize_strips_accents(monkeypatch) -> None:
    nlp = _catalog_no_network(monkeypatch)
    assert nlp._normalize("Isla Cántabría Ñandú") == "isla cantabria nandu"