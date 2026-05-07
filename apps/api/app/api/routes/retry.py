"""Adaptive retry routes — contextual retry, revision, and status endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user_id
from app.db.session import get_db
from app.services import adaptive_retry_service
from app.services.authz_service import check_project_permission, Action

router = APIRouter()


async def _resolve_task_project(db, task_id: uuid.UUID) -> uuid.UUID:
    """Return the project_id for a task, raising 404 if not found."""
    from app.models.task import Task
    from app.models.run import Run
    from sqlalchemy import select

    row = await db.execute(
        select(Run.project_id)
        .join(Task, Task.run_id == Run.id)
        .where(Task.id == task_id)
    )
    project_id = row.scalar_one_or_none()
    if project_id is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return project_id


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
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> RetryCheckResponse:
    """Check whether a task can be retried and get context."""
    # VULN-2 fix: authenticate + verify project membership
    project_id = await _resolve_task_project(db, task_id)
    await check_project_permission(db, project_id, user_id, Action.PROJECT_VIEW)

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
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> AdaptiveRetryResponse:
    """Perform an adaptive retry of a failed task."""
    # VULN-2 fix: authenticate + verify project run permission
    project_id = await _resolve_task_project(db, task_id)
    await check_project_permission(db, project_id, user_id, Action.PROJECT_RUN)

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
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> RevisionResponse:
    """Create a revision task for a failed task that has exhausted retries."""
    # VULN-2 fix: authenticate + verify project run permission
    project_id = await _resolve_task_project(db, task_id)
    await check_project_permission(db, project_id, user_id, Action.PROJECT_RUN)

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
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> RetryStatusResponse:
    """Get retry status summary for all tasks in a run."""
    # VULN-3 fix: authenticate + verify project membership
    from app.models.run import Run

    run = await db.get(Run, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    await check_project_permission(db, run.project_id, user_id, Action.PROJECT_VIEW)

    result = await adaptive_retry_service.get_retry_status(db, run_id)
    return RetryStatusResponse(**result)
