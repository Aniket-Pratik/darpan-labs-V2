"""Twin profile API endpoints."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.twin import TwinProfile
from app.schemas.twin import (
    CoverageConfidence,
    TwinGenerateRequest,
    TwinGenerateResponse,
    TwinListItem,
    TwinProfileResponse,
    TwinVersionInfo,
)
from app.services.twin_generation_service import (
    TwinGenerationService,
    get_twin_generation_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/twins", tags=["Twins"])


def get_service() -> TwinGenerationService:
    """Dependency for twin generation service."""
    return get_twin_generation_service()


@router.post(
    "/generate",
    response_model=TwinProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a digital twin",
    description="""
    Trigger twin generation for a user. Requires all mandatory modules (M1-M4)
    to be completed. Runs the full pipeline: profile extraction, persona summary
    generation, and evidence indexing with embeddings.
    """,
)
async def generate_twin(
    request: TwinGenerateRequest,
    user_id: UUID,
    session: AsyncSession = Depends(get_session),
    service: TwinGenerationService = Depends(get_service),
):
    """Generate a digital twin from completed interview modules."""
    try:
        twin = await service.generate_twin(
            user_id=user_id,
            modules_to_include=request.modules_to_include,
            db=session,
        )

        # Build version history
        versions = await _get_version_history(user_id, session)

        # Build coverage confidence list
        coverage_list = _build_coverage_list(twin.coverage_confidence)

        return TwinProfileResponse(
            id=twin.id,
            user_id=twin.user_id,
            version=twin.version,
            status=twin.status,
            modules_included=twin.modules_included,
            quality_label=twin.quality_label,
            quality_score=twin.quality_score,
            structured_profile=twin.structured_profile_json,
            persona_summary_text=twin.persona_summary_text,
            coverage_confidence=coverage_list,
            created_at=twin.created_at,
            version_history=versions,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Twin generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Twin generation failed: {str(e)}",
        )


@router.get(
    "/{twin_id}",
    response_model=TwinProfileResponse,
    summary="Get twin profile",
    description="Get a twin profile by ID with full structured data.",
)
async def get_twin(
    twin_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """Get a twin profile by ID."""
    twin = await _load_twin(twin_id, session)

    versions = await _get_version_history(twin.user_id, session)
    coverage_list = _build_coverage_list(twin.coverage_confidence)

    return TwinProfileResponse(
        id=twin.id,
        user_id=twin.user_id,
        version=twin.version,
        status=twin.status,
        modules_included=twin.modules_included,
        quality_label=twin.quality_label,
        quality_score=twin.quality_score,
        structured_profile=twin.structured_profile_json,
        persona_summary_text=twin.persona_summary_text,
        coverage_confidence=coverage_list,
        created_at=twin.created_at,
        version_history=versions,
    )


@router.get(
    "/user/{user_id}",
    response_model=TwinProfileResponse | None,
    summary="Get user's latest twin",
    description="Get the latest (highest version) twin profile for a user.",
)
async def get_user_twin(
    user_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """Get the latest twin for a user."""
    stmt = (
        select(TwinProfile)
        .where(TwinProfile.user_id == user_id, TwinProfile.status == "ready")
        .order_by(TwinProfile.version.desc())
        .limit(1)
    )
    result = await session.execute(stmt)
    twin = result.scalar_one_or_none()

    if not twin:
        return None

    versions = await _get_version_history(user_id, session)
    coverage_list = _build_coverage_list(twin.coverage_confidence)

    return TwinProfileResponse(
        id=twin.id,
        user_id=twin.user_id,
        version=twin.version,
        status=twin.status,
        modules_included=twin.modules_included,
        quality_label=twin.quality_label,
        quality_score=twin.quality_score,
        structured_profile=twin.structured_profile_json,
        persona_summary_text=twin.persona_summary_text,
        coverage_confidence=coverage_list,
        created_at=twin.created_at,
        version_history=versions,
    )


@router.get(
    "/{twin_id}/versions",
    response_model=list[TwinVersionInfo],
    summary="Get twin version history",
    description="Get all versions of a twin profile.",
)
async def get_twin_versions(
    twin_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """Get version history for a twin's user."""
    twin = await _load_twin(twin_id, session)
    return await _get_version_history(twin.user_id, session)


# --- Helper functions ---


async def _load_twin(twin_id: UUID, db: AsyncSession) -> TwinProfile:
    """Load a twin or raise 404."""
    stmt = select(TwinProfile).where(TwinProfile.id == twin_id)
    result = await db.execute(stmt)
    twin = result.scalar_one_or_none()
    if not twin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Twin {twin_id} not found",
        )
    return twin


async def _get_version_history(
    user_id: UUID, db: AsyncSession
) -> list[TwinVersionInfo]:
    """Get all twin versions for a user."""
    stmt = (
        select(TwinProfile)
        .where(TwinProfile.user_id == user_id)
        .order_by(TwinProfile.version.desc())
    )
    result = await db.execute(stmt)
    twins = result.scalars().all()

    return [
        TwinVersionInfo(
            version=t.version,
            modules_included=t.modules_included,
            quality_label=t.quality_label,
            quality_score=t.quality_score,
            created_at=t.created_at,
        )
        for t in twins
    ]


def _build_coverage_list(
    coverage_confidence: dict | None,
) -> list[CoverageConfidence]:
    """Convert coverage_confidence dict to list of CoverageConfidence."""
    if not coverage_confidence:
        return []

    by_module = coverage_confidence.get("by_module", {})
    result = []
    for module_id, data in by_module.items():
        result.append(
            CoverageConfidence(
                domain=module_id,
                coverage_score=data.get("coverage", 0.0),
                confidence_score=data.get("confidence", 0.0),
                signals_captured=data.get("signals_captured", []),
            )
        )
    return result
