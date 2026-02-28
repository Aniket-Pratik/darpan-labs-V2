"""Twin profile and evidence models."""

import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TwinProfile(Base):
    """Digital twin profile model."""

    __tablename__ = "twin_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="generating",
    )  # generating, ready, failed
    modules_included: Mapped[list[str]] = mapped_column(
        ARRAY(String(10)),
        nullable=False,
    )  # ["M1", "M2", "M3", "M4", "A1"]
    quality_label: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="base",
    )  # base, enhanced, rich, full
    quality_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )  # 0.0-1.0
    structured_profile_json: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )
    persona_summary_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )  # compact prompt payload ≤2500 tokens
    persona_full_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )  # optional full narrative
    coverage_confidence: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )  # per-module and per-domain map
    extraction_meta: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )  # model, prompt version, retries
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="twin_profiles",
    )
    evidence_snippets: Mapped[list["EvidenceSnippet"]] = relationship(
        "EvidenceSnippet",
        back_populates="twin_profile",
        cascade="all, delete-orphan",
    )
    chat_sessions: Mapped[list["TwinChatSession"]] = relationship(
        "TwinChatSession",
        back_populates="twin",
        cascade="all, delete-orphan",
    )
    experiment_results: Mapped[list["ExperimentResult"]] = relationship(
        "ExperimentResult",
        back_populates="twin",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<TwinProfile(id={self.id}, version={self.version}, quality={self.quality_label})>"


class EvidenceSnippet(Base):
    """Evidence snippet model with vector embedding."""

    __tablename__ = "evidence_snippets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    twin_profile_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("twin_profiles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    module_id: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )
    turn_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("interview_turns.id", ondelete="CASCADE"),
        nullable=False,
    )
    snippet_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    snippet_category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )  # personality, preference, behavior, context
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(1536),  # OpenAI embedding dimension
        nullable=True,
    )
    snippet_metadata: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="evidence_snippets",
    )
    twin_profile: Mapped["TwinProfile"] = relationship(
        "TwinProfile",
        back_populates="evidence_snippets",
    )

    def __repr__(self) -> str:
        return f"<EvidenceSnippet(id={self.id}, category={self.snippet_category})>"
