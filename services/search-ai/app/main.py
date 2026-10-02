import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import assistant, scrape, search
from app.db import Base, engine
from app.models import ScrapedPackage, UserHistory  # noqa: F401  (registra modelos)
from app.services.fusion import refresh_scraped_packages


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    asyncio.create_task(_startup_scrape())
    yield


async def _startup_scrape() -> None:
    try:
        await refresh_scraped_packages()
    except Exception as exc:  # noqa: BLE001
        print(f"[startup] scraping asÃ­ncrono no disponible: {exc}")


app = FastAPI(
    title="Agencia de Viajes - Search & AI",
    description=(
        "Asistente de reservas inteligente (intenciones TF-IDF + RegresiÃ³n LogÃ­stica, "
        "extracciÃ³n de entidades, hook Beto), buscador semÃ¡ntico con embeddings y web "
        "scraping asÃ­ncrono (httpx + BeautifulSoup) de paquetes turÃ­sticos fusionados "
        "con datos sintÃ©ticos."
    ),
    version="0.5.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:4173",
        "http://localhost:8083",
        "http://localhost:8084",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search.router)
app.include_router(scrape.router)
app.include_router(assistant.router)


@app.get("/api/v1/health")
def health() -> dict:
    return {"status": "UP", "service": "search-ai"}
