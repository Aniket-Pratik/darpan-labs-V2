"""Experiment API endpoints."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.schemas.experiment import (
    ExperimentCreateRequest,
    ExperimentCreateResponse,
    ExperimentListItem,
    ExperimentResultsResponse,
)
from app.services.experiment_service import ExperimentService, get_experiment_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/experiments", tags=["Experiments"])


def get_service() -> ExperimentService:
    return get_experiment_service()


@router.post(
    "",
    response_model=ExperimentCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create and run an experiment",
)
async def create_experiment(
    request: ExperimentCreateRequest,
    user_id: UUID = Query(..., description="User creating the experiment"),
    db: AsyncSession = Depends(get_session),
    service: ExperimentService = Depends(get_service),
):
    """Create an experiment and start running it against the cohort."""
    try:
        return await service.create_and_run(user_id, request, db)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/user/{user_id}",
    response_model=list[ExperimentListItem],
    summary="List user's experiments",
)
async def list_experiments(
    user_id: UUID,
    db: AsyncSession = Depends(get_session),
    service: ExperimentService = Depends(get_service),
):
    """List all experiments created by a user."""
    return await service.list_experiments(user_id, db)


@router.get(
    "/{experiment_id}",
    response_model=ExperimentResultsResponse,
    summary="Get experiment results",
)
async def get_experiment_results(
    experiment_id: UUID,
    db: AsyncSession = Depends(get_session),
    service: ExperimentService = Depends(get_service),
):
    """Get full experiment results including aggregate and individual responses."""
    try:
        return await service.get_results(experiment_id, db)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/{experiment_id}/status",
    summary="Get experiment status",
)
async def get_experiment_status(
    experiment_id: UUID,
    db: AsyncSession = Depends(get_session),
    service: ExperimentService = Depends(get_service),
):
    """Get experiment execution status and progress."""
    try:
        return await service.get_status(experiment_id, db)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
