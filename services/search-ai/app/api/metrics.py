from fastapi import APIRouter

from app.schemas import MetricsSummaryOut
from app.services.metrics import get_metrics_summary

router = APIRouter(prefix="/api/v1/metrics", tags=["metrics"])


@router.get("/summary", response_model=MetricsSummaryOut)
def metrics_summary() -> MetricsSummaryOut:
    return MetricsSummaryOut(**get_metrics_summary())