"""Tests for SQLAlchemy database models."""

import uuid

from app.models.user import User
from app.models.consent import ConsentEvent
from app.models.interview import InterviewSession, InterviewModule, InterviewTurn
from app.models.twin import TwinProfile, EvidenceSnippet
from app.models.chat import TwinChatSession, TwinChatMessage
from app.models.experiment import Cohort, Experiment, ExperimentResult


class TestUserModel:
    """Tests for User model."""

    def test_user_creation_with_required_fields(self):
        """Test User model instantiation with required fields."""
        user = User(
            email="test@example.com",
            display_name="Test User",
        )
        assert user.email == "test@example.com"
        assert user.display_name == "Test User"
        assert user.auth_provider_id is None

    def test_user_creation_with_all_fields(self):
        """Test User model instantiation with all fields."""
        user_id = uuid.uuid4()
        user = User(
            id=user_id,
            email="test@example.com",
            display_name="Test User",
            auth_provider_id="google-oauth2|12345",
        )
        assert user.id == user_id
        assert user.auth_provider_id == "google-oauth2|12345"

    def test_user_repr(self):
        """Test User model string representation."""
        user = User(
            email="test@example.com",
            display_name="Test User",
        )
        assert "User" in repr(user)
        assert "test@example.com" in repr(user)


class TestConsentEventModel:
    """Tests for ConsentEvent model."""

    def test_consent_event_creation(self):
        """Test ConsentEvent model instantiation."""
        user_id = uuid.uuid4()
        consent = ConsentEvent(
            user_id=user_id,
            consent_type="interview",
            consent_version="1.0",
            accepted=True,
        )
        assert consent.user_id == user_id
        assert consent.consent_type == "interview"
        assert consent.consent_version == "1.0"
        assert consent.accepted is True
        assert consent.consent_metadata is None

    def test_consent_event_with_metadata(self):
        """Test ConsentEvent with metadata."""
        consent = ConsentEvent(
            user_id=uuid.uuid4(),
            consent_type="audio_storage",
            consent_version="1.0",
            accepted=True,
            consent_metadata={"ip_address": "127.0.0.1", "user_agent": "test"},
        )
        assert consent.consent_metadata["ip_address"] == "127.0.0.1"

    def test_consent_event_repr(self):
        """Test ConsentEvent string representation."""
        consent = ConsentEvent(
            user_id=uuid.uuid4(),
            consent_type="interview",
            consent_version="1.0",
            accepted=False,
        )
        assert "ConsentEvent" in repr(consent)
        assert "interview" in repr(consent)


class TestInterviewSessionModel:
    """Tests for InterviewSession model."""

    def test_interview_session_creation_defaults(self):
        """Test InterviewSession with default values.

        Note: SQLAlchemy column defaults are applied at DB level, not on object creation.
        We test that values can be set and optional fields are None when not provided.
        """
        user_id = uuid.uuid4()
        session = InterviewSession(
            user_id=user_id,
            status="active",
            input_mode="text",
            language_preference="auto",
        )
        assert session.user_id == user_id
        assert session.status == "active"
        assert session.input_mode == "text"
        assert session.language_preference == "auto"
        assert session.ended_at is None
        assert session.total_duration_sec is None

    def test_interview_session_creation_voice_mode(self):
        """Test InterviewSession with voice mode."""
        session = InterviewSession(
            user_id=uuid.uuid4(),
            status="active",
            input_mode="voice",
            language_preference="hi",
            settings={"sensitivity_settings": {"finance": False}},
        )
        assert session.input_mode == "voice"
        assert session.language_preference == "hi"
        assert session.settings["sensitivity_settings"]["finance"] is False

    def test_interview_session_repr(self):
        """Test InterviewSession string representation."""
        session = InterviewSession(user_id=uuid.uuid4(), status="completed")
        assert "InterviewSession" in repr(session)
        assert "completed" in repr(session)


class TestInterviewModuleModel:
    """Tests for InterviewModule model."""

    def test_interview_module_creation_defaults(self):
        """Test InterviewModule with default values.

        Note: SQLAlchemy column defaults are applied at DB level, not on object creation.
        """
        session_id = uuid.uuid4()
        module = InterviewModule(
            session_id=session_id,
            module_id="M1",
            status="pending",
            question_count=0,
            coverage_score=0.0,
            confidence_score=0.0,
        )
        assert module.session_id == session_id
        assert module.module_id == "M1"
        assert module.status == "pending"
        assert module.question_count == 0
        assert module.coverage_score == 0.0
        assert module.confidence_score == 0.0

    def test_interview_module_all_statuses(self):
        """Test InterviewModule with different statuses."""
        for status in ["pending", "active", "completed", "skipped"]:
            module = InterviewModule(
                session_id=uuid.uuid4(),
                module_id="M2",
                status=status,
            )
            assert module.status == status

    def test_interview_module_with_scores(self):
        """Test InterviewModule with coverage and confidence scores."""
        module = InterviewModule(
            session_id=uuid.uuid4(),
            module_id="M3",
            status="completed",
            question_count=10,
            coverage_score=0.85,
            confidence_score=0.9,
            signals_captured=["signal_1", "signal_2"],
            completion_eval={"passed": True, "reason": "All criteria met"},
        )
        assert module.question_count == 10
        assert module.coverage_score == 0.85
        assert module.confidence_score == 0.9
        assert "signal_1" in module.signals_captured

    def test_interview_module_repr(self):
        """Test InterviewModule string representation."""
        module = InterviewModule(
            session_id=uuid.uuid4(),
            module_id="M1",
            status="active",
        )
        assert "InterviewModule" in repr(module)
        assert "M1" in repr(module)


class TestInterviewTurnModel:
    """Tests for InterviewTurn model."""

    def test_interview_turn_interviewer(self):
        """Test InterviewTurn for interviewer role."""
        turn = InterviewTurn(
            session_id=uuid.uuid4(),
            module_id="M1",
            turn_index=0,
            role="interviewer",
            question_text="What is your occupation?",
            question_meta={"category": "identity", "type": "open_text"},
        )
        assert turn.role == "interviewer"
        assert turn.question_text == "What is your occupation?"
        assert turn.question_meta["category"] == "identity"

    def test_interview_turn_user_text(self):
        """Test InterviewTurn for user text response."""
        turn = InterviewTurn(
            session_id=uuid.uuid4(),
            module_id="M1",
            turn_index=1,
            role="user",
            input_mode="text",
            answer_text="I am a software engineer",
            answer_language="EN",
            answer_structured={"occupation": "software engineer"},
            answer_meta={"sentiment": "neutral", "specificity": "high"},
        )
        assert turn.role == "user"
        assert turn.answer_text == "I am a software engineer"
        assert turn.answer_language == "EN"

    def test_interview_turn_user_voice(self):
        """Test InterviewTurn for user voice response."""
        turn = InterviewTurn(
            session_id=uuid.uuid4(),
            module_id="M2",
            turn_index=3,
            role="user",
            input_mode="voice",
            answer_text="Main ek doctor hoon",
            answer_raw_transcript="main ek doctor hun",
            answer_language="HG",
            audio_meta={"duration_ms": 2500, "sample_rate": 16000, "asr_confidence": 0.95},
            audio_storage_ref="s3://bucket/audio/turn_123.wav",
        )
        assert turn.input_mode == "voice"
        assert turn.answer_raw_transcript == "main ek doctor hun"
        assert turn.audio_meta["asr_confidence"] == 0.95

    def test_interview_turn_repr(self):
        """Test InterviewTurn string representation."""
        turn = InterviewTurn(
            session_id=uuid.uuid4(),
            module_id="M1",
            turn_index=0,
            role="interviewer",
        )
        assert "InterviewTurn" in repr(turn)
        assert "interviewer" in repr(turn)


class TestTwinProfileModel:
    """Tests for TwinProfile model."""

    def test_twin_profile_creation_defaults(self):
        """Test TwinProfile with default values.

        Note: SQLAlchemy column defaults are applied at DB level, not on object creation.
        """
        user_id = uuid.uuid4()
        twin = TwinProfile(
            user_id=user_id,
            modules_included=["M1", "M2", "M3", "M4"],
            version=1,
            status="generating",
            quality_label="base",
            quality_score=0.0,
        )
        assert twin.user_id == user_id
        assert twin.version == 1
        assert twin.status == "generating"
        assert twin.quality_label == "base"
        assert twin.quality_score == 0.0

    def test_twin_profile_full_creation(self):
        """Test TwinProfile with all fields."""
        twin = TwinProfile(
            user_id=uuid.uuid4(),
            version=2,
            status="ready",
            modules_included=["M1", "M2", "M3", "M4", "A1"],
            quality_label="enhanced",
            quality_score=0.85,
            structured_profile_json={
                "demographics": {"age_range": "25-34"},
                "personality": {"openness": "high"},
            },
            persona_summary_text="A tech-savvy professional...",
            persona_full_text="Detailed narrative...",
            coverage_confidence={"M1": 0.9, "M2": 0.85},
            extraction_meta={"model": "gpt-4", "prompt_version": "1.0"},
        )
        assert twin.status == "ready"
        assert twin.quality_label == "enhanced"
        assert twin.structured_profile_json["personality"]["openness"] == "high"

    def test_twin_profile_repr(self):
        """Test TwinProfile string representation."""
        twin = TwinProfile(
            user_id=uuid.uuid4(),
            modules_included=["M1"],
            quality_label="full",
        )
        assert "TwinProfile" in repr(twin)
        assert "full" in repr(twin)


class TestEvidenceSnippetModel:
    """Tests for EvidenceSnippet model."""

    def test_evidence_snippet_creation(self):
        """Test EvidenceSnippet creation."""
        snippet = EvidenceSnippet(
            user_id=uuid.uuid4(),
            module_id="M1",
            turn_id=uuid.uuid4(),
            snippet_text="I prefer working from home because it gives me flexibility.",
            snippet_category="preference",
        )
        assert snippet.snippet_category == "preference"
        assert "flexibility" in snippet.snippet_text
        assert snippet.embedding is None

    def test_evidence_snippet_with_embedding(self):
        """Test EvidenceSnippet with vector embedding."""
        embedding = [0.1] * 1536  # OpenAI embedding dimension
        snippet = EvidenceSnippet(
            user_id=uuid.uuid4(),
            module_id="M2",
            turn_id=uuid.uuid4(),
            snippet_text="I make decisions based on data.",
            snippet_category="behavior",
            embedding=embedding,
            snippet_metadata={"confidence": 0.9, "source": "direct_statement"},
        )
        assert snippet.embedding is not None
        assert len(snippet.embedding) == 1536
        assert snippet.snippet_metadata["confidence"] == 0.9

    def test_evidence_snippet_categories(self):
        """Test different snippet categories."""
        for category in ["personality", "preference", "behavior", "context"]:
            snippet = EvidenceSnippet(
                user_id=uuid.uuid4(),
                module_id="M1",
                turn_id=uuid.uuid4(),
                snippet_text="Test snippet",
                snippet_category=category,
            )
            assert snippet.snippet_category == category

    def test_evidence_snippet_repr(self):
        """Test EvidenceSnippet string representation."""
        snippet = EvidenceSnippet(
            user_id=uuid.uuid4(),
            module_id="M1",
            turn_id=uuid.uuid4(),
            snippet_text="Test",
            snippet_category="personality",
        )
        assert "EvidenceSnippet" in repr(snippet)
        assert "personality" in repr(snippet)


class TestTwinChatSessionModel:
    """Tests for TwinChatSession model."""

    def test_twin_chat_session_creation(self):
        """Test TwinChatSession creation."""
        twin_id = uuid.uuid4()
        user_id = uuid.uuid4()
        session = TwinChatSession(
            twin_id=twin_id,
            created_by=user_id,
        )
        assert session.twin_id == twin_id
        assert session.created_by == user_id

    def test_twin_chat_session_repr(self):
        """Test TwinChatSession string representation."""
        twin_id = uuid.uuid4()
        session = TwinChatSession(
            twin_id=twin_id,
            created_by=uuid.uuid4(),
        )
        assert "TwinChatSession" in repr(session)


class TestTwinChatMessageModel:
    """Tests for TwinChatMessage model."""

    def test_chat_message_user_role(self):
        """Test TwinChatMessage for user role."""
        message = TwinChatMessage(
            session_id=uuid.uuid4(),
            role="user",
            content="What would you do in this situation?",
        )
        assert message.role == "user"
        assert message.content == "What would you do in this situation?"
        assert message.confidence_score is None

    def test_chat_message_twin_role(self):
        """Test TwinChatMessage for twin role."""
        message = TwinChatMessage(
            session_id=uuid.uuid4(),
            role="twin",
            content="Based on my preferences, I would...",
            confidence_score=0.85,
            confidence_label="high",
            evidence_used=[{"snippet_id": "abc123", "why": "Directly relevant"}],
            coverage_gaps=["financial_decisions"],
            model_meta={"model": "gpt-4", "tokens": 150, "latency_ms": 1200},
        )
        assert message.role == "twin"
        assert message.confidence_score == 0.85
        assert message.confidence_label == "high"
        assert len(message.evidence_used) == 1

    def test_chat_message_repr(self):
        """Test TwinChatMessage string representation."""
        message = TwinChatMessage(
            session_id=uuid.uuid4(),
            role="twin",
            content="Test",
        )
        assert "TwinChatMessage" in repr(message)
        assert "twin" in repr(message)


class TestCohortModel:
    """Tests for Cohort model."""

    def test_cohort_creation(self):
        """Test Cohort creation."""
        user_id = uuid.uuid4()
        twin_ids = [uuid.uuid4(), uuid.uuid4(), uuid.uuid4()]
        cohort = Cohort(
            created_by=user_id,
            name="Urban Millennials",
            twin_ids=twin_ids,
        )
        assert cohort.name == "Urban Millennials"
        assert len(cohort.twin_ids) == 3
        assert cohort.filters_used is None

    def test_cohort_with_filters(self):
        """Test Cohort with filters."""
        cohort = Cohort(
            created_by=uuid.uuid4(),
            name="High Quality Twins",
            twin_ids=[uuid.uuid4()],
            filters_used={
                "quality_label": "enhanced",
                "modules_required": ["M1", "M2", "M3", "M4"],
                "min_quality_score": 0.7,
            },
        )
        assert cohort.filters_used["quality_label"] == "enhanced"
        assert cohort.filters_used["min_quality_score"] == 0.7

    def test_cohort_repr(self):
        """Test Cohort string representation."""
        cohort = Cohort(
            created_by=uuid.uuid4(),
            name="Test Cohort",
            twin_ids=[uuid.uuid4(), uuid.uuid4()],
        )
        assert "Cohort" in repr(cohort)
        assert "Test Cohort" in repr(cohort)


class TestExperimentModel:
    """Tests for Experiment model."""

    def test_experiment_creation_defaults(self):
        """Test Experiment with default values.

        Note: SQLAlchemy column defaults are applied at DB level, not on object creation.
        """
        experiment = Experiment(
            created_by=uuid.uuid4(),
            name="Price Sensitivity Test",
            cohort_id=uuid.uuid4(),
            scenario={
                "type": "forced_choice",
                "prompt": "Would you pay $50 or $75 for this product?",
                "options": ["$50", "$75"],
            },
            status="pending",
        )
        assert experiment.name == "Price Sensitivity Test"
        assert experiment.status == "pending"
        assert experiment.scenario["type"] == "forced_choice"
        assert experiment.completed_at is None

    def test_experiment_all_statuses(self):
        """Test Experiment with different statuses."""
        for status in ["pending", "running", "completed", "failed"]:
            experiment = Experiment(
                created_by=uuid.uuid4(),
                name="Test",
                cohort_id=uuid.uuid4(),
                scenario={"type": "open_ended", "prompt": "Test"},
                status=status,
            )
            assert experiment.status == status

    def test_experiment_with_results(self):
        """Test Experiment with aggregate results."""
        experiment = Experiment(
            created_by=uuid.uuid4(),
            name="Feature Preference",
            cohort_id=uuid.uuid4(),
            scenario={
                "type": "forced_choice",
                "prompt": "Which feature matters more?",
                "options": ["Speed", "Price"],
            },
            status="completed",
            settings={"temperature": 0.5, "max_tokens": 500},
            aggregate_results={
                "total_responses": 100,
                "distribution": {"Speed": 60, "Price": 40},
                "avg_confidence": 0.78,
            },
        )
        assert experiment.aggregate_results["total_responses"] == 100
        assert experiment.settings["temperature"] == 0.5

    def test_experiment_repr(self):
        """Test Experiment string representation."""
        experiment = Experiment(
            created_by=uuid.uuid4(),
            name="Test Exp",
            cohort_id=uuid.uuid4(),
            scenario={"type": "test"},
            status="running",
        )
        assert "Experiment" in repr(experiment)
        assert "running" in repr(experiment)


class TestExperimentResultModel:
    """Tests for ExperimentResult model."""

    def test_experiment_result_creation(self):
        """Test ExperimentResult creation."""
        result = ExperimentResult(
            experiment_id=uuid.uuid4(),
            twin_id=uuid.uuid4(),
            choice="Option A",
            reasoning="Based on my preference for quality over price...",
            confidence_score=0.85,
            confidence_label="high",
        )
        assert result.choice == "Option A"
        assert result.confidence_score == 0.85
        assert result.confidence_label == "high"

    def test_experiment_result_with_evidence(self):
        """Test ExperimentResult with evidence and gaps."""
        result = ExperimentResult(
            experiment_id=uuid.uuid4(),
            twin_id=uuid.uuid4(),
            choice="Budget Option",
            reasoning="I typically prioritize saving money.",
            confidence_score=0.6,
            confidence_label="medium",
            evidence_used=[
                {"snippet_id": "snp_1", "why": "Direct price preference"},
                {"snippet_id": "snp_2", "why": "Historical spending pattern"},
            ],
            coverage_gaps=["luxury_preferences", "impulse_buying"],
            model_meta={"model": "gpt-4", "tokens": 200},
        )
        assert len(result.evidence_used) == 2
        assert "luxury_preferences" in result.coverage_gaps
        assert result.model_meta["tokens"] == 200

    def test_experiment_result_confidence_labels(self):
        """Test ExperimentResult confidence labels."""
        for label in ["low", "medium", "high"]:
            result = ExperimentResult(
                experiment_id=uuid.uuid4(),
                twin_id=uuid.uuid4(),
                reasoning="Test reasoning",
                confidence_score=0.5,
                confidence_label=label,
            )
            assert result.confidence_label == label

    def test_experiment_result_repr(self):
        """Test ExperimentResult string representation."""
        result = ExperimentResult(
            experiment_id=uuid.uuid4(),
            twin_id=uuid.uuid4(),
            choice="Test Choice",
            reasoning="Test",
            confidence_score=0.7,
            confidence_label="medium",
        )
        assert "ExperimentResult" in repr(result)


class TestModelTableNames:
    """Tests to verify correct table names for all models."""

    def test_all_table_names(self):
        """Verify all 12 table names are correctly defined."""
        assert User.__tablename__ == "users"
        assert ConsentEvent.__tablename__ == "consent_events"
        assert InterviewSession.__tablename__ == "interview_sessions"
        assert InterviewModule.__tablename__ == "interview_modules"
        assert InterviewTurn.__tablename__ == "interview_turns"
        assert TwinProfile.__tablename__ == "twin_profiles"
        assert EvidenceSnippet.__tablename__ == "evidence_snippets"
        assert TwinChatSession.__tablename__ == "twin_chat_sessions"
        assert TwinChatMessage.__tablename__ == "twin_chat_messages"
        assert Cohort.__tablename__ == "cohorts"
        assert Experiment.__tablename__ == "experiments"
        assert ExperimentResult.__tablename__ == "experiment_results"
