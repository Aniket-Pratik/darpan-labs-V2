"""Routes wiring the state machine to HTTP.

The actual flow lives in `services.orchestrator` — this file stays
thin so the business logic is unit-testable without FastAPI."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.schemas import (
    CompleteInterviewResponse,
    InterviewStateResponse,
    PostTurnRequest,
    PostTurnResponse,
    StartInterviewRequest,
    StartInterviewResponse,
)
from app.services.orchestrator import Orchestrator

router = APIRouter(prefix="/adaptive", tags=["Adaptive Interview"])


@router.post("/start", response_model=StartInterviewResponse)
async def start_interview(
    req: StartInterviewRequest,
    db: AsyncSession = Depends(get_session),
) -> StartInterviewResponse:
    orch = Orchestrator(db)
    session_id, message = await orch.start(
        user_id=req.user_id,
        input_mode=req.input_mode,
        language_preference=req.language_preference,
    )
    return StartInterviewResponse(session_id=session_id, message=message)


@router.post("/{session_id}/turn", response_model=PostTurnResponse)
async def post_turn(
    session_id: UUID,
    req: PostTurnRequest,
    db: AsyncSession = Depends(get_session),
) -> PostTurnResponse:
    orch = Orchestrator(db)
    try:
        message = await orch.post_turn(
            session_id=session_id,
            answer_text=req.answer_text,
            answer_structured=req.answer_structured,
            client_meta=req.client_meta,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return PostTurnResponse(session_id=session_id, message=message)


@router.get("/{session_id}/state", response_model=InterviewStateResponse)
async def get_state(
    session_id: UUID,
    db: AsyncSession = Depends(get_session),
) -> InterviewStateResponse:
    orch = Orchestrator(db)
    state = await orch.get_state(session_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return state


@router.post("/{session_id}/complete", response_model=CompleteInterviewResponse)
async def complete_interview(
    session_id: UUID,
    db: AsyncSession = Depends(get_session),
) -> CompleteInterviewResponse:
    orch = Orchestrator(db)
    result = await orch.finalize(session_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return result
