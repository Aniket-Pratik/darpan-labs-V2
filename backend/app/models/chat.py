"""Twin chat models: Session and Message."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TwinChatSession(Base):
    """Twin chat session model."""

    __tablename__ = "twin_chat_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    twin_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("twin_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    twin: Mapped["TwinProfile"] = relationship(
        "TwinProfile",
        back_populates="chat_sessions",
    )
    messages: Mapped[list["TwinChatMessage"]] = relationship(
        "TwinChatMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="TwinChatMessage.created_at",
    )

    def __repr__(self) -> str:
        return f"<TwinChatSession(id={self.id}, twin_id={self.twin_id})>"


class TwinChatMessage(Base):
    """Twin chat message model."""

    __tablename__ = "twin_chat_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("twin_chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )  # user, twin
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    confidence_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    confidence_label: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )  # low, medium, high
    evidence_used: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
    )  # [{"snippet_id": "...", "why": "..."}]
    coverage_gaps: Mapped[list[str] | None] = mapped_column(
        ARRAY(String(100)),
        nullable=True,
    )
    model_meta: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )  # model, tokens, latency
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    session: Mapped["TwinChatSession"] = relationship(
        "TwinChatSession",
        back_populates="messages",
    )

    def __repr__(self) -> str:
        return f"<TwinChatMessage(id={self.id}, role={self.role})>"
