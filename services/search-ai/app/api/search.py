from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import HistoryIn, SearchResponse, SemanticSearchResponse, TourPackageOut
from app.services.catalog import CatalogClient
from app.services.nlp import NlpService
from app.services.package_sync import sync_package
from app.services.recommender import Recommender
from app.services.search_engine import get_search_engine

router = APIRouter(prefix="/api/v1", tags=["search-nlp"])

_catalog = CatalogClient()
_nlp = NlpService(_catalog)
_recommender = Recommender(get_search_engine())


@router.get("/search/suggestions", response_model=SearchResponse)
def search_suggestions(
    query: str = Query(..., min_length=1, max_length=200),
    user_id: str | None = Query(default=None),
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
) -> SearchResponse:
    payloads = _nlp.rank(query, limit=limit)
    if user_id:
        _recommender.record(
            db,
            user_id=user_id,
            event_type="search",
            query=query,
        )
    return SearchResponse(
        query=query,
        suggestions=_nlp.suggestions_for(query),
        packages=[TourPackageOut(**package) for package in payloads],
    )


@router.get("/search/semantic", response_model=SemanticSearchResponse)
def semantic_search(
    query: str = Query(..., min_length=1, max_length=200),
    destination: str | None = Query(default=None, max_length=120),
    category: str | None = Query(default=None, max_length=40),
    max_price: float | None = Query(default=None, gt=0),
    limit: int = Query(default=10, ge=1, le=50),
) -> SemanticSearchResponse:
    engine = get_search_engine()
    pairs = engine.search(
        query,
        destination=destination,
        category=category,
        max_budget=max_price,
        limit=limit,
        return_scores=True,
    )
    return SemanticSearchResponse(
        query=query,
        packages=[TourPackageOut(**doc.to_dict()) for doc, _ in pairs],
        filters={"destination": destination, "category": category, "max_price": max_price},
        scores=[round(score, 4) for _, score in pairs],
    )


@router.get("/packages/{package_id}", response_model=TourPackageOut)
def package_detail(package_id: int) -> TourPackageOut:
    engine = get_search_engine()
    doc = engine.doc(package_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Paquete no encontrado en el índice")
    if doc.source == "catalogo":
        payload = doc.to_dict()
    else:
        payload = sync_package(doc)
    return TourPackageOut(**payload)


@router.get("/recommendations/{user_id}", response_model=list[TourPackageOut])
def recommendations(
    user_id: str,
    limit: int = Query(default=5, ge=1, le=20),
    db: Session = Depends(get_db),
) -> list[TourPackageOut]:
    payloads = _recommender.recommend(db, user_id, limit=limit)
    return [TourPackageOut(**package) for package in payloads]


@router.post("/history", status_code=201)
def record_history(payload: HistoryIn, db: Session = Depends(get_db)) -> dict:
    entry = _recommender.record(
        db,
        user_id=payload.user_id,
        event_type=payload.event_type,
        query=payload.query,
    )
    return {"id": entry.id, "status": "ok"}
