"""Core interview orchestration service."""

import logging
import uuid
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.llm import LLMClient, get_llm_client
from app.models.interview import InterviewModule, InterviewSession, InterviewTurn
from app.models.consent import ConsentEvent
from app.models.user import User
from app.schemas.interview import (
    ConsentData,
    FirstQuestion,
    InterviewAnswerRequest,
    InterviewAnswerResponse,
    InterviewNextQuestionResponse,
    InterviewPauseResponse,
    InterviewSkipRequest,
    InterviewStartRequest,
    InterviewStartResponse,
    InterviewStatusResponse,
    ModuleCompleteResponse,
    ModuleInfo,
    ModulePlanItem,
    ModuleProgress,
    QuestionMeta,
    StartSingleModuleRequest,
    TwinEligibilityResponse,
    UserModulesResponse,
    UserModuleStatus,
)
from app.schemas.llm_responses import (
    AdaptiveQuestionResponse,
    AdaptiveQuestionResult,
    ParsedAnswer,
)
from app.services.answer_parser_service import (
    AnswerParserService,
    get_answer_parser_service,
)
from app.services.module_state_service import (
    ModuleStateService,
    get_module_state_service,
)
from app.services.prompt_service import PromptService, get_prompt_service
from app.services.question_bank_service import (
    MODULE_FILES,
    Question,
    QuestionBankService,
    get_question_bank_service,
)

logger = logging.getLogger(__name__)


class InterviewService:
    """Core interview orchestration service."""

    def __init__(
        self,
        question_bank: QuestionBankService | None = None,
        module_state: ModuleStateService | None = None,
        answer_parser: AnswerParserService | None = None,
        prompt_service: PromptService | None = None,
        llm_client: LLMClient | None = None,
    ):
        """Initialize interview service.

        Args:
            question_bank: Service for loading question banks.
            module_state: Service for tracking module state.
            answer_parser: Service for parsing answers.
            prompt_service: Service for loading prompts.
            llm_client: LLM client for generating questions.
        """
        self.question_bank = question_bank or get_question_bank_service()
        self.module_state = module_state or get_module_state_service()
        self.answer_parser = answer_parser or get_answer_parser_service()
        self.prompt_service = prompt_service or get_prompt_service()
        self.llm_client = llm_client or get_llm_client()

    async def start_interview(
        self,
        session: AsyncSession,
        request: InterviewStartRequest,
    ) -> InterviewStartResponse:
        """Create new interview session with modules initialized.

        Args:
            session: Database session.
            request: Interview start request.

        Returns:
            InterviewStartResponse with session info and first question.
        """
        # Ensure user exists (auto-create for demo purposes)
        await self._ensure_user_exists(session, request.user_id)

        # Create interview session
        interview_session = InterviewSession(
            user_id=request.user_id,
            status="active",
            input_mode=request.input_mode,
            language_preference=request.language_preference,
            settings={
                "sensitivity_settings": request.sensitivity_settings.model_dump(),
                "modules_to_complete": request.modules_to_complete,
            },
        )
        session.add(interview_session)
        await session.flush()

        # Record consent if provided
        if request.consent:
            await self._record_consent(session, request.user_id, request.consent)

        # Initialize modules
        modules = await self.module_state.initialize_modules(
            session,
            interview_session.id,
            request.modules_to_complete,
        )

        # Get first module and question
        first_module = modules[0]
        first_question = self.question_bank.get_first_question(first_module.module_id)

        # Create first interviewer turn
        await self._create_interviewer_turn(
            session,
            interview_session.id,
            first_module.module_id,
            first_question,
            turn_index=0,
        )

        # Build response
        module_plan = self._build_module_plan(modules)
        first_module_info = ModuleInfo(
            module_id=first_module.module_id,
            module_name=self.question_bank.get_module_name(first_module.module_id),
            estimated_duration_min=3,
            status="active",
        )

        logger.info(f"Started interview session {interview_session.id}")

        return InterviewStartResponse(
            session_id=interview_session.id,
            status="active",
            first_module=first_module_info,
            module_plan=module_plan,
            first_question=FirstQuestion(
                question_id=first_question.question_id,
                question_text=first_question.question_text,
                question_type=first_question.question_type,
                target_signal=first_question.target_signals[0]
                if first_question.target_signals
                else "",
            ),
        )

    async def submit_answer(
        self,
        session: AsyncSession,
        interview_session_id: UUID,
        request: InterviewAnswerRequest,
    ) -> InterviewAnswerResponse:
        """Process and persist user answer.

        Args:
            session: Database session.
            interview_session_id: Interview session ID.
            request: Answer submission request.

        Returns:
            InterviewAnswerResponse confirming answer receipt.
        """
        # Get active module
        active_module = await self.module_state.get_active_module(
            session, interview_session_id
        )
        if not active_module:
            raise ValueError("No active module for this session")

        # Get last interviewer turn to know the question
        last_turn = await self._get_last_turn(session, interview_session_id)
        if not last_turn or last_turn.role != "interviewer":
            raise ValueError("Expected interviewer turn before answer")

        # Get next turn index
        turn_index = last_turn.turn_index + 1

        # Create user turn
        user_turn = InterviewTurn(
            session_id=interview_session_id,
            module_id=active_module.module_id,
            turn_index=turn_index,
            role="user",
            input_mode=request.input_mode,
            answer_text=request.answer_text,
            question_meta=last_turn.question_meta,  # Copy question context
            audio_meta=request.audio_meta,
        )
        session.add(user_turn)
        await session.flush()

        # Parse answer
        question_meta = last_turn.question_meta or {}
        parsed_answer = await self.answer_parser.parse_answer(
            module_id=active_module.module_id,
            module_name=self.question_bank.get_module_name(active_module.module_id),
            question_text=last_turn.question_text or "",
            target_signal=question_meta.get("target_signal", ""),
            answer_text=request.answer_text,
            previous_answers=await self._get_previous_answers(
                session, interview_session_id, active_module.module_id
            ),
            signal_targets=self.question_bank.get_signal_targets(active_module.module_id),
        )

        # Update turn with parsed data
        user_turn.answer_meta = {
            "specificity_score": parsed_answer.specificity_score,
            "sentiment": parsed_answer.sentiment,
            "needs_followup": parsed_answer.needs_followup,
            "followup_reason": parsed_answer.followup_reason,
            "signals_extracted": [
                s.model_dump() for s in parsed_answer.signals_extracted
            ],
        }
        user_turn.answer_language = parsed_answer.language

        # Update module state
        await self.module_state.update_module_after_answer(
            session, active_module, parsed_answer
        )

        logger.debug(f"Submitted answer for turn {turn_index}")

        return InterviewAnswerResponse(
            turn_id=user_turn.id,
            answer_received=True,
            answer_meta=user_turn.answer_meta,
        )

    async def get_next_question(
        self,
        session: AsyncSession,
        interview_session_id: UUID,
    ) -> InterviewNextQuestionResponse:
        """Get next question using adaptive selection.

        Args:
            session: Database session.
            interview_session_id: Interview session ID.

        Returns:
            InterviewNextQuestionResponse with next question or completion status.
        """
        # Get active module
        active_module = await self.module_state.get_active_module(
            session, interview_session_id
        )
        if not active_module:
            # Check if interview is complete
            interview = await self._get_interview_session(session, interview_session_id)
            if interview and interview.status == "completed":
                return self._build_all_complete_response()
            raise ValueError("No active module for this session")

        # Evaluate module completion
        completion = await self.module_state.evaluate_module_completion(
            session, interview_session_id, active_module.module_id
        )

        if completion.is_complete:
            # Transition to next module
            next_module = await self.module_state.transition_to_next_module(
                session,
                interview_session_id,
                active_module.module_id,
                completion.module_summary,
            )

            if next_module is None:
                # All modules complete
                await self._mark_interview_complete(session, interview_session_id)
                return self._build_module_complete_response(
                    active_module,
                    completion.module_summary,
                    all_complete=True,
                )

            # Get first question for new module
            first_question = self.question_bank.get_first_question(next_module.module_id)
            turn_index = await self._get_next_turn_index(session, interview_session_id)

            await self._create_interviewer_turn(
                session,
                interview_session_id,
                next_module.module_id,
                first_question,
                turn_index,
            )

            return self._build_module_complete_response(
                active_module,
                completion.module_summary,
                next_question=first_question,
                next_module=next_module,
            )

        # Get next question (adaptive)
        question_result = await self._get_adaptive_question(
            session, interview_session_id, active_module
        )

        if question_result.action == "MODULE_COMPLETE":
            # LLM decided module is complete
            return await self._handle_module_complete(
                session,
                interview_session_id,
                active_module,
                question_result.module_summary,
            )

        # Create interviewer turn
        turn_index = await self._get_next_turn_index(session, interview_session_id)
        await self._create_adaptive_turn(
            session,
            interview_session_id,
            active_module.module_id,
            question_result,
            turn_index,
        )

        return self._build_continue_response(active_module, question_result)

    async def skip_question(
        self,
        session: AsyncSession,
        interview_session_id: UUID,
        request: InterviewSkipRequest,
    ) -> InterviewNextQuestionResponse:
        """Skip current question and get next.

        Args:
            session: Database session.
            interview_session_id: Interview session ID.
            request: Skip request with optional reason.

        Returns:
            InterviewNextQuestionResponse with next question.
        """
        # Get active module
        active_module = await self.module_state.get_active_module(
            session, interview_session_id
        )
        if not active_module:
            raise ValueError("No active module for this session")

        # Get last turn
        last_turn = await self._get_last_turn(session, interview_session_id)
        if not last_turn or last_turn.role != "interviewer":
            raise ValueError("Expected interviewer turn to skip")

        # Create skip turn
        turn_index = last_turn.turn_index + 1
        skip_turn = InterviewTurn(
            session_id=interview_session_id,
            module_id=active_module.module_id,
            turn_index=turn_index,
            role="user",
            input_mode="text",
            answer_text="[SKIPPED]",
            question_meta=last_turn.question_meta,
            answer_meta={"skipped": True, "skip_reason": request.reason},
        )
        session.add(skip_turn)
        await session.flush()

        logger.debug(f"Skipped question at turn {turn_index}")

        # Get next question
        return await self.get_next_question(session, interview_session_id)

    async def pause_interview(
        self,
        session: AsyncSession,
        interview_session_id: UUID,
    ) -> InterviewPauseResponse:
        """Pause interview for later resumption.

        Args:
            session: Database session.
            interview_session_id: Interview session ID.

        Returns:
            InterviewPauseResponse with resume info.
        """
        interview = await self._get_interview_session(session, interview_session_id)
        if not interview:
            raise ValueError("Interview session not found")

        interview.status = "paused"

        # Get current position
        active_module = await self.module_state.get_active_module(
            session, interview_session_id
        )
        last_turn = await self._get_last_turn(session, interview_session_id)

        module_id = active_module.module_id if active_module else "M1"
        question_index = last_turn.turn_index if last_turn else 0

        await session.flush()
        logger.info(f"Paused interview {interview_session_id}")

        return InterviewPauseResponse(
            session_id=interview_session_id,
            status="paused",
            can_resume=True,
            resume_at_module=module_id,
            resume_at_question=question_index,
        )

    async def resume_interview(
        self,
        session: AsyncSession,
        interview_session_id: UUID,
    ) -> InterviewStartResponse:
        """Resume paused interview from last position.

        Args:
            session: Database session.
            interview_session_id: Interview session ID.

        Returns:
            InterviewStartResponse with current state.
        """
        interview = await self._get_interview_session(session, interview_session_id)
        if not interview:
            raise ValueError("Interview session not found")

        if interview.status not in ("paused", "active"):
            raise ValueError(f"Cannot resume interview with status: {interview.status}")

        interview.status = "active"

        # Get current module
        active_module = await self.module_state.get_active_module(
            session, interview_session_id
        )
        if not active_module:
            # Find first non-completed module
            modules = await self.module_state.get_all_modules(
                session, interview_session_id
            )
            for m in modules:
                if m.status != "completed":
                    m.status = "active"
                    active_module = m
                    break

        if not active_module:
            raise ValueError("All modules completed, cannot resume")

        # Get last turn to determine current question
        last_turn = await self._get_last_turn(session, interview_session_id)

        # Determine current question
        if last_turn and last_turn.role == "interviewer":
            # Last turn was a question, return it
            current_question = FirstQuestion(
                question_id=(last_turn.question_meta or {}).get("question_id", ""),
                question_text=last_turn.question_text or "",
                question_type=(last_turn.question_meta or {}).get(
                    "question_type", "open_text"
                ),
                target_signal=(last_turn.question_meta or {}).get("target_signal", ""),
            )
        else:
            # Need to generate next question
            question = self.question_bank.get_next_static_question(
                active_module.module_id,
                await self._get_asked_question_ids(
                    session, interview_session_id, active_module.module_id
                ),
            )
            if not question:
                question = self.question_bank.get_first_question(active_module.module_id)

            turn_index = await self._get_next_turn_index(session, interview_session_id)
            await self._create_interviewer_turn(
                session,
                interview_session_id,
                active_module.module_id,
                question,
                turn_index,
            )

            current_question = FirstQuestion(
                question_id=question.question_id,
                question_text=question.question_text,
                question_type=question.question_type,
                target_signal=question.target_signals[0]
                if question.target_signals
                else "",
            )

        # Build response
        modules = await self.module_state.get_all_modules(session, interview_session_id)
        module_plan = self._build_module_plan_from_db(modules)

        await session.flush()
        logger.info(f"Resumed interview {interview_session_id}")

        return InterviewStartResponse(
            session_id=interview_session_id,
            status="active",
            first_module=ModuleInfo(
                module_id=active_module.module_id,
                module_name=self.question_bank.get_module_name(active_module.module_id),
                estimated_duration_min=3,
                status="active",
            ),
            module_plan=module_plan,
            first_question=current_question,
        )

    async def get_interview_status(
        self,
        session: AsyncSession,
        interview_session_id: UUID,
    ) -> InterviewStatusResponse:
        """Get full interview status with all module progress.

        Args:
            session: Database session.
            interview_session_id: Interview session ID.

        Returns:
            InterviewStatusResponse with complete status.
        """
        interview = await self._get_interview_session(session, interview_session_id)
        if not interview:
            raise ValueError("Interview session not found")

        modules = await self.module_state.get_all_modules(session, interview_session_id)
        active_module = next((m for m in modules if m.status == "active"), None)

        # Calculate total duration
        if interview.ended_at:
            duration = int((interview.ended_at - interview.started_at).total_seconds())
        else:
            duration = int(
                (datetime.now(timezone.utc) - interview.started_at).total_seconds()
            )

        module_progress = [
            ModuleProgress(
                module_id=m.module_id,
                module_name=self.question_bank.get_module_name(m.module_id),
                questions_asked=m.question_count,
                coverage_score=m.coverage_score,
                confidence_score=m.confidence_score,
                signals_captured=list(m.signals_captured or []),
                status=m.status,
            )
            for m in modules
        ]

        return InterviewStatusResponse(
            session_id=interview_session_id,
            status=interview.status,
            input_mode=interview.input_mode,
            language_preference=interview.language_preference,
            started_at=interview.started_at,
            total_duration_sec=duration,
            modules=module_progress,
            current_module=active_module.module_id if active_module else None,
            completed_modules=[m.module_id for m in modules if m.status == "completed"],
        )

    # ========== Private Helper Methods ==========

    async def _ensure_user_exists(
        self,
        session: AsyncSession,
        user_id: UUID,
    ) -> User:
        """Ensure user exists, creating a demo user if not.

        For demo purposes, auto-creates users if they don't exist.
        In production, this should be replaced with proper auth.

        Args:
            session: Database session.
            user_id: User ID to check/create.

        Returns:
            User instance.
        """
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if user is None:
            # Auto-create demo user
            user = User(
                id=user_id,
                email=f"demo_{user_id}@darpan.local",
                display_name=f"Demo User {str(user_id)[:8]}",
            )
            session.add(user)
            await session.flush()
            logger.info(f"Created demo user {user_id}")

        return user

    async def _get_adaptive_question(
        self,
        session: AsyncSession,
        interview_session_id: UUID,
        module: InterviewModule,
    ) -> AdaptiveQuestionResult:
        """Get adaptive question using LLM.

        Args:
            session: Database session.
            interview_session_id: Interview session ID.
            module: Current module.

        Returns:
            AdaptiveQuestionResult with question details.
        """
        # Get context for prompt
        asked_ids = await self._get_asked_question_ids(
            session, interview_session_id, module.module_id
        )
        recent_turns = await self._get_recent_turns(
            session, interview_session_id, module.module_id
        )
        cross_module_summary = await self.module_state.get_completed_modules_summary(
            session, interview_session_id
        )

        interview = await self._get_interview_session(session, interview_session_id)
        sensitivity_settings = (interview.settings or {}).get(
            "sensitivity_settings", {}
        )

        # Get module info
        target_signals = self.question_bank.get_signal_targets(module.module_id)
        captured_signals = list(module.signals_captured or [])
        missing_signals = [s for s in target_signals if s not in captured_signals]

        try:
            # Call LLM for adaptive question
            prompt = self.prompt_service.get_interviewer_question_prompt(
                module_id=module.module_id,
                module_name=self.question_bank.get_module_name(module.module_id),
                module_goal=self.question_bank.get_module_goal(module.module_id),
                signal_targets=target_signals,
                questions_asked=module.question_count,
                max_questions=15,
                coverage=module.coverage_score,
                confidence=module.confidence_score,
                captured_signals=captured_signals,
                missing_signals=missing_signals,
                recent_turns=recent_turns,
                cross_module_summary=cross_module_summary,
                sensitivity_settings=sensitivity_settings,
            )

            response = await self.llm_client.generate(
                prompt=prompt,
                response_format=AdaptiveQuestionResponse,
                temperature=0.5,
                metadata={
                    "prompt_name": "interviewer_question",
                    "module_id": module.module_id,
                },
            )

            return AdaptiveQuestionResult.from_llm_response(response)

        except Exception as e:
            logger.warning(f"LLM adaptive question failed, using static: {e}")
            # Fallback to static question
            question = self.question_bank.get_next_static_question(
                module.module_id, asked_ids
            )
            if not question:
                # No more questions, mark complete
                return AdaptiveQuestionResult(
                    action="MODULE_COMPLETE",
                    question_text="",
                    language="EN",
                    question_type="open_text",
                    target_signal="",
                    rationale="No more questions available",
                    module_summary="Module completed.",
                )

            return AdaptiveQuestionResult(
                action="ASK_QUESTION",
                question_text=question.question_text,
                language="EN",
                question_type=question.question_type,
                target_signal=question.target_signals[0]
                if question.target_signals
                else "",
                rationale="Static fallback",
                question_id=question.question_id,  # Preserve static question ID
            )

    async def _record_consent(
        self,
        session: AsyncSession,
        user_id: UUID,
        consent: ConsentData,
    ) -> None:
        """Record consent event."""
        event = ConsentEvent(
            user_id=user_id,
            consent_type="interview",
            consent_version=consent.consent_version,
            accepted=consent.accepted,
            consent_metadata={
                "allow_audio_storage_days": consent.allow_audio_storage_days,
                "allow_data_retention_days": consent.allow_data_retention_days,
            },
        )
        session.add(event)

    async def _create_interviewer_turn(
        self,
        session: AsyncSession,
        interview_session_id: UUID,
        module_id: str,
        question: Question,
        turn_index: int,
    ) -> InterviewTurn:
        """Create an interviewer turn with a question."""
        turn = InterviewTurn(
            session_id=interview_session_id,
            module_id=module_id,
            turn_index=turn_index,
            role="interviewer",
            input_mode="text",
            question_text=question.question_text,
            question_meta={
                "question_id": question.question_id,
                "question_type": question.question_type,
                "target_signal": question.target_signals[0]
                if question.target_signals
                else "",
                "is_followup": question.is_followup,
            },
        )
        session.add(turn)
        await session.flush()
        return turn

    async def _create_adaptive_turn(
        self,
        session: AsyncSession,
        interview_session_id: UUID,
        module_id: str,
        question_result: AdaptiveQuestionResult,
        turn_index: int,
    ) -> InterviewTurn:
        """Create an interviewer turn from adaptive question result."""
        # Use the static question_id if available (from fallback), otherwise generate adaptive ID
        question_id = question_result.question_id or f"adaptive_{turn_index}"
        turn = InterviewTurn(
            session_id=interview_session_id,
            module_id=module_id,
            turn_index=turn_index,
            role="interviewer",
            input_mode="text",
            question_text=question_result.question_text,
            question_meta={
                "question_id": question_id,
                "question_type": question_result.question_type,
                "target_signal": question_result.target_signal,
                "is_followup": question_result.is_followup,
                "rationale": question_result.rationale,
                "acknowledgment_text": question_result.acknowledgment_text,
            },
        )
        session.add(turn)
        await session.flush()
        return turn

    async def _get_interview_session(
        self,
        session: AsyncSession,
        interview_session_id: UUID,
    ) -> InterviewSession | None:
        """Get interview session by ID."""
        result = await session.execute(
            select(InterviewSession).where(InterviewSession.id == interview_session_id)
        )
        return result.scalar_one_or_none()

    async def _get_last_turn(
        self,
        session: AsyncSession,
        interview_session_id: UUID,
    ) -> InterviewTurn | None:
        """Get the last turn for a session."""
        result = await session.execute(
            select(InterviewTurn)
            .where(InterviewTurn.session_id == interview_session_id)
            .order_by(InterviewTurn.turn_index.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def _get_next_turn_index(
        self,
        session: AsyncSession,
        interview_session_id: UUID,
    ) -> int:
        """Get the next turn index for a session."""
        last_turn = await self._get_last_turn(session, interview_session_id)
        return (last_turn.turn_index + 1) if last_turn else 0

    async def _get_asked_question_ids(
        self,
        session: AsyncSession,
        interview_session_id: UUID,
        module_id: str,
    ) -> list[str]:
        """Get IDs of questions already asked in a module."""
        result = await session.execute(
            select(InterviewTurn.question_meta)
            .where(
                InterviewTurn.session_id == interview_session_id,
                InterviewTurn.module_id == module_id,
                InterviewTurn.role == "interviewer",
            )
        )
        asked = []
        for (meta,) in result:
            if meta and "question_id" in meta:
                asked.append(meta["question_id"])
        return asked

    async def _get_previous_answers(
        self,
        session: AsyncSession,
        interview_session_id: UUID,
        module_id: str,
    ) -> list[dict]:
        """Get previous Q&A pairs for context."""
        result = await session.execute(
            select(InterviewTurn)
            .where(
                InterviewTurn.session_id == interview_session_id,
                InterviewTurn.module_id == module_id,
            )
            .order_by(InterviewTurn.turn_index)
        )
        turns = list(result.scalars().all())

        pairs = []
        for i in range(0, len(turns) - 1, 2):
            if turns[i].role == "interviewer" and turns[i + 1].role == "user":
                pairs.append(
                    {
                        "question": turns[i].question_text,
                        "answer": turns[i + 1].answer_text,
                    }
                )
        return pairs

    async def _get_recent_turns(
        self,
        session: AsyncSession,
        interview_session_id: UUID,
        module_id: str,
        limit: int = 6,
    ) -> list[dict]:
        """Get recent turns for context."""
        result = await session.execute(
            select(InterviewTurn)
            .where(
                InterviewTurn.session_id == interview_session_id,
                InterviewTurn.module_id == module_id,
            )
            .order_by(InterviewTurn.turn_index.desc())
            .limit(limit)
        )
        turns = list(reversed(result.scalars().all()))

        return [
            {
                "role": t.role,
                "question": t.question_text if t.role == "interviewer" else None,
                "answer": t.answer_text if t.role == "user" else None,
            }
            for t in turns
        ]

    async def _mark_interview_complete(
        self,
        session: AsyncSession,
        interview_session_id: UUID,
    ) -> None:
        """Mark interview as complete."""
        interview = await self._get_interview_session(session, interview_session_id)
        if interview:
            interview.status = "completed"
            interview.ended_at = datetime.now(timezone.utc)
            interview.total_duration_sec = int(
                (interview.ended_at - interview.started_at).total_seconds()
            )

    async def _handle_module_complete(
        self,
        session: AsyncSession,
        interview_session_id: UUID,
        module: InterviewModule,
        module_summary: str | None,
    ) -> InterviewNextQuestionResponse:
        """Handle module completion transition."""
        next_module = await self.module_state.transition_to_next_module(
            session, interview_session_id, module.module_id, module_summary
        )

        if next_module is None:
            await self._mark_interview_complete(session, interview_session_id)
            return self._build_module_complete_response(
                module, module_summary, all_complete=True
            )

        first_question = self.question_bank.get_first_question(next_module.module_id)
        turn_index = await self._get_next_turn_index(session, interview_session_id)

        await self._create_interviewer_turn(
            session,
            interview_session_id,
            next_module.module_id,
            first_question,
            turn_index,
        )

        return self._build_module_complete_response(
            module, module_summary, next_question=first_question, next_module=next_module
        )

    def _build_module_plan(
        self, modules: list[InterviewModule]
    ) -> list[ModulePlanItem]:
        """Build module plan from InterviewModule list."""
        return [
            ModulePlanItem(
                module_id=m.module_id,
                status=m.status,
                est_min=3,
            )
            for m in modules
        ]

    def _build_module_plan_from_db(
        self, modules: list[InterviewModule]
    ) -> list[ModulePlanItem]:
        """Build module plan from database modules."""
        return self._build_module_plan(modules)

    def _build_continue_response(
        self,
        module: InterviewModule,
        question_result: AdaptiveQuestionResult,
    ) -> InterviewNextQuestionResponse:
        """Build response for continuing interview."""
        # Use static question_id if available, otherwise generate adaptive ID
        question_id = question_result.question_id or f"adaptive_{module.question_count}"
        return InterviewNextQuestionResponse(
            question_id=question_id,
            question_text=question_result.question_text,
            question_type=question_result.question_type,
            question_meta=QuestionMeta(
                question_id=question_id,
                question_type=question_result.question_type,
                target_signal=question_result.target_signal,
                rationale=question_result.rationale,
                is_followup=question_result.is_followup,
            ),
            module_id=module.module_id,
            module_progress=ModuleProgress(
                module_id=module.module_id,
                module_name=self.question_bank.get_module_name(module.module_id),
                questions_asked=module.question_count,
                coverage_score=module.coverage_score,
                confidence_score=module.confidence_score,
                signals_captured=list(module.signals_captured or []),
                status=module.status,
            ),
            status="continue",
            acknowledgment_text=question_result.acknowledgment_text,
        )

    def _build_module_complete_response(
        self,
        module: InterviewModule,
        module_summary: str | None,
        next_question: Question | None = None,
        next_module: InterviewModule | None = None,
        all_complete: bool = False,
    ) -> InterviewNextQuestionResponse:
        """Build response for module completion."""
        status = "all_modules_complete" if all_complete else "module_complete"

        response = InterviewNextQuestionResponse(
            module_id=module.module_id,
            module_progress=ModuleProgress(
                module_id=module.module_id,
                module_name=self.question_bank.get_module_name(module.module_id),
                questions_asked=module.question_count,
                coverage_score=module.coverage_score,
                confidence_score=module.confidence_score,
                signals_captured=list(module.signals_captured or []),
                status="completed",
            ),
            status=status,
            module_summary=module_summary,
        )

        if next_question and next_module:
            response.question_id = next_question.question_id
            response.question_text = next_question.question_text
            response.question_type = next_question.question_type
            response.question_meta = QuestionMeta(
                question_id=next_question.question_id,
                question_type=next_question.question_type,
                target_signal=next_question.target_signals[0]
                if next_question.target_signals
                else "",
            )
            response.module_id = next_module.module_id

        return response

    def _build_all_complete_response(self) -> InterviewNextQuestionResponse:
        """Build response when all modules are complete."""
        return InterviewNextQuestionResponse(
            module_id="",
            module_progress=ModuleProgress(
                module_id="",
                module_name="",
                questions_asked=0,
                coverage_score=1.0,
                confidence_score=1.0,
                signals_captured=[],
                status="completed",
            ),
            status="all_modules_complete",
            module_summary="All interview modules completed successfully.",
        )

    # ========== Module-Based Onboarding Methods ==========

    async def get_user_modules(
        self,
        session: AsyncSession,
        user_id: UUID,
    ) -> UserModulesResponse:
        """Get all module completion status for a user.

        Args:
            session: Database session.
            user_id: User ID.

        Returns:
            UserModulesResponse with all modules and their status.
        """
        # Ensure user exists
        await self._ensure_user_exists(session, user_id)

        # Get all completed modules across all sessions for this user
        result = await session.execute(
            select(InterviewModule, InterviewSession)
            .join(InterviewSession, InterviewModule.session_id == InterviewSession.id)
            .where(InterviewSession.user_id == user_id)
            .order_by(InterviewModule.ended_at.desc().nulls_last())
        )
        rows = result.all()

        # Track best completion for each module
        module_completions: dict[str, tuple[InterviewModule, InterviewSession]] = {}
        for module, interview_session in rows:
            if module.module_id not in module_completions:
                module_completions[module.module_id] = (module, interview_session)
            elif module.status == "completed" and module_completions[module.module_id][0].status != "completed":
                module_completions[module.module_id] = (module, interview_session)

        # Define all modules (mandatory + add-ons)
        mandatory_modules = ["M1", "M2", "M3", "M4"]
        addon_modules = ["A1", "A2", "A3", "A4"]
        all_modules = mandatory_modules + addon_modules
        module_info = {
            "M1": {"name": "Core Identity & Context", "description": "Understanding who you are and your life context"},
            "M2": {"name": "Decision Logic & Risk", "description": "How you make decisions and handle uncertainty"},
            "M3": {"name": "Preferences & Values", "description": "Your priorities and what matters to you"},
            "M4": {"name": "Communication & Social", "description": "Your interaction style and social tendencies"},
            "A1": {"name": "Lifestyle & Routines", "description": "Your daily habits, routines, and lifestyle choices"},
            "A2": {"name": "Spending & Financial Behavior", "description": "How you manage money and make purchase decisions"},
            "A3": {"name": "Career & Growth Aspirations", "description": "Your career goals and personal growth mindset"},
            "A4": {"name": "Work & Learning Style", "description": "How you work, learn, and solve problems"},
        }

        modules: list[UserModuleStatus] = []
        completed_count = 0

        for module_id in all_modules:
            if module_id in module_completions:
                module, interview_session = module_completions[module_id]
                if module.status == "completed":
                    status = "completed"
                    if module_id in mandatory_modules:
                        completed_count += 1
                elif module.status == "active":
                    status = "in_progress"
                else:
                    status = "not_started"

                modules.append(UserModuleStatus(
                    module_id=module_id,
                    module_name=module_info[module_id]["name"],
                    description=module_info[module_id]["description"],
                    status=status,
                    coverage_score=module.coverage_score if module.status == "completed" else None,
                    confidence_score=module.confidence_score if module.status == "completed" else None,
                    session_id=interview_session.id if module.status in ("completed", "active") else None,
                ))
            else:
                modules.append(UserModuleStatus(
                    module_id=module_id,
                    module_name=module_info[module_id]["name"],
                    description=module_info[module_id]["description"],
                    status="not_started",
                ))

        can_generate_twin = completed_count >= 4

        return UserModulesResponse(
            user_id=user_id,
            modules=modules,
            completed_count=completed_count,
            total_required=4,
            can_generate_twin=can_generate_twin,
            existing_twin_id=None,  # TODO: Check for existing twin
        )

    async def start_single_module(
        self,
        session: AsyncSession,
        request: StartSingleModuleRequest,
    ) -> InterviewStartResponse:
        """Start a single module for a user.

        Args:
            session: Database session.
            request: Module start request.

        Returns:
            InterviewStartResponse with session info and first question.
        """
        # Validate module ID against registered question banks
        valid_modules = list(MODULE_FILES.keys())
        if request.module_id not in valid_modules:
            raise ValueError(f"Invalid module ID: {request.module_id}. Must be one of {valid_modules}")

        # Check if module is already completed or has an active/paused session
        user_modules = await self.get_user_modules(session, request.user_id)
        for mod in user_modules.modules:
            if mod.module_id == request.module_id:
                if mod.status == "completed":
                    raise ValueError(f"Module {request.module_id} is already completed")
                if mod.status == "in_progress" and mod.session_id:
                    # Resume existing session instead of creating a new one
                    logger.info(
                        f"Resuming existing session {mod.session_id} for module {request.module_id}"
                    )
                    return await self.resume_interview(session, mod.session_id)

        # Ensure user exists
        await self._ensure_user_exists(session, request.user_id)

        # Create interview session for this single module
        interview_session = InterviewSession(
            user_id=request.user_id,
            status="active",
            input_mode=request.input_mode,
            language_preference=request.language_preference,
            settings={
                "sensitivity_settings": {},
                "modules_to_complete": [request.module_id],
                "single_module_mode": True,
            },
        )
        session.add(interview_session)
        await session.flush()

        # Record consent if provided
        if request.consent:
            await self._record_consent(session, request.user_id, request.consent)

        # Initialize only this module
        modules = await self.module_state.initialize_modules(
            session,
            interview_session.id,
            [request.module_id],
        )

        # Get first question
        first_module = modules[0]
        first_question = self.question_bank.get_first_question(first_module.module_id)

        # Create first interviewer turn
        await self._create_interviewer_turn(
            session,
            interview_session.id,
            first_module.module_id,
            first_question,
            turn_index=0,
        )

        # Build response
        module_plan = self._build_module_plan(modules)
        first_module_info = ModuleInfo(
            module_id=first_module.module_id,
            module_name=self.question_bank.get_module_name(first_module.module_id),
            estimated_duration_min=3,
            status="active",
        )

        logger.info(f"Started single module {request.module_id} session {interview_session.id}")

        return InterviewStartResponse(
            session_id=interview_session.id,
            status="active",
            first_module=first_module_info,
            module_plan=module_plan,
            first_question=FirstQuestion(
                question_id=first_question.question_id,
                question_text=first_question.question_text,
                question_type=first_question.question_type,
                target_signal=first_question.target_signals[0]
                if first_question.target_signals
                else "",
            ),
        )

    async def complete_module_and_exit(
        self,
        session: AsyncSession,
        interview_session_id: UUID,
    ) -> ModuleCompleteResponse:
        """Save progress and exit to module selection.

        If module meets completion criteria, marks it as completed.
        Otherwise, pauses the session so the user can resume later.

        Args:
            session: Database session.
            interview_session_id: Interview session ID.

        Returns:
            ModuleCompleteResponse with completion status.
        """
        interview = await self._get_interview_session(session, interview_session_id)
        if not interview:
            raise ValueError("Interview session not found")

        # Get active module
        active_module = await self.module_state.get_active_module(
            session, interview_session_id
        )
        if not active_module:
            raise ValueError("No active module to complete")

        # Evaluate module completion
        completion = await self.module_state.evaluate_module_completion(
            session, interview_session_id, active_module.module_id
        )

        criteria = self.question_bank.get_module_completion_criteria(active_module.module_id)
        meets_criteria = (
            completion.is_complete
            or active_module.coverage_score >= criteria.coverage_threshold
        )

        if meets_criteria:
            # Module genuinely complete
            active_module.status = "completed"
            active_module.ended_at = datetime.now(timezone.utc)
            if completion.module_summary:
                active_module.completion_eval = {"summary": completion.module_summary}
            interview.status = "completed"
            interview.ended_at = datetime.now(timezone.utc)
            interview.total_duration_sec = int(
                (interview.ended_at - interview.started_at).total_seconds()
            )
            status = "module_completed"
            logger.info(f"Completed module {active_module.module_id} session {interview_session_id}")
        else:
            # Not enough coverage — pause so user can resume later
            active_module.status = "active"  # Keep active for resume
            interview.status = "paused"
            status = "module_paused"
            logger.info(
                f"Paused module {active_module.module_id} session {interview_session_id} "
                f"(coverage={active_module.coverage_score:.2f})"
            )

        await session.flush()

        # Check twin eligibility
        user_modules = await self.get_user_modules(session, interview.user_id)
        remaining = [m.module_id for m in user_modules.modules if m.status != "completed"]

        return ModuleCompleteResponse(
            session_id=interview_session_id,
            module_id=active_module.module_id,
            module_name=self.question_bank.get_module_name(active_module.module_id),
            status=status,
            module_summary=completion.module_summary if meets_criteria else None,
            coverage_score=active_module.coverage_score,
            confidence_score=active_module.confidence_score,
            can_generate_twin=user_modules.can_generate_twin,
            remaining_modules=remaining,
        )

    async def check_twin_eligibility(
        self,
        session: AsyncSession,
        user_id: UUID,
    ) -> TwinEligibilityResponse:
        """Check if user can generate their digital twin.

        Args:
            session: Database session.
            user_id: User ID.

        Returns:
            TwinEligibilityResponse with eligibility status.
        """
        user_modules = await self.get_user_modules(session, user_id)

        completed = [m.module_id for m in user_modules.modules if m.status == "completed"]
        missing = [m.module_id for m in user_modules.modules if m.status != "completed"]

        if user_modules.can_generate_twin:
            message = "All mandatory modules completed! You can now generate your digital twin."
        else:
            message = f"Complete {len(missing)} more module(s) to generate your digital twin: {', '.join(missing)}"

        return TwinEligibilityResponse(
            user_id=user_id,
            can_generate_twin=user_modules.can_generate_twin,
            completed_modules=completed,
            missing_modules=missing,
            message=message,
        )


# Singleton instance
_interview_service: InterviewService | None = None


def get_interview_service() -> InterviewService:
    """Get the singleton interview service instance."""
    global _interview_service
    if _interview_service is None:
        _interview_service = InterviewService()
    return _interview_service
