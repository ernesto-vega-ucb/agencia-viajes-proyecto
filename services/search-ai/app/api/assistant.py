from fastapi import APIRouter

from app.schemas import (
    AgentTraceOut,
    ChatRequest,
    ChatResponse,
    NlpDebugOut,
    TourPackageOut,
)
from app.services.agent import AIAgent, build_agent

router = APIRouter(prefix="/api/v1/assistant", tags=["assistant"])

_agent: AIAgent | None = None


def _get_agent() -> AIAgent:
    global _agent
    if _agent is None:
        _agent = build_agent()
    return _agent


@router.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest) -> ChatResponse:
    result = await _get_agent().run(payload.message)
    return ChatResponse(
        message=result["message"],
        intent=result["intent"],
        confidence=result["confidence"],
        scores=result["scores"],
        entities=result["entities"],
        context=result["context"],
        suggestions=[TourPackageOut(**item) for item in result["suggestions"]],
        nlp_debug=NlpDebugOut(**result["nlp_debug"]),
        agent_trace=AgentTraceOut(**result["agent_trace"]),
    )