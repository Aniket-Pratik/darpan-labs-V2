"""Twin chat Pydantic schemas."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from .common import BaseSchema


class EvidenceUsed(BaseModel):
    """Evidence used in a response."""

    snippet_id: str
    why: str
    snippet_text: str | None = None


class TwinChatRequest(BaseModel):
    """Request to chat with a twin."""

    message: str
    session_id: UUID | None = None


class TwinChatResponse(BaseSchema):
    """Response from twin chat."""

    session_id: UUID
    message_id: UUID
    response_text: str
    confidence_score: float
    confidence_label: Literal["low", "medium", "high"]
    uncertainty_reason: str | None = None
    evidence_used: list[EvidenceUsed] = Field(default_factory=list)
    coverage_gaps: list[str] = Field(default_factory=list)
    suggested_module: str | None = None


class ChatMessageResponse(BaseSchema):
    """A single chat message."""

    id: UUID
    role: Literal["user", "twin"]
    content: str
    confidence_score: float | None = None
    confidence_label: str | None = None
    evidence_used: list[EvidenceUsed] | None = None
    coverage_gaps: list[str] | None = None
    created_at: datetime


class ChatHistoryResponse(BaseSchema):
    """Chat history response."""

    session_id: UUID
    twin_id: UUID
    messages: list[ChatMessageResponse]
    created_at: datetime


class BrandChatSessionItem(BaseSchema):
    """Brand chat session list item with twin info."""

    id: UUID
    twin_id: UUID
    twin_quality_label: str
    twin_quality_score: float
    twin_modules: list[str]
    created_at: datetime
    message_count: int = 0
