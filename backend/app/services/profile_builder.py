"""Profile extraction service — extracts structured profile from interview data."""

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.llm import LLMClient, get_llm_client
from app.models.interview import InterviewModule, InterviewSession, InterviewTurn
from app.schemas.llm_responses import ProfileExtractionResponse
from app.services.prompt_service import PromptService, get_prompt_service

logger = logging.getLogger(__name__)

# Module ID to domain mapping
MODULE_DOMAINS = {
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


class ProfileBuilderService:
    """Extract structured personality/behavioral profile from interview transcripts."""

    def __init__(
        self,
        llm_client: LLMClient | None = None,
        prompt_service: PromptService | None = None,
    ):
        self.llm_client = llm_client or get_llm_client()
        self.prompt_service = prompt_service or get_prompt_service()

    async def extract_profile(
        self,
        user_id: UUID,
        db: AsyncSession,
    ) -> ProfileExtractionResponse:
        """Extract structured profile from all completed interview modules.

        Args:
            user_id: The user whose profile to extract.
            db: Database session.

        Returns:
            Validated ProfileExtractionResponse from LLM.

        Raises:
            ValueError: If no completed modules found.
        """
        # 1. Find all completed modules across all sessions for this user
        completed_modules = await self._get_completed_modules(user_id, db)
        if not completed_modules:
            raise ValueError(f"No completed modules found for user {user_id}")

        # 2. Load all turns for completed modules
        all_module_turns = await self._get_all_module_turns(user_id, completed_modules, db)

        # 3. Format turns by module for the prompt
        completed_modules_str = ", ".join(
            f"{mid} ({MODULE_DOMAINS.get(mid, mid)})" for mid in completed_modules
        )
        turns_str = self._format_turns_by_module(all_module_turns)

        # 4. Build and call LLM
        prompt = self.prompt_service.format_prompt(
            "profile_extraction",
            completed_modules=completed_modules_str,
            all_module_turns=turns_str,
        )

        logger.info(f"Extracting profile for user {user_id} from modules: {completed_modules}")

        result = await self.llm_client.generate(
            prompt=prompt,
            response_format=ProfileExtractionResponse,
            temperature=0.3,  # Low temperature for factual extraction
            max_tokens=4500,
            metadata={"task": "profile_extraction", "user_id": str(user_id)},
        )

        logger.info(
            f"Profile extracted for user {user_id}: "
            f"{len(result.uncertainty_flags)} uncertainty flags"
        )
        return result

    async def _get_completed_modules(
        self, user_id: UUID, db: AsyncSession
    ) -> list[str]:
        """Get list of completed module IDs for a user across all sessions."""
        stmt = (
            select(InterviewModule.module_id)
            .join(InterviewSession, InterviewModule.session_id == InterviewSession.id)
            .where(
                InterviewSession.user_id == user_id,
                InterviewModule.status == "completed",
            )
            .distinct()
        )
        result = await db.execute(stmt)
        return [row[0] for row in result.fetchall()]

    async def _get_all_module_turns(
        self,
        user_id: UUID,
        module_ids: list[str],
        db: AsyncSession,
    ) -> dict[str, list[dict]]:
        """Get all interview turns grouped by module ID.

        Returns:
            Dict mapping module_id -> list of {role, question_text/answer_text, turn_index}
        """
        stmt = (
            select(InterviewTurn)
            .join(InterviewSession, InterviewTurn.session_id == InterviewSession.id)
            .where(
                InterviewSession.user_id == user_id,
                InterviewTurn.module_id.in_(module_ids),
            )
            .order_by(InterviewTurn.module_id, InterviewTurn.turn_index)
        )
        result = await db.execute(stmt)
        turns = result.scalars().all()

        grouped: dict[str, list[dict]] = {}
        for turn in turns:
            mid = turn.module_id
            if mid not in grouped:
                grouped[mid] = []
            grouped[mid].append({
                "role": turn.role,
                "question_text": turn.question_text,
                "answer_text": turn.answer_text,
                "turn_index": turn.turn_index,
            })

        return grouped

    def _format_turns_by_module(self, module_turns: dict[str, list[dict]]) -> str:
        """Format all turns grouped by module for the LLM prompt."""
        sections = []
        for module_id in sorted(module_turns.keys()):
            turns = module_turns[module_id]
            module_name = MODULE_DOMAINS.get(module_id, module_id)
            section_lines = [f"\n--- {module_id}: {module_name} ---"]

            for turn in turns:
                if turn["role"] == "interviewer" and turn["question_text"]:
                    section_lines.append(f"Q: {turn['question_text']}")
                elif turn["role"] == "user" and turn["answer_text"]:
                    section_lines.append(f"A: {turn['answer_text']}")

            sections.append("\n".join(section_lines))

        return "\n".join(sections)


# Singleton
_service: ProfileBuilderService | None = None


def get_profile_builder_service() -> ProfileBuilderService:
    """Get the singleton profile builder service."""
    global _service
    if _service is None:
        _service = ProfileBuilderService()
    return _service
