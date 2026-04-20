"""Pydantic request/response models."""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    version: str
    database: str
    timestamp: datetime


class StartInterviewRequest(BaseModel):
    user_id: UUID
    input_mode: str = "text"
    language_preference: str = "auto"


class InterviewerMessage(BaseModel):
    """A message from the interviewer sent back to the client. May
    include a UI widget spec (slider battery / conjoint cards / rank)
    — when widget is null the client renders plain chat text."""

    phase: str
    block: Optional[str] = None
    item_id: Optional[str] = None
    text: str
    widget: Optional[dict[str, Any]] = None
    progress_label: Optional[str] = None
    is_terminal: bool = False


class StartInterviewResponse(BaseModel):
    session_id: UUID
    message: InterviewerMessage


class PostTurnRequest(BaseModel):
    """Client-submitted response to the previous interviewer turn.

    Either `answer_text` (for free-text items) or `answer_structured`
    (for slider batteries, conjoint choices, forced-rank) must be set.
    """

    answer_text: Optional[str] = None
    answer_structured: Optional[dict[str, Any]] = None
    client_meta: Optional[dict[str, Any]] = None


class PostTurnResponse(BaseModel):
    session_id: UUID
    message: InterviewerMessage


class InterviewStateResponse(BaseModel):
    session_id: UUID
    status: str
    phase: str
    block: Optional[str] = None
    archetype: Optional[str] = None
    progress_pct: float = Field(ge=0, le=100)
    elapsed_sec: int


class CompleteInterviewResponse(BaseModel):
    session_id: UUID
    output: dict[str, Any]
    qa: dict[str, Any]
