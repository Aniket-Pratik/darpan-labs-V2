"""Evidence indexer — chunks interview answers and creates embeddings."""

import logging
from uuid import UUID

import litellm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.llm import LLMClient, get_llm_client
from app.models.interview import InterviewModule, InterviewSession, InterviewTurn
from app.models.twin import EvidenceSnippet
from app.schemas.llm_responses import EvidenceChunkingResponse
from app.services.prompt_service import PromptService, get_prompt_service

logger = logging.getLogger(__name__)

# Module names for prompt context
MODULE_NAMES = {
    "M1": "Core Identity & Context",
    "M2": "Decision Logic & Risk",
    "M3": "Preferences & Values",
    "M4": "Communication & Social",
    "A1": "Lifestyle & Routines",
    "A2": "Spending & Financial",
    "A3": "Career & Growth",
    "A4": "Work & Learning",
    "A5": "Technology & Product",
    "A6": "Health & Wellness",
}

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSION = 1536


class EvidenceIndexerService:
    """Chunk interview answers into evidence snippets and generate embeddings."""

    def __init__(
        self,
        llm_client: LLMClient | None = None,
        prompt_service: PromptService | None = None,
    ):
        self.llm_client = llm_client or get_llm_client()
        self.prompt_service = prompt_service or get_prompt_service()

    async def index_evidence(
        self,
        user_id: UUID,
        twin_profile_id: UUID,
        db: AsyncSession,
    ) -> list[EvidenceSnippet]:
        """Extract evidence snippets from all interview answers and store with embeddings.

        Args:
            user_id: The user whose interview data to process.
            twin_profile_id: The twin profile to associate snippets with.
            db: Database session.

        Returns:
            List of created EvidenceSnippet records.
        """
        # 1. Load all user answer turns with their question context
        answer_turns = await self._get_answer_turns(user_id, db)
        if not answer_turns:
            logger.warning(f"No answer turns found for user {user_id}")
            return []

        logger.info(f"Processing {len(answer_turns)} answer turns for evidence extraction")

        # 2. Extract evidence chunks from each answer using LLM
        all_chunks = []
        for turn in answer_turns:
            chunks = await self._extract_chunks(turn)
            for chunk in chunks:
                all_chunks.append({
                    "text": chunk.text,
                    "category": chunk.category,
                    "question_context": chunk.question_context,
                    "module_id": turn["module_id"],
                    "turn_id": turn["turn_id"],
                })

        if not all_chunks:
            logger.warning(f"No evidence chunks extracted for user {user_id}")
            return []

        logger.info(f"Extracted {len(all_chunks)} evidence chunks, generating embeddings")

        # 3. Generate embeddings in batch
        texts = [c["text"] for c in all_chunks]
        embeddings = await self._generate_embeddings(texts)

        # 4. Create EvidenceSnippet records
        snippets = []
        for i, chunk in enumerate(all_chunks):
            snippet = EvidenceSnippet(
                user_id=user_id,
                twin_profile_id=twin_profile_id,
                module_id=chunk["module_id"],
                turn_id=chunk["turn_id"],
                snippet_text=chunk["text"],
                snippet_category=chunk["category"],
                embedding=embeddings[i] if i < len(embeddings) else None,
                snippet_metadata={
                    "question_context": chunk["question_context"],
                },
            )
            db.add(snippet)
            snippets.append(snippet)

        await db.flush()
        logger.info(f"Created {len(snippets)} evidence snippets for twin {twin_profile_id}")
        return snippets

    async def _get_answer_turns(
        self, user_id: UUID, db: AsyncSession
    ) -> list[dict]:
        """Get all user answer turns with question context."""
        # Get pairs: for each user answer, find the preceding interviewer question
        stmt = (
            select(InterviewTurn)
            .join(InterviewSession, InterviewTurn.session_id == InterviewSession.id)
            .join(
                InterviewModule,
                (InterviewModule.session_id == InterviewSession.id)
                & (InterviewModule.module_id == InterviewTurn.module_id),
            )
            .where(
                InterviewSession.user_id == user_id,
                InterviewModule.status == "completed",
            )
            .order_by(InterviewTurn.module_id, InterviewTurn.turn_index)
        )
        result = await db.execute(stmt)
        all_turns = result.scalars().all()

        # Build (question, answer) pairs
        answer_turns = []
        prev_question = None
        for turn in all_turns:
            if turn.role == "interviewer":
                prev_question = turn.question_text
            elif turn.role == "user" and turn.answer_text:
                answer_turns.append({
                    "turn_id": turn.id,
                    "module_id": turn.module_id,
                    "question_text": prev_question or "",
                    "answer_text": turn.answer_text,
                })
                prev_question = None

        return answer_turns

    async def _extract_chunks(self, turn: dict) -> list:
        """Extract evidence chunks from a single answer using LLM."""
        try:
            prompt = self.prompt_service.format_prompt(
                "evidence_chunking",
                module_id=turn["module_id"],
                module_name=MODULE_NAMES.get(turn["module_id"], turn["module_id"]),
                question_text=turn["question_text"],
                answer_text=turn["answer_text"],
            )

            result = await self.llm_client.generate(
                prompt=prompt,
                response_format=EvidenceChunkingResponse,
                temperature=0.2,
                max_tokens=500,
                metadata={"task": "evidence_chunking"},
            )
            return result.snippets
        except Exception as e:
            # Fallback: use the full answer as a single snippet
            logger.warning(f"LLM chunking failed, using heuristic: {e}")
            return self._heuristic_chunk(turn)

    def _heuristic_chunk(self, turn: dict) -> list:
        """Fallback heuristic: split answer into sentence-based chunks."""
        from app.schemas.llm_responses import EvidenceChunkLLM

        text = turn["answer_text"].strip()
        if len(text) < 20:
            return []

        # Simple sentence split
        sentences = []
        for sep in [". ", "! ", "? "]:
            if sep in text:
                parts = text.split(sep)
                sentences = [p.strip() + sep.strip() for p in parts if p.strip()]
                break

        if not sentences:
            sentences = [text]

        # Group into chunks of 1-3 sentences
        chunks = []
        current = []
        for s in sentences:
            current.append(s)
            if len(current) >= 2 or len(" ".join(current)) > 300:
                chunks.append(EvidenceChunkLLM(
                    text=" ".join(current),
                    category="context",  # Default category for heuristic
                    question_context=turn["question_text"][:100],
                ))
                current = []

        if current:
            chunks.append(EvidenceChunkLLM(
                text=" ".join(current),
                category="context",
                question_context=turn["question_text"][:100],
            ))

        return chunks

    async def _generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a batch of texts using LiteLLM."""
        if not texts:
            return []

        try:
            # Process in batches of 50 for API limits
            all_embeddings = []
            batch_size = 50
            for i in range(0, len(texts), batch_size):
                batch = texts[i : i + batch_size]
                response = await litellm.aembedding(
                    model=EMBEDDING_MODEL,
                    input=batch,
                )
                batch_embeddings = [item["embedding"] for item in response.data]
                all_embeddings.extend(batch_embeddings)

            return all_embeddings
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            # Return empty embeddings — snippets are still useful without vectors
            return [[] for _ in texts]


# Singleton
_service: EvidenceIndexerService | None = None


def get_evidence_indexer_service() -> EvidenceIndexerService:
    """Get the singleton evidence indexer service."""
    global _service
    if _service is None:
        _service = EvidenceIndexerService()
    return _service
