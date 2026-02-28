"""Twin chat service — handles chat with digital twins."""

import json
import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.llm import LLMClient, get_llm_client
from app.models.chat import TwinChatMessage, TwinChatSession
from app.models.twin import TwinProfile
from app.schemas.chat import (
    ChatHistoryResponse,
    ChatMessageResponse,
    EvidenceUsed,
    TwinChatResponse,
)
from app.schemas.llm_responses import TwinResponseLLM
from app.services.evidence_retriever import (
    EvidenceRetrieverService,
    get_evidence_retriever_service,
)
from app.services.prompt_service import PromptService, get_prompt_service

logger = logging.getLogger(__name__)

# All known modules for gap detection
ALL_MODULES = {"M1", "M2", "M3", "M4", "A1", "A2", "A3", "A4", "A5", "A6"}

MODULE_DOMAIN_NAMES = {
    "M1": "Core Identity",
    "M2": "Decision Logic",
    "M3": "Preferences & Values",
    "M4": "Communication",
    "A1": "Lifestyle & Routines",
    "A2": "Spending & Financial",
    "A3": "Career & Growth",
    "A4": "Work & Learning",
    "A5": "Technology & Product",
    "A6": "Health & Wellness",
}

MAX_CHAT_HISTORY = 20  # Messages to include in context


class TwinChatService:
    """Handle chat interactions with digital twins."""

    def __init__(
        self,
        llm_client: LLMClient | None = None,
        prompt_service: PromptService | None = None,
        evidence_retriever: EvidenceRetrieverService | None = None,
    ):
        self.llm_client = llm_client or get_llm_client()
        self.prompt_service = prompt_service or get_prompt_service()
        self.evidence_retriever = evidence_retriever or get_evidence_retriever_service()

    async def chat(
        self,
        twin_id: UUID,
        message: str,
        user_id: UUID,
        db: AsyncSession,
        session_id: UUID | None = None,
    ) -> TwinChatResponse:
        """Send a message to a twin and get a response.

        Args:
            twin_id: The twin to chat with.
            message: The user's message.
            user_id: The user sending the message.
            db: Database session.
            session_id: Optional existing chat session ID.

        Returns:
            TwinChatResponse with the twin's response, confidence, evidence.

        Raises:
            ValueError: If twin not found or not ready.
        """
        # 1. Load twin profile
        twin = await self._get_twin(twin_id, db)
        if not twin:
            raise ValueError(f"Twin {twin_id} not found")
        if twin.status != "ready":
            raise ValueError(f"Twin {twin_id} is not ready (status: {twin.status})")

        # 2. Get or create chat session
        chat_session = await self._get_or_create_session(
            twin_id, user_id, db, session_id
        )

        # 3. Save user message
        user_msg = TwinChatMessage(
            session_id=chat_session.id,
            role="user",
            content=message,
        )
        db.add(user_msg)
        await db.flush()

        # 4. Load recent chat history
        chat_history = await self._get_chat_history(chat_session.id, db)

        # 5. Retrieve relevant evidence
        evidence = await self.evidence_retriever.retrieve(
            query=message,
            twin_profile_id=twin_id,
            db=db,
            k=5,
        )

        # 6. Build prompt and call LLM
        missing_modules = sorted(ALL_MODULES - set(twin.modules_included))
        missing_str = ", ".join(
            f"{m} ({MODULE_DOMAIN_NAMES.get(m, m)})" for m in missing_modules
        ) if missing_modules else "None"

        evidence_str = self._format_evidence(evidence)
        history_str = self._format_chat_history(chat_history)

        prompt = self.prompt_service.format_prompt(
            "twin_response",
            persona_summary_text=twin.persona_summary_text or "",
            retrieved_evidence=evidence_str,
            modules_included=", ".join(twin.modules_included),
            missing_modules=missing_str,
            chat_history=history_str,
            user_question=message,
        )

        llm_response = await self.llm_client.generate(
            prompt=prompt,
            response_format=TwinResponseLLM,
            temperature=0.6,
            max_tokens=1000,
            metadata={"task": "twin_chat", "twin_id": str(twin_id)},
        )

        # 7. Save twin response message
        evidence_used_data = [
            {"snippet_id": e.snippet_id, "why": e.why}
            for e in llm_response.evidence_used
        ]
        twin_msg = TwinChatMessage(
            session_id=chat_session.id,
            role="twin",
            content=llm_response.response_text,
            confidence_score=llm_response.confidence_score,
            confidence_label=llm_response.confidence_label,
            evidence_used=evidence_used_data,
            coverage_gaps=llm_response.coverage_gaps or None,
            model_meta={"task": "twin_chat"},
        )
        db.add(twin_msg)
        await db.flush()

        # 8. Build response with enriched evidence (include snippet text)
        evidence_map = {e["snippet_id"]: e["text"] for e in evidence}
        evidence_used_enriched = [
            EvidenceUsed(
                snippet_id=e.snippet_id,
                why=e.why,
                snippet_text=evidence_map.get(e.snippet_id),
            )
            for e in llm_response.evidence_used
        ]

        logger.info(
            f"Twin chat response: confidence={llm_response.confidence_label}, "
            f"evidence={len(evidence_used_data)}"
        )

        return TwinChatResponse(
            session_id=chat_session.id,
            message_id=twin_msg.id,
            response_text=llm_response.response_text,
            confidence_score=llm_response.confidence_score,
            confidence_label=llm_response.confidence_label,
            uncertainty_reason=llm_response.uncertainty_reason,
            evidence_used=evidence_used_enriched,
            coverage_gaps=llm_response.coverage_gaps,
            suggested_module=llm_response.suggested_module,
        )

    async def get_chat_history(
        self,
        twin_id: UUID,
        session_id: UUID,
        db: AsyncSession,
    ) -> ChatHistoryResponse:
        """Get full chat history for a session.

        Args:
            twin_id: The twin ID.
            session_id: The chat session ID.
            db: Database session.

        Returns:
            ChatHistoryResponse with all messages.
        """
        session = await self._get_session(session_id, db)
        if not session or session.twin_id != twin_id:
            raise ValueError(f"Chat session {session_id} not found for twin {twin_id}")

        stmt = (
            select(TwinChatMessage)
            .where(TwinChatMessage.session_id == session_id)
            .order_by(TwinChatMessage.created_at)
        )
        result = await db.execute(stmt)
        messages = result.scalars().all()

        return ChatHistoryResponse(
            session_id=session_id,
            twin_id=twin_id,
            messages=[
                ChatMessageResponse(
                    id=msg.id,
                    role=msg.role,
                    content=msg.content,
                    confidence_score=msg.confidence_score,
                    confidence_label=msg.confidence_label,
                    evidence_used=[
                        EvidenceUsed(snippet_id=e["snippet_id"], why=e["why"])
                        for e in (msg.evidence_used or [])
                    ] if msg.evidence_used else None,
                    coverage_gaps=list(msg.coverage_gaps) if msg.coverage_gaps else None,
                    created_at=msg.created_at,
                )
                for msg in messages
            ],
            created_at=session.created_at,
        )

    async def get_sessions(
        self, twin_id: UUID, db: AsyncSession
    ) -> list[TwinChatSession]:
        """Get all chat sessions for a twin."""
        stmt = (
            select(TwinChatSession)
            .where(TwinChatSession.twin_id == twin_id)
            .order_by(TwinChatSession.created_at.desc())
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_brand_sessions(
        self, user_id: UUID, db: AsyncSession
    ) -> list[dict]:
        """Get all chat sessions created by a user (brand), with twin info.

        Returns sessions joined with twin profile data for display.
        """
        from sqlalchemy.orm import selectinload

        stmt = (
            select(TwinChatSession)
            .options(selectinload(TwinChatSession.twin), selectinload(TwinChatSession.messages))
            .where(TwinChatSession.created_by == user_id)
            .order_by(TwinChatSession.created_at.desc())
        )
        result = await db.execute(stmt)
        sessions = result.scalars().all()

        items = []
        for s in sessions:
            twin = s.twin
            if not twin:
                continue
            items.append({
                "id": s.id,
                "twin_id": s.twin_id,
                "twin_quality_label": twin.quality_label or "base",
                "twin_quality_score": twin.quality_score or 0.0,
                "twin_modules": twin.modules_included or [],
                "created_at": s.created_at,
                "message_count": len(s.messages) if s.messages else 0,
            })
        return items

    async def _get_twin(self, twin_id: UUID, db: AsyncSession) -> TwinProfile | None:
        """Load a twin profile."""
        stmt = select(TwinProfile).where(TwinProfile.id == twin_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_or_create_session(
        self,
        twin_id: UUID,
        user_id: UUID,
        db: AsyncSession,
        session_id: UUID | None = None,
    ) -> TwinChatSession:
        """Get existing session or create a new one."""
        if session_id:
            session = await self._get_session(session_id, db)
            if session:
                return session

        # Create new session
        session = TwinChatSession(
            twin_id=twin_id,
            created_by=user_id,
        )
        db.add(session)
        await db.flush()
        return session

    async def _get_session(
        self, session_id: UUID, db: AsyncSession
    ) -> TwinChatSession | None:
        """Load a chat session."""
        stmt = select(TwinChatSession).where(TwinChatSession.id == session_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_chat_history(
        self, session_id: UUID, db: AsyncSession
    ) -> list[dict]:
        """Load recent chat messages for context."""
        stmt = (
            select(TwinChatMessage)
            .where(TwinChatMessage.session_id == session_id)
            .order_by(TwinChatMessage.created_at.desc())
            .limit(MAX_CHAT_HISTORY)
        )
        result = await db.execute(stmt)
        messages = list(reversed(result.scalars().all()))

        return [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

    def _format_evidence(self, evidence: list[dict]) -> str:
        """Format evidence snippets for the LLM prompt."""
        if not evidence:
            return "No relevant evidence found."

        lines = []
        for e in evidence:
            lines.append(
                f"[{e['snippet_id']}] ({e['category']}, {e['module_id']}) "
                f"{e['text']}"
            )
        return "\n".join(lines)

    def _format_chat_history(self, history: list[dict]) -> str:
        """Format chat history for the LLM prompt."""
        if not history:
            return "No previous messages in this session."

        lines = []
        for msg in history:
            role_label = "User" if msg["role"] == "user" else "Twin"
            lines.append(f"{role_label}: {msg['content']}")
        return "\n".join(lines)


# Singleton
_service: TwinChatService | None = None


def get_twin_chat_service() -> TwinChatService:
    """Get the singleton twin chat service."""
    global _service
    if _service is None:
        _service = TwinChatService()
    return _service
