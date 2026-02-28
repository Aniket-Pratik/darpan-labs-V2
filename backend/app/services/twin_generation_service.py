"""Twin generation orchestrator — coordinates the full twin creation pipeline."""

import logging
import time
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.interview import InterviewModule, InterviewSession
from app.models.twin import TwinProfile
from app.schemas.llm_responses import ProfileExtractionResponse
from app.services.evidence_indexer import (
    EvidenceIndexerService,
    get_evidence_indexer_service,
)
from app.services.persona_generator import (
    PersonaGeneratorService,
    get_persona_generator_service,
)
from app.services.profile_builder import (
    ProfileBuilderService,
    get_profile_builder_service,
)

logger = logging.getLogger(__name__)

MANDATORY_MODULES = {"M1", "M2", "M3", "M4"}


class TwinGenerationService:
    """Orchestrate the full twin generation pipeline."""

    def __init__(
        self,
        profile_builder: ProfileBuilderService | None = None,
        persona_generator: PersonaGeneratorService | None = None,
        evidence_indexer: EvidenceIndexerService | None = None,
    ):
        self.profile_builder = profile_builder or get_profile_builder_service()
        self.persona_generator = persona_generator or get_persona_generator_service()
        self.evidence_indexer = evidence_indexer or get_evidence_indexer_service()

    async def generate_twin(
        self,
        user_id: UUID,
        modules_to_include: list[str],
        db: AsyncSession,
    ) -> TwinProfile:
        """Run the full twin generation pipeline.

        Steps:
            1. Validate modules are completed
            2. Create TwinProfile with status="generating"
            3. Extract structured profile (LLM)
            4. Generate persona summary (LLM)
            5. Index evidence snippets + embeddings
            6. Calculate quality metrics
            7. Update TwinProfile to status="ready"

        Args:
            user_id: User to generate twin for.
            modules_to_include: List of module IDs to include.
            db: Database session.

        Returns:
            Completed TwinProfile.

        Raises:
            ValueError: If required modules are not completed.
        """
        start_time = time.time()

        # 1. Validate all requested modules are completed
        completed = await self._get_completed_modules(user_id, db)
        requested = set(modules_to_include)
        missing = requested - completed
        if missing:
            raise ValueError(
                f"Modules not completed: {', '.join(sorted(missing))}. "
                f"Completed: {', '.join(sorted(completed))}"
            )

        # 2. Determine version number
        version = await self._get_next_version(user_id, db)

        # 3. Create initial twin profile
        quality_label = self._determine_quality_label(modules_to_include)
        twin = TwinProfile(
            user_id=user_id,
            version=version,
            status="generating",
            modules_included=sorted(modules_to_include),
            quality_label=quality_label,
            quality_score=0.0,
        )
        db.add(twin)
        await db.flush()  # Get the twin ID

        logger.info(
            f"Starting twin generation for user {user_id}, "
            f"version {version}, modules: {modules_to_include}"
        )

        try:
            # 4. Extract structured profile
            profile_response = await self.profile_builder.extract_profile(user_id, db)

            # 5. Generate persona summary
            profile_dict = profile_response.model_dump()
            persona_response = await self.persona_generator.generate_summary(
                structured_profile=profile_dict,
                modules_included=modules_to_include,
                uncertainty_flags=profile_response.uncertainty_flags,
            )

            # 6. Index evidence snippets with embeddings
            snippets = await self.evidence_indexer.index_evidence(
                user_id=user_id,
                twin_profile_id=twin.id,
                db=db,
            )

            # 7. Calculate quality metrics
            coverage_confidence = await self._build_coverage_confidence(
                user_id, modules_to_include, db
            )
            quality_score = self._calculate_quality_score(coverage_confidence)

            # 8. Update twin profile
            elapsed = time.time() - start_time
            twin.status = "ready"
            twin.structured_profile_json = profile_dict
            twin.persona_summary_text = persona_response.persona_summary_text
            twin.persona_full_text = None  # Could add extended narrative later
            twin.quality_score = quality_score
            twin.coverage_confidence = coverage_confidence
            twin.extraction_meta = {
                "completion_time_sec": round(elapsed, 1),
                "evidence_snippets_count": len(snippets),
                "key_traits": persona_response.key_traits,
                "uncertainty_flags": profile_response.uncertainty_flags,
            }

            await db.flush()

            logger.info(
                f"Twin generation complete for user {user_id}: "
                f"version={version}, quality={quality_label} ({quality_score:.2f}), "
                f"snippets={len(snippets)}, time={elapsed:.1f}s"
            )
            return twin

        except Exception as e:
            # Mark twin as failed
            twin.status = "failed"
            twin.extraction_meta = {"error": str(e)}
            await db.flush()
            logger.error(f"Twin generation failed for user {user_id}: {e}")
            raise

    async def _get_completed_modules(
        self, user_id: UUID, db: AsyncSession
    ) -> set[str]:
        """Get set of completed module IDs for a user."""
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
        return {row[0] for row in result.fetchall()}

    async def _get_next_version(self, user_id: UUID, db: AsyncSession) -> int:
        """Get the next version number for a user's twin."""
        stmt = select(func.max(TwinProfile.version)).where(
            TwinProfile.user_id == user_id
        )
        result = await db.execute(stmt)
        max_version = result.scalar()
        return (max_version or 0) + 1

    def _determine_quality_label(self, modules: list[str]) -> str:
        """Determine quality label based on modules included."""
        addons = set(modules) - MANDATORY_MODULES
        addon_count = len(addons)
        if addon_count == 0:
            return "base"
        elif addon_count <= 2:
            return "enhanced"
        elif addon_count <= 4:
            return "rich"
        else:
            return "full"

    async def _build_coverage_confidence(
        self,
        user_id: UUID,
        modules: list[str],
        db: AsyncSession,
    ) -> dict:
        """Build coverage/confidence map from completed modules."""
        stmt = (
            select(
                InterviewModule.module_id,
                InterviewModule.coverage_score,
                InterviewModule.confidence_score,
                InterviewModule.signals_captured,
            )
            .join(InterviewSession, InterviewModule.session_id == InterviewSession.id)
            .where(
                InterviewSession.user_id == user_id,
                InterviewModule.module_id.in_(modules),
                InterviewModule.status == "completed",
            )
        )
        result = await db.execute(stmt)
        rows = result.fetchall()

        by_module = {}
        for row in rows:
            module_id, coverage, confidence, signals = row
            by_module[module_id] = {
                "coverage": round(coverage, 2),
                "confidence": round(confidence, 2),
                "signals_captured": signals or [],
            }

        # Map modules to domains
        module_to_domain = {
            "M1": "identity",
            "M2": "decision_making",
            "M3": "preferences",
            "M4": "communication",
            "A1": "lifestyle",
            "A2": "spending",
            "A3": "career",
            "A4": "work_style",
            "A5": "technology",
            "A6": "health",
        }

        by_domain = {}
        for mid, data in by_module.items():
            domain = module_to_domain.get(mid, mid)
            by_domain[domain] = {
                "coverage": data["coverage"],
                "confidence": data["confidence"],
            }

        return {"by_module": by_module, "by_domain": by_domain}

    def _calculate_quality_score(self, coverage_confidence: dict) -> float:
        """Calculate overall quality score as weighted average of module scores."""
        by_module = coverage_confidence.get("by_module", {})
        if not by_module:
            return 0.0

        # Weights: mandatory modules are more important
        weights = {
            "M1": 0.20, "M2": 0.25, "M3": 0.25, "M4": 0.20,
            "A1": 0.10, "A2": 0.10, "A3": 0.10, "A4": 0.10,
            "A5": 0.10, "A6": 0.08,
        }

        total_weight = 0.0
        weighted_sum = 0.0
        for mid, data in by_module.items():
            w = weights.get(mid, 0.10)
            # Combined score = 60% coverage + 40% confidence
            score = 0.6 * data["coverage"] + 0.4 * data["confidence"]
            weighted_sum += w * score
            total_weight += w

        return round(weighted_sum / total_weight, 3) if total_weight > 0 else 0.0


# Singleton
_service: TwinGenerationService | None = None


def get_twin_generation_service() -> TwinGenerationService:
    """Get the singleton twin generation service."""
    global _service
    if _service is None:
        _service = TwinGenerationService()
    return _service
