"""Pydantic schemas for LLM responses.

These schemas are used with the LLM client's response_format parameter
to validate and parse LLM JSON outputs.
"""

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class ExtractedSignal(BaseModel):
    """A signal extracted from an answer."""

    signal: str = Field(description="Name of the signal extracted")
    value: str = Field(description="Value or summary of what was learned")
    confidence: float = Field(
        ge=0.0, le=1.0, description="Confidence in this extraction (0-1)"
    )


class BehavioralRule(BaseModel):
    """A behavioral rule extracted from an answer."""

    rule: str = Field(description="Behavioral rule in 'if X then Y' format")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in this rule (0-1)")


class BehavioralRuleWithEvidence(BaseModel):
    """Behavioral rule with evidence references."""

    rule: str = Field(description="Behavioral rule statement")
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_turn_ids: list[str] = Field(
        default_factory=list, description="Turn IDs supporting this rule"
    )


class ParsedAnswerResponse(BaseModel):
    """LLM response from answer_parser.txt prompt.

    Used to analyze user answers and extract signals.
    """

    specificity_score: float = Field(
        ge=0.0,
        le=1.0,
        description="How specific/detailed the answer is (0=vague, 1=very specific)",
    )
    signals_extracted: list[ExtractedSignal] = Field(
        default_factory=list, description="Signals extracted from this answer"
    )
    behavioral_rules: list[BehavioralRule] = Field(
        default_factory=list, description="Behavioral rules identified"
    )
    needs_followup: bool = Field(
        default=False, description="Whether a follow-up question is needed"
    )
    followup_reason: Literal["vague", "contradiction", "high_leverage", None] = Field(
        default=None, description="Reason for follow-up if needed"
    )
    sentiment: Literal["positive", "neutral", "negative", "mixed"] = Field(
        default="neutral", description="Overall sentiment of the answer"
    )
    language_detected: Literal["EN", "HI", "HG"] = Field(
        default="EN", description="Detected language (EN=English, HI=Hindi, HG=Hinglish)"
    )

    @field_validator("followup_reason", mode="before")
    @classmethod
    def normalize_null_string(cls, v: Any) -> str | None:
        """LLMs sometimes return the string 'null' instead of JSON null."""
        if isinstance(v, str) and v.lower() == "null":
            return None
        return v


class ModuleCompletionResponse(BaseModel):
    """LLM response from module_completion.txt prompt.

    Used to evaluate if a module has reached completion criteria.
    """

    module_id: str = Field(description="Module being evaluated")
    is_complete: bool = Field(description="Whether module meets completion criteria")
    coverage_score: float = Field(
        ge=0.0, le=1.0, description="Proportion of target signals covered"
    )
    confidence_score: float = Field(
        ge=0.0, le=1.0, description="Overall confidence in captured data"
    )
    signals_captured: list[str] = Field(
        default_factory=list, description="Signal names that have been captured"
    )
    signals_missing: list[str] = Field(
        default_factory=list, description="Signal names still needed"
    )
    behavioral_rules_extracted: list[BehavioralRuleWithEvidence] = Field(
        default_factory=list, description="Behavioral rules with evidence"
    )
    recommendation: Literal["COMPLETE", "ASK_MORE", "SKIP_OPTIONAL"] = Field(
        description="Recommended action"
    )
    suggested_next_questions: list[str] = Field(
        default_factory=list, description="Suggested questions if ASK_MORE"
    )
    module_summary: str | None = Field(
        default=None, description="Summary of what was learned (if COMPLETE)"
    )


class AdaptiveQuestionResponse(BaseModel):
    """LLM response from interviewer_question.txt prompt.

    Used to generate the next adaptive question.
    """

    action: Literal["ASK_QUESTION", "ASK_FOLLOWUP", "MODULE_COMPLETE", "OFFER_BREAK"] = (
        Field(description="What action to take")
    )
    acknowledgment_text: str | None = Field(
        default=None,
        description="Brief acknowledgment of user's previous answer",
    )
    question_text: str = Field(description="The question to ask (always in English)")
    question_text_hindi: str | None = Field(
        default=None, description="Deprecated — kept for backwards compat, always None"
    )
    language: Literal["EN", "HI", "HG"] = Field(
        default="EN", description="Always EN — kept for backwards compat"
    )
    question_type: str = Field(description="Type of question")
    target_signal: str = Field(description="Signal this question targets")
    rationale_short: str = Field(description="Brief rationale for asking this question")
    module_summary: str | None = Field(
        default=None, description="Summary if MODULE_COMPLETE"
    )


# Internal service models (not for LLM response parsing)


class ParsedAnswer(BaseModel):
    """Internal representation of a parsed answer."""

    specificity_score: float
    signals_extracted: list[ExtractedSignal]
    behavioral_rules: list[BehavioralRule]
    needs_followup: bool
    followup_reason: str | None
    sentiment: str
    language: str

    @classmethod
    def from_llm_response(cls, response: ParsedAnswerResponse) -> "ParsedAnswer":
        """Create from LLM response."""
        return cls(
            specificity_score=response.specificity_score,
            signals_extracted=response.signals_extracted,
            behavioral_rules=response.behavioral_rules,
            needs_followup=response.needs_followup,
            followup_reason=response.followup_reason,
            sentiment=response.sentiment,
            language=response.language_detected,
        )


class ModuleCompletionResult(BaseModel):
    """Internal result of module completion evaluation."""

    is_complete: bool
    coverage_score: float
    confidence_score: float
    signals_captured: list[str]
    signals_missing: list[str]
    recommendation: str
    module_summary: str | None = None
    suggested_questions: list[str] = Field(default_factory=list)

    @classmethod
    def from_llm_response(cls, response: ModuleCompletionResponse) -> "ModuleCompletionResult":
        """Create from LLM response."""
        return cls(
            is_complete=response.is_complete,
            coverage_score=response.coverage_score,
            confidence_score=response.confidence_score,
            signals_captured=response.signals_captured,
            signals_missing=response.signals_missing,
            recommendation=response.recommendation,
            module_summary=response.module_summary,
            suggested_questions=response.suggested_next_questions,
        )


# ============================================================
# Phase 2: Twin Generation + Chat LLM Response Schemas
# ============================================================


class OceanEstimateLLM(BaseModel):
    """OCEAN trait estimate from profile extraction."""

    score: float = Field(ge=0.0, le=1.0, description="Trait score (0=low, 1=high)")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in this estimate")
    evidence: str = Field(default="", description="Supporting evidence from interview")


class ProfileDemographicsLLM(BaseModel):
    """Demographics section from profile extraction."""

    age_band: str = Field(default="unknown", description="Age range estimate")
    occupation_type: str = Field(default="unknown", description="Type of occupation")
    living_context: str = Field(default="unknown", description="Living situation")
    life_stage: str = Field(default="unknown", description="Current life stage")


class ProfilePersonalityLLM(BaseModel):
    """Personality section from profile extraction."""

    self_description: str = Field(default="", description="How the person describes themselves")
    ocean_estimates: dict[str, OceanEstimateLLM] = Field(
        default_factory=dict,
        description="OCEAN personality estimates (openness, conscientiousness, extraversion, agreeableness, neuroticism)",
    )


class ProfileDecisionMakingLLM(BaseModel):
    """Decision-making section from profile extraction."""

    speed_vs_deliberation: str = Field(default="", description="Fast vs careful decision style")
    gut_vs_data: str = Field(default="", description="Intuition vs data-driven")
    risk_appetite: str = Field(default="", description="Risk tolerance level")
    behavioral_rules: list[BehavioralRule] = Field(
        default_factory=list, description="If-then behavioral rules"
    )


class PreferenceDimensionLLM(BaseModel):
    """A preference dimension from profile extraction."""

    axis: str = Field(description="Preference axis name")
    leaning: str = Field(description="Which direction the person leans")
    strength: float = Field(ge=0.0, le=1.0, description="Strength of preference")


class ProfilePreferencesLLM(BaseModel):
    """Preferences section from profile extraction."""

    dimensions: list[PreferenceDimensionLLM] = Field(
        default_factory=list, description="Preference dimensions"
    )


class ProfileCommunicationLLM(BaseModel):
    """Communication section from profile extraction."""

    directness: str = Field(default="", description="Communication directness style")
    conflict_style: str = Field(default="", description="How they handle conflict")
    social_energy: str = Field(default="", description="Introvert/extrovert tendency")


class ProfileExtractionResponse(BaseModel):
    """LLM response from profile_extraction.txt prompt.

    Used to extract structured personality/behavioral profile from interview transcripts.
    """

    demographics: ProfileDemographicsLLM = Field(default_factory=ProfileDemographicsLLM)
    personality: ProfilePersonalityLLM = Field(default_factory=ProfilePersonalityLLM)
    decision_making: ProfileDecisionMakingLLM = Field(default_factory=ProfileDecisionMakingLLM)
    preferences: ProfilePreferencesLLM = Field(default_factory=ProfilePreferencesLLM)
    communication: ProfileCommunicationLLM = Field(default_factory=ProfileCommunicationLLM)
    domain_specific: dict[str, Any] = Field(default_factory=dict)
    uncertainty_flags: list[str] = Field(default_factory=list)


class PersonaSummaryResponse(BaseModel):
    """LLM response from persona_summary.txt prompt.

    Used to generate a compact natural-language persona summary.
    """

    persona_summary_text: str = Field(
        description="First-person persona summary, max 2500 tokens"
    )
    key_traits: list[str] = Field(
        default_factory=list, description="Top 5-8 defining traits"
    )
    token_estimate: int = Field(
        default=0, description="Estimated token count of summary"
    )


class EvidenceChunkLLM(BaseModel):
    """A single evidence chunk extracted from an answer."""

    text: str = Field(description="The evidence snippet text (1-3 sentences)")
    category: Literal["personality", "preference", "behavior", "context", "decision_rule"] = Field(
        description="Category of this evidence"
    )
    question_context: str = Field(default="", description="What question this answers")


class EvidenceChunkingResponse(BaseModel):
    """LLM response for evidence chunking from a single answer."""

    snippets: list[EvidenceChunkLLM] = Field(
        default_factory=list, description="Evidence snippets extracted from the answer"
    )


class EvidenceUsedLLM(BaseModel):
    """Evidence reference in a twin response."""

    snippet_id: str = Field(description="ID of the evidence snippet used")
    why: str = Field(description="Why this evidence is relevant")


class TwinResponseLLM(BaseModel):
    """LLM response from twin_response.txt prompt.

    Used for twin chat responses and experiment responses.
    """

    response_text: str = Field(description="First-person response as the twin")
    confidence_score: float = Field(
        ge=0.0, le=1.0, description="Confidence in this response"
    )
    confidence_label: Literal["low", "medium", "high"] = Field(
        description="Confidence band"
    )
    uncertainty_reason: str | None = Field(
        default=None, description="Why confidence is limited"
    )
    evidence_used: list[EvidenceUsedLLM] = Field(
        default_factory=list, description="Evidence snippets used"
    )
    coverage_gaps: list[str] = Field(
        default_factory=list, description="Missing module domains"
    )
    suggested_module: str | None = Field(
        default=None, description="Module to complete for better answer"
    )


class CorrectedTranscript(BaseModel):
    """LLM response from transcript_correction.txt prompt.

    Used to correct ASR transcripts and tag language segments.
    """

    corrected_transcript: str = Field(description="Corrected transcript text")
    language_tags: list[dict] = Field(
        default_factory=list,
        description="Language tags per segment [{start, end, lang}]",
    )
    primary_language: Literal["EN", "HI", "HG"] = Field(
        default="EN", description="Primary language of the transcript"
    )
    correction_applied: bool = Field(
        default=False, description="Whether any corrections were applied"
    )
    corrections: list[dict] = Field(
        default_factory=list,
        description="List of corrections [{original, corrected, reason}]",
    )


class AdaptiveQuestionResult(BaseModel):
    """Internal result of adaptive question generation."""

    action: str
    question_text: str
    question_text_hindi: str | None = None
    language: str
    question_type: str
    target_signal: str
    rationale: str
    module_summary: str | None = None
    acknowledgment_text: str | None = None
    is_followup: bool = False
    question_id: str | None = None  # Static question ID if using fallback

    @classmethod
    def from_llm_response(cls, response: AdaptiveQuestionResponse) -> "AdaptiveQuestionResult":
        """Create from LLM response."""
        # Normalize question_type to match expected values
        QUESTION_TYPE_MAP = {
            "tradeoff": "trade_off",
            "trade-off": "trade_off",
            "clarification": "open_text",
            "follow_up": "open_text",
            "followup": "open_text",
        }
        VALID_TYPES = {"open_text", "forced_choice", "scenario", "trade_off", "likert"}
        q_type = response.question_type.lower().strip()
        q_type = QUESTION_TYPE_MAP.get(q_type, q_type)
        if q_type not in VALID_TYPES:
            q_type = "open_text"

        return cls(
            action=response.action,
            question_text=response.question_text,
            question_text_hindi=response.question_text_hindi,
            language=response.language,
            question_type=q_type,
            target_signal=response.target_signal,
            rationale=response.rationale_short,
            module_summary=response.module_summary,
            acknowledgment_text=response.acknowledgment_text,
            is_followup=response.action == "ASK_FOLLOWUP",
        )
