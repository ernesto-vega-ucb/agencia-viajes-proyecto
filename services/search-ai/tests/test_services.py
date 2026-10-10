from app.services.catalog import CatalogClient
from app.services.embeddings import EmbeddingsProvider
from app.services.nlp import NlpService
from app.services.scraper import PackageScraper
from app.services.search_engine import SearchEngine


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


class _SourceCatalog(CatalogClient):
    def packages(self, force: bool = False) -> list[dict]:
        return [
            {
                "id": 1,
                "code": "SYN-001",
                "title": "Atardecer en Seychelles",
                "destination": "Seychelles",
                "country": "Seychelles",
                "description": "playa paradisiaca",
                "category": "playa",
                "durationDays": 7,
                "basePrice": 2450.0,
                "currency": "EUR",
                "rating": 4.7,
                "source": "SINTETICO",
            },
            {
                "id": 2,
                "code": "EXT-003",
                "title": "Hotel Diagonal Mar",
                "destination": "Roma",
                "country": "Italia",
                "description": "ciudad histórica",
                "category": "ciudad",
                "durationDays": 5,
                "basePrice": 495.0,
                "currency": "EUR",
                "rating": 4.3,
                "source": "SCRAPED",
            },
        ]


def test_engine_preserves_catalog_source_field() -> None:
    engine = SearchEngine(_SourceCatalog(), EmbeddingsProvider())
    by_code = {doc.code: doc for doc in engine.docs}
    assert by_code["SYN-001"].source == "sintetico"
    assert by_code["EXT-003"].source == "external"


def test_engine_scraped_ids_use_source_id_and_dedupe_by_code() -> None:
    scraped = [
        {
            "db_id": 3,
            "source_id": "EXT-003",
            "title": "Hotel en Roma",
            "destination": "Roma",
            "price": 499.0,
        },
        {
            "db_id": 18,
            "source_id": "https://mock/hotel/1018",
            "title": "La Concha Seafront 4 días",
            "destination": "San Sebastián",
            "price": 890.0,
        },
        {
            "db_id": 5,
            "source_id": "EXT-001",
            "title": "Hotel Diagonal Mar 4 noches",
            "destination": "Barcelona",
            "price": 689.0,
        },
    ]
    engine = SearchEngine(_SourceCatalog(), EmbeddingsProvider(), scraped=scraped)
    by_code = {doc.code: doc for doc in engine.docs}
    assert engine.doc_by_code("EXT-003").id == 2
    assert engine.doc(9003) is None
    assert by_code["EXT-018"].id == 9018
    assert by_code["EXT-001"].id == 9001
    assert engine.doc_by_code("EXT-018") is by_code["EXT-018"]
    assert engine.doc(9018).code == "EXT-018"