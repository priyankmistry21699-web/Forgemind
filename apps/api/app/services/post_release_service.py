"""FM-136: Post-release report and outcome tracking.

Generates comprehensive post-release reports from release package state,
gate results, deployment readiness checks, and rollback metadata.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.approval_request import ApprovalRequest
from app.models.artifact import Artifact
from app.models.execution_checkpoint import ExecutionCheckpoint
from app.models.execution_event import ExecutionEvent
from app.models.release_ops import (
    ReleaseGateResult,
    ReleasePackage,
    ReleaseStatus,
)
from app.models.run import Run
from app.models.task import Task, TaskStatus

logger = logging.getLogger(__name__)


async def generate_post_release_report(
    db: AsyncSession,
    *,
    release_package_id: uuid.UUID,
) -> dict[str, Any]:
    """Generate a post-release report for a release package.

    Aggregates:
    - Release metadata and status timeline
    - Gate evaluation results
    - Task outcomes
    - Approval summary
    - Artifact inventory
    - Checkpoint coverage
    - Event timeline
    """
    pkg_result = await db.execute(
        select(ReleasePackage).where(ReleasePackage.id == release_package_id)
    )
    pkg = pkg_result.scalar_one_or_none()
    if pkg is None:
        return {"error": "release_package_not_found"}

    # Task outcomes
    task_result = await db.execute(
        select(Task).where(Task.run_id == pkg.run_id)
    )
    tasks = list(task_result.scalars().all())
    task_summary = _build_task_summary(tasks)

    # Gate results
    gate_result = await db.execute(
        select(ReleaseGateResult)
        .where(ReleaseGateResult.release_package_id == pkg.id)
        .order_by(ReleaseGateResult.evaluated_at)
    )
    gates = list(gate_result.scalars().all())
    gate_summary = _build_gate_summary(gates)

    # Approvals
    approval_result = await db.execute(
        select(ApprovalRequest).where(ApprovalRequest.run_id == pkg.run_id)
    )
    approvals = list(approval_result.scalars().all())
    approval_summary = _build_approval_summary(approvals)

    # Artifacts
    artifact_result = await db.execute(
        select(Artifact).where(Artifact.run_id == pkg.run_id)
    )
    artifacts = list(artifact_result.scalars().all())

    # Checkpoints
    cp_result = await db.execute(
        select(ExecutionCheckpoint).where(ExecutionCheckpoint.run_id == pkg.run_id)
    )
    checkpoints = list(cp_result.scalars().all())

    # Events (last 50)
    event_result = await db.execute(
        select(ExecutionEvent)
        .where(ExecutionEvent.run_id == pkg.run_id)
        .order_by(ExecutionEvent.created_at.desc())
        .limit(50)
    )
    events = list(event_result.scalars().all())

    # Run info
    run_result = await db.execute(select(Run).where(Run.id == pkg.run_id))
    run = run_result.scalar_one_or_none()

    return {
        "release_package_id": str(pkg.id),
        "project_id": str(pkg.project_id),
        "version": pkg.version,
        "status": pkg.status.value,
        "summary": pkg.summary,
        "created_at": pkg.created_at.isoformat() if pkg.created_at else None,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "run": {
            "id": str(run.id) if run else None,
            "run_number": run.run_number if run else None,
            "status": run.status.value if run else None,
        },
        "tasks": task_summary,
        "gates": gate_summary,
        "approvals": approval_summary,
        "artifacts": {
            "total": len(artifacts),
            "by_type": _count_by_type(artifacts),
        },
        "checkpoints": {
            "total": len(checkpoints),
            "types": _count_checkpoint_types(checkpoints),
        },
        "event_count": len(events),
        "confidence": pkg.confidence_snapshot,
        "rollback": pkg.rollback_metadata,
    }


async def record_outcome(
    db: AsyncSession,
    *,
    release_package_id: uuid.UUID,
    status: ReleaseStatus,
    notes: str | None = None,
) -> dict[str, Any]:
    """Record a release outcome (deployed, rolled_back, failed).

    Updates the package status and returns the updated state.
    """
    pkg_result = await db.execute(
        select(ReleasePackage).where(ReleasePackage.id == release_package_id)
    )
    pkg = pkg_result.scalar_one_or_none()
    if pkg is None:
        return {"error": "release_package_not_found"}

    valid_outcomes = {
        ReleaseStatus.DEPLOYED,
        ReleaseStatus.ROLLED_BACK,
        ReleaseStatus.FAILED,
    }
    if status not in valid_outcomes:
        return {
            "error": "invalid_outcome",
            "detail": f"Status must be one of: {[s.value for s in valid_outcomes]}",
        }

    old_status = pkg.status
    pkg.status = status

    if notes:
        meta = pkg.rollback_metadata or {}
        meta["outcome_notes"] = notes
        meta["outcome_recorded_at"] = datetime.now(timezone.utc).isoformat()
        pkg.rollback_metadata = meta

    await db.flush()
    logger.info(
        "Release %s outcome recorded: %s → %s",
        release_package_id, old_status.value, status.value,
    )

    return {
        "release_package_id": str(pkg.id),
        "previous_status": old_status.value,
        "new_status": status.value,
        "outcome_notes": notes,
    }


# ---------------------------------------------------------------------------
# Summary builders
# ---------------------------------------------------------------------------


def _build_task_summary(tasks: list[Task]) -> dict[str, Any]:
    total = len(tasks)
    by_status: dict[str, int] = {}
    for t in tasks:
        by_status[t.status.value] = by_status.get(t.status.value, 0) + 1

    failed_details = [
        {"id": str(t.id), "title": t.title, "error": t.error_message}
        for t in tasks
        if t.status == TaskStatus.FAILED
    ]

    return {
        "total": total,
        "by_status": by_status,
        "completed": by_status.get("completed", 0),
        "failed": by_status.get("failed", 0),
        "failed_details": failed_details,
    }


def _build_gate_summary(gates: list[ReleaseGateResult]) -> dict[str, Any]:
    results = []
    for g in gates:
        results.append({
            "gate": g.gate_name,
            "status": g.gate_status.value,
            "detail": g.detail,
        })
    passed = sum(1 for g in gates if g.gate_status.value == "passed")
    failed = sum(1 for g in gates if g.gate_status.value == "failed")
    return {
        "total": len(gates),
        "passed": passed,
        "failed": failed,
        "results": results,
    }


def _build_approval_summary(approvals: list[ApprovalRequest]) -> dict[str, Any]:
    total = len(approvals)
    by_status: dict[str, int] = {}
    for a in approvals:
        by_status[a.status] = by_status.get(a.status, 0) + 1
    return {
        "total": total,
        "approved": by_status.get("approved", 0),
        "pending": by_status.get("pending", 0),
        "rejected": by_status.get("rejected", 0),
    }


def _count_by_type(artifacts: list[Artifact]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for a in artifacts:
        counts[a.artifact_type.value] = counts.get(a.artifact_type.value, 0) + 1
    return counts


def _count_checkpoint_types(checkpoints: list[ExecutionCheckpoint]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for cp in checkpoints:
        counts[cp.checkpoint_type.value] = counts.get(cp.checkpoint_type.value, 0) + 1
    return counts
