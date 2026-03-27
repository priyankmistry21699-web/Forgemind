"""Replay and trace routes — execution trace inspection and replay.

FM-046: Endpoints for viewing execution traces, replaying snapshots,
and comparing original vs replayed outputs.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.replay import (
    ReplaySnapshotRead,
    ReplaySnapshotList,
    ReplaySnapshotCreate,
    ReplayRequest,
    ExecutionTrace,
)
from app.services import replay_service

router = APIRouter()


# ── Execution Trace ──────────────────────────────────────────────

@router.get("/runs/{run_id}/trace", response_model=ExecutionTrace)
async def get_execution_trace(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> ExecutionTrace:
    """Get the full execution trace for a run (ordered snapshots)."""
    trace = await replay_service.get_execution_trace(db, run_id)
    return ExecutionTrace(
        run_id=run_id,
        total_steps=trace["total_steps"],
        snapshots=[ReplaySnapshotRead.model_validate(s) for s in trace["snapshots"]],
        total_tokens=trace["total_tokens"],
        total_cost_usd=trace["total_cost_usd"],
        total_duration_ms=trace["total_duration_ms"],
    )


# ── Task-level snapshots ────────────────────────────────────────

@router.get("/tasks/{task_id}/snapshots", response_model=ReplaySnapshotList)
async def get_task_snapshots(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> ReplaySnapshotList:
    """Get all execution snapshots for a specific task."""
    snapshots = await replay_service.get_task_snapshots(db, task_id)
    return ReplaySnapshotList(
        items=[ReplaySnapshotRead.model_validate(s) for s in snapshots],
        total=len(snapshots),
    )


# ── Snapshot CRUD ────────────────────────────────────────────────

@router.get("/replay/snapshots/{snapshot_id}", response_model=ReplaySnapshotRead)
async def get_snapshot(
    snapshot_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> ReplaySnapshotRead:
    """Get a single replay snapshot by ID."""
    snapshot = await replay_service.get_snapshot(db, snapshot_id)
    if snapshot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Snapshot not found",
        )
    return ReplaySnapshotRead.model_validate(snapshot)


@router.post(
    "/replay/snapshots",
    response_model=ReplaySnapshotRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_snapshot(
    body: ReplaySnapshotCreate,
    db: AsyncSession = Depends(get_db),
) -> ReplaySnapshotRead:
    """Manually capture an execution snapshot."""
    snapshot = await replay_service.capture_snapshot(
        db,
        task_id=body.task_id,
        run_id=body.run_id,
        project_id=body.project_id,
        agent_slug=body.agent_slug,
        input_snapshot=body.input_snapshot,
        prompt_snapshot=body.prompt_snapshot,
        model_used=body.model_used,
        temperature=body.temperature,
        output_snapshot=body.output_snapshot,
        error=body.error,
        tokens_used=body.tokens_used,
        duration_ms=body.duration_ms,
        cost_usd=body.cost_usd,
    )
    await db.commit()
    return ReplaySnapshotRead.model_validate(snapshot)


@router.get("/replay/snapshots", response_model=ReplaySnapshotList)
async def list_snapshots(
    run_id: uuid.UUID | None = Query(None),
    task_id: uuid.UUID | None = Query(None),
    project_id: uuid.UUID | None = Query(None),
    include_replays: bool = Query(False),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> ReplaySnapshotList:
    """List replay snapshots with optional filters."""
    snapshots, total = await replay_service.list_snapshots(
        db,
        run_id=run_id,
        task_id=task_id,
        project_id=project_id,
        include_replays=include_replays,
        limit=limit,
        offset=offset,
    )
    return ReplaySnapshotList(
        items=[ReplaySnapshotRead.model_validate(s) for s in snapshots],
        total=total,
    )


# ── Replay ───────────────────────────────────────────────────────

@router.post("/replay/snapshots/{snapshot_id}/replay")
async def replay_snapshot(
    snapshot_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Replay an execution snapshot — re-run with identical inputs and compare."""
    result = await replay_service.replay_snapshot(db, snapshot_id)
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["error"],
        )
    await db.commit()
    return result


@router.get("/replay/compare")
async def compare_snapshots(
    original_id: uuid.UUID = Query(...),
    replay_id: uuid.UUID = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Compare original and replay snapshot outputs."""
    result = await replay_service.compare_snapshots(db, original_id, replay_id)
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["error"],
        )
    return result
