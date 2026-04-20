"""ORM models.

Three tables are **shared** with the `ai-interviewer` service —
`interview_sessions`, `interview_modules`, `interview_turns` — declared
here with identical schema so create_all is a no-op and reads/writes
hit the same rows.

Two tables are new and specific to this service:
    - adaptive_classifications : archetype probability vectors + history
    - adaptive_outputs         : final assembled per-respondent JSON
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    """Minimal stub so the ORM can resolve `users.id` foreign keys.

    The table is owned by the ai-interviewer service; create_all
    skips it here because it already exists in the shared database.
    We only declare columns we reference (id), not the full schema.
    """

    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    input_mode: Mapped[str] = mapped_column(String(20), nullable=False, default="text")
    language_preference: Mapped[str] = mapped_column(String(10), nullable=False, default="auto")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    total_duration_sec: Mapped[int | None] = mapped_column(Integer, nullable=True)
    settings: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    modules: Mapped[list["InterviewModule"]] = relationship(
        "InterviewModule", back_populates="session", cascade="all, delete-orphan",
        primaryjoin="InterviewSession.id == InterviewModule.session_id",
    )
    turns: Mapped[list["InterviewTurn"]] = relationship(
        "InterviewTurn", back_populates="session", cascade="all, delete-orphan",
        primaryjoin="InterviewSession.id == InterviewTurn.session_id",
        order_by="InterviewTurn.turn_index",
    )
    classifications: Mapped[list["AdaptiveClassification"]] = relationship(
        "AdaptiveClassification", back_populates="session", cascade="all, delete-orphan",
    )
    output: Mapped["AdaptiveOutput | None"] = relationship(
        "AdaptiveOutput", back_populates="session", uselist=False, cascade="all, delete-orphan",
    )


class InterviewModule(Base):
    __tablename__ = "interview_modules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    module_id: Mapped[str] = mapped_column(String(10), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    question_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    coverage_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    signals_captured: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    completion_eval: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    session: Mapped["InterviewSession"] = relationship("InterviewSession", back_populates="modules")


class InterviewTurn(Base):
    __tablename__ = "interview_turns"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    module_id: Mapped[str] = mapped_column(String(10), nullable=False)
    turn_index: Mapped[int] = mapped_column(Integer, nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    input_mode: Mapped[str] = mapped_column(String(20), nullable=False, default="text")

    question_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    question_meta: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    answer_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    answer_raw_transcript: Mapped[str | None] = mapped_column(Text, nullable=True)
    answer_language: Mapped[str | None] = mapped_column(String(10), nullable=True)
    answer_structured: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    answer_meta: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    audio_meta: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    audio_storage_ref: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    session: Mapped["InterviewSession"] = relationship("InterviewSession", back_populates="turns")


class AdaptiveClassification(Base):
    """Classification events. One session may have multiple rows
    (initial + reclassification after a mid-interview trigger)."""

    __tablename__ = "adaptive_classifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    sequence_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    probs: Mapped[dict] = mapped_column(JSONB, nullable=False)
    primary_archetype: Mapped[str] = mapped_column(String(20), nullable=False)
    secondary_archetype: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_hybrid: Mapped[bool] = mapped_column(nullable=False, default=False)
    is_enterprise_flag: Mapped[bool] = mapped_column(nullable=False, default=False)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    trigger: Mapped[str] = mapped_column(String(40), nullable=False, default="initial")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    session: Mapped["InterviewSession"] = relationship("InterviewSession", back_populates="classifications")


class AdaptiveOutput(Base):
    """One row per completed interview — the assembled digital-twin
    output object. Keeps raw block outputs addressable in their own
    JSONB columns so downstream consumers don't have to dig through
    a single blob."""

    __tablename__ = "adaptive_outputs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    context: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    archetype: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    jtbd: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    conjoint: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    brand_lattice: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    personality: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    values: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    identity: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    tone_preference: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    projective: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    qa: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    session: Mapped["InterviewSession"] = relationship("InterviewSession", back_populates="output")
