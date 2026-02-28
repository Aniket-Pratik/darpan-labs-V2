"""Tests for enhanced interview system (narrative extraction, conversation memory,
confidence-weighted scoring, intent-based questions, multi-factor completion)."""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.schemas.llm_responses import (
    AdaptiveQuestionResponse,
    AdaptiveQuestionResult,
    BehavioralRule,
    ExtractedSignal,
    ModuleCompletionResponse,
    ModuleCompletionResult,
    NarrativeSnippet,
    OpenLoop,
    ParsedAnswer,
    ParsedAnswerResponse,
    StyleMarker,
)
from app.services.answer_parser_service import AnswerParserService
from app.services.prompt_service import PromptService
from app.services.question_bank_service import Question


# ============================================================
# 1. Schema Tests
# ============================================================


class TestNewSchemaModels:
    """Test new Pydantic models and extended fields."""

    def test_narrative_snippet_valid(self):
        ns = NarrativeSnippet(text="I quit my job last year", category="anecdote")
        assert ns.text == "I quit my job last year"
        assert ns.category == "anecdote"

    def test_narrative_snippet_all_categories(self):
        for cat in ["anecdote", "self_description", "rule_of_thumb",
                     "preference_statement", "emotional_reveal"]:
            ns = NarrativeSnippet(text="test", category=cat)
            assert ns.category == cat

    def test_narrative_snippet_invalid_category(self):
        with pytest.raises(Exception):
            NarrativeSnippet(text="test", category="invalid")

    def test_style_marker_valid(self):
        sm = StyleMarker(marker="hedges_frequently", evidence="pretty, kind of")
        assert sm.marker == "hedges_frequently"
        assert sm.evidence == "pretty, kind of"

    def test_open_loop_valid(self):
        ol = OpenLoop(topic="startup role", reason="didn't explain why they left")
        assert ol.topic == "startup role"
        assert ol.source_signal == ""

    def test_open_loop_with_signal(self):
        ol = OpenLoop(topic="spending habits", reason="vague", source_signal="price_vs_quality")
        assert ol.source_signal == "price_vs_quality"

    def test_parsed_answer_response_defaults(self):
        """All new fields have defaults — backward compat with existing LLM responses."""
        response = ParsedAnswerResponse(
            specificity_score=0.5,
            signals_extracted=[],
            needs_followup=False,
            sentiment="neutral",
        )
        assert response.narrative_snippets == []
        assert response.style_markers == []
        assert response.exceptions_mentioned == []
        assert response.contradiction_candidates == []
        assert response.self_descriptors == []
        assert response.open_loops == []
        assert response.exemplar_quality == 0.5

    def test_parsed_answer_response_full(self):
        response = ParsedAnswerResponse(
            specificity_score=0.85,
            signals_extracted=[
                ExtractedSignal(signal="risk_appetite", value="high", confidence=0.9)
            ],
            behavioral_rules=[
                BehavioralRule(rule="if reversible then fast", confidence=0.8)
            ],
            needs_followup=False,
            sentiment="positive",
            narrative_snippets=[
                NarrativeSnippet(text="I quit my job", category="anecdote")
            ],
            style_markers=[
                StyleMarker(marker="storyteller", evidence="told vivid story")
            ],
            exceptions_mentioned=["except for books"],
            contradiction_candidates=["said risk-averse but quit job"],
            self_descriptors=["I'm pretty methodical"],
            open_loops=[
                OpenLoop(topic="startup role", reason="didn't elaborate")
            ],
            exemplar_quality=0.9,
        )
        assert len(response.narrative_snippets) == 1
        assert len(response.style_markers) == 1
        assert response.exemplar_quality == 0.9

    def test_parsed_answer_from_llm_response_maps_new_fields(self):
        response = ParsedAnswerResponse(
            specificity_score=0.7,
            signals_extracted=[],
            needs_followup=False,
            sentiment="neutral",
            narrative_snippets=[
                NarrativeSnippet(text="test quote", category="anecdote")
            ],
            style_markers=[
                StyleMarker(marker="verbose", evidence="long answer")
            ],
            exceptions_mentioned=["unless tired"],
            contradiction_candidates=["contradiction 1"],
            self_descriptors=["I'm careful"],
            open_loops=[
                OpenLoop(topic="career change", reason="hinted but didn't explain")
            ],
            exemplar_quality=0.8,
        )
        parsed = ParsedAnswer.from_llm_response(response)
        assert len(parsed.narrative_snippets) == 1
        assert parsed.narrative_snippets[0].text == "test quote"
        assert len(parsed.style_markers) == 1
        assert parsed.style_markers[0].marker == "verbose"
        assert parsed.exceptions_mentioned == ["unless tired"]
        assert parsed.contradiction_candidates == ["contradiction 1"]
        assert parsed.self_descriptors == ["I'm careful"]
        assert len(parsed.open_loops) == 1
        assert parsed.exemplar_quality == 0.8


class TestAdaptiveQuestionIntent:
    """Test question intent on AdaptiveQuestionResponse/Result."""

    def test_adaptive_question_response_default_intent(self):
        response = AdaptiveQuestionResponse(
            action="ASK_QUESTION",
            question_text="Tell me about your day",
            question_type="open_text",
            target_signal="daily_routine_pattern",
            rationale_short="exploration",
        )
        assert response.question_intent == "EXPLORE"

    def test_adaptive_question_response_with_intent(self):
        response = AdaptiveQuestionResponse(
            action="ASK_QUESTION",
            question_text="You said X but now Y",
            question_type="open_text",
            target_signal="risk_appetite",
            rationale_short="contradiction",
            question_intent="CLARIFY",
        )
        assert response.question_intent == "CLARIFY"

    def test_adaptive_question_result_maps_intent(self):
        response = AdaptiveQuestionResponse(
            action="ASK_QUESTION",
            question_text="Walk me through last time",
            question_type="open_text",
            target_signal="speed_vs_deliberation",
            rationale_short="deepen",
            question_intent="DEEPEN",
        )
        result = AdaptiveQuestionResult.from_llm_response(response)
        assert result.question_intent == "DEEPEN"

    def test_adaptive_question_response_rejects_invalid_intent(self):
        """Pydantic Literal validation catches invalid intents at schema level."""
        with pytest.raises(Exception):
            AdaptiveQuestionResponse(
                action="ASK_QUESTION",
                question_text="test",
                question_type="open_text",
                target_signal="test",
                rationale_short="test",
                question_intent="INVALID_INTENT",
            )

    def test_adaptive_question_result_normalizes_intent_case(self):
        """from_llm_response normalizes case for valid intents."""
        response = AdaptiveQuestionResponse(
            action="ASK_QUESTION",
            question_text="test",
            question_type="open_text",
            target_signal="test",
            rationale_short="test",
            question_intent="DEEPEN",
        )
        result = AdaptiveQuestionResult.from_llm_response(response)
        assert result.question_intent == "DEEPEN"

    def test_adaptive_question_result_default_intent(self):
        result = AdaptiveQuestionResult(
            action="ASK_QUESTION",
            question_text="test",
            language="EN",
            question_type="open_text",
            target_signal="test",
            rationale="test",
        )
        assert result.question_intent == "EXPLORE"


class TestModuleCompletionMultiFactor:
    """Test multi-factor fields on ModuleCompletionResponse/Result."""

    def test_module_completion_response_defaults(self):
        response = ModuleCompletionResponse(
            module_id="M1",
            is_complete=True,
            coverage_score=0.8,
            confidence_score=0.7,
            recommendation="COMPLETE",
        )
        assert response.narrative_depth_score == 0.0
        assert response.style_coverage_score == 0.0
        assert response.contradiction_count == 0
        assert response.twin_readiness_score == 0.0

    def test_module_completion_response_with_multifactor(self):
        response = ModuleCompletionResponse(
            module_id="M2",
            is_complete=True,
            coverage_score=0.85,
            confidence_score=0.75,
            recommendation="COMPLETE",
            narrative_depth_score=0.7,
            style_coverage_score=0.6,
            contradiction_count=2,
            twin_readiness_score=0.72,
        )
        assert response.narrative_depth_score == 0.7
        assert response.twin_readiness_score == 0.72

    def test_module_completion_result_from_llm_maps_new_fields(self):
        response = ModuleCompletionResponse(
            module_id="M1",
            is_complete=True,
            coverage_score=0.9,
            confidence_score=0.8,
            recommendation="COMPLETE",
            narrative_depth_score=0.75,
            style_coverage_score=0.65,
            contradiction_count=3,
            twin_readiness_score=0.78,
        )
        result = ModuleCompletionResult.from_llm_response(response)
        assert result.narrative_depth_score == 0.75
        assert result.style_coverage_score == 0.65
        assert result.contradiction_count == 3
        assert result.twin_readiness_score == 0.78


# ============================================================
# 2. Conversation State Tests
# ============================================================


class TestConversationState:
    """Test conversation state init and update logic."""

    def _make_interview_session(self, settings=None):
        """Create a mock InterviewSession."""
        mock = MagicMock()
        mock.settings = settings or {}
        return mock

    def _make_parsed_answer(self, **kwargs):
        """Create a ParsedAnswer with defaults."""
        defaults = {
            "specificity_score": 0.5,
            "signals_extracted": [],
            "behavioral_rules": [],
            "needs_followup": False,
            "followup_reason": None,
            "sentiment": "neutral",
            "language": "EN",
            "narrative_snippets": [],
            "style_markers": [],
            "exceptions_mentioned": [],
            "contradiction_candidates": [],
            "self_descriptors": [],
            "open_loops": [],
            "exemplar_quality": 0.5,
        }
        defaults.update(kwargs)
        return ParsedAnswer(**defaults)

    def test_init_conversation_state(self):
        from app.services.interview_service import InterviewService
        state = InterviewService._init_conversation_state()
        assert state["themes"] == []
        assert state["style_hypothesis"] == []
        assert state["open_loops"] == []
        assert state["notable_quotes"] == []
        assert state["engagement_trend"] == []
        assert state["follow_up_count"] == 0
        assert state["contradiction_log"] == []
        assert state["self_descriptors"] == []

    def test_update_adds_open_loops(self):
        from app.services.interview_service import InterviewService
        interview = self._make_interview_session({
            "conversation_state": InterviewService._init_conversation_state()
        })
        parsed = self._make_parsed_answer(
            open_loops=[OpenLoop(topic="startup", reason="hinted at it")]
        )
        InterviewService._update_conversation_state(interview, parsed, "some answer")
        state = interview.settings["conversation_state"]
        assert len(state["open_loops"]) == 1
        assert state["open_loops"][0]["topic"] == "startup"

    def test_update_deduplicates_open_loops(self):
        from app.services.interview_service import InterviewService
        interview = self._make_interview_session({
            "conversation_state": {
                **InterviewService._init_conversation_state(),
                "open_loops": [{"topic": "startup", "reason": "first"}],
            }
        })
        parsed = self._make_parsed_answer(
            open_loops=[OpenLoop(topic="startup", reason="second mention")]
        )
        InterviewService._update_conversation_state(interview, parsed, "answer")
        state = interview.settings["conversation_state"]
        assert len(state["open_loops"]) == 1  # Not duplicated

    def test_update_caps_open_loops_at_10(self):
        from app.services.interview_service import InterviewService
        existing_loops = [{"topic": f"topic_{i}", "reason": "r"} for i in range(9)]
        interview = self._make_interview_session({
            "conversation_state": {
                **InterviewService._init_conversation_state(),
                "open_loops": existing_loops,
            }
        })
        parsed = self._make_parsed_answer(
            open_loops=[
                OpenLoop(topic="new_topic_1", reason="r"),
                OpenLoop(topic="new_topic_2", reason="r"),
            ]
        )
        InterviewService._update_conversation_state(interview, parsed, "answer")
        state = interview.settings["conversation_state"]
        assert len(state["open_loops"]) == 10

    def test_update_adds_style_markers(self):
        from app.services.interview_service import InterviewService
        interview = self._make_interview_session({
            "conversation_state": InterviewService._init_conversation_state()
        })
        parsed = self._make_parsed_answer(
            style_markers=[StyleMarker(marker="verbose", evidence="long answer")]
        )
        InterviewService._update_conversation_state(interview, parsed, "answer text")
        state = interview.settings["conversation_state"]
        assert len(state["style_hypothesis"]) == 1
        assert state["style_hypothesis"][0]["marker"] == "verbose"

    def test_update_notable_quotes_sorted_by_quality(self):
        from app.services.interview_service import InterviewService
        interview = self._make_interview_session({
            "conversation_state": InterviewService._init_conversation_state()
        })
        # First answer: low quality
        parsed1 = self._make_parsed_answer(
            narrative_snippets=[NarrativeSnippet(text="vague thing", category="anecdote")],
            exemplar_quality=0.2,
        )
        InterviewService._update_conversation_state(interview, parsed1, "vague")
        # Second answer: high quality
        parsed2 = self._make_parsed_answer(
            narrative_snippets=[NarrativeSnippet(text="vivid story", category="anecdote")],
            exemplar_quality=0.9,
        )
        InterviewService._update_conversation_state(interview, parsed2, "vivid story")
        state = interview.settings["conversation_state"]
        assert len(state["notable_quotes"]) == 2
        # Highest quality first
        assert state["notable_quotes"][0]["text"] == "vivid story"
        assert state["notable_quotes"][0]["exemplar_quality"] == 0.9

    def test_update_tracks_engagement_trend(self):
        from app.services.interview_service import InterviewService
        interview = self._make_interview_session({
            "conversation_state": InterviewService._init_conversation_state()
        })
        parsed = self._make_parsed_answer()
        InterviewService._update_conversation_state(
            interview, parsed, "This is a five word answer"
        )
        state = interview.settings["conversation_state"]
        assert state["engagement_trend"] == [6]  # 6 words

    def test_update_caps_engagement_trend_at_20(self):
        from app.services.interview_service import InterviewService
        interview = self._make_interview_session({
            "conversation_state": {
                **InterviewService._init_conversation_state(),
                "engagement_trend": list(range(20)),
            }
        })
        parsed = self._make_parsed_answer()
        InterviewService._update_conversation_state(interview, parsed, "new answer")
        state = interview.settings["conversation_state"]
        assert len(state["engagement_trend"]) == 20

    def test_update_increments_followup_count(self):
        from app.services.interview_service import InterviewService
        interview = self._make_interview_session({
            "conversation_state": InterviewService._init_conversation_state()
        })
        parsed = self._make_parsed_answer(needs_followup=True)
        InterviewService._update_conversation_state(interview, parsed, "vague answer")
        state = interview.settings["conversation_state"]
        assert state["follow_up_count"] == 1

    def test_update_adds_self_descriptors(self):
        from app.services.interview_service import InterviewService
        interview = self._make_interview_session({
            "conversation_state": InterviewService._init_conversation_state()
        })
        parsed = self._make_parsed_answer(
            self_descriptors=["I'm pretty cautious", "I consider myself analytical"]
        )
        InterviewService._update_conversation_state(interview, parsed, "answer")
        state = interview.settings["conversation_state"]
        assert len(state["self_descriptors"]) == 2

    def test_update_adds_contradictions(self):
        from app.services.interview_service import InterviewService
        interview = self._make_interview_session({
            "conversation_state": InterviewService._init_conversation_state()
        })
        parsed = self._make_parsed_answer(
            contradiction_candidates=["said risk-averse but quit stable job"]
        )
        InterviewService._update_conversation_state(interview, parsed, "answer")
        state = interview.settings["conversation_state"]
        assert len(state["contradiction_log"]) == 1


# ============================================================
# 3. Confidence-Weighted Scoring Tests
# ============================================================


class TestConfidenceWeightedScoring:
    """Test confidence-weighted coverage in module_state_service."""

    def _make_module(self, **kwargs):
        """Create a mock InterviewModule."""
        mock = MagicMock()
        mock.module_id = kwargs.get("module_id", "M2")
        mock.question_count = kwargs.get("question_count", 0)
        mock.signals_captured = kwargs.get("signals_captured", [])
        mock.coverage_score = kwargs.get("coverage_score", 0.0)
        mock.confidence_score = kwargs.get("confidence_score", 0.0)
        mock.completion_eval = kwargs.get("completion_eval", None)
        return mock

    @pytest.mark.asyncio
    async def test_confidence_weighted_coverage(self):
        from app.services.module_state_service import ModuleStateService

        mock_qb = MagicMock()
        mock_qb.get_signal_targets.return_value = ["sig_a", "sig_b"]

        service = ModuleStateService(question_bank=mock_qb)

        module = self._make_module(question_count=0, signals_captured=[])
        parsed = ParsedAnswer(
            specificity_score=0.7,
            signals_extracted=[
                ExtractedSignal(signal="sig_a", value="test", confidence=0.6),
            ],
            behavioral_rules=[],
            needs_followup=False,
            followup_reason=None,
            sentiment="neutral",
            language="EN",
        )

        mock_session = AsyncMock()
        await service.update_module_after_answer(mock_session, module, parsed)

        # coverage = 0.6 (sig_a confidence) / 2 (total signals) = 0.3
        assert abs(module.coverage_score - 0.3) < 0.01

    @pytest.mark.asyncio
    async def test_signal_confidence_max_tracking(self):
        from app.services.module_state_service import ModuleStateService

        mock_qb = MagicMock()
        mock_qb.get_signal_targets.return_value = ["sig_a"]

        service = ModuleStateService(question_bank=mock_qb)

        module = self._make_module(
            question_count=1,
            signals_captured=["sig_a"],
            confidence_score=0.5,
            completion_eval={"signal_confidences": {"sig_a": 0.4}},
        )
        parsed = ParsedAnswer(
            specificity_score=0.8,
            signals_extracted=[
                ExtractedSignal(signal="sig_a", value="updated", confidence=0.9),
            ],
            behavioral_rules=[],
            needs_followup=False,
            followup_reason=None,
            sentiment="neutral",
            language="EN",
        )

        mock_session = AsyncMock()
        await service.update_module_after_answer(mock_session, module, parsed)

        # Max confidence for sig_a should be 0.9 (updated from 0.4)
        assert module.completion_eval["signal_confidences"]["sig_a"] == 0.9
        # coverage = 0.9 / 1 = 0.9
        assert abs(module.coverage_score - 0.9) < 0.01

    @pytest.mark.asyncio
    async def test_narrative_count_increments(self):
        from app.services.module_state_service import ModuleStateService

        mock_qb = MagicMock()
        mock_qb.get_signal_targets.return_value = ["sig_a"]

        service = ModuleStateService(question_bank=mock_qb)

        module = self._make_module(question_count=0, signals_captured=[])
        parsed = ParsedAnswer(
            specificity_score=0.7,
            signals_extracted=[],
            behavioral_rules=[],
            needs_followup=False,
            followup_reason=None,
            sentiment="neutral",
            language="EN",
            narrative_snippets=[
                NarrativeSnippet(text="story 1", category="anecdote"),
                NarrativeSnippet(text="feeling", category="emotional_reveal"),
                NarrativeSnippet(text="pref", category="preference_statement"),
            ],
        )

        mock_session = AsyncMock()
        await service.update_module_after_answer(mock_session, module, parsed)

        # Only anecdote + emotional_reveal count
        assert module.completion_eval["narrative_count"] == 2

    @pytest.mark.asyncio
    async def test_style_marker_count_tracks(self):
        from app.services.module_state_service import ModuleStateService

        mock_qb = MagicMock()
        mock_qb.get_signal_targets.return_value = []

        service = ModuleStateService(question_bank=mock_qb)

        module = self._make_module(question_count=0, signals_captured=[])
        parsed = ParsedAnswer(
            specificity_score=0.5,
            signals_extracted=[],
            behavioral_rules=[],
            needs_followup=False,
            followup_reason=None,
            sentiment="neutral",
            language="EN",
            style_markers=[
                StyleMarker(marker="verbose", evidence="long"),
                StyleMarker(marker="storyteller", evidence="vivid"),
            ],
        )

        mock_session = AsyncMock()
        await service.update_module_after_answer(mock_session, module, parsed)

        assert module.completion_eval["style_marker_count"] == 2


# ============================================================
# 4. Heuristic Fallback Tests
# ============================================================


class TestHeuristicFallbackEnhanced:
    """Test enhanced heuristic fallback in AnswerParserService."""

    def test_verbose_style_detection(self):
        service = AnswerParserService(llm_client=MagicMock(), prompt_service=MagicMock())
        long_answer = " ".join(["word"] * 100)
        result = service._parse_heuristic(long_answer, "test_signal")
        markers = [m.marker for m in result.style_markers]
        assert "verbose" in markers

    def test_terse_style_detection(self):
        service = AnswerParserService(llm_client=MagicMock(), prompt_service=MagicMock())
        result = service._parse_heuristic("Yes, sure.", "test_signal")
        markers = [m.marker for m in result.style_markers]
        assert "terse" in markers

    def test_no_style_marker_for_medium_length(self):
        service = AnswerParserService(llm_client=MagicMock(), prompt_service=MagicMock())
        medium_answer = " ".join(["word"] * 30)
        result = service._parse_heuristic(medium_answer, "test_signal")
        markers = [m.marker for m in result.style_markers]
        assert "verbose" not in markers
        assert "terse" not in markers

    def test_self_descriptor_regex_im_pretty(self):
        service = AnswerParserService(llm_client=MagicMock(), prompt_service=MagicMock())
        result = service._parse_heuristic(
            "I'm pretty cautious when it comes to money.", "test"
        )
        assert len(result.self_descriptors) >= 1
        assert any("pretty cautious" in d for d in result.self_descriptors)

    def test_self_descriptor_regex_i_tend(self):
        service = AnswerParserService(llm_client=MagicMock(), prompt_service=MagicMock())
        result = service._parse_heuristic(
            "I tend to be analytical about these things.", "test"
        )
        assert len(result.self_descriptors) >= 1

    def test_self_descriptor_no_match(self):
        service = AnswerParserService(llm_client=MagicMock(), prompt_service=MagicMock())
        result = service._parse_heuristic(
            "The weather is nice today.", "test"
        )
        assert len(result.self_descriptors) == 0

    def test_exemplar_quality_computation(self):
        service = AnswerParserService(llm_client=MagicMock(), prompt_service=MagicMock())
        # High specificity → exemplar capped at 0.5
        long_answer = " ".join(["word"] * 100) + " 42 years daily"
        result = service._parse_heuristic(long_answer, "test")
        assert result.exemplar_quality <= 0.5

    def test_exemplar_quality_low_for_vague(self):
        service = AnswerParserService(llm_client=MagicMock(), prompt_service=MagicMock())
        result = service._parse_heuristic("ok", "test")
        assert result.exemplar_quality < 0.2

    def test_anecdote_detection_via_regex(self):
        service = AnswerParserService(llm_client=MagicMock(), prompt_service=MagicMock())
        result = service._parse_heuristic(
            "Last time I went shopping I spent way too much money on clothes.", "test"
        )
        assert len(result.narrative_snippets) >= 1
        assert result.narrative_snippets[0].category == "anecdote"

    def test_no_anecdote_for_generic_answer(self):
        service = AnswerParserService(llm_client=MagicMock(), prompt_service=MagicMock())
        result = service._parse_heuristic(
            "I usually prefer quality over price.", "test"
        )
        assert len(result.narrative_snippets) == 0


# ============================================================
# 5. Prompt Tests
# ============================================================


class TestPromptEnhancements:
    """Test that prompts load and format correctly with new placeholders."""

    def test_interviewer_prompt_includes_conversation_state(self):
        service = PromptService()
        conversation_state = {"open_loops": [{"topic": "career"}], "style_hypothesis": []}
        prompt = service.get_interviewer_question_prompt(
            module_id="M1",
            module_name="Core Identity",
            module_goal="Understand who they are",
            signal_targets=["occupation", "age_band"],
            questions_asked=3,
            max_questions=15,
            coverage=0.4,
            confidence=0.5,
            captured_signals=["occupation"],
            missing_signals=["age_band"],
            recent_turns=[],
            cross_module_summary="No modules completed.",
            sensitivity_settings={},
            conversation_state=conversation_state,
        )
        assert "career" in prompt
        assert "open_loops" in prompt

    def test_interviewer_prompt_without_conversation_state(self):
        """Backward compat: conversation_state defaults to empty dict."""
        service = PromptService()
        prompt = service.get_interviewer_question_prompt(
            module_id="M1",
            module_name="Core Identity",
            module_goal="Understand who they are",
            signal_targets=["occupation"],
            questions_asked=1,
            max_questions=15,
            coverage=0.0,
            confidence=0.0,
            captured_signals=[],
            missing_signals=["occupation"],
            recent_turns=[],
            cross_module_summary="No modules completed.",
            sensitivity_settings={},
        )
        assert "question_intent" in prompt  # New output format present
        assert "EXPLORE" in prompt  # Intent system present

    def test_answer_parser_prompt_loads_with_narrative_section(self):
        service = PromptService()
        prompt = service.load_prompt("answer_parser")
        assert "NARRATIVE & STYLE EXTRACTION" in prompt
        assert "narrative_snippets" in prompt
        assert "style_markers" in prompt
        assert "exemplar_quality" in prompt

    def test_module_completion_prompt_has_multi_factor(self):
        service = PromptService()
        prompt = service.load_prompt("module_completion")
        assert "MULTI-FACTOR EVALUATION" in prompt
        assert "twin_readiness_score" in prompt
        assert "narrative_depth_score" in prompt
        assert "style_coverage_score" in prompt


# ============================================================
# 6. Question Bank Intent Tests
# ============================================================


class TestQuestionBankIntent:
    """Test optional intent field on Question model."""

    def test_question_defaults_to_explore(self):
        q = Question(
            question_id="test_q1",
            question_text="Tell me about yourself",
            question_type="open_text",
            target_signals=["self_described_personality"],
        )
        assert q.intent == "EXPLORE"

    def test_question_with_explicit_intent(self):
        q = Question(
            question_id="test_q2",
            question_text="You mentioned X but also Y...",
            question_type="open_text",
            target_signals=["risk_appetite"],
            intent="CLARIFY",
        )
        assert q.intent == "CLARIFY"

    def test_question_all_intents_valid(self):
        for intent in ["EXPLORE", "DEEPEN", "CONTRAST", "CLARIFY", "RESOLVE"]:
            q = Question(
                question_id="test",
                question_text="test",
                question_type="open_text",
                target_signals=["test"],
                intent=intent,
            )
            assert q.intent == intent

    def test_question_invalid_intent_rejected(self):
        with pytest.raises(Exception):
            Question(
                question_id="test",
                question_text="test",
                question_type="open_text",
                target_signals=["test"],
                intent="INVALID",
            )


# ============================================================
# 7. Module Completion Heuristic Multi-Factor Tests
# ============================================================


class TestModuleCompletionHeuristic:
    """Test multi-factor heuristic completion evaluation."""

    def _make_module(self, **kwargs):
        mock = MagicMock()
        mock.module_id = kwargs.get("module_id", "M1")
        mock.question_count = kwargs.get("question_count", 5)
        mock.signals_captured = kwargs.get("signals_captured", ["a", "b", "c"])
        mock.coverage_score = kwargs.get("coverage_score", 0.7)
        mock.confidence_score = kwargs.get("confidence_score", 0.6)
        mock.completion_eval = kwargs.get("completion_eval", {
            "narrative_count": 5,
            "style_marker_count": 4,
            "contradiction_count": 1,
        })
        return mock

    def _make_criteria(self):
        mock = MagicMock()
        mock.coverage_threshold = 0.6
        mock.confidence_threshold = 0.5
        mock.min_questions = 3
        return mock

    def test_heuristic_twin_readiness_calculation(self):
        from app.services.module_state_service import ModuleStateService
        service = ModuleStateService(question_bank=MagicMock())
        module = self._make_module()
        criteria = self._make_criteria()

        result = service._evaluate_heuristic(module, criteria)

        # narrative_depth = min(5/5, 1.0) = 1.0
        # style_coverage = min(4/4, 1.0) = 1.0
        # twin_readiness = 0.4*0.7 + 0.25*0.6 + 0.2*1.0 + 0.15*1.0 = 0.28+0.15+0.2+0.15 = 0.78
        assert result.twin_readiness_score == pytest.approx(0.78, abs=0.01)
        assert result.is_complete is True
        assert result.narrative_depth_score == 1.0
        assert result.style_coverage_score == 1.0

    def test_heuristic_incomplete_low_readiness(self):
        from app.services.module_state_service import ModuleStateService
        service = ModuleStateService(question_bank=MagicMock())
        module = self._make_module(
            coverage_score=0.3,
            confidence_score=0.3,
            question_count=2,
            completion_eval={
                "narrative_count": 0,
                "style_marker_count": 0,
                "contradiction_count": 0,
            },
        )
        criteria = self._make_criteria()

        result = service._evaluate_heuristic(module, criteria)

        # twin_readiness = 0.4*0.3 + 0.25*0.3 + 0.2*0 + 0.15*0 = 0.12+0.075 = 0.195
        assert result.twin_readiness_score == pytest.approx(0.195, abs=0.01)
        assert result.is_complete is False

    def test_heuristic_legacy_complete_overrides(self):
        """Legacy thresholds can still trigger completion even with low readiness metrics."""
        from app.services.module_state_service import ModuleStateService

        mock_qb = MagicMock()
        mock_qb.get_signal_targets.return_value = ["a", "b"]

        service = ModuleStateService(question_bank=mock_qb)
        module = self._make_module(
            coverage_score=0.7,
            confidence_score=0.6,
            question_count=5,
            completion_eval={
                "narrative_count": 0,
                "style_marker_count": 0,
                "contradiction_count": 0,
            },
        )
        criteria = self._make_criteria()

        result = service._evaluate_heuristic(module, criteria)
        # Legacy: coverage 0.7 >= 0.6, confidence 0.6 >= 0.5, questions 5 >= 3
        assert result.is_complete is True
