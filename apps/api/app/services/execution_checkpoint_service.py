"""FM-121/122/123: Execution Checkpoint service.

CRUD, listing, latest retrieval, auto-checkpoint generation, and resume semantics.
"""

import uuid
import logging
from typing import Any

from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.execution_checkpoint import ExecutionCheckpoint, CheckpointType
from app.models.run import Run
from app.models.task import Task
from app.models.artifact import Artifact
from app.models.approval_request import ApprovalRequest
from app.models.execution_event import EventType
from app.services import event_service

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------


async def create_checkpoint(
    db: AsyncSession,
    *,
    run_id: uuid.UUID,
    project_id: uuid.UUID,
    checkpoint_type: CheckpointType = CheckpointType.MANUAL,
    summary: str,
    name: str | None = None,
    task_id: uuid.UUID | None = None,
    status_snapshot: dict | None = None,
    artifact_refs: dict | None = None,
    validation_snapshot: dict | None = None,
    approval_snapshot: dict | None = None,
    architecture_snapshot: dict | None = None,
    metadata: dict | None = None,
    created_by: str | None = None,
) -> ExecutionCheckpoint:
    """Create a new checkpoint for a run."""
    # Determine next sequence number
    seq_result = await db.execute(
        select(
            sa_func.coalesce(sa_func.max(ExecutionCheckpoint.sequence_number), -1)
        ).where(ExecutionCheckpoint.run_id == run_id)
    )
    next_seq = seq_result.scalar_one() + 1

    checkpoint = ExecutionCheckpoint(
        run_id=run_id,
        project_id=project_id,
        task_id=task_id,
        name=name,
        checkpoint_type=checkpoint_type,
        summary=summary,
        status_snapshot=status_snapshot,
        artifact_refs=artifact_refs,
        validation_snapshot=validation_snapshot,
        approval_snapshot=approval_snapshot,
        architecture_snapshot=architecture_snapshot,
        metadata_=metadata,
        sequence_number=next_seq,
        created_by=created_by,
    )
    db.add(checkpoint)
    await db.flush()

    # Emit event
    await event_service.emit_event(
        db,
        event_type=EventType.LIFECYCLE_TRANSITION,
        summary=f"Checkpoint created: {checkpoint_type.value} (seq {next_seq})",
        project_id=project_id,
        run_id=run_id,
        metadata={"checkpoint_id": str(checkpoint.id), "type": checkpoint_type.value},
    )

    logger.info(
        "Checkpoint %s created for run %s (seq %d)", checkpoint.id, run_id, next_seq
    )
    return checkpoint


async def list_checkpoints(
    db: AsyncSession,
    run_id: uuid.UUID,
    *,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[ExecutionCheckpoint], int]:
    """List checkpoints for a run, ordered by sequence number."""
    base = select(ExecutionCheckpoint).where(ExecutionCheckpoint.run_id == run_id)

    count_result = await db.execute(
        select(sa_func.count()).select_from(base.subquery())
    )
    total = count_result.scalar_one()

    result = await db.execute(
        base.order_by(ExecutionCheckpoint.sequence_number.asc())
        .offset(skip)
        .limit(limit)
    )
    items = list(result.scalars().all())
    return items, total


async def get_checkpoint(
    db: AsyncSession,
    checkpoint_id: uuid.UUID,
) -> ExecutionCheckpoint | None:
    """Get a single checkpoint by ID."""
    result = await db.execute(
        select(ExecutionCheckpoint).where(ExecutionCheckpoint.id == checkpoint_id)
    )
    return result.scalar_one_or_none()


async def get_latest_checkpoint(
    db: AsyncSession,
    run_id: uuid.UUID,
) -> ExecutionCheckpoint | None:
    """Get the most recent checkpoint for a run."""
    result = await db.execute(
        select(ExecutionCheckpoint)
        .where(ExecutionCheckpoint.run_id == run_id)
        .order_by(ExecutionCheckpoint.sequence_number.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


# ---------------------------------------------------------------------------
# FM-122: Auto-checkpoint from current run state
# ---------------------------------------------------------------------------


async def _build_status_snapshot(db: AsyncSession, run_id: uuid.UUID) -> dict[str, Any]:
    """Build a status snapshot from the current run state."""
    run_result = await db.execute(select(Run).where(Run.id == run_id))
    run = run_result.scalar_one_or_none()
    if run is None:
        return {"error": "run_not_found"}

    # Task counts
    task_result = await db.execute(
        select(Task.status, sa_func.count())
        .where(Task.run_id == run_id)
        .group_by(Task.status)
    )
    task_counts = {status.value: count for status, count in task_result.all()}

    return {
        "run_status": run.status.value,
        "run_number": run.run_number,
        "task_counts": task_counts,
        "total_tasks": sum(task_counts.values()),
    }


async def _build_artifact_refs(db: AsyncSession, run_id: uuid.UUID) -> dict[str, Any]:
    """Build artifact references snapshot."""
    result = await db.execute(
        select(Artifact.id, Artifact.title, Artifact.artifact_type).where(
            Artifact.run_id == run_id
        )
    )
    artifacts = [
        {"id": str(a_id), "title": title, "type": a_type.value}
        for a_id, title, a_type in result.all()
    ]
    return {"artifacts": artifacts, "count": len(artifacts)}


async def _build_approval_snapshot(
    db: AsyncSession, run_id: uuid.UUID
) -> dict[str, Any]:
    """Build approval state snapshot."""
    result = await db.execute(
        select(ApprovalRequest.id, ApprovalRequest.status, ApprovalRequest.title).where(
            ApprovalRequest.run_id == run_id
        )
    )
    approvals = []
    for a_id, a_status, a_title in result.all():
        approvals.append(
            {
                "id": str(a_id),
                "status": a_status.value
                if hasattr(a_status, "value")
                else str(a_status),
                "title": a_title,
            }
        )
    pending = sum(1 for a in approvals if a["status"] == "pending")
    return {"approvals": approvals, "pending_count": pending, "total": len(approvals)}


async def create_auto_checkpoint(
    db: AsyncSession,
    *,
    run_id: uuid.UUID,
    project_id: uuid.UUID,
    checkpoint_type: CheckpointType,
    summary: str,
    task_id: uuid.UUID | None = None,
) -> ExecutionCheckpoint:
    """Create an auto-checkpoint with computed snapshots from current run state."""
    status_snapshot = await _build_status_snapshot(db, run_id)
    artifact_refs = await _build_artifact_refs(db, run_id)
    approval_snapshot = await _build_approval_snapshot(db, run_id)

    return await create_checkpoint(
        db,
        run_id=run_id,
        project_id=project_id,
        checkpoint_type=checkpoint_type,
        summary=summary,
        task_id=task_id,
        status_snapshot=status_snapshot,
        artifact_refs=artifact_refs,
        approval_snapshot=approval_snapshot,
        created_by="system",
    )


# ---------------------------------------------------------------------------
# FM-123: Resume from checkpoint
# ---------------------------------------------------------------------------


async def resume_from_checkpoint(
    db: AsyncSession,
    *,
    run_id: uuid.UUID,
    checkpoint_id: uuid.UUID,
) -> dict[str, Any]:
    """Resume a run from a selected checkpoint.

    Validates checkpoint ownership, builds a continuation context, and
    records a resume event. Does NOT promise deterministic replay.

    Returns:
        context dict with completed/pending work, constraints, and stale info.
    """
    checkpoint = await get_checkpoint(db, checkpoint_id)
    if checkpoint is None:
        return {"error": "checkpoint_not_found"}

    if checkpoint.run_id != run_id:
        return {"error": "checkpoint_does_not_belong_to_run"}

    # Build continuation context from checkpoint + current state
    status_snapshot = checkpoint.status_snapshot or {}
    artifact_refs = checkpoint.artifact_refs or {}
    approval_snapshot = checkpoint.approval_snapshot or {}

    # Current state for comparison
    current_status = await _build_status_snapshot(db, run_id)
    current_approvals = await _build_approval_snapshot(db, run_id)

    # Determine what's already done vs what remains
    task_counts = current_status.get("task_counts", {})
    completed_tasks = task_counts.get("completed", 0)
    total_tasks = current_status.get("total_tasks", 0)

    # Stale approvals: approvals that existed at checkpoint but have since changed
    stale_approvals = []
    cp_approvals = approval_snapshot.get("approvals", [])
    current_approval_list = current_approvals.get("approvals", [])
    current_approval_ids = {a["id"] for a in current_approval_list}
    for a in cp_approvals:
        if a["id"] not in current_approval_ids:
            stale_approvals.append(a)

    continuation_context = {
        "checkpoint_id": str(checkpoint_id),
        "checkpoint_type": checkpoint.checkpoint_type.value,
        "checkpoint_sequence": checkpoint.sequence_number,
        "checkpoint_summary": checkpoint.summary,
        "completed_at_checkpoint": status_snapshot,
        "current_state": current_status,
        "artifacts_at_checkpoint": artifact_refs,
        "pending_tasks": total_tasks - completed_tasks,
        "completed_tasks": completed_tasks,
        "stale_approvals": stale_approvals,
        "constraints": {
            "approvals_pending": current_approvals.get("pending_count", 0),
        },
    }

    # Record resume event
    await event_service.emit_event(
        db,
        event_type=EventType.LIFECYCLE_TRANSITION,
        summary=f"Resumed from checkpoint #{checkpoint.sequence_number}",
        project_id=checkpoint.project_id,
        run_id=run_id,
        metadata={
            "checkpoint_id": str(checkpoint_id),
            "resume_type": checkpoint.checkpoint_type.value,
        },
    )

    logger.info("Run %s resumed from checkpoint %s", run_id, checkpoint_id)
    return {"resumed": True, "context": continuation_context}
