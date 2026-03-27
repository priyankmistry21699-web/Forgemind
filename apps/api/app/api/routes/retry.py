"""Adaptive retry routes — contextual retry, revision, and status endpoints."""

import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services import adaptive_retry_service

router = APIRouter()


class RetryCheckResponse(BaseModel):
    can_retry: bool
    reason: str
    retry_count: int
    max_retries: int
    suggested_action: str


class AdaptiveRetryResponse(BaseModel):
    success: bool
    task_id: str
    retry_count: int
    message: str


class RevisionRequest(BaseModel):
    revision_description: str | None = None


class RevisionResponse(BaseModel):
    success: bool
    revision_task_id: str | None = None
    message: str


class RetryStatusResponse(BaseModel):
    total_tasks: int
    failed_count: int
    exhausted_count: int
    retried_count: int
    failed_tasks: list[dict]
    exhausted_tasks: list[dict]
    retried_tasks: list[dict]
    needs_escalation: bool


@router.get(
    "/tasks/{task_id}/retry/check",
    response_model=RetryCheckResponse,
)
async def check_retry(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> RetryCheckResponse:
    """Check whether a task can be retried and get context."""
    from app.services.task_service import get_task
    task = await get_task(db, task_id)
    result = await adaptive_retry_service.can_retry(db, task)
    return RetryCheckResponse(**result)


@router.post(
    "/tasks/{task_id}/retry/adaptive",
    response_model=AdaptiveRetryResponse,
)
async def adaptive_retry(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> AdaptiveRetryResponse:
    """Perform an adaptive retry of a failed task."""
    result = await adaptive_retry_service.adaptive_retry(db, task_id)
    return AdaptiveRetryResponse(**result)


@router.post(
    "/tasks/{task_id}/revision",
    response_model=RevisionResponse,
)
async def create_revision(
    task_id: uuid.UUID,
    body: RevisionRequest | None = None,
    db: AsyncSession = Depends(get_db),
) -> RevisionResponse:
    """Create a revision task for a failed task that has exhausted retries."""
    desc = body.revision_description if body else None
    result = await adaptive_retry_service.create_revision_task(
        db, task_id, revision_description=desc
    )
    return RevisionResponse(**result)


@router.get(
    "/runs/{run_id}/retry/status",
    response_model=RetryStatusResponse,
)
async def get_retry_status(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> RetryStatusResponse:
    """Get retry status summary for all tasks in a run."""
    result = await adaptive_retry_service.get_retry_status(db, run_id)
    return RetryStatusResponse(**result)
