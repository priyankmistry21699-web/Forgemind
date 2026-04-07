"""FM-137: Operational timeline view.

Builds a unified chronological timeline of all release-related events:
run phases, checkpoints, approvals, gate evaluations, and release status changes.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.approval_request import ApprovalRequest
from app.models.execution_checkpoint import ExecutionCheckpoint
from app.models.execution_event import ExecutionEvent
from app.models.release_ops import ReleaseGateResult, ReleasePackage
from app.models.run import Run
from app.models.task import Task

logger = logging.getLogger(__name__)


async def build_operational_timeline(
    db: AsyncSession,
    *,
    run_id: uuid.UUID,
) -> dict[str, Any]:
    """Build a unified operational timeline for a run.

    Merges events from multiple sources into a single chronological view.
    """
    run_result = await db.execute(select(Run).where(Run.id == run_id))
    run = run_result.scalar_one_or_none()
    if run is None:
        return {"error": "run_not_found"}

    entries: list[dict[str, Any]] = []

    # 1. Run lifecycle event
    entries.append({
        "timestamp": run.created_at.isoformat() if run.created_at else None,
        "category": "lifecycle",
        "event": "run_created",
        "detail": f"Run #{run.run_number} created (trigger: {run.trigger})",
    })

    # 2. Execution events
    event_result = await db.execute(
        select(ExecutionEvent)
        .where(ExecutionEvent.run_id == run_id)
        .order_by(ExecutionEvent.created_at)
    )
    for event in event_result.scalars().all():
        entries.append({
            "timestamp": event.created_at.isoformat() if event.created_at else None,
            "category": "execution",
            "event": event.event_type.value if hasattr(event.event_type, "value") else str(event.event_type),
            "detail": event.summary,
        })

    # 3. Checkpoints
    cp_result = await db.execute(
        select(ExecutionCheckpoint)
        .where(ExecutionCheckpoint.run_id == run_id)
        .order_by(ExecutionCheckpoint.created_at)
    )
    for cp in cp_result.scalars().all():
        entries.append({
            "timestamp": cp.created_at.isoformat() if cp.created_at else None,
            "category": "checkpoint",
            "event": f"checkpoint_{cp.checkpoint_type.value}",
            "detail": f"#{cp.sequence_number}: {cp.summary}",
        })

    # 4. Approvals
    approval_result = await db.execute(
        select(ApprovalRequest)
        .where(ApprovalRequest.run_id == run_id)
        .order_by(ApprovalRequest.created_at)
    )
    for approval in approval_result.scalars().all():
        entries.append({
            "timestamp": approval.created_at.isoformat() if approval.created_at else None,
            "category": "approval",
            "event": f"approval_{approval.status}",
            "detail": approval.title,
        })

    # 5. Release packages & gate results
    pkg_result = await db.execute(
        select(ReleasePackage)
        .where(ReleasePackage.run_id == run_id)
        .order_by(ReleasePackage.created_at)
    )
    for pkg in pkg_result.scalars().all():
        entries.append({
            "timestamp": pkg.created_at.isoformat() if pkg.created_at else None,
            "category": "release",
            "event": f"release_{pkg.status.value}",
            "detail": f"v{pkg.version}: {pkg.summary}",
        })

        # Gate results for this package
        gate_result = await db.execute(
            select(ReleaseGateResult)
            .where(ReleaseGateResult.release_package_id == pkg.id)
            .order_by(ReleaseGateResult.evaluated_at)
        )
        for gate in gate_result.scalars().all():
            entries.append({
                "timestamp": gate.evaluated_at.isoformat() if gate.evaluated_at else None,
                "category": "gate",
                "event": f"gate_{gate.gate_status.value}",
                "detail": f"{gate.gate_name}: {gate.detail}",
            })

    # 6. Tasks (start/end markers)
    task_result = await db.execute(
        select(Task)
        .where(Task.run_id == run_id)
        .order_by(Task.created_at)
    )
    for task in task_result.scalars().all():
        entries.append({
            "timestamp": task.created_at.isoformat() if task.created_at else None,
            "category": "task",
            "event": f"task_{task.status.value}",
            "detail": f"{task.title} ({task.task_type})",
        })

    # Sort chronologically
    entries.sort(key=lambda e: e.get("timestamp") or "")

    # Category counts
    categories: dict[str, int] = {}
    for e in entries:
        categories[e["category"]] = categories.get(e["category"], 0) + 1

    return {
        "run_id": str(run_id),
        "project_id": str(run.project_id),
        "run_status": run.status.value,
        "total_entries": len(entries),
        "categories": categories,
        "timeline": entries,
    }
