"""Tests for Pydantic schemas validation."""

import pytest
from uuid import uuid4

from app.schemas import (
    InterviewStartRequest,
    InterviewStartResponse,
    InterviewAnswerRequest,
    TwinChatRequest,
    CohortCreateRequest,
    ExperimentCreateRequest,
    ExperimentScenario,
    HealthResponse,
)


def test_interview_start_request_valid():
    """Test InterviewStartRequest with valid data."""
    request = InterviewStartRequest(
        user_id=uuid4(),
        input_mode="voice",
        language_preference="auto",
        modules_to_complete=["M1", "M2", "M3", "M4"],
    )
    assert request.input_mode == "voice"
    assert len(request.modules_to_complete) == 4


def test_interview_start_request_defaults():
    """Test InterviewStartRequest default values."""
    request = InterviewStartRequest(user_id=uuid4())
    assert request.input_mode == "text"
    assert request.language_preference == "auto"
    assert request.modules_to_complete == ["M1", "M2", "M3", "M4"]


def test_interview_answer_request_valid():
    """Test InterviewAnswerRequest with valid data."""
    request = InterviewAnswerRequest(
        answer_text="I work as a software engineer",
        question_id="M1_q01",
    )
    assert request.answer_text == "I work as a software engineer"


def test_twin_chat_request_valid():
    """Test TwinChatRequest with valid data."""
    request = TwinChatRequest(
        message="How would you react to a price increase?",
    )
    assert request.message == "How would you react to a price increase?"


def test_cohort_create_request_valid():
    """Test CohortCreateRequest with valid data."""
    request = CohortCreateRequest(
        name="Test Cohort",
        twin_ids=[uuid4(), uuid4()],
    )
    assert request.name == "Test Cohort"
    assert len(request.twin_ids) == 2


def test_experiment_create_request_valid():
    """Test ExperimentCreateRequest with valid data."""
    request = ExperimentCreateRequest(
        name="Pricing Test",
        cohort_id=uuid4(),
        scenario=ExperimentScenario(
            type="forced_choice",
            prompt="Would you prefer A or B?",
            options=["Option A", "Option B"],
        ),
    )
    assert request.name == "Pricing Test"
    assert request.scenario.type == "forced_choice"


def test_health_response_valid():
    """Test HealthResponse with valid data."""
    from datetime import datetime, timezone

    response = HealthResponse(
        status="healthy",
        version="0.1.0",
        database="connected",
        timestamp=datetime.now(timezone.utc),
    )
    assert response.status == "healthy"
