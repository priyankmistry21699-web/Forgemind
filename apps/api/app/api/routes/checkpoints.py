"""FM-121: Execution Checkpoint routes — run-scoped checkpoint CRUD."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.auth import get_current_user_id
from app.schemas.execution_checkpoint import (
    CheckpointCreate,
    CheckpointList,
    CheckpointRead,
)
from app.services import execution_checkpoint_service
from app.services.authz_service import check_project_permission, Action

router = APIRouter()


async def _resolve_project_for_run(db: AsyncSession, run_id: uuid.UUID) -> uuid.UUID:
    from sqlalchemy import select
    from app.models.run import Run

    result = await db.execute(select(Run.project_id).where(Run.id == run_id))
    pid = result.scalar_one_or_none()
    if pid is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Run not found"
        )
    return pid


@router.get("/runs/{run_id}/checkpoints", response_model=CheckpointList)
async def list_checkpoints(
    run_id: uuid.UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> CheckpointList:
    """List all checkpoints for a run, ordered by sequence number."""
    pid = await _resolve_project_for_run(db, run_id)
    await check_project_permission(db, pid, user_id, Action.PROJECT_VIEW)

    items, total = await execution_checkpoint_service.list_checkpoints(
        db, run_id, skip=skip, limit=limit
    )
    return CheckpointList(
        items=[CheckpointRead.model_validate(c) for c in items],
        total=total,
    )


@router.post(
    "/runs/{run_id}/checkpoints",
    response_model=CheckpointRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_checkpoint(
    run_id: uuid.UUID,
    body: CheckpointCreate,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> CheckpointRead:
    """Create a manual checkpoint for a run."""
    pid = await _resolve_project_for_run(db, run_id)
    await check_project_permission(db, pid, user_id, Action.PROJECT_UPDATE)

    checkpoint = await execution_checkpoint_service.create_checkpoint(
        db,
        run_id=run_id,
        project_id=pid,
        checkpoint_type=body.checkpoint_type,
        summary=body.summary,
        name=body.name,
        task_id=body.task_id,
        status_snapshot=body.status_snapshot,
        artifact_refs=body.artifact_refs,
        validation_snapshot=body.validation_snapshot,
        approval_snapshot=body.approval_snapshot,
        architecture_snapshot=body.architecture_snapshot,
        metadata=body.metadata_,
        created_by=str(user_id),
    )
    await db.commit()
    return CheckpointRead.model_validate(checkpoint)


@router.get("/runs/{run_id}/checkpoints/latest", response_model=CheckpointRead)
async def get_latest_checkpoint(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> CheckpointRead:
    """Get the most recent checkpoint for a run."""
    pid = await _resolve_project_for_run(db, run_id)
    await check_project_permission(db, pid, user_id, Action.PROJECT_VIEW)

    checkpoint = await execution_checkpoint_service.get_latest_checkpoint(db, run_id)
    if checkpoint is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No checkpoints found for this run",
        )
    return CheckpointRead.model_validate(checkpoint)


@router.get("/checkpoints/{checkpoint_id}", response_model=CheckpointRead)
async def get_checkpoint(
    checkpoint_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> CheckpointRead:
    """Get a single checkpoint by ID."""
    checkpoint = await execution_checkpoint_service.get_checkpoint(db, checkpoint_id)
    if checkpoint is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Checkpoint not found",
        )
    await check_project_permission(
        db, checkpoint.project_id, user_id, Action.PROJECT_VIEW
    )
    return CheckpointRead.model_validate(checkpoint)


# ---------------------------------------------------------------------------
# FM-123: Resume from checkpoint
# ---------------------------------------------------------------------------


@router.post(
    "/runs/{run_id}/checkpoints/{checkpoint_id}/resume",
    status_code=status.HTTP_200_OK,
)
async def resume_from_checkpoint(
    run_id: uuid.UUID,
    checkpoint_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> dict:
    """Resume a run from a specific checkpoint.

    Validates checkpoint ownership, builds continuation context, and records event.
    """
    pid = await _resolve_project_for_run(db, run_id)
    await check_project_permission(db, pid, user_id, Action.PROJECT_UPDATE)

    result = await execution_checkpoint_service.resume_from_checkpoint(
        db, run_id=run_id, checkpoint_id=checkpoint_id
    )
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["error"],
        )
    await db.commit()
    return result
