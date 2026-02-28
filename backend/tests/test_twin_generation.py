"""Tests for Phase 2a: Twin Generation Pipeline."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.schemas.llm_responses import (
    ProfileExtractionResponse,
    ProfileDemographicsLLM,
    ProfilePersonalityLLM,
    ProfileDecisionMakingLLM,
    ProfilePreferencesLLM,
    ProfileCommunicationLLM,
    OceanEstimateLLM,
    PreferenceDimensionLLM,
    BehavioralRule,
    PersonaSummaryResponse,
    EvidenceChunkingResponse,
    EvidenceChunkLLM,
    TwinResponseLLM,
    EvidenceUsedLLM,
)
from app.schemas.twin import (
    TwinGenerateRequest,
    TwinProfileResponse,
    CoverageConfidence,
    StructuredProfile,
    TwinVersionInfo,
)
from app.services.twin_generation_service import TwinGenerationService


# ============================================================
# ProfileExtractionResponse Schema Tests
# ============================================================


class TestProfileExtractionSchema:
    """Test ProfileExtractionResponse Pydantic validation."""

    def test_minimal_valid_profile(self):
        """A profile with all defaults should validate."""
        profile = ProfileExtractionResponse()
        assert profile.demographics.age_band == "unknown"
        assert profile.personality.self_description == ""
        assert profile.decision_making.behavioral_rules == []
        assert profile.uncertainty_flags == []

    def test_full_profile(self):
        """A full profile with all fields should validate."""
        profile = ProfileExtractionResponse(
            demographics=ProfileDemographicsLLM(
                age_band="25-34",
                occupation_type="software engineer",
                living_context="urban, shared apartment",
                life_stage="early career",
            ),
            personality=ProfilePersonalityLLM(
                self_description="I'm analytical and curious",
                ocean_estimates={
                    "openness": OceanEstimateLLM(
                        score=0.8, confidence=0.7, evidence="explores many hobbies"
                    ),
                    "conscientiousness": OceanEstimateLLM(
                        score=0.6, confidence=0.5, evidence="somewhat organized"
                    ),
                },
            ),
            decision_making=ProfileDecisionMakingLLM(
                speed_vs_deliberation="deliberate",
                gut_vs_data="data-driven",
                risk_appetite="moderate",
                behavioral_rules=[
                    BehavioralRule(rule="if price > 500, research for at least a week", confidence=0.9),
                ],
            ),
            preferences=ProfilePreferencesLLM(
                dimensions=[
                    PreferenceDimensionLLM(axis="price_vs_quality", leaning="quality", strength=0.7),
                ]
            ),
            communication=ProfileCommunicationLLM(
                directness="direct",
                conflict_style="avoidant",
                social_energy="introvert",
            ),
            uncertainty_flags=["spending_behavior", "health"],
        )
        assert profile.demographics.age_band == "25-34"
        assert len(profile.personality.ocean_estimates) == 2
        assert profile.personality.ocean_estimates["openness"].score == 0.8
        assert len(profile.decision_making.behavioral_rules) == 1
        assert profile.preferences.dimensions[0].axis == "price_vs_quality"
        assert len(profile.uncertainty_flags) == 2

    def test_ocean_score_bounds(self):
        """OCEAN scores must be 0.0-1.0."""
        with pytest.raises(Exception):
            OceanEstimateLLM(score=1.5, confidence=0.5, evidence="")
        with pytest.raises(Exception):
            OceanEstimateLLM(score=-0.1, confidence=0.5, evidence="")

    def test_behavioral_rule_confidence_bounds(self):
        """Rule confidence must be 0.0-1.0."""
        valid = BehavioralRule(rule="test rule", confidence=0.5)
        assert valid.confidence == 0.5

        with pytest.raises(Exception):
            BehavioralRule(rule="test", confidence=1.5)

    def test_preference_strength_bounds(self):
        """Preference strength must be 0.0-1.0."""
        valid = PreferenceDimensionLLM(axis="test", leaning="left", strength=0.7)
        assert valid.strength == 0.7

        with pytest.raises(Exception):
            PreferenceDimensionLLM(axis="test", leaning="left", strength=-0.1)


# ============================================================
# PersonaSummaryResponse Schema Tests
# ============================================================


class TestPersonaSummarySchema:
    """Test PersonaSummaryResponse validation."""

    def test_valid_summary(self):
        """A valid persona summary should pass."""
        summary = PersonaSummaryResponse(
            persona_summary_text="I am a 28-year-old software engineer...",
            key_traits=["analytical", "introverted", "data-driven"],
            token_estimate=150,
        )
        assert "software engineer" in summary.persona_summary_text
        assert len(summary.key_traits) == 3

    def test_empty_traits_allowed(self):
        """Empty key_traits list should be valid."""
        summary = PersonaSummaryResponse(
            persona_summary_text="Short summary.",
            key_traits=[],
            token_estimate=10,
        )
        assert summary.key_traits == []


# ============================================================
# EvidenceChunkingResponse Schema Tests
# ============================================================


class TestEvidenceChunkingSchema:
    """Test EvidenceChunkingResponse validation."""

    def test_valid_chunks(self):
        """Valid evidence chunks should pass."""
        response = EvidenceChunkingResponse(
            snippets=[
                EvidenceChunkLLM(
                    text="I prefer to plan ahead rather than be spontaneous",
                    category="personality",
                    question_context="How do you approach decisions?",
                ),
                EvidenceChunkLLM(
                    text="I always compare prices before buying",
                    category="decision_rule",
                    question_context="Tell me about your shopping habits",
                ),
            ]
        )
        assert len(response.snippets) == 2
        assert response.snippets[0].category == "personality"

    def test_valid_categories(self):
        """All valid categories should pass."""
        for cat in ["personality", "preference", "behavior", "context", "decision_rule"]:
            chunk = EvidenceChunkLLM(text="test", category=cat, question_context="")
            assert chunk.category == cat

    def test_empty_snippets(self):
        """Empty snippets list should be valid."""
        response = EvidenceChunkingResponse(snippets=[])
        assert response.snippets == []


# ============================================================
# TwinResponseLLM Schema Tests
# ============================================================


class TestTwinResponseSchema:
    """Test TwinResponseLLM validation."""

    def test_high_confidence_response(self):
        """A high-confidence response should validate."""
        response = TwinResponseLLM(
            response_text="I would definitely choose the subscription.",
            confidence_score=0.85,
            confidence_label="high",
            uncertainty_reason=None,
            evidence_used=[
                EvidenceUsedLLM(snippet_id="s1", why="supports preference"),
            ],
            coverage_gaps=[],
            suggested_module=None,
        )
        assert response.confidence_label == "high"
        assert response.suggested_module is None

    def test_low_confidence_with_suggestion(self):
        """A low-confidence response with module suggestion should validate."""
        response = TwinResponseLLM(
            response_text="I'm not sure about my spending habits.",
            confidence_score=0.3,
            confidence_label="low",
            uncertainty_reason="No spending data from module A2",
            evidence_used=[],
            coverage_gaps=["spending_behavior"],
            suggested_module="A2",
        )
        assert response.confidence_label == "low"
        assert response.suggested_module == "A2"
        assert len(response.coverage_gaps) == 1

    def test_confidence_score_bounds(self):
        """Confidence score must be 0.0-1.0."""
        with pytest.raises(Exception):
            TwinResponseLLM(
                response_text="test",
                confidence_score=1.5,
                confidence_label="high",
            )


# ============================================================
# TwinGenerationService Quality Logic Tests
# ============================================================


class TestQualityLabel:
    """Test quality label determination logic."""

    def setup_method(self):
        self.service = TwinGenerationService()

    def test_base_quality_mandatory_only(self):
        """4 mandatory modules = base quality."""
        label = self.service._determine_quality_label(["M1", "M2", "M3", "M4"])
        assert label == "base"

    def test_enhanced_quality_one_addon(self):
        """Mandatory + 1 addon = enhanced."""
        label = self.service._determine_quality_label(["M1", "M2", "M3", "M4", "A1"])
        assert label == "enhanced"

    def test_enhanced_quality_two_addons(self):
        """Mandatory + 2 addons = enhanced."""
        label = self.service._determine_quality_label(
            ["M1", "M2", "M3", "M4", "A1", "A2"]
        )
        assert label == "enhanced"

    def test_rich_quality_three_addons(self):
        """Mandatory + 3 addons = rich."""
        label = self.service._determine_quality_label(
            ["M1", "M2", "M3", "M4", "A1", "A2", "A3"]
        )
        assert label == "rich"

    def test_rich_quality_four_addons(self):
        """Mandatory + 4 addons = rich."""
        label = self.service._determine_quality_label(
            ["M1", "M2", "M3", "M4", "A1", "A2", "A3", "A4"]
        )
        assert label == "rich"

    def test_full_quality_five_plus_addons(self):
        """Mandatory + 5+ addons = full."""
        label = self.service._determine_quality_label(
            ["M1", "M2", "M3", "M4", "A1", "A2", "A3", "A4", "A5"]
        )
        assert label == "full"


class TestQualityScore:
    """Test quality score calculation."""

    def setup_method(self):
        self.service = TwinGenerationService()

    def test_quality_score_all_perfect(self):
        """Perfect coverage and confidence should give high score."""
        coverage = {
            "by_module": {
                "M1": {"coverage": 1.0, "confidence": 1.0, "signals_captured": []},
                "M2": {"coverage": 1.0, "confidence": 1.0, "signals_captured": []},
                "M3": {"coverage": 1.0, "confidence": 1.0, "signals_captured": []},
                "M4": {"coverage": 1.0, "confidence": 1.0, "signals_captured": []},
            }
        }
        score = self.service._calculate_quality_score(coverage)
        assert score == 1.0

    def test_quality_score_mixed(self):
        """Mixed scores should give intermediate value."""
        coverage = {
            "by_module": {
                "M1": {"coverage": 0.8, "confidence": 0.7, "signals_captured": []},
                "M2": {"coverage": 0.6, "confidence": 0.5, "signals_captured": []},
                "M3": {"coverage": 0.7, "confidence": 0.6, "signals_captured": []},
                "M4": {"coverage": 0.5, "confidence": 0.4, "signals_captured": []},
            }
        }
        score = self.service._calculate_quality_score(coverage)
        assert 0.5 < score < 0.8

    def test_quality_score_empty(self):
        """Empty coverage should return 0."""
        score = self.service._calculate_quality_score({})
        assert score == 0.0
        score = self.service._calculate_quality_score({"by_module": {}})
        assert score == 0.0


# ============================================================
# Twin Schema Tests
# ============================================================


class TestTwinSchemas:
    """Test twin Pydantic schemas."""

    def test_twin_generate_request(self):
        """TwinGenerateRequest should validate."""
        req = TwinGenerateRequest(
            trigger="mandatory_modules_complete",
            modules_to_include=["M1", "M2", "M3", "M4"],
        )
        assert req.trigger == "mandatory_modules_complete"
        assert len(req.modules_to_include) == 4

    def test_coverage_confidence(self):
        """CoverageConfidence should validate."""
        cc = CoverageConfidence(
            domain="M1",
            coverage_score=0.85,
            confidence_score=0.80,
            signals_captured=["occupation", "age_band"],
        )
        assert cc.domain == "M1"
        assert len(cc.signals_captured) == 2

    def test_twin_version_info(self):
        """TwinVersionInfo should validate."""
        from datetime import datetime
        vi = TwinVersionInfo(
            version=1,
            modules_included=["M1", "M2", "M3", "M4"],
            quality_label="base",
            quality_score=0.65,
            created_at=datetime.now(),
        )
        assert vi.version == 1


# ============================================================
# Prompt Template Tests
# ============================================================


class TestTwinPromptTemplates:
    """Test that Phase 2 prompt templates load and format correctly."""

    def test_profile_extraction_prompt_loads(self):
        from app.services.prompt_service import get_prompt_service
        ps = get_prompt_service()
        text = ps.load_prompt("profile_extraction")
        assert "structured" in text.lower()
        assert "{completed_modules}" in text
        assert "{all_module_turns}" in text

    def test_persona_summary_prompt_loads(self):
        from app.services.prompt_service import get_prompt_service
        ps = get_prompt_service()
        text = ps.load_prompt("persona_summary")
        assert "first person" in text.lower() or "first-person" in text.lower()
        assert "{structured_profile}" in text
        assert "{modules_included}" in text

    def test_evidence_chunking_prompt_loads(self):
        from app.services.prompt_service import get_prompt_service
        ps = get_prompt_service()
        text = ps.load_prompt("evidence_chunking")
        assert "snippet" in text.lower()
        assert "{module_id}" in text
        assert "{answer_text}" in text

    def test_twin_response_prompt_loads(self):
        from app.services.prompt_service import get_prompt_service
        ps = get_prompt_service()
        text = ps.load_prompt("twin_response")
        assert "first person" in text.lower() or "first-person" in text.lower()
        assert "{persona_summary_text}" in text
        assert "{user_question}" in text

    def test_profile_extraction_prompt_formats(self):
        from app.services.prompt_service import get_prompt_service
        ps = get_prompt_service()
        result = ps.format_prompt(
            "profile_extraction",
            completed_modules="M1, M2, M3, M4",
            all_module_turns="Q: test\nA: test answer",
        )
        assert "M1, M2, M3, M4" in result
        assert "test answer" in result

    def test_persona_summary_prompt_formats(self):
        from app.services.prompt_service import get_prompt_service
        ps = get_prompt_service()
        result = ps.format_prompt(
            "persona_summary",
            structured_profile='{"demographics": {}}',
            modules_included="M1, M2",
            uncertainty_flags="spending, health",
        )
        assert "M1, M2" in result
        assert "spending" in result

    def test_evidence_chunking_prompt_formats(self):
        from app.services.prompt_service import get_prompt_service
        ps = get_prompt_service()
        result = ps.format_prompt(
            "evidence_chunking",
            module_id="M1",
            module_name="Core Identity",
            question_text="Tell me about yourself",
            answer_text="I am a software engineer",
        )
        assert "M1" in result
        assert "software engineer" in result

    def test_twin_response_prompt_formats(self):
        from app.services.prompt_service import get_prompt_service
        ps = get_prompt_service()
        result = ps.format_prompt(
            "twin_response",
            persona_summary_text="I am analytical.",
            retrieved_evidence="[s1] I prefer data-driven decisions",
            modules_included="M1, M2, M3, M4",
            missing_modules="A1, A2",
            chat_history="User: How are you?",
            user_question="What phone would you buy?",
        )
        assert "analytical" in result
        assert "What phone" in result


# ============================================================
# Service Instantiation Tests
# ============================================================


class TestServiceInstantiation:
    """Test that all Phase 2 services can be instantiated."""

    def test_profile_builder_creates(self):
        from app.services.profile_builder import get_profile_builder_service
        service = get_profile_builder_service()
        assert service is not None

    def test_persona_generator_creates(self):
        from app.services.persona_generator import get_persona_generator_service
        service = get_persona_generator_service()
        assert service is not None

    def test_evidence_indexer_creates(self):
        from app.services.evidence_indexer import get_evidence_indexer_service
        service = get_evidence_indexer_service()
        assert service is not None

    def test_evidence_retriever_creates(self):
        from app.services.evidence_retriever import get_evidence_retriever_service
        service = get_evidence_retriever_service()
        assert service is not None

    def test_twin_generation_service_creates(self):
        from app.services.twin_generation_service import get_twin_generation_service
        service = get_twin_generation_service()
        assert service is not None

    def test_twin_chat_service_creates(self):
        from app.services.twin_chat_service import get_twin_chat_service
        service = get_twin_chat_service()
        assert service is not None


# ============================================================
# Evidence Indexer Heuristic Tests
# ============================================================


class TestEvidenceHeuristic:
    """Test heuristic evidence chunking fallback."""

    def test_heuristic_splits_sentences(self):
        from app.services.evidence_indexer import EvidenceIndexerService
        service = EvidenceIndexerService()

        turn = {
            "turn_id": uuid4(),
            "module_id": "M1",
            "question_text": "Tell me about yourself",
            "answer_text": "I am a software engineer. I love building things. I work remotely from home.",
        }
        chunks = service._heuristic_chunk(turn)
        assert len(chunks) >= 1
        for chunk in chunks:
            assert chunk.category == "context"
            assert len(chunk.text) > 0

    def test_heuristic_skips_short_text(self):
        from app.services.evidence_indexer import EvidenceIndexerService
        service = EvidenceIndexerService()

        turn = {
            "turn_id": uuid4(),
            "module_id": "M1",
            "question_text": "Age?",
            "answer_text": "28",
        }
        chunks = service._heuristic_chunk(turn)
        assert len(chunks) == 0

    def test_heuristic_handles_no_periods(self):
        from app.services.evidence_indexer import EvidenceIndexerService
        service = EvidenceIndexerService()

        turn = {
            "turn_id": uuid4(),
            "module_id": "M1",
            "question_text": "What do you do?",
            "answer_text": "I am a teacher who loves working with kids and exploring new teaching methods",
        }
        chunks = service._heuristic_chunk(turn)
        assert len(chunks) >= 1
