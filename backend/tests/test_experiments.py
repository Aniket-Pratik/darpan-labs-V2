"""Tests for Phase 4: Experiment Engine + Cohort Management."""

import uuid
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.schemas.experiment import (
    AggregateResults,
    ChoiceDistribution,
    CohortCreateRequest,
    CohortCreateResponse,
    CohortFilters,
    CohortResponse,
    ExperimentCreateRequest,
    ExperimentCreateResponse,
    ExperimentListItem,
    ExperimentResultsResponse,
    ExperimentScenario,
    ExperimentSettings,
    IndividualResult,
    KeyPattern,
    TwinSummary,
)
from app.services.prompt_service import get_prompt_service


# =============================================================================
# Experiment Schemas
# =============================================================================


class TestExperimentScenario:
    """Test ExperimentScenario schema."""

    def test_forced_choice(self):
        s = ExperimentScenario(
            type="forced_choice",
            prompt="Which do you prefer?",
            options=["A", "B"],
        )
        assert s.type == "forced_choice"
        assert len(s.options) == 2

    def test_likert_scale(self):
        s = ExperimentScenario(
            type="likert_scale",
            prompt="Rate from 1-5",
        )
        assert s.type == "likert_scale"
        assert s.options is None

    def test_open_scenario(self):
        s = ExperimentScenario(
            type="open_scenario",
            prompt="What would you do?",
            context="You're at a store.",
        )
        assert s.context == "You're at a store."

    def test_preference_rank(self):
        s = ExperimentScenario(
            type="preference_rank",
            prompt="Rank these",
            options=["X", "Y", "Z"],
        )
        assert len(s.options) == 3

    def test_invalid_type_rejected(self):
        with pytest.raises(ValidationError):
            ExperimentScenario(type="invalid", prompt="test")


class TestExperimentSettings:
    """Test ExperimentSettings schema."""

    def test_defaults(self):
        s = ExperimentSettings()
        assert s.require_reasoning is True
        assert s.temperature == 0.2
        assert s.max_tokens == 500

    def test_custom_settings(self):
        s = ExperimentSettings(
            require_reasoning=False,
            temperature=0.5,
            max_tokens=300,
        )
        assert s.require_reasoning is False
        assert s.temperature == 0.5


class TestExperimentCreateRequest:
    """Test ExperimentCreateRequest schema."""

    def test_valid_request(self):
        req = ExperimentCreateRequest(
            name="Test Experiment",
            cohort_id=uuid.uuid4(),
            scenario=ExperimentScenario(
                type="forced_choice",
                prompt="Pick one",
                options=["A", "B"],
            ),
        )
        assert req.name == "Test Experiment"
        assert req.settings.temperature == 0.2  # default

    def test_with_custom_settings(self):
        req = ExperimentCreateRequest(
            name="Custom",
            cohort_id=uuid.uuid4(),
            scenario=ExperimentScenario(type="open_scenario", prompt="test"),
            settings=ExperimentSettings(temperature=0.8),
        )
        assert req.settings.temperature == 0.8


class TestExperimentCreateResponse:
    """Test ExperimentCreateResponse schema."""

    def test_valid_response(self):
        resp = ExperimentCreateResponse(
            experiment_id=uuid.uuid4(),
            status="running",
            cohort_size=10,
            estimated_completion_sec=15,
        )
        assert resp.status == "running"


class TestIndividualResult:
    """Test IndividualResult schema."""

    def test_full_result(self):
        r = IndividualResult(
            twin_id=uuid.uuid4(),
            twin_quality="enhanced",
            modules_completed=["M1", "M2", "M3", "M4", "A1"],
            choice="Option A",
            reasoning="I prefer A because of my values.",
            confidence_score=0.85,
            confidence_label="high",
            evidence_used=[{"snippet_id": "abc", "why": "relevant"}],
            coverage_gaps=["lifestyle"],
        )
        assert r.choice == "Option A"
        assert r.confidence_label == "high"

    def test_no_choice_open_scenario(self):
        r = IndividualResult(
            twin_id=uuid.uuid4(),
            twin_quality="base",
            modules_completed=["M1", "M2", "M3", "M4"],
            choice=None,
            reasoning="I would explore the store first.",
            confidence_score=0.6,
            confidence_label="medium",
        )
        assert r.choice is None


class TestAggregateResults:
    """Test AggregateResults schema."""

    def test_empty_aggregate(self):
        a = AggregateResults(aggregate_confidence=0.0)
        assert a.aggregate_confidence == 0
        assert a.choice_distribution == {}

    def test_full_aggregate(self):
        a = AggregateResults(
            choice_distribution={
                "A": ChoiceDistribution(count=7, percentage=70.0),
                "B": ChoiceDistribution(count=3, percentage=30.0),
            },
            aggregate_confidence=0.78,
            confidence_distribution={"high": 5, "medium": 3, "low": 2},
            key_patterns=[
                KeyPattern(
                    pattern="Most prefer A for convenience",
                    supporting_twins=6,
                    confidence=0.8,
                )
            ],
            dominant_reasoning_themes=["convenience", "price sensitivity"],
        )
        assert a.choice_distribution["A"].count == 7
        assert len(a.key_patterns) == 1
        assert len(a.dominant_reasoning_themes) == 2


class TestExperimentResultsResponse:
    """Test ExperimentResultsResponse schema."""

    def test_completed_response(self):
        now = datetime.now(timezone.utc)
        resp = ExperimentResultsResponse(
            experiment_id=uuid.uuid4(),
            name="Test",
            status="completed",
            cohort_size=10,
            completed_responses=10,
            execution_time_sec=12.5,
            aggregate_results=AggregateResults(aggregate_confidence=0.75),
            individual_results=[],
            created_at=now,
            completed_at=now,
        )
        assert resp.status == "completed"
        assert "simulated" in resp.limitations_disclaimer.lower()

    def test_running_response(self):
        resp = ExperimentResultsResponse(
            experiment_id=uuid.uuid4(),
            name="In Progress",
            status="running",
            cohort_size=20,
            completed_responses=8,
            created_at=datetime.now(timezone.utc),
        )
        assert resp.aggregate_results is None
        assert resp.completed_at is None


class TestExperimentListItem:
    """Test ExperimentListItem schema."""

    def test_list_item(self):
        item = ExperimentListItem(
            id=uuid.uuid4(),
            name="Experiment 1",
            status="completed",
            cohort_size=15,
            created_at=datetime.now(timezone.utc),
        )
        assert item.status == "completed"


# =============================================================================
# Cohort Schemas
# =============================================================================


class TestCohortSchemas:
    """Test Cohort-related schemas."""

    def test_cohort_filters_defaults(self):
        f = CohortFilters()
        assert f.min_quality is None
        assert f.required_modules == []

    def test_cohort_filters_with_values(self):
        f = CohortFilters(
            min_quality="enhanced",
            required_modules=["M1", "M2", "M3", "M4"],
        )
        assert f.min_quality == "enhanced"

    def test_cohort_create_request(self):
        req = CohortCreateRequest(
            name="Test Cohort",
            twin_ids=[uuid.uuid4(), uuid.uuid4()],
        )
        assert len(req.twin_ids) == 2
        assert req.filters is None

    def test_cohort_create_response(self):
        resp = CohortCreateResponse(
            id=uuid.uuid4(),
            name="Test",
            twin_count=5,
            created_at=datetime.now(timezone.utc),
        )
        assert resp.twin_count == 5

    def test_twin_summary(self):
        ts = TwinSummary(
            twin_id=uuid.uuid4(),
            quality_label="rich",
            quality_score=0.85,
            modules_completed=["M1", "M2", "M3", "M4", "A1", "A2", "A3"],
        )
        assert ts.quality_label == "rich"

    def test_cohort_response(self):
        cr = CohortResponse(
            id=uuid.uuid4(),
            name="My Cohort",
            twin_ids=[uuid.uuid4()],
            twins=[
                TwinSummary(
                    twin_id=uuid.uuid4(),
                    quality_label="base",
                    quality_score=0.7,
                    modules_completed=["M1", "M2", "M3", "M4"],
                )
            ],
            created_at=datetime.now(timezone.utc),
        )
        assert len(cr.twins) == 1


# =============================================================================
# Prompt Template
# =============================================================================


class TestExperimentPrompt:
    """Test experiment response prompt template."""

    def test_prompt_loads(self):
        svc = get_prompt_service()
        prompt = svc.load_prompt("experiment_response")
        assert "experiment_type" in prompt
        assert "persona_profile_payload" in prompt
        assert "retrieved_evidence" in prompt

    def test_prompt_formats(self):
        svc = get_prompt_service()
        formatted = svc.format_prompt(
            "experiment_response",
            experiment_type="forced_choice",
            persona_profile_payload="I am a 30-year-old professional...",
            retrieved_evidence="[abc123] Prefers quality over price",
            completed_modules="M1, M2, M3, M4",
            experiment_prompt="Which cola do you prefer?",
            options="1. Coca-Cola\n2. Pepsi",
        )
        assert "forced_choice" in formatted
        assert "Coca-Cola" in formatted


# =============================================================================
# Service Instantiation
# =============================================================================


class TestServiceInstantiation:
    """Test that services can be instantiated."""

    def test_cohort_service_creates(self):
        from app.services.cohort_service import CohortService, get_cohort_service

        svc = CohortService()
        assert svc is not None
        singleton = get_cohort_service()
        assert singleton is not None

    def test_experiment_service_creates(self):
        from app.services.experiment_service import (
            ExperimentService,
            get_experiment_service,
        )

        svc = ExperimentService()
        assert svc is not None
        singleton = get_experiment_service()
        assert singleton is not None


# =============================================================================
# Question Banks (Add-ons A1-A4)
# =============================================================================


class TestAddonQuestionBanks:
    """Test that add-on question banks load correctly."""

    def test_a1_loads(self):
        from app.services.question_bank_service import get_question_bank_service

        svc = get_question_bank_service()
        bank = svc.load_question_bank("A1")
        assert bank.module_id == "A1"
        assert bank.module_name == "Lifestyle & Routines"
        assert len(bank.questions) == 15
        assert len(bank.signal_targets) == 8

    def test_a2_loads(self):
        from app.services.question_bank_service import get_question_bank_service

        svc = get_question_bank_service()
        bank = svc.load_question_bank("A2")
        assert bank.module_id == "A2"
        assert len(bank.questions) == 15

    def test_a3_loads(self):
        from app.services.question_bank_service import get_question_bank_service

        svc = get_question_bank_service()
        bank = svc.load_question_bank("A3")
        assert bank.module_id == "A3"
        assert len(bank.questions) == 15

    def test_a4_loads(self):
        from app.services.question_bank_service import get_question_bank_service

        svc = get_question_bank_service()
        bank = svc.load_question_bank("A4")
        assert bank.module_id == "A4"
        assert len(bank.questions) == 15

    def test_addon_modules_are_addon_type(self):
        from app.services.question_bank_service import get_question_bank_service

        svc = get_question_bank_service()
        modules = svc.get_all_modules()
        addon_modules = [m for m in modules if m.module_type == "addon"]
        assert len(addon_modules) == 4
        assert [m.module_id for m in addon_modules] == ["A1", "A2", "A3", "A4"]

    def test_mandatory_modules_unchanged(self):
        from app.services.question_bank_service import get_question_bank_service

        svc = get_question_bank_service()
        mandatory = svc.get_mandatory_modules()
        assert mandatory == ["M1", "M2", "M3", "M4"]

    def test_all_addon_questions_have_signals(self):
        from app.services.question_bank_service import get_question_bank_service

        svc = get_question_bank_service()
        for mid in ["A1", "A2", "A3", "A4"]:
            bank = svc.load_question_bank(mid)
            for q in bank.questions:
                assert len(q.target_signals) > 0, f"{q.question_id} has no signals"

    def test_all_addon_completion_criteria(self):
        from app.services.question_bank_service import get_question_bank_service

        svc = get_question_bank_service()
        for mid in ["A1", "A2", "A3", "A4"]:
            criteria = svc.get_module_completion_criteria(mid)
            assert criteria.coverage_threshold == 0.65
            assert criteria.confidence_threshold == 0.60
            assert criteria.min_questions == 4


# =============================================================================
# Router Registration
# =============================================================================


class TestRouterRegistration:
    """Test that experiment and cohort routers are properly configured."""

    def test_cohort_router_has_routes(self):
        from app.routers.cohorts import router

        paths = [r.path for r in router.routes if hasattr(r, "path")]
        assert "/cohorts" in paths or "" in paths
        assert any("cohort_id" in p for p in paths)

    def test_experiment_router_has_routes(self):
        from app.routers.experiments import router

        paths = [r.path for r in router.routes if hasattr(r, "path")]
        assert any("experiment_id" in p for p in paths)

    def test_cohort_router_methods(self):
        from app.routers.cohorts import router

        methods = set()
        for r in router.routes:
            if hasattr(r, "methods"):
                methods.update(r.methods)
        assert "GET" in methods
        assert "POST" in methods
        assert "DELETE" in methods

    def test_experiment_router_methods(self):
        from app.routers.experiments import router

        methods = set()
        for r in router.routes:
            if hasattr(r, "methods"):
                methods.update(r.methods)
        assert "GET" in methods
        assert "POST" in methods
