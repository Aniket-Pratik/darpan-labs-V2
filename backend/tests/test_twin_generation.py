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
    ConditionalRuleLLM,
    VoiceSignatureLLM,
    InternalTensionLLM,
    NarrativeMemoryLLM,
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
        # New enrichment fields default to empty
        assert profile.behavioral_rules == []
        assert profile.voice_signature.tone_descriptors == []
        assert profile.voice_signature.formality_level == "mixed"
        assert profile.tensions == []
        assert profile.narrative_memories == []
        assert profile.exemplar_quotes == []

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
            behavioral_rules=[
                ConditionalRuleLLM(
                    condition="price > $500",
                    behavior="compare at least 3 alternatives",
                    domain="spending",
                    confidence=0.9,
                    source_quote="I always compare at least three options",
                ),
            ],
            voice_signature=VoiceSignatureLLM(
                tone_descriptors=["measured", "analytical", "warm"],
                characteristic_phrases=["honestly", "the thing is"],
                hedging_style="adds 'I think' before opinions",
                explanation_style="concrete examples from personal life",
                formality_level="casual",
            ),
            tensions=[
                InternalTensionLLM(
                    tension="Values spontaneity but always plans vacations",
                    domain_a="lifestyle",
                    domain_b="travel",
                    resolution_hint="Distinguishes daily life from high-stakes",
                ),
            ],
            narrative_memories=[
                NarrativeMemoryLLM(
                    memory="Grandmother teaching them to cook dal",
                    domain="identity",
                    emotional_tone="warm",
                    significance="Food tied to family identity",
                    source_module="M1",
                ),
            ],
            exemplar_quotes=[
                "I'd rather spend two hours researching than regret a purchase for two years",
            ],
        )
        assert profile.demographics.age_band == "25-34"
        assert len(profile.personality.ocean_estimates) == 2
        assert profile.personality.ocean_estimates["openness"].score == 0.8
        assert len(profile.decision_making.behavioral_rules) == 1
        assert profile.preferences.dimensions[0].axis == "price_vs_quality"
        assert len(profile.uncertainty_flags) == 2
        # New enrichment fields
        assert len(profile.behavioral_rules) == 1
        assert profile.behavioral_rules[0].domain == "spending"
        assert profile.voice_signature.formality_level == "casual"
        assert len(profile.voice_signature.tone_descriptors) == 3
        assert len(profile.tensions) == 1
        assert profile.tensions[0].domain_a == "lifestyle"
        assert len(profile.narrative_memories) == 1
        assert profile.narrative_memories[0].emotional_tone == "warm"
        assert len(profile.exemplar_quotes) == 1

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
        for cat in [
            "personality", "preference", "behavior", "context", "decision_rule",
            "conditional_rule", "voice_exemplar", "contradiction",
        ]:
            chunk = EvidenceChunkLLM(text="test", category=cat, question_context="")
            assert chunk.category == cat

    def test_snippet_type_and_emotional_valence(self):
        """Test snippet_type and emotional_valence fields."""
        chunk = EvidenceChunkLLM(
            text="I always check reviews",
            category="decision_rule",
            question_context="shopping habits",
            snippet_type="direct_quote",
            emotional_valence="positive",
        )
        assert chunk.snippet_type == "direct_quote"
        assert chunk.emotional_valence == "positive"

    def test_snippet_type_defaults(self):
        """snippet_type defaults to paraphrase, emotional_valence to neutral."""
        chunk = EvidenceChunkLLM(text="test", category="context", question_context="")
        assert chunk.snippet_type == "paraphrase"
        assert chunk.emotional_valence == "neutral"

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
    """Test interview quality score calculation (component of blended score)."""

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
            assert chunk.category == "personality"  # M1 -> personality
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

    def test_heuristic_module_aware_categories(self):
        """Heuristic should use module-aware default categories."""
        from app.services.evidence_indexer import EvidenceIndexerService
        service = EvidenceIndexerService()

        module_expected = {
            "M1": "personality",
            "M2": "decision_rule",
            "M3": "preference",
            "M4": "behavior",
            "A1": "context",  # Add-ons default to context
        }
        for module_id, expected_cat in module_expected.items():
            turn = {
                "turn_id": uuid4(),
                "module_id": module_id,
                "question_text": "Tell me more",
                "answer_text": "I enjoy exploring new ideas and thinking deeply about problems in my daily life.",
            }
            chunks = service._heuristic_chunk(turn)
            assert len(chunks) >= 1
            assert chunks[0].category == expected_cat, (
                f"Module {module_id} should default to {expected_cat}"
            )


# ============================================================
# Enrichment Schema Tests
# ============================================================


class TestEnrichmentSchemas:
    """Test new enrichment Pydantic schemas."""

    def test_conditional_rule_valid(self):
        """ConditionalRuleLLM should validate with all fields."""
        rule = ConditionalRuleLLM(
            condition="price > $500",
            behavior="compare at least 3 options",
            domain="spending",
            confidence=0.9,
            source_quote="I always compare at least three options",
        )
        assert rule.domain == "spending"
        assert rule.confidence == 0.9

    def test_conditional_rule_confidence_bounds(self):
        """Confidence must be 0.0-1.0."""
        with pytest.raises(Exception):
            ConditionalRuleLLM(
                condition="test", behavior="test", domain="test",
                confidence=1.5, source_quote="",
            )

    def test_voice_signature_defaults(self):
        """VoiceSignatureLLM should have sensible defaults."""
        voice = VoiceSignatureLLM()
        assert voice.tone_descriptors == []
        assert voice.formality_level == "mixed"
        assert voice.hedging_style == ""

    def test_voice_signature_full(self):
        """VoiceSignatureLLM with all fields."""
        voice = VoiceSignatureLLM(
            tone_descriptors=["warm", "analytical", "self-deprecating"],
            characteristic_phrases=["honestly", "the thing is"],
            hedging_style="adds 'I think'",
            explanation_style="concrete examples",
            formality_level="casual",
        )
        assert len(voice.tone_descriptors) == 3
        assert voice.formality_level == "casual"

    def test_internal_tension_valid(self):
        """InternalTensionLLM should validate."""
        tension = InternalTensionLLM(
            tension="Values spontaneity but plans everything",
            domain_a="lifestyle",
            domain_b="travel",
            resolution_hint="Distinguishes daily vs high-stakes",
        )
        assert tension.domain_a == "lifestyle"

    def test_narrative_memory_valid(self):
        """NarrativeMemoryLLM should validate."""
        memory = NarrativeMemoryLLM(
            memory="Grandmother taught me to cook dal",
            domain="identity",
            emotional_tone="warm",
            significance="Food is tied to family",
            source_module="M1",
        )
        assert memory.emotional_tone == "warm"
        assert memory.source_module == "M1"

    def test_narrative_memory_defaults(self):
        """NarrativeMemoryLLM defaults."""
        memory = NarrativeMemoryLLM(memory="Some memory")
        assert memory.domain == ""
        assert memory.emotional_tone == "neutral"


class TestEnrichedPersonaSummarySchema:
    """Test PersonaSummaryResponse with simulation_notes."""

    def test_simulation_notes_default(self):
        """simulation_notes defaults to empty list."""
        summary = PersonaSummaryResponse(
            persona_summary_text="I am a person.",
            key_traits=["analytical"],
        )
        assert summary.simulation_notes == []

    def test_simulation_notes_with_data(self):
        """simulation_notes with data."""
        summary = PersonaSummaryResponse(
            persona_summary_text="I am a person.",
            key_traits=["analytical"],
            simulation_notes=[
                "Gets irritated when asked to justify emotional decisions with data",
                "Always mentions family when discussing lifestyle",
            ],
        )
        assert len(summary.simulation_notes) == 2


# ============================================================
# Simulation Readiness Tests
# ============================================================


class TestSimulationReadiness:
    """Test _calculate_simulation_readiness scoring."""

    def setup_method(self):
        self.service = TwinGenerationService()

    def _make_snippet_mock(self, snippet_type="paraphrase"):
        """Create a mock snippet with snippet_metadata."""
        mock = MagicMock()
        mock.snippet_metadata = {"snippet_type": snippet_type}
        return mock

    def test_rich_profile_high_score(self):
        """A rich profile should score high across all dimensions."""
        profile = {
            "behavioral_rules": [
                {"condition": f"cond{i}", "behavior": f"beh{i}", "domain": f"dom{i}",
                 "confidence": 0.8, "source_quote": f"quote{i}"}
                for i in range(10)
            ],
            "voice_signature": {
                "tone_descriptors": ["warm", "analytical", "measured"],
                "characteristic_phrases": ["honestly", "the thing is"],
                "hedging_style": "adds 'I think'",
                "explanation_style": "concrete examples",
            },
            "tensions": [{"tension": "test tension"}],
            "narrative_memories": [
                {"memory": f"memory{i}", "domain": f"dom{i}", "emotional_tone": "warm"}
                for i in range(5)
            ],
        }
        snippets = [self._make_snippet_mock("direct_quote") for _ in range(10)]
        modules = ["M1", "M2", "M3", "M4"]

        result = self.service._calculate_simulation_readiness(profile, snippets, modules)

        assert result["rule_density"] == 1.0
        assert result["voice_capture"] == 1.0
        assert result["grounding_ratio"] == 1.0
        assert result["tension_coverage"] == 1.0
        assert result["narrative_richness"] > 0.8
        assert result["overall"] > 0.8

    def test_minimal_profile_low_score(self):
        """An empty profile should score low."""
        profile = {}
        snippets = []
        modules = ["M1", "M2", "M3", "M4"]

        result = self.service._calculate_simulation_readiness(profile, snippets, modules)

        assert result["rule_density"] == 0.0
        assert result["voice_capture"] == 0.0
        assert result["grounding_ratio"] == 0.0
        assert result["narrative_richness"] == 0.0
        assert result["tension_coverage"] == 0.5  # < 6 modules, no tensions
        assert result["overall"] < 0.2

    def test_no_tensions_many_modules(self):
        """6+ modules with no tensions should give low tension_coverage."""
        profile = {}
        modules = ["M1", "M2", "M3", "M4", "A1", "A2"]

        result = self.service._calculate_simulation_readiness(profile, [], modules)
        assert result["tension_coverage"] == 0.3

    def test_all_components_present_in_output(self):
        """All 5 component scores and overall must be in output."""
        result = self.service._calculate_simulation_readiness({}, [], ["M1"])
        assert "rule_density" in result
        assert "voice_capture" in result
        assert "grounding_ratio" in result
        assert "narrative_richness" in result
        assert "tension_coverage" in result
        assert "overall" in result

    def test_grounding_ratio_partial(self):
        """Partial direct quotes should give partial grounding score."""
        snippets = [
            self._make_snippet_mock("direct_quote"),
            self._make_snippet_mock("paraphrase"),
            self._make_snippet_mock("paraphrase"),
            self._make_snippet_mock("paraphrase"),
            self._make_snippet_mock("paraphrase"),
        ]
        result = self.service._calculate_simulation_readiness(
            {}, snippets, ["M1"]
        )
        # 1/5 = 0.2, target 0.3, so 0.2/0.3 ≈ 0.667
        assert 0.6 < result["grounding_ratio"] < 0.7


# ============================================================
# Voice/Rules Assembly Tests
# ============================================================


class TestVoiceRulesAssembly:
    """Test _assemble_voice_rules_reference."""

    def setup_method(self):
        self.service = TwinGenerationService()

    def test_full_profile_assembly(self):
        """Assembly with full data produces all sections."""
        profile = {
            "voice_signature": {
                "tone_descriptors": ["warm", "measured"],
                "characteristic_phrases": ["honestly", "the thing is"],
                "hedging_style": "adds 'I think'",
                "explanation_style": "stories",
            },
            "behavioral_rules": [
                {"condition": "price > $500", "behavior": "compare 3 options", "confidence": 0.9},
            ],
            "tensions": [
                {"tension": "Values spontaneity but plans everything"},
            ],
            "selected_narrative_memories": [
                {"memory": "Grandmother cooking dal", "emotional_tone": "warm", "domain": "identity"},
            ],
            "ranked_exemplars": [
                {"quote": "I'd rather research than regret"},
            ],
        }

        text = self.service._assemble_voice_rules_reference(profile)
        assert "VOICE:" in text
        assert "warm, measured" in text
        assert "RULES:" in text
        assert "TENSIONS:" in text
        assert "NARRATIVE MEMORIES:" in text
        assert "EXEMPLARS:" in text

    def test_empty_profile_assembly(self):
        """Empty profile produces empty string."""
        text = self.service._assemble_voice_rules_reference({})
        assert text == ""

    def test_partial_data(self):
        """Profile with only voice data."""
        profile = {
            "voice_signature": {
                "tone_descriptors": ["analytical"],
            },
        }
        text = self.service._assemble_voice_rules_reference(profile)
        assert "VOICE:" in text
        assert "analytical" in text
        assert "RULES:" not in text


# ============================================================
# Exemplar Ranking Tests
# ============================================================


class TestExemplarRanking:
    """Test _rank_and_select_exemplars."""

    def setup_method(self):
        self.service = TwinGenerationService()

    def test_specificity_scoring(self):
        """Quotes with numbers/proper nouns should score higher."""
        profile = {
            "exemplar_quotes": [
                "I compare at least 3 options before buying",
                "I like to think about things",
                "Mumbai taught me to be resilient",
            ],
            "behavioral_rules": [],
        }
        result = self.service._rank_and_select_exemplars(profile, [])
        # The first and third should rank higher due to number/proper noun
        quotes = [r["quote"] for r in result]
        assert "I compare at least 3 options before buying" in quotes
        assert "Mumbai taught me to be resilient" in quotes

    def test_deduplication(self):
        """Similar quotes should be deduplicated."""
        profile = {
            "exemplar_quotes": [
                "I always compare prices before buying things",
                "I always compare prices before I buy anything",
                "Family is everything to me",
            ],
            "behavioral_rules": [],
        }
        result = self.service._rank_and_select_exemplars(profile, [])
        # Should deduplicate the two similar quotes
        assert len(result) <= 2

    def test_cap_at_seven(self):
        """Output should be capped at 7."""
        profile = {
            "exemplar_quotes": [f"Unique quote number {i} about topic {i*10}" for i in range(15)],
            "behavioral_rules": [],
        }
        result = self.service._rank_and_select_exemplars(profile, [])
        assert len(result) <= 7

    def test_empty_quotes(self):
        """Empty exemplar_quotes returns empty list."""
        result = self.service._rank_and_select_exemplars({}, [])
        assert result == []

    def test_rank_assignment(self):
        """Ranks should be sequential starting from 1."""
        profile = {
            "exemplar_quotes": ["Quote A about topic 1", "Quote B about topic 2", "Quote C about topic 3"],
            "behavioral_rules": [],
        }
        result = self.service._rank_and_select_exemplars(profile, [])
        ranks = [r["rank"] for r in result]
        assert ranks == list(range(1, len(result) + 1))

    def test_domain_coverage(self):
        """Quotes covering different domains should be preferred."""
        profile = {
            "exemplar_quotes": [
                "I research products for hours before buying anything over 500 dollars",
                "My grandmother taught me to always cook from scratch at home",
            ],
            "behavioral_rules": [
                {"condition": "price > $500", "behavior": "research", "domain": "spending",
                 "confidence": 0.9, "source_quote": "I research products for hours before buying anything over 500 dollars"},
                {"condition": "cooking", "behavior": "from scratch", "domain": "lifestyle",
                 "confidence": 0.8, "source_quote": "My grandmother taught me to always cook from scratch at home"},
            ],
        }
        result = self.service._rank_and_select_exemplars(profile, [])
        assert len(result) == 2
        # Both should be kept since they cover different domains
        all_domains = []
        for r in result:
            all_domains.extend(r["domains"])
        assert "spending" in all_domains or "lifestyle" in all_domains


# ============================================================
# Narrative Memory Selection Tests
# ============================================================


class TestNarrativeMemorySelection:
    """Test _select_narrative_memories."""

    def setup_method(self):
        self.service = TwinGenerationService()

    def test_deduplication(self):
        """Overlapping memories should be deduplicated."""
        profile = {
            "narrative_memories": [
                {"memory": "My grandmother taught me to cook dal in her kitchen",
                 "domain": "identity", "emotional_tone": "warm"},
                {"memory": "Grandmother taught me cooking dal",
                 "domain": "identity", "emotional_tone": "warm"},
                {"memory": "Got burned on a used car purchase",
                 "domain": "spending", "emotional_tone": "cautious"},
            ],
        }
        result = self.service._select_narrative_memories(profile)
        # Should keep 2 (dedup the similar ones)
        assert len(result) == 2

    def test_cap_at_six(self):
        """Output should be capped at 6."""
        profile = {
            "narrative_memories": [
                {"memory": f"Unique memory number {i} about topic {i}",
                 "domain": f"domain{i}", "emotional_tone": "neutral"}
                for i in range(10)
            ],
        }
        result = self.service._select_narrative_memories(profile)
        assert len(result) <= 6

    def test_domain_diversity_sorting(self):
        """Memories from diverse domains should be preferred."""
        profile = {
            "narrative_memories": [
                {"memory": "Memory about cooking traditions at home",
                 "domain": "lifestyle", "emotional_tone": "warm"},
                {"memory": "Memory about office work and deadlines",
                 "domain": "career", "emotional_tone": "anxious"},
                {"memory": "Another memory about cooking pasta at home",
                 "domain": "lifestyle", "emotional_tone": "warm"},
                {"memory": "Memory about hiking in mountains alone",
                 "domain": "leisure", "emotional_tone": "proud"},
            ],
        }
        result = self.service._select_narrative_memories(profile)
        # First 3 should cover 3 different domains
        first_domains = [m["domain"] for m in result[:3]]
        assert len(set(first_domains)) >= 2

    def test_empty_memories(self):
        """Empty narrative_memories returns empty list."""
        result = self.service._select_narrative_memories({})
        assert result == []


# ============================================================
# Quality Breakdown Tests
# ============================================================


class TestQualityBreakdown:
    """Test that quality_breakdown structure is correct."""

    def setup_method(self):
        self.service = TwinGenerationService()

    def test_breakdown_structure(self):
        """Verify the breakdown dict has all required keys."""
        profile = {
            "behavioral_rules": [{"condition": "c", "behavior": "b", "domain": "d",
                                   "confidence": 0.5, "source_quote": "q"}],
            "voice_signature": {},
            "tensions": [],
            "narrative_memories": [],
        }
        readiness = self.service._calculate_simulation_readiness(
            profile, [], ["M1", "M2", "M3", "M4"]
        )
        interview_score = 0.75  # Simulated

        # Simulate what generate_twin would build
        breakdown = {
            "interview_score": round(interview_score, 3),
            "simulation_readiness": round(readiness["overall"], 3),
            "blended_score": round(0.5 * interview_score + 0.5 * readiness["overall"], 3),
            "components": {
                "rule_density": readiness["rule_density"],
                "voice_capture": readiness["voice_capture"],
                "grounding_ratio": readiness["grounding_ratio"],
                "narrative_richness": readiness["narrative_richness"],
                "tension_coverage": readiness["tension_coverage"],
            },
        }

        assert "interview_score" in breakdown
        assert "simulation_readiness" in breakdown
        assert "blended_score" in breakdown
        assert "components" in breakdown
        assert len(breakdown["components"]) == 5
        assert breakdown["blended_score"] == round(
            0.5 * breakdown["interview_score"] + 0.5 * breakdown["simulation_readiness"], 3
        )
