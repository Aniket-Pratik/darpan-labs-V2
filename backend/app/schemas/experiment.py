"""Experiment Pydantic schemas."""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

from .common import BaseSchema


class CohortFilters(BaseModel):
    """Filters for cohort creation."""

    min_quality: Literal["base", "enhanced", "rich", "full"] | None = None
    required_modules: list[str] = Field(default_factory=list)


class CohortCreateRequest(BaseModel):
    """Request to create a cohort."""

    name: str
    twin_ids: list[UUID]
    filters: CohortFilters | None = None


class CohortCreateResponse(BaseSchema):
    """Response after creating a cohort."""

    id: UUID
    name: str
    twin_count: int
    created_at: datetime


class TwinSummary(BaseModel):
    """Summary of a twin in a cohort."""

    twin_id: UUID
    quality_label: str
    quality_score: float
    modules_completed: list[str]


class CohortResponse(BaseSchema):
    """Full cohort response."""

    id: UUID
    name: str
    twin_ids: list[UUID]
    twins: list[TwinSummary] = Field(default_factory=list)
    filters_used: CohortFilters | None = None
    created_at: datetime


class ExperimentScenario(BaseModel):
    """Experiment scenario definition."""

    type: Literal["forced_choice", "likert_scale", "open_scenario", "preference_rank"]
    prompt: str
    options: list[str] | None = None
    context: str | None = None


class ExperimentSettings(BaseModel):
    """Experiment settings."""

    require_reasoning: bool = True
    temperature: float = 0.2
    max_tokens: int = 500


class ExperimentCreateRequest(BaseModel):
    """Request to create an experiment."""

    name: str
    cohort_id: UUID
    scenario: ExperimentScenario
    settings: ExperimentSettings = Field(default_factory=ExperimentSettings)


class ExperimentCreateResponse(BaseSchema):
    """Response after creating an experiment."""

    experiment_id: UUID
    status: Literal["queued", "running", "completed", "failed"]
    cohort_size: int
    estimated_completion_sec: int


class EvidenceUsedInExperiment(BaseModel):
    """Evidence used in experiment response."""

    snippet_id: str
    why: str


class IndividualResult(BaseModel):
    """Individual twin result in an experiment."""

    twin_id: UUID
    twin_name: str | None = None
    twin_quality: str
    modules_completed: list[str]
    choice: str | None = None
    reasoning: str
    confidence_score: float
    confidence_label: Literal["low", "medium", "high"]
    evidence_used: list[EvidenceUsedInExperiment] = Field(default_factory=list)
    coverage_gaps: list[str] = Field(default_factory=list)


class ChoiceDistribution(BaseModel):
    """Distribution of a choice."""

    count: int
    percentage: float


class KeyPattern(BaseModel):
    """Key pattern identified in experiment."""

    pattern: str
    supporting_twins: int
    confidence: float


class AggregateResults(BaseModel):
    """Aggregate results of an experiment."""

    choice_distribution: dict[str, ChoiceDistribution] = Field(default_factory=dict)
    aggregate_confidence: float
    confidence_distribution: dict[str, int] = Field(default_factory=dict)
    key_patterns: list[KeyPattern] = Field(default_factory=list)
    dominant_reasoning_themes: list[str] = Field(default_factory=list)


class ExperimentResultsResponse(BaseSchema):
    """Full experiment results response."""

    experiment_id: UUID
    name: str
    status: Literal["pending", "running", "completed", "failed"]
    cohort_size: int
    completed_responses: int
    execution_time_sec: float | None = None
    aggregate_results: AggregateResults | None = None
    individual_results: list[IndividualResult] = Field(default_factory=list)
    limitations_disclaimer: str = (
        "These results are simulated based on interview-derived digital twin profiles. "
        "They represent approximations of likely responses, not actual user decisions. "
        "Confidence indicators reflect data coverage quality, not statistical significance. "
        "Do not use for high-stakes decisions without live validation."
    )
    created_at: datetime
    completed_at: datetime | None = None


class ExperimentListItem(BaseSchema):
    """Experiment item for list views."""

    id: UUID
    name: str
    status: str
    cohort_size: int
    created_at: datetime
    completed_at: datetime | None = None
