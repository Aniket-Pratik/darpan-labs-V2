"""Experiment execution and aggregation service."""

import asyncio
import json
import logging
from collections import Counter
from datetime import datetime, timezone
from uuid import UUID

from pydantic import BaseModel, Field
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_factory
from app.llm.client import LLMClient, get_llm_client
from app.models.experiment import Cohort, Experiment, ExperimentResult
from app.models.twin import TwinProfile
from app.schemas.experiment import (
    AggregateResults,
    ChoiceDistribution,
    ExperimentCreateRequest,
    ExperimentCreateResponse,
    ExperimentListItem,
    ExperimentResultsResponse,
    ExperimentScenario,
    IndividualResult,
    KeyPattern,
)
from app.services.evidence_retriever import (
    EvidenceRetrieverService,
    get_evidence_retriever_service,
)
from app.services.prompt_service import PromptService, get_prompt_service

logger = logging.getLogger(__name__)

TWIN_TIMEOUT_S = 30
MAX_EVIDENCE_PER_TWIN = 8


class ExperimentResponseLLM(BaseModel):
    """LLM response for a single twin's experiment response."""

    choice: str | None = None
    choice_index: int | None = None
    reasoning: str = ""
    confidence_score: float = Field(ge=0.0, le=1.0, default=0.5)
    confidence_label: str = "medium"
    uncertainty_reason: str | None = None
    evidence_used: list[dict] = Field(default_factory=list)
    coverage_gaps: list[str] = Field(default_factory=list)


class ExperimentService:
    """Execute experiments against cohorts of twins."""

    def __init__(
        self,
        llm_client: LLMClient | None = None,
        prompt_service: PromptService | None = None,
        evidence_retriever: EvidenceRetrieverService | None = None,
    ):
        self.llm = llm_client or get_llm_client()
        self.prompt_service = prompt_service or get_prompt_service()
        self.evidence_retriever = evidence_retriever or get_evidence_retriever_service()

    async def create_and_run(
        self,
        user_id: UUID,
        request: ExperimentCreateRequest,
        db: AsyncSession,
    ) -> ExperimentCreateResponse:
        """Create an experiment and start execution."""
        # Validate cohort exists
        stmt = select(Cohort).where(Cohort.id == request.cohort_id)
        result = await db.execute(stmt)
        cohort = result.scalar_one_or_none()
        if not cohort:
            raise ValueError(f"Cohort {request.cohort_id} not found")

        # Validate scenario has options for types that require them
        if request.scenario.type in ("forced_choice", "preference_rank"):
            if not request.scenario.options or len(request.scenario.options) < 2:
                raise ValueError(
                    f"Scenario type '{request.scenario.type}' requires at least 2 options"
                )
        if request.scenario.type == "likert_scale" and not request.scenario.options:
            request.scenario.options = ["1", "2", "3", "4", "5"]

        cohort_size = len(cohort.twin_ids)

        # Create experiment record
        experiment = Experiment(
            created_by=user_id,
            name=request.name,
            cohort_id=request.cohort_id,
            scenario=request.scenario.model_dump(),
            settings=request.settings.model_dump(),
            status="running",
        )
        db.add(experiment)
        await db.flush()

        experiment_id = experiment.id
        estimated_sec = max(5, cohort_size * 1)  # ~1s per twin estimate

        # Run execution in background
        asyncio.create_task(
            self._run_experiment_background(experiment_id, cohort.twin_ids, request)
        )

        return ExperimentCreateResponse(
            experiment_id=experiment_id,
            status="running",
            cohort_size=cohort_size,
            estimated_completion_sec=estimated_sec,
        )

    async def get_results(
        self,
        experiment_id: UUID,
        db: AsyncSession,
    ) -> ExperimentResultsResponse:
        """Get full experiment results."""
        stmt = select(Experiment).where(Experiment.id == experiment_id)
        result = await db.execute(stmt)
        experiment = result.scalar_one_or_none()
        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")

        # Get cohort size
        stmt_cohort = select(Cohort).where(Cohort.id == experiment.cohort_id)
        result_cohort = await db.execute(stmt_cohort)
        cohort = result_cohort.scalar_one_or_none()
        cohort_size = len(cohort.twin_ids) if cohort else 0

        # Get individual results
        stmt_results = (
            select(ExperimentResult)
            .where(ExperimentResult.experiment_id == experiment_id)
            .order_by(ExperimentResult.created_at)
        )
        result_rows = await db.execute(stmt_results)
        results = result_rows.scalars().all()

        # Load twin info for results
        twin_ids = [r.twin_id for r in results]
        twin_map = {}
        if twin_ids:
            stmt_twins = select(TwinProfile).where(TwinProfile.id.in_(twin_ids))
            result_twins = await db.execute(stmt_twins)
            twins = result_twins.scalars().all()
            twin_map = {t.id: t for t in twins}

        individual_results = []
        for r in results:
            twin = twin_map.get(r.twin_id)
            individual_results.append(
                IndividualResult(
                    twin_id=r.twin_id,
                    twin_name=None,
                    twin_quality=twin.quality_label if twin else "unknown",
                    modules_completed=twin.modules_included if twin else [],
                    choice=r.choice,
                    reasoning=r.reasoning,
                    confidence_score=r.confidence_score,
                    confidence_label=r.confidence_label,
                    evidence_used=r.evidence_used or [],
                    coverage_gaps=r.coverage_gaps or [],
                )
            )

        # Parse aggregate results
        aggregate = None
        if experiment.aggregate_results:
            aggregate = AggregateResults(**experiment.aggregate_results)

        execution_time = None
        if experiment.completed_at and experiment.created_at:
            execution_time = (
                experiment.completed_at - experiment.created_at
            ).total_seconds()

        return ExperimentResultsResponse(
            experiment_id=experiment.id,
            name=experiment.name,
            status=experiment.status,
            cohort_size=cohort_size,
            completed_responses=len(results),
            execution_time_sec=execution_time,
            aggregate_results=aggregate,
            individual_results=individual_results,
            created_at=experiment.created_at,
            completed_at=experiment.completed_at,
        )

    async def get_status(
        self,
        experiment_id: UUID,
        db: AsyncSession,
    ) -> dict:
        """Get experiment status with completion progress."""
        stmt = select(Experiment).where(Experiment.id == experiment_id)
        result = await db.execute(stmt)
        experiment = result.scalar_one_or_none()
        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")

        # Count completed results
        stmt_count = select(ExperimentResult).where(
            ExperimentResult.experiment_id == experiment_id
        )
        result_count = await db.execute(stmt_count)
        completed = len(result_count.scalars().all())

        # Get cohort size
        stmt_cohort = select(Cohort).where(Cohort.id == experiment.cohort_id)
        result_cohort = await db.execute(stmt_cohort)
        cohort = result_cohort.scalar_one_or_none()
        total = len(cohort.twin_ids) if cohort else 0

        return {
            "experiment_id": str(experiment.id),
            "status": experiment.status,
            "completed_responses": completed,
            "total_twins": total,
            "progress_pct": round(completed / total * 100) if total > 0 else 0,
        }

    async def list_experiments(
        self,
        user_id: UUID,
        db: AsyncSession,
    ) -> list[ExperimentListItem]:
        """List experiments for a user."""
        stmt = (
            select(Experiment)
            .where(Experiment.created_by == user_id)
            .order_by(Experiment.created_at.desc())
        )
        result = await db.execute(stmt)
        experiments = result.scalars().all()

        items = []
        for exp in experiments:
            # Get cohort size
            stmt_cohort = select(Cohort).where(Cohort.id == exp.cohort_id)
            result_cohort = await db.execute(stmt_cohort)
            cohort = result_cohort.scalar_one_or_none()
            cohort_size = len(cohort.twin_ids) if cohort else 0

            items.append(
                ExperimentListItem(
                    id=exp.id,
                    name=exp.name,
                    status=exp.status,
                    cohort_size=cohort_size,
                    created_at=exp.created_at,
                    completed_at=exp.completed_at,
                )
            )
        return items

    # --- Background execution ---

    async def _run_experiment_background(
        self,
        experiment_id: UUID,
        twin_ids: list[UUID],
        request: ExperimentCreateRequest,
    ) -> None:
        """Run experiment in background, processing all twins."""
        try:
            # Process twins concurrently — each gets its own DB session
            sem = asyncio.Semaphore(5)
            tasks = [
                self._process_single_twin(
                    experiment_id, twin_id, request, sem
                )
                for twin_id in twin_ids
            ]
            await asyncio.gather(*tasks, return_exceptions=True)

            # Compute aggregates and finalize in a dedicated session
            async with async_session_factory() as db:
                aggregate = await self._compute_aggregates(experiment_id, request.scenario, db)

                now = datetime.now(timezone.utc)
                stmt = (
                    update(Experiment)
                    .where(Experiment.id == experiment_id)
                    .values(
                        status="completed",
                        completed_at=now,
                        aggregate_results=aggregate.model_dump(),
                    )
                )
                await db.execute(stmt)
                await db.commit()
                logger.info(f"Experiment {experiment_id} completed")

        except Exception as e:
            logger.error(f"Experiment {experiment_id} failed: {e}")
            try:
                async with async_session_factory() as db:
                    stmt = (
                        update(Experiment)
                        .where(Experiment.id == experiment_id)
                        .values(status="failed")
                    )
                    await db.execute(stmt)
                    await db.commit()
            except Exception as db_err:
                logger.error(f"Failed to update experiment status: {db_err}")

    async def _process_single_twin(
        self,
        experiment_id: UUID,
        twin_id: UUID,
        request: ExperimentCreateRequest,
        sem: asyncio.Semaphore,
    ) -> None:
        """Process a single twin for an experiment with timeout and retry."""
        async with sem:
            for attempt in range(2):  # 1 initial + 1 retry
                try:
                    result = await asyncio.wait_for(
                        self._generate_twin_response(twin_id, request),
                        timeout=TWIN_TIMEOUT_S,
                    )

                    # Store result in its own session
                    async with async_session_factory() as db:
                        exp_result = ExperimentResult(
                            experiment_id=experiment_id,
                            twin_id=twin_id,
                            choice=result.choice,
                            reasoning=result.reasoning,
                            confidence_score=result.confidence_score,
                            confidence_label=result.confidence_label,
                            evidence_used=result.evidence_used,
                            coverage_gaps=result.coverage_gaps,
                            model_meta={
                                "model": self.llm.model,
                                "attempt": attempt + 1,
                                "uncertainty_reason": result.uncertainty_reason,
                            },
                        )
                        db.add(exp_result)
                        await db.commit()
                    return

                except asyncio.TimeoutError:
                    logger.warning(
                        f"Twin {twin_id} timed out (attempt {attempt + 1})"
                    )
                    if attempt == 1:
                        async with async_session_factory() as db:
                            exp_result = ExperimentResult(
                                experiment_id=experiment_id,
                                twin_id=twin_id,
                                choice=None,
                                reasoning="Response timed out after retries",
                                confidence_score=0.0,
                                confidence_label="low",
                                model_meta={"error": "timeout", "attempts": 2},
                            )
                            db.add(exp_result)
                            await db.commit()

                except Exception as e:
                    logger.error(f"Twin {twin_id} error: {e}")
                    if attempt == 1:
                        async with async_session_factory() as db:
                            exp_result = ExperimentResult(
                                experiment_id=experiment_id,
                                twin_id=twin_id,
                                choice=None,
                                reasoning=f"Error: {str(e)[:200]}",
                                confidence_score=0.0,
                                confidence_label="low",
                                model_meta={"error": str(e)[:200], "attempts": 2},
                            )
                            db.add(exp_result)
                            await db.commit()

    async def _generate_twin_response(
        self,
        twin_id: UUID,
        request: ExperimentCreateRequest,
    ) -> ExperimentResponseLLM:
        """Generate a single twin's response to an experiment scenario."""
        async with async_session_factory() as db:
            # Load twin profile
            stmt = select(TwinProfile).where(TwinProfile.id == twin_id)
            result = await db.execute(stmt)
            twin = result.scalar_one_or_none()
            if not twin:
                raise ValueError(f"Twin {twin_id} not found")

            # Retrieve relevant evidence
            evidence = await self.evidence_retriever.retrieve(
                query=request.scenario.prompt,
                twin_profile_id=twin_id,
                db=db,
                k=MAX_EVIDENCE_PER_TWIN,
            )

        # Format evidence for prompt
        evidence_text = self._format_evidence(evidence)

        # Format options
        options_text = "N/A"
        if request.scenario.options:
            options_text = "\n".join(
                f"  {i+1}. {opt}"
                for i, opt in enumerate(request.scenario.options)
            )

        # Build persona payload
        persona_payload = twin.persona_summary_text or ""
        if twin.structured_profile_json:
            persona_payload += f"\n\nStructured Profile:\n{json.dumps(twin.structured_profile_json, indent=2)[:2000]}"

        # Format prompt using template
        prompt = self.prompt_service.format_prompt(
            "experiment_response",
            experiment_type=request.scenario.type,
            persona_profile_payload=persona_payload,
            retrieved_evidence=evidence_text,
            completed_modules=", ".join(twin.modules_included or []),
            experiment_prompt=request.scenario.prompt,
            options=options_text,
        )

        # Call LLM
        response = await self.llm.generate(
            prompt=prompt,
            temperature=request.settings.temperature,
            max_tokens=request.settings.max_tokens,
            response_format=ExperimentResponseLLM,
        )

        return response

    def _format_evidence(self, evidence: list[dict]) -> str:
        """Format evidence snippets for the prompt."""
        if not evidence:
            return "No evidence available."

        lines = []
        for e in evidence:
            lines.append(
                f"[{e['snippet_id'][:8]}] ({e['category']}) "
                f"{e['text']} (relevance: {e.get('relevance_score', 0):.2f})"
            )
        return "\n".join(lines)

    async def _compute_aggregates(
        self,
        experiment_id: UUID,
        scenario: ExperimentScenario,
        db: AsyncSession,
    ) -> AggregateResults:
        """Compute aggregate results from individual responses."""
        stmt = select(ExperimentResult).where(
            ExperimentResult.experiment_id == experiment_id
        )
        result = await db.execute(stmt)
        results = result.scalars().all()

        if not results:
            return AggregateResults()

        # Choice distribution
        choice_counts: Counter = Counter()
        confidence_counts: Counter = Counter()
        all_reasoning: list[str] = []
        total_confidence = 0.0
        valid_count = 0

        for r in results:
            if r.choice:
                choice_counts[r.choice] += 1
            confidence_counts[r.confidence_label] += 1
            total_confidence += r.confidence_score
            valid_count += 1
            if r.reasoning and r.reasoning not in (
                "Response timed out after retries",
            ):
                all_reasoning.append(r.reasoning)

        total = len(results)
        choice_dist = {
            choice: ChoiceDistribution(
                count=count,
                percentage=round(count / total * 100, 1),
            )
            for choice, count in choice_counts.most_common()
        }

        confidence_dist = dict(confidence_counts)
        avg_confidence = total_confidence / valid_count if valid_count > 0 else 0.0

        # Extract key patterns using LLM if enough reasoning
        patterns = []
        themes = []
        if len(all_reasoning) >= 3:
            patterns, themes = await self._extract_patterns(
                all_reasoning, scenario, total
            )

        return AggregateResults(
            choice_distribution=choice_dist,
            aggregate_confidence=round(avg_confidence, 3),
            confidence_distribution=confidence_dist,
            key_patterns=patterns,
            dominant_reasoning_themes=themes,
        )

    async def _extract_patterns(
        self,
        reasoning_texts: list[str],
        scenario: ExperimentScenario,
        total_twins: int,
    ) -> tuple[list[KeyPattern], list[str]]:
        """Use LLM to extract key patterns and themes from reasoning texts."""
        try:
            sample = reasoning_texts[:20]  # Limit to 20 for cost control
            reasoning_block = "\n---\n".join(
                f"Twin {i+1}: {r}" for i, r in enumerate(sample)
            )

            prompt = (
                f"Analyze these {len(sample)} responses to the scenario: "
                f"\"{scenario.prompt}\"\n\n"
                f"Responses:\n{reasoning_block}\n\n"
                "Return JSON with:\n"
                "1. 'key_patterns': array of {{pattern: string, supporting_count: int, confidence: float}}\n"
                "   - 3-5 most common behavioral patterns\n"
                "2. 'themes': array of strings - 3-5 dominant reasoning themes\n"
                "Keep patterns concrete and grounded in the responses."
            )

            result = await self.llm.generate(
                prompt=prompt,
                system="You are an analyst summarizing experiment results. Return valid JSON only.",
                temperature=0.1,
                max_tokens=500,
            )

            raw_patterns = result.get("key_patterns", [])
            patterns = [
                KeyPattern(
                    pattern=p.get("pattern", ""),
                    supporting_twins=min(p.get("supporting_count", 1), total_twins),
                    confidence=p.get("confidence", 0.5),
                )
                for p in raw_patterns[:5]
                if p.get("pattern")
            ]

            themes = [str(t) for t in result.get("themes", [])][:5]
            return patterns, themes

        except Exception as e:
            logger.warning(f"Pattern extraction failed: {e}")
            return [], []


# Singleton
_service: ExperimentService | None = None


def get_experiment_service() -> ExperimentService:
    """Get the singleton experiment service."""
    global _service
    if _service is None:
        _service = ExperimentService()
    return _service
