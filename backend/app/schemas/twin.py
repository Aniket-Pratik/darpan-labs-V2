"""Twin profile Pydantic schemas."""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

from .common import BaseSchema


class TwinGenerateRequest(BaseModel):
    """Request to generate a twin."""

    trigger: Literal["mandatory_modules_complete", "addon_module_complete", "manual"]
    modules_to_include: list[str]


class TwinGenerateResponse(BaseSchema):
    """Response after triggering twin generation."""

    job_id: str
    status: Literal["queued", "processing", "completed", "failed"]
    expected_completion_sec: int
    twin_version: int
    quality_label: Literal["base", "enhanced", "rich", "full"]


class CoverageConfidence(BaseModel):
    """Coverage and confidence for a domain/module."""

    domain: str
    coverage_score: float
    confidence_score: float
    signals_captured: list[str]
    uncertainty_flags: list[str] = Field(default_factory=list)


class OceanEstimate(BaseModel):
    """OCEAN personality trait estimate."""

    score: float
    confidence: float
    evidence: str | None = None


class PersonalityProfile(BaseModel):
    """Personality profile from twin."""

    self_description: str | None = None
    ocean_estimates: dict[str, OceanEstimate] | None = None


class PreferenceDimension(BaseModel):
    """A preference dimension."""

    axis: str
    leaning: str
    strength: float


class BehavioralRule(BaseModel):
    """A behavioral rule extracted from interview."""

    rule: str
    confidence: float
    evidence_turn_ids: list[str] = Field(default_factory=list)


class DecisionProfile(BaseModel):
    """Decision-making profile."""

    speed_vs_deliberation: str | None = None
    gut_vs_data: str | None = None
    risk_appetite: str | None = None
    behavioral_rules: list[BehavioralRule] = Field(default_factory=list)


class StructuredProfile(BaseModel):
    """Full structured profile."""

    demographics: dict[str, Any] = Field(default_factory=dict)
    personality: PersonalityProfile | None = None
    decision_making: DecisionProfile | None = None
    preferences: dict[str, Any] = Field(default_factory=dict)
    communication: dict[str, Any] = Field(default_factory=dict)
    domain_specific: dict[str, Any] = Field(default_factory=dict)
    uncertainty_flags: list[str] = Field(default_factory=list)


class TwinVersionInfo(BaseModel):
    """Information about a twin version."""

    version: int
    modules_included: list[str]
    quality_label: str
    quality_score: float
    created_at: datetime


class TwinProfileResponse(BaseSchema):
    """Full twin profile response."""

    id: UUID
    user_id: UUID
    version: int
    status: Literal["generating", "ready", "failed"]
    modules_included: list[str]
    quality_label: Literal["base", "enhanced", "rich", "full"]
    quality_score: float
    structured_profile: StructuredProfile | None = None
    persona_summary_text: str | None = None
    coverage_confidence: list[CoverageConfidence] = Field(default_factory=list)
    created_at: datetime
    version_history: list[TwinVersionInfo] = Field(default_factory=list)


class TwinListItem(BaseSchema):
    """Twin item for list views."""

    id: UUID
    version: int
    quality_label: str
    quality_score: float
    modules_included: list[str]
    status: str
    created_at: datetime


class AvailableModule(BaseModel):
    """Available add-on module."""

    module_id: str
    module_name: str
    estimated_duration_min: int
    estimated_improvement_percent: str
    description: str
