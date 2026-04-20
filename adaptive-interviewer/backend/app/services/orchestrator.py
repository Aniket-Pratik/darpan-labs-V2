"""Orchestrator — entry point from the HTTP layer.

Stub in chunk A; the state machine + phase logic lands in chunk B.
Kept in its own file so the router can import it today.
"""

from typing import Any, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas import CompleteInterviewResponse, InterviewStateResponse, InterviewerMessage


class Orchestrator:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def start(
        self,
        user_id: UUID,
        input_mode: str = "text",
        language_preference: str = "auto",
    ) -> tuple[UUID, InterviewerMessage]:
        raise NotImplementedError("Implemented in chunk B")

    async def post_turn(
        self,
        session_id: UUID,
        answer_text: Optional[str] = None,
        answer_structured: Optional[dict[str, Any]] = None,
        client_meta: Optional[dict[str, Any]] = None,
    ) -> InterviewerMessage:
        raise NotImplementedError("Implemented in chunk B")

    async def get_state(self, session_id: UUID) -> Optional[InterviewStateResponse]:
        raise NotImplementedError("Implemented in chunk B")

    async def finalize(self, session_id: UUID) -> Optional[CompleteInterviewResponse]:
        raise NotImplementedError("Implemented in chunk F")
