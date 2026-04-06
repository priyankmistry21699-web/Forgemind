"""FM-127: Structured Run Memory Enrichment service.

Promotes run memory from loose state into queryable, structured execution
memory covering objectives, blockers, concerns, validation outcomes,
confidence factors, and delivery notes.
"""

import uuid
import logging
from typing import Any

from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.run import Run
from app.models.task import Task, TaskStatus
from app.models.artifact import Artifact, ArtifactType
from app.models.approval_request import ApprovalRequest
from app.models.execution_event import ExecutionEvent
from app.models.execution_checkpoint import ExecutionCheckpoint

logger = logging.getLogger(__name__)


async def enrich_run_memory(
    db: AsyncSession,
    run_id: uuid.UUID,
) -> dict[str, Any]:
    """Generate a structured memory enrichment for a run.

    Returns a comprehensive structured summary covering:
    - completed objectives
    - unresolved blockers
    - validation outcomes
    - confidence factors
    - delivery notes
    """
    # Load run
    run_result = await db.execute(select(Run).where(Run.id == run_id))
    run = run_result.scalar_one_or_none()
    if run is None:
        return {"error": "run_not_found"}

    # Tasks
    task_result = await db.execute(
        select(Task).where(Task.run_id == run_id).order_by(Task.created_at)
    )
    tasks = list(task_result.scalars().all())

    completed_objectives = [
        {"task_id": str(t.id), "title": t.title, "type": t.task_type}
        for t in tasks
        if t.status == TaskStatus.COMPLETED
    ]

    unresolved_blockers = [
        {"task_id": str(t.id), "title": t.title, "status": t.status.value}
        for t in tasks
        if t.status == TaskStatus.FAILED
    ]

    pending_work = [
        {"task_id": str(t.id), "title": t.title, "status": t.status.value}
        for t in tasks
        if t.status in (TaskStatus.READY, TaskStatus.RUNNING)
    ]

    # Artifacts
    art_result = await db.execute(select(Artifact).where(Artifact.run_id == run_id))
    artifacts = list(art_result.scalars().all())
    has_spec = any(a.artifact_type == ArtifactType.SPEC for a in artifacts)
    has_plan = any(a.artifact_type == ArtifactType.PLAN for a in artifacts)

    # Approvals
    approval_result = await db.execute(
        select(ApprovalRequest).where(ApprovalRequest.run_id == run_id)
    )
    approvals = list(approval_result.scalars().all())
    pending_approvals = [a for a in approvals if a.status.value == "pending"]
    rejected_approvals = [a for a in approvals if a.status.value == "rejected"]

    # Checkpoints
    cp_result = await db.execute(
        select(sa_func.count()).where(ExecutionCheckpoint.run_id == run_id)
    )
    checkpoint_count = cp_result.scalar_one()

    # Events
    event_result = await db.execute(
        select(sa_func.count()).where(ExecutionEvent.run_id == run_id)
    )
    event_count = event_result.scalar_one()

    # Validation outcomes
    validation_outcomes = {
        "has_spec": has_spec,
        "has_plan": has_plan,
        "tasks_completed": len(completed_objectives),
        "tasks_total": len(tasks),
        "completion_rate": round(len(completed_objectives) / max(len(tasks), 1), 2),
        "all_approved": len(pending_approvals) == 0 and len(rejected_approvals) == 0,
        "has_rejections": len(rejected_approvals) > 0,
    }

    # Confidence factors
    confidence_factors = []
    if has_spec:
        confidence_factors.append({"factor": "spec_present", "positive": True})
    else:
        confidence_factors.append({"factor": "spec_missing", "positive": False})

    if has_plan:
        confidence_factors.append({"factor": "plan_present", "positive": True})
    else:
        confidence_factors.append({"factor": "plan_missing", "positive": False})

    if len(completed_objectives) == len(tasks) and len(tasks) > 0:
        confidence_factors.append({"factor": "all_tasks_completed", "positive": True})
    elif len(unresolved_blockers) > 0:
        confidence_factors.append({"factor": "has_failed_tasks", "positive": False})

    if len(pending_approvals) == 0 and len(approvals) > 0:
        confidence_factors.append(
            {"factor": "all_approvals_resolved", "positive": True}
        )
    elif len(pending_approvals) > 0:
        confidence_factors.append({"factor": "pending_approvals", "positive": False})

    if len(rejected_approvals) > 0:
        confidence_factors.append({"factor": "has_rejections", "positive": False})

    # Delivery notes
    delivery_notes = []
    if run.status.value == "completed":
        delivery_notes.append("Run completed successfully")
    elif run.status.value == "failed":
        delivery_notes.append("Run failed — review blockers before delivery")
    elif run.status.value == "paused":
        delivery_notes.append("Run paused — resume before delivery")

    if len(pending_work) > 0:
        delivery_notes.append(f"{len(pending_work)} task(s) still pending")

    return {
        "run_id": str(run_id),
        "project_id": str(run.project_id),
        "run_status": run.status.value,
        "completed_objectives": completed_objectives,
        "unresolved_blockers": unresolved_blockers,
        "pending_work": pending_work,
        "validation_outcomes": validation_outcomes,
        "confidence_factors": confidence_factors,
        "delivery_notes": delivery_notes,
        "metadata": {
            "artifact_count": len(artifacts),
            "checkpoint_count": checkpoint_count,
            "event_count": event_count,
            "approval_count": len(approvals),
        },
    }
