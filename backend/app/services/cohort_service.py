"""Cohort management service."""

import logging
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.experiment import Cohort
from app.models.twin import TwinProfile
from app.schemas.experiment import (
    CohortCreateRequest,
    CohortCreateResponse,
    CohortFilters,
    CohortResponse,
    TwinSummary,
)

logger = logging.getLogger(__name__)

MAX_COHORT_SIZE = 50


class CohortService:
    """Manage cohorts of twins for experiments."""

    async def create_cohort(
        self,
        user_id: UUID,
        request: CohortCreateRequest,
        db: AsyncSession,
    ) -> CohortCreateResponse:
        """Create a new cohort from a list of twin IDs.

        Validates that all twins exist, are ready, and meet optional filter criteria.
        """
        if len(request.twin_ids) == 0:
            raise ValueError("Cohort must contain at least one twin")
        if len(request.twin_ids) > MAX_COHORT_SIZE:
            raise ValueError(f"Cohort cannot exceed {MAX_COHORT_SIZE} twins")

        # Deduplicate
        unique_ids = list(set(request.twin_ids))

        # Validate all twins exist and are ready
        stmt = select(TwinProfile).where(
            TwinProfile.id.in_(unique_ids),
            TwinProfile.status == "ready",
        )
        result = await db.execute(stmt)
        twins = result.scalars().all()
        twin_map = {t.id: t for t in twins}

        missing = [tid for tid in unique_ids if tid not in twin_map]
        if missing:
            raise ValueError(
                f"{len(missing)} twin(s) not found or not ready: {missing[:3]}"
            )

        # Apply filters if provided
        if request.filters:
            unique_ids = self._apply_filters(twins, request.filters)
            if not unique_ids:
                raise ValueError("No twins match the specified filters")

        cohort = Cohort(
            created_by=user_id,
            name=request.name,
            twin_ids=unique_ids,
            filters_used=request.filters.model_dump() if request.filters else None,
        )
        db.add(cohort)
        await db.flush()

        return CohortCreateResponse(
            id=cohort.id,
            name=cohort.name,
            twin_count=len(cohort.twin_ids),
            created_at=cohort.created_at,
        )

    async def get_cohort(
        self,
        cohort_id: UUID,
        db: AsyncSession,
    ) -> CohortResponse:
        """Get a cohort with twin summaries."""
        cohort = await self._load_cohort(cohort_id, db)

        # Load twin summaries
        twins = await self._get_twin_summaries(cohort.twin_ids, db)

        filters = None
        if cohort.filters_used:
            filters = CohortFilters(**cohort.filters_used)

        return CohortResponse(
            id=cohort.id,
            name=cohort.name,
            twin_ids=cohort.twin_ids,
            twins=twins,
            filters_used=filters,
            created_at=cohort.created_at,
        )

    async def list_cohorts(
        self,
        user_id: UUID,
        db: AsyncSession,
    ) -> list[CohortResponse]:
        """List all cohorts for a user."""
        stmt = (
            select(Cohort)
            .where(Cohort.created_by == user_id)
            .order_by(Cohort.created_at.desc())
        )
        result = await db.execute(stmt)
        cohorts = result.scalars().all()

        responses = []
        for cohort in cohorts:
            twins = await self._get_twin_summaries(cohort.twin_ids, db)
            filters = None
            if cohort.filters_used:
                filters = CohortFilters(**cohort.filters_used)
            responses.append(
                CohortResponse(
                    id=cohort.id,
                    name=cohort.name,
                    twin_ids=cohort.twin_ids,
                    twins=twins,
                    filters_used=filters,
                    created_at=cohort.created_at,
                )
            )
        return responses

    async def delete_cohort(
        self,
        cohort_id: UUID,
        db: AsyncSession,
    ) -> None:
        """Delete a cohort."""
        cohort = await self._load_cohort(cohort_id, db)
        await db.delete(cohort)

    async def get_available_twins(
        self,
        user_id: UUID,
        db: AsyncSession,
        min_quality: str | None = None,
    ) -> list[TwinSummary]:
        """Get all ready twins available for cohort creation."""
        stmt = select(TwinProfile).where(
            TwinProfile.status == "ready",
        )
        if min_quality:
            quality_order = {"base": 0, "enhanced": 1, "rich": 2, "full": 3}
            min_idx = quality_order.get(min_quality, 0)
            allowed = [q for q, idx in quality_order.items() if idx >= min_idx]
            stmt = stmt.where(TwinProfile.quality_label.in_(allowed))

        stmt = stmt.order_by(TwinProfile.created_at.desc())
        result = await db.execute(stmt)
        twins = result.scalars().all()

        return [
            TwinSummary(
                twin_id=t.id,
                quality_label=t.quality_label,
                quality_score=t.quality_score,
                modules_completed=t.modules_included,
            )
            for t in twins
        ]

    # --- Helpers ---

    def _apply_filters(
        self,
        twins: list[TwinProfile],
        filters: CohortFilters,
    ) -> list[UUID]:
        """Filter twins by quality and module requirements."""
        quality_order = {"base": 0, "enhanced": 1, "rich": 2, "full": 3}
        min_idx = quality_order.get(filters.min_quality, 0) if filters.min_quality else 0

        filtered_ids = []
        for twin in twins:
            twin_idx = quality_order.get(twin.quality_label, 0)
            if twin_idx < min_idx:
                continue
            if filters.required_modules:
                if not all(m in (twin.modules_included or []) for m in filters.required_modules):
                    continue
            filtered_ids.append(twin.id)

        return filtered_ids

    async def _load_cohort(self, cohort_id: UUID, db: AsyncSession) -> Cohort:
        """Load a cohort or raise ValueError."""
        stmt = select(Cohort).where(Cohort.id == cohort_id)
        result = await db.execute(stmt)
        cohort = result.scalar_one_or_none()
        if not cohort:
            raise ValueError(f"Cohort {cohort_id} not found")
        return cohort

    async def _get_twin_summaries(
        self,
        twin_ids: list[UUID],
        db: AsyncSession,
    ) -> list[TwinSummary]:
        """Get summaries for a list of twin IDs."""
        if not twin_ids:
            return []
        stmt = select(TwinProfile).where(TwinProfile.id.in_(twin_ids))
        result = await db.execute(stmt)
        twins = result.scalars().all()
        return [
            TwinSummary(
                twin_id=t.id,
                quality_label=t.quality_label,
                quality_score=t.quality_score,
                modules_completed=t.modules_included,
            )
            for t in twins
        ]


# Singleton
_service: CohortService | None = None


def get_cohort_service() -> CohortService:
    """Get the singleton cohort service."""
    global _service
    if _service is None:
        _service = CohortService()
    return _service
