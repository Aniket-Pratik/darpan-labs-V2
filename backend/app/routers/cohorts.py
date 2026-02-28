"""Cohort management API endpoints."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.schemas.experiment import (
    CohortCreateRequest,
    CohortCreateResponse,
    CohortResponse,
    TwinSummary,
)
from app.services.cohort_service import CohortService, get_cohort_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cohorts", tags=["Cohorts"])


def get_service() -> CohortService:
    return get_cohort_service()


@router.get(
    "/available-twins",
    response_model=list[TwinSummary],
    summary="List available twins for cohort creation",
)
async def get_available_twins(
    user_id: UUID = Query(...),
    min_quality: str | None = Query(None, description="Minimum quality: base, enhanced, rich, full"),
    db: AsyncSession = Depends(get_session),
    service: CohortService = Depends(get_service),
):
    """Get all ready twins that can be added to a cohort."""
    return await service.get_available_twins(user_id, db, min_quality)


@router.post(
    "",
    response_model=CohortCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a cohort",
)
async def create_cohort(
    request: CohortCreateRequest,
    user_id: UUID = Query(..., description="User creating the cohort"),
    db: AsyncSession = Depends(get_session),
    service: CohortService = Depends(get_service),
):
    """Create a new cohort from a list of twin IDs."""
    try:
        return await service.create_cohort(user_id, request, db)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/user/{user_id}",
    response_model=list[CohortResponse],
    summary="List user's cohorts",
)
async def list_cohorts(
    user_id: UUID,
    db: AsyncSession = Depends(get_session),
    service: CohortService = Depends(get_service),
):
    """List all cohorts created by a user."""
    return await service.list_cohorts(user_id, db)


@router.get(
    "/{cohort_id}",
    response_model=CohortResponse,
    summary="Get cohort details",
)
async def get_cohort(
    cohort_id: UUID,
    db: AsyncSession = Depends(get_session),
    service: CohortService = Depends(get_service),
):
    """Get a cohort with twin summaries."""
    try:
        return await service.get_cohort(cohort_id, db)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete(
    "/{cohort_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a cohort",
)
async def delete_cohort(
    cohort_id: UUID,
    db: AsyncSession = Depends(get_session),
    service: CohortService = Depends(get_service),
):
    """Delete a cohort."""
    try:
        await service.delete_cohort(cohort_id, db)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
