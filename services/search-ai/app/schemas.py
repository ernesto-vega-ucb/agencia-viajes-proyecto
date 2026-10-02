from datetime import datetime

from pydantic import BaseModel, Field


class TourPackageOut(BaseModel):
    id: int
    code: str
    title: str
    destination: str
    country: str
    description: str
    category: str
    durationDays: int
    basePrice: float
    currency: str
    rating: float
    source: str = "catalogo"
    startDates: list[str] = Field(default_factory=list)
    images: list[str] = Field(default_factory=list)
    maxTravelers: int = 8
    cancelDaysBefore: int = 15
    cancelRefundPercent: int = 100
    active: bool = True

    model_config = {"from_attributes": True}


class SearchResponse(BaseModel):
    query: str
    suggestions: list[str] = Field(default_factory=list)
    packages: list[TourPackageOut] = Field(default_factory=list)


class HistoryIn(BaseModel):
    user_id: str
    event_type: str = "search"
    query: str | None = None


class ScrapeRequest(BaseModel):
    source: str | None = None
    urls: list[str] | None = None


class ScrapeTaskOut(BaseModel):
    task_id: str
    status: str
    detail: str


class ScrapedPackageOut(BaseModel):
    id: int
    source: str
    source_id: str | None
    title: str
    destination: str | None
    price: float | None
    currency: str | None
    url: str | None
    scraped_at: datetime

    model_config = {"from_attributes": True}


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=500)
    user_id: str | None = None


class ChatResponse(BaseModel):
    message: str
    intent: str
    confidence: float
    scores: dict[str, float] = Field(default_factory=dict)
    entities: dict[str, list] = Field(default_factory=dict)
    context: dict[str, float | str | None] = Field(default_factory=dict)
    suggestions: list[TourPackageOut] = Field(default_factory=list)


class SemanticSearchResponse(SearchResponse):
    filters: dict[str, float | str | None] = Field(default_factory=dict)
    scores: list[float] = Field(default_factory=list)
