"""Evidence retriever — semantic search over evidence snippets using pgvector."""

import logging
from collections import defaultdict
from uuid import UUID

import litellm
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.twin import EvidenceSnippet

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "text-embedding-3-small"
MAX_PER_CATEGORY = 2  # Diversity: max snippets per category


class EvidenceRetrieverService:
    """Retrieve relevant evidence snippets using semantic search."""

    async def retrieve(
        self,
        query: str,
        twin_profile_id: UUID,
        db: AsyncSession,
        k: int = 5,
    ) -> list[dict]:
        """Retrieve top-k relevant evidence snippets for a query.

        Uses pgvector cosine similarity search with category diversity filtering.

        Args:
            query: The user's question or message.
            twin_profile_id: The twin to search evidence for.
            db: Database session.
            k: Number of snippets to return.

        Returns:
            List of dicts with snippet_id, text, category, module_id, relevance_score.
        """
        # 1. Generate query embedding
        query_embedding = await self._embed_query(query)
        if not query_embedding:
            # Fallback: return most recent snippets without semantic ranking
            return await self._fallback_retrieve(twin_profile_id, db, k)

        # 2. pgvector cosine similarity search (over-fetch for diversity filtering)
        fetch_k = k * 3
        stmt = text("""
            SELECT
                id,
                snippet_text,
                snippet_category,
                module_id,
                snippet_metadata,
                1 - (embedding <=> CAST(:query_embedding AS vector)) as relevance_score
            FROM evidence_snippets
            WHERE twin_profile_id = :twin_id
                AND embedding IS NOT NULL
            ORDER BY embedding <=> CAST(:query_embedding AS vector)
            LIMIT :fetch_k
        """)

        result = await db.execute(
            stmt,
            {
                "query_embedding": str(query_embedding),
                "twin_id": str(twin_profile_id),
                "fetch_k": fetch_k,
            },
        )
        rows = result.fetchall()

        # 3. Diversity filter: max N per category
        diverse_results = []
        category_counts: dict[str, int] = defaultdict(int)
        for row in rows:
            category = row[2]
            if category_counts[category] < MAX_PER_CATEGORY:
                diverse_results.append({
                    "snippet_id": str(row[0]),
                    "text": row[1],
                    "category": category,
                    "module_id": row[3],
                    "question_context": (row[4] or {}).get("question_context", ""),
                    "relevance_score": round(float(row[5]), 3),
                })
                category_counts[category] += 1
                if len(diverse_results) == k:
                    break

        logger.info(
            f"Retrieved {len(diverse_results)} evidence snippets for twin {twin_profile_id}"
        )
        return diverse_results

    async def _embed_query(self, query: str) -> list[float] | None:
        """Generate embedding for a query string."""
        try:
            response = await litellm.aembedding(
                model=EMBEDDING_MODEL,
                input=[query],
            )
            return response.data[0]["embedding"]
        except Exception as e:
            logger.error(f"Query embedding failed: {e}")
            return None

    async def _fallback_retrieve(
        self, twin_profile_id: UUID, db: AsyncSession, k: int
    ) -> list[dict]:
        """Fallback: return most recent snippets without semantic ranking."""
        stmt = (
            select(EvidenceSnippet)
            .where(EvidenceSnippet.twin_profile_id == twin_profile_id)
            .order_by(EvidenceSnippet.created_at.desc())
            .limit(k)
        )
        result = await db.execute(stmt)
        snippets = result.scalars().all()

        return [
            {
                "snippet_id": str(s.id),
                "text": s.snippet_text,
                "category": s.snippet_category,
                "module_id": s.module_id,
                "question_context": (s.snippet_metadata or {}).get("question_context", ""),
                "relevance_score": 0.5,  # Default score for non-semantic results
            }
            for s in snippets
        ]


# Singleton
_service: EvidenceRetrieverService | None = None


def get_evidence_retriever_service() -> EvidenceRetrieverService:
    """Get the singleton evidence retriever service."""
    global _service
    if _service is None:
        _service = EvidenceRetrieverService()
    return _service
