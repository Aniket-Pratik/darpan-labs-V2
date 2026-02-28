"""Tests for Phase 2b: Twin Chat."""

import pytest
from uuid import uuid4

from app.schemas.chat import (
    TwinChatRequest,
    TwinChatResponse,
    ChatMessageResponse,
    ChatHistoryResponse,
    EvidenceUsed,
)
from app.schemas.llm_responses import TwinResponseLLM, EvidenceUsedLLM


# ============================================================
# Chat Schema Tests
# ============================================================


class TestChatSchemas:
    """Test twin chat Pydantic schemas."""

    def test_chat_request_minimal(self):
        """Minimal chat request should validate."""
        req = TwinChatRequest(message="What phone would you buy?")
        assert req.message == "What phone would you buy?"
        assert req.session_id is None

    def test_chat_request_with_session(self):
        """Chat request with session ID should validate."""
        sid = uuid4()
        req = TwinChatRequest(message="Tell me more", session_id=sid)
        assert req.session_id == sid

    def test_chat_response(self):
        """Full chat response should validate."""
        response = TwinChatResponse(
            session_id=uuid4(),
            message_id=uuid4(),
            response_text="I would choose the iPhone.",
            confidence_score=0.85,
            confidence_label="high",
            uncertainty_reason=None,
            evidence_used=[
                EvidenceUsed(
                    snippet_id="s1",
                    why="User prefers premium products",
                    snippet_text="I always buy the best quality",
                ),
            ],
            coverage_gaps=[],
            suggested_module=None,
        )
        assert response.confidence_label == "high"
        assert len(response.evidence_used) == 1
        assert response.evidence_used[0].snippet_text is not None

    def test_chat_response_low_confidence(self):
        """Low confidence response with gaps should validate."""
        response = TwinChatResponse(
            session_id=uuid4(),
            message_id=uuid4(),
            response_text="I'm not sure about my health habits.",
            confidence_score=0.3,
            confidence_label="low",
            uncertainty_reason="No health module (A6) data",
            evidence_used=[],
            coverage_gaps=["health", "wellness"],
            suggested_module="A6",
        )
        assert response.confidence_label == "low"
        assert response.suggested_module == "A6"
        assert len(response.coverage_gaps) == 2

    def test_chat_message_response_user(self):
        """User message response should validate."""
        from datetime import datetime
        msg = ChatMessageResponse(
            id=uuid4(),
            role="user",
            content="What do you think?",
            created_at=datetime.now(),
        )
        assert msg.role == "user"
        assert msg.confidence_score is None

    def test_chat_message_response_twin(self):
        """Twin message response should validate."""
        from datetime import datetime
        msg = ChatMessageResponse(
            id=uuid4(),
            role="twin",
            content="I think quality matters most.",
            confidence_score=0.8,
            confidence_label="high",
            evidence_used=[
                EvidenceUsed(snippet_id="s1", why="quality preference"),
            ],
            coverage_gaps=None,
            created_at=datetime.now(),
        )
        assert msg.role == "twin"
        assert msg.confidence_score == 0.8

    def test_chat_history_response(self):
        """Chat history response should validate."""
        from datetime import datetime
        history = ChatHistoryResponse(
            session_id=uuid4(),
            twin_id=uuid4(),
            messages=[
                ChatMessageResponse(
                    id=uuid4(),
                    role="user",
                    content="Hello",
                    created_at=datetime.now(),
                ),
                ChatMessageResponse(
                    id=uuid4(),
                    role="twin",
                    content="Hi there!",
                    confidence_score=0.9,
                    confidence_label="high",
                    created_at=datetime.now(),
                ),
            ],
            created_at=datetime.now(),
        )
        assert len(history.messages) == 2
        assert history.messages[0].role == "user"
        assert history.messages[1].role == "twin"

    def test_evidence_used(self):
        """EvidenceUsed should validate with and without snippet_text."""
        e1 = EvidenceUsed(snippet_id="s1", why="relevant")
        assert e1.snippet_text is None

        e2 = EvidenceUsed(snippet_id="s2", why="relevant", snippet_text="I prefer X")
        assert e2.snippet_text == "I prefer X"


# ============================================================
# TwinResponseLLM Schema Tests
# ============================================================


class TestTwinResponseLLMSchema:
    """Test TwinResponseLLM schema used for LLM output validation."""

    def test_all_confidence_labels(self):
        """All confidence labels should be valid."""
        for label in ["low", "medium", "high"]:
            response = TwinResponseLLM(
                response_text="Test",
                confidence_score=0.5,
                confidence_label=label,
            )
            assert response.confidence_label == label

    def test_invalid_confidence_label_rejected(self):
        """Invalid confidence label should fail validation."""
        with pytest.raises(Exception):
            TwinResponseLLM(
                response_text="Test",
                confidence_score=0.5,
                confidence_label="very_high",
            )

    def test_evidence_used_llm(self):
        """EvidenceUsedLLM should validate."""
        e = EvidenceUsedLLM(snippet_id="s_001", why="Supports preference")
        assert e.snippet_id == "s_001"

    def test_optional_fields_default(self):
        """Optional fields should default properly."""
        response = TwinResponseLLM(
            response_text="I would choose A.",
            confidence_score=0.7,
            confidence_label="medium",
        )
        assert response.uncertainty_reason is None
        assert response.evidence_used == []
        assert response.coverage_gaps == []
        assert response.suggested_module is None


# ============================================================
# Chat Service Format Tests
# ============================================================


class TestChatServiceFormatting:
    """Test chat service formatting helpers."""

    def test_format_evidence(self):
        from app.services.twin_chat_service import TwinChatService
        service = TwinChatService()

        evidence = [
            {
                "snippet_id": "s1",
                "text": "I prefer quality over price",
                "category": "preference",
                "module_id": "M3",
                "question_context": "",
                "relevance_score": 0.9,
            }
        ]
        result = service._format_evidence(evidence)
        assert "s1" in result
        assert "preference" in result
        assert "quality over price" in result

    def test_format_evidence_empty(self):
        from app.services.twin_chat_service import TwinChatService
        service = TwinChatService()

        result = service._format_evidence([])
        assert "no relevant evidence" in result.lower()

    def test_format_chat_history(self):
        from app.services.twin_chat_service import TwinChatService
        service = TwinChatService()

        history = [
            {"role": "user", "content": "Hello"},
            {"role": "twin", "content": "Hi there!"},
        ]
        result = service._format_chat_history(history)
        assert "User: Hello" in result
        assert "Twin: Hi there!" in result

    def test_format_chat_history_empty(self):
        from app.services.twin_chat_service import TwinChatService
        service = TwinChatService()

        result = service._format_chat_history([])
        assert "no previous" in result.lower()


# ============================================================
# Router Tests
# ============================================================


class TestChatRouterRegistration:
    """Test that chat routes are properly registered."""

    def test_chat_routes_exist(self):
        from app.routers.chat import router
        paths = [r.path for r in router.routes]
        assert "/twins/{twin_id}/chat" in paths
        assert "/twins/{twin_id}/chat/sessions" in paths
        assert "/twins/{twin_id}/chat/{session_id}/history" in paths

    def test_twins_routes_exist(self):
        from app.routers.twins import router
        paths = [r.path for r in router.routes]
        assert "/twins/generate" in paths
        assert "/twins/{twin_id}" in paths
        assert "/twins/user/{user_id}" in paths
        assert "/twins/{twin_id}/versions" in paths


class TestTwinsRouterMethods:
    """Test that routes have correct HTTP methods."""

    def test_generate_is_post(self):
        from app.routers.twins import router
        for r in router.routes:
            if r.path == "/twins/generate":
                assert "POST" in r.methods

    def test_get_twin_is_get(self):
        from app.routers.twins import router
        for r in router.routes:
            if r.path == "/twins/{twin_id}":
                assert "GET" in r.methods

    def test_chat_is_post(self):
        from app.routers.chat import router
        for r in router.routes:
            if r.path == "/twins/{twin_id}/chat":
                assert "POST" in r.methods

    def test_history_is_get(self):
        from app.routers.chat import router
        for r in router.routes:
            if r.path == "/twins/{twin_id}/chat/{session_id}/history":
                assert "GET" in r.methods
