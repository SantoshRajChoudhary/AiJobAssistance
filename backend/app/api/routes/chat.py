"""
Conversational Chat Route.
Accepts natural-language queries, runs the orchestrator agent, and returns structured responses.
"""

from fastapi import APIRouter, status
from app.models.schemas import ChatRequest, ChatResponse
from app.agents.orchestrator import orchestrator
from app.utils.errors import InvalidInputError

router = APIRouter(tags=["Chat"])


@router.post(
    "/api/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Conversational chat endpoint for job search, filtering, applications, and status",
)
async def chat_endpoint(req: ChatRequest):
    if not req.message or not req.message.strip():
        raise InvalidInputError("Message cannot be empty.")

    response = await orchestrator.orchestrate(
        message=req.message.strip(),
        session_id=req.session_id,
        client_resume=req.resume,
        client_applied=req.applied_jobs,
        client_recommended=req.recommended_jobs,
    )
    return response
