"""Experiment models: Cohort, Experiment, ExperimentResult."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Cohort(Base):
    """Twin cohort model for experiments."""

    __tablename__ = "cohorts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    twin_ids: Mapped[list[uuid.UUID]] = mapped_column(
        ARRAY(UUID(as_uuid=True)),
        nullable=False,
    )
    filters_used: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )  # quality, modules, etc.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    created_by_user: Mapped["User"] = relationship(
        "User",
        back_populates="cohorts",
    )
    experiments: Mapped[list["Experiment"]] = relationship(
        "Experiment",
        back_populates="cohort",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Cohort(id={self.id}, name={self.name}, size={len(self.twin_ids)})>"


class Experiment(Base):
    """Experiment model for cohort simulation."""

    __tablename__ = "experiments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    cohort_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cohorts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    scenario: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
    )  # type, prompt, options, context
    settings: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )  # temperature, max_tokens, etc.
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
    )  # pending, running, completed, failed
    aggregate_results: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    created_by_user: Mapped["User"] = relationship(
        "User",
        back_populates="experiments",
    )
    cohort: Mapped["Cohort"] = relationship(
        "Cohort",
        back_populates="experiments",
    )
    results: Mapped[list["ExperimentResult"]] = relationship(
        "ExperimentResult",
        back_populates="experiment",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Experiment(id={self.id}, name={self.name}, status={self.status})>"


class ExperimentResult(Base):
    """Individual twin result for an experiment."""

    __tablename__ = "experiment_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    experiment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("experiments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    twin_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("twin_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    choice: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    reasoning: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    confidence_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    confidence_label: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )  # low, medium, high
    evidence_used: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
    )
    coverage_gaps: Mapped[list[str] | None] = mapped_column(
        ARRAY(String(100)),
        nullable=True,
    )
    model_meta: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    experiment: Mapped["Experiment"] = relationship(
        "Experiment",
        back_populates="results",
    )
    twin: Mapped["TwinProfile"] = relationship(
        "TwinProfile",
        back_populates="experiment_results",
    )

    def __repr__(self) -> str:
        return f"<ExperimentResult(id={self.id}, choice={self.choice})>"
