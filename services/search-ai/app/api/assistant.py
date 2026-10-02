from fastapi import APIRouter

from app.schemas import ChatRequest, ChatResponse, TourPackageOut
from app.services.assistant import ChatAssistant, build_assistant

router = APIRouter(prefix="/api/v1/assistant", tags=["assistant"])

_assistant: ChatAssistant | None = None


def _get_assistant() -> ChatAssistant:
    global _assistant
    if _assistant is None:
        _assistant = build_assistant()
    return _assistant


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    result = _get_assistant().handle(payload.message)
    return ChatResponse(
        message=result["message"],
        intent=result["intent"],
        confidence=result["confidence"],
        scores=result["scores"],
        entities=result["entities"],
        context=result["context"],
        suggestions=[TourPackageOut(**item) for item in result["suggestions"]],
    )
