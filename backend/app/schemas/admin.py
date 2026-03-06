"""Admin dashboard Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel


class AdminModuleSummary(BaseModel):
    """Module summary for admin user listing."""

    module_id: str
    status: str


class AdminUserSummary(BaseModel):
    """User summary for admin dashboard."""

    user_id: str
    email: str
    display_name: str
    sex: str | None
    age: int | None
    created_at: datetime
    modules: list[AdminModuleSummary]
    completed_module_count: int
    total_turns: int


class AdminUserListResponse(BaseModel):
    """Paginated list of users for admin."""

    users: list[AdminUserSummary]
    total_count: int
    skip: int
    limit: int


class TranscriptTurn(BaseModel):
    """Single Q&A turn in a transcript."""

    turn_index: int
    role: str
    question_text: str | None
    answer_text: str | None
    module_id: str
    created_at: datetime


class TranscriptModule(BaseModel):
    """Module section in a transcript."""

    module_id: str
    module_name: str
    status: str
    turns: list[TranscriptTurn]


class TranscriptResponse(BaseModel):
    """Full transcript for a user."""

    user_id: str
    display_name: str
    email: str
    sex: str | None
    age: int | None
    modules: list[TranscriptModule]
    total_turns: int
