"""Module state tracking and scoring service."""

import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.llm import LLMClient, get_llm_client
from app.models.interview import InterviewModule, InterviewSession, InterviewTurn
from app.schemas.llm_responses import (
    ModuleCompletionResponse,
    ModuleCompletionResult,
    ParsedAnswer,
)
from app.services.prompt_service import PromptService, get_prompt_service
from app.services.question_bank_service import (
    QuestionBankService,
    get_question_bank_service,
)

logger = logging.getLogger(__name__)


class ModuleStateService:
    """Track and update module state (coverage, confidence, signals)."""

    def __init__(
        self,
        question_bank: QuestionBankService | None = None,
        llm_client: LLMClient | None = None,
        prompt_service: PromptService | None = None,
    ):
        """Initialize module state service.

        Args:
            question_bank: Service for loading question banks.
            llm_client: LLM client for completion evaluation.
            prompt_service: Service for loading prompts.
        """
        self.question_bank = question_bank or get_question_bank_service()
        self.llm_client = llm_client or get_llm_client()
        self.prompt_service = prompt_service or get_prompt_service()

    async def initialize_modules(
        self,
        session: AsyncSession,
        interview_session_id: UUID,
        module_ids: list[str],
    ) -> list[InterviewModule]:
        """Create module records for a new session.

        Args:
            session: Database session.
            interview_session_id: Interview session ID.
            module_ids: List of module IDs to initialize.

        Returns:
            List of created InterviewModule records.
        """
        modules = []
        for i, module_id in enumerate(module_ids):
            status = "active" if i == 0 else "pending"
            started_at = datetime.now(timezone.utc) if i == 0 else None

            module = InterviewModule(
                session_id=interview_session_id,
                module_id=module_id,
                status=status,
                started_at=started_at,
                question_count=0,
                coverage_score=0.0,
                confidence_score=0.0,
                signals_captured=[],
            )
            session.add(module)
            modules.append(module)

        await session.flush()
        logger.info(
            f"Initialized {len(modules)} modules for session {interview_session_id}"
        )
        return modules

    async def get_module_state(
        self,
        session: AsyncSession,
        interview_session_id: UUID,
        module_id: str,
    ) -> InterviewModule | None:
        """Get current state of a specific module.

        Args:
            session: Database session.
            interview_session_id: Interview session ID.
            module_id: Module ID to get.

        Returns:
            InterviewModule if found, None otherwise.
        """
        result = await session.execute(
            select(InterviewModule).where(
                InterviewModule.session_id == interview_session_id,
                InterviewModule.module_id == module_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_active_module(
        self,
        session: AsyncSession,
        interview_session_id: UUID,
    ) -> InterviewModule | None:
        """Get the currently active module for a session.

        Args:
            session: Database session.
            interview_session_id: Interview session ID.

        Returns:
            Active InterviewModule if found, None otherwise.
        """
        result = await session.execute(
            select(InterviewModule).where(
                InterviewModule.session_id == interview_session_id,
                InterviewModule.status == "active",
            )
        )
        return result.scalar_one_or_none()

    async def get_all_modules(
        self,
        session: AsyncSession,
        interview_session_id: UUID,
    ) -> list[InterviewModule]:
        """Get all modules for a session.

        Args:
            session: Database session.
            interview_session_id: Interview session ID.

        Returns:
            List of InterviewModule records.
        """
        result = await session.execute(
            select(InterviewModule)
            .where(InterviewModule.session_id == interview_session_id)
            .order_by(InterviewModule.module_id)
        )
        return list(result.scalars().all())

    async def update_module_after_answer(
        self,
        session: AsyncSession,
        module: InterviewModule,
        parsed_answer: ParsedAnswer,
    ) -> InterviewModule:
        """Update module scores after receiving an answer.

        Updates coverage and confidence scores based on the parsed answer.
        Uses heuristics for Sprint 1a, LLM evaluation for Sprint 1b.

        Args:
            session: Database session.
            module: Module to update.
            parsed_answer: Parsed answer data.

        Returns:
            Updated InterviewModule.
        """
        # Increment question count
        module.question_count += 1

        # Get target signals for this module
        target_signals = self.question_bank.get_signal_targets(module.module_id)
        total_signals = len(target_signals)

        # Update captured signals
        current_signals = list(module.signals_captured or [])
        target_signal_set = set(target_signals)
        for signal in parsed_answer.signals_extracted:
            if signal.signal not in current_signals:
                current_signals.append(signal.signal)
        module.signals_captured = current_signals

        # Calculate coverage (only count signals that match targets)
        if total_signals > 0:
            matched = len([s for s in current_signals if s in target_signal_set])
            module.coverage_score = min(matched / total_signals, 1.0)
        else:
            module.coverage_score = 0.0

        # Update confidence based on answer specificity
        # Weighted average with existing confidence
        if module.question_count == 1:
            module.confidence_score = parsed_answer.specificity_score
        else:
            # Rolling average weighted toward recent answers
            weight = 0.7  # Weight for new answer
            module.confidence_score = (
                weight * parsed_answer.specificity_score
                + (1 - weight) * module.confidence_score
            )

        await session.flush()
        logger.info(
            f"Updated module {module.module_id}: "
            f"coverage={module.coverage_score:.2f}, "
            f"confidence={module.confidence_score:.2f}, "
            f"signals_captured={current_signals}, "
            f"target_signals={target_signals}, "
            f"matched={len([s for s in current_signals if s in target_signal_set])}/{total_signals}"
        )
        return module

    async def evaluate_module_completion(
        self,
        session: AsyncSession,
        interview_session_id: UUID,
        module_id: str,
    ) -> ModuleCompletionResult:
        """Evaluate if a module meets completion criteria using LLM.

        Args:
            session: Database session.
            interview_session_id: Interview session ID.
            module_id: Module to evaluate.

        Returns:
            ModuleCompletionResult with completion status and scores.
        """
        # Get module state
        module = await self.get_module_state(session, interview_session_id, module_id)
        if not module:
            raise ValueError(f"Module {module_id} not found for session")

        # Get completion criteria
        criteria = self.question_bank.get_module_completion_criteria(module_id)

        # Quick check: if below thresholds, don't bother with LLM
        if (
            module.coverage_score < criteria.coverage_threshold * 0.8
            or module.question_count < criteria.min_questions
        ):
            return ModuleCompletionResult(
                is_complete=False,
                coverage_score=module.coverage_score,
                confidence_score=module.confidence_score,
                signals_captured=list(module.signals_captured or []),
                signals_missing=self._get_missing_signals(module),
                recommendation="ASK_MORE",
            )

        # Get all turns for this module
        turns = await self._get_module_turns(session, interview_session_id, module_id)

        # Format turns for prompt
        turns_data = [
            {
                "question": t.question_text,
                "answer": t.answer_text,
                "target_signal": (t.question_meta or {}).get("target_signal", ""),
            }
            for t in turns
            if t.role == "user" and t.answer_text
        ]

        # Call LLM for evaluation
        try:
            prompt = self.prompt_service.get_module_completion_prompt(
                module_id=module_id,
                module_name=self.question_bank.get_module_name(module_id),
                signal_targets=self.question_bank.get_signal_targets(module_id),
                coverage_threshold=criteria.coverage_threshold,
                confidence_threshold=criteria.confidence_threshold,
                module_turns=turns_data,
            )

            response = await self.llm_client.generate(
                prompt=prompt,
                response_format=ModuleCompletionResponse,
                temperature=0.2,
                metadata={"prompt_name": "module_completion", "module_id": module_id},
            )

            result = ModuleCompletionResult.from_llm_response(response)

            # Update module with LLM scores (cap coverage at 1.0)
            module.coverage_score = min(result.coverage_score, 1.0)
            module.confidence_score = min(result.confidence_score, 1.0)
            module.signals_captured = result.signals_captured
            module.completion_eval = {
                "recommendation": result.recommendation,
                "signals_missing": result.signals_missing,
                "module_summary": result.module_summary,
            }
            await session.flush()

            return result

        except Exception as e:
            logger.warning(f"LLM completion evaluation failed: {e}")
            # Fallback to heuristic evaluation
            return self._evaluate_heuristic(module, criteria)

    def _evaluate_heuristic(
        self,
        module: InterviewModule,
        criteria,
    ) -> ModuleCompletionResult:
        """Heuristic completion evaluation when LLM fails.

        Args:
            module: Module to evaluate.
            criteria: Completion criteria.

        Returns:
            ModuleCompletionResult based on heuristics.
        """
        is_complete = (
            module.coverage_score >= criteria.coverage_threshold
            and module.confidence_score >= criteria.confidence_threshold
            and module.question_count >= criteria.min_questions
        )

        return ModuleCompletionResult(
            is_complete=is_complete,
            coverage_score=module.coverage_score,
            confidence_score=module.confidence_score,
            signals_captured=list(module.signals_captured or []),
            signals_missing=self._get_missing_signals(module),
            recommendation="COMPLETE" if is_complete else "ASK_MORE",
            module_summary=None,
        )

    def _get_missing_signals(self, module: InterviewModule) -> list[str]:
        """Get signals not yet captured for a module.

        Args:
            module: Module to check.

        Returns:
            List of missing signal names.
        """
        target_signals = set(self.question_bank.get_signal_targets(module.module_id))
        captured = set(module.signals_captured or [])
        return list(target_signals - captured)

    async def transition_to_next_module(
        self,
        session: AsyncSession,
        interview_session_id: UUID,
        current_module_id: str,
        module_summary: str | None = None,
    ) -> InterviewModule | None:
        """Mark current module complete and activate next.

        Args:
            session: Database session.
            interview_session_id: Interview session ID.
            current_module_id: Module to mark complete.
            module_summary: Optional summary of the completed module.

        Returns:
            Next InterviewModule if available, None if all complete.
        """
        # Get all modules
        modules = await self.get_all_modules(session, interview_session_id)

        # Find and update current module
        current_idx = None
        for i, m in enumerate(modules):
            if m.module_id == current_module_id:
                m.status = "completed"
                m.ended_at = datetime.now(timezone.utc)
                if module_summary:
                    m.completion_eval = {
                        **(m.completion_eval or {}),
                        "module_summary": module_summary,
                    }
                current_idx = i
                break

        if current_idx is None:
            raise ValueError(f"Module {current_module_id} not found")

        # Find next pending module
        for m in modules[current_idx + 1 :]:
            if m.status == "pending":
                m.status = "active"
                m.started_at = datetime.now(timezone.utc)
                await session.flush()
                logger.info(f"Transitioned to module {m.module_id}")
                return m

        # No more modules
        await session.flush()
        logger.info("All modules completed")
        return None

    async def get_completed_modules_summary(
        self,
        session: AsyncSession,
        interview_session_id: UUID,
    ) -> str:
        """Get summary of all completed modules for cross-module context.

        Args:
            session: Database session.
            interview_session_id: Interview session ID.

        Returns:
            Formatted summary string.
        """
        modules = await self.get_all_modules(session, interview_session_id)
        completed = [m for m in modules if m.status == "completed"]

        if not completed:
            return "No modules completed yet."

        summaries = []
        for m in completed:
            eval_data = m.completion_eval or {}
            summary = eval_data.get("module_summary", "")
            signals = m.signals_captured or []
            summaries.append(
                f"{m.module_id} ({self.question_bank.get_module_name(m.module_id)}): "
                f"Signals: {', '.join(signals)}. {summary}"
            )

        return "\n".join(summaries)

    async def _get_module_turns(
        self,
        session: AsyncSession,
        interview_session_id: UUID,
        module_id: str,
    ) -> list[InterviewTurn]:
        """Get all turns for a specific module.

        Args:
            session: Database session.
            interview_session_id: Interview session ID.
            module_id: Module ID.

        Returns:
            List of InterviewTurn records.
        """
        result = await session.execute(
            select(InterviewTurn)
            .where(
                InterviewTurn.session_id == interview_session_id,
                InterviewTurn.module_id == module_id,
            )
            .order_by(InterviewTurn.turn_index)
        )
        return list(result.scalars().all())


# Singleton instance
_module_state_service: ModuleStateService | None = None


def get_module_state_service() -> ModuleStateService:
    """Get the singleton module state service instance."""
    global _module_state_service
    if _module_state_service is None:
        _module_state_service = ModuleStateService()
    return _module_state_service
