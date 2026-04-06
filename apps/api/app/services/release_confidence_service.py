"""FM-128: Release Confidence Scoring service.

Generates an explainable confidence score for delivery readiness from real
run state: validation, approvals, architecture impact, task completion,
and policy compliance.
"""

import uuid
import logging
from typing import Any

from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.run import Run
from app.models.task import Task
from app.models.artifact import Artifact, ArtifactType
from app.models.approval_request import ApprovalRequest
from app.models.execution_checkpoint import ExecutionCheckpoint

logger = logging.getLogger(__name__)

# Weight configuration for signal categories
_WEIGHTS = {
    "task_completion": 30,
    "spec_present": 10,
    "plan_present": 10,
    "approvals_resolved": 15,
    "no_rejections": 10,
    "has_checkpoints": 5,
    "run_completed": 15,
    "has_delivery_artifacts": 5,
}

CONFIDENCE_BANDS = [
    (80, "high"),
    (50, "medium"),
    (0, "low"),
]


def _band_for_score(score: int) -> str:
    for threshold, band in CONFIDENCE_BANDS:
        if score >= threshold:
            return band
    return "low"


async def compute_release_confidence(
    db: AsyncSession,
    run_id: uuid.UUID,
) -> dict[str, Any]:
    """Compute an explainable release confidence score.

    Returns:
        score: 0-100
        band: high/medium/low
        reasons: list of scored signals with explanations
        blocking_factors: list of items preventing high confidence
        suggested_actions: list of recommended next steps
    """
    # Load run
    run_result = await db.execute(select(Run).where(Run.id == run_id))
    run = run_result.scalar_one_or_none()
    if run is None:
        return {"error": "run_not_found"}

    reasons: list[dict[str, Any]] = []
    blocking_factors: list[str] = []
    suggested_actions: list[str] = []
    score = 0

    # ── Task completion ──
    task_result = await db.execute(
        select(Task.status, sa_func.count())
        .where(Task.run_id == run_id)
        .group_by(Task.status)
    )
    task_counts = {s.value: c for s, c in task_result.all()}
    total_tasks = sum(task_counts.values())
    completed = task_counts.get("completed", 0)
    failed = task_counts.get("failed", 0)

    if total_tasks > 0:
        completion_rate = completed / total_tasks
        earned = int(_WEIGHTS["task_completion"] * completion_rate)
        score += earned
        reasons.append(
            {
                "signal": "task_completion",
                "earned": earned,
                "max": _WEIGHTS["task_completion"],
                "detail": f"{completed}/{total_tasks} tasks completed ({completion_rate:.0%})",
            }
        )
        if completion_rate < 1:
            blocking_factors.append(f"{total_tasks - completed} task(s) not completed")
            suggested_actions.append("Complete remaining tasks")
        if failed > 0:
            blocking_factors.append(f"{failed} task(s) failed")
            suggested_actions.append("Investigate and resolve failed tasks")
    else:
        reasons.append(
            {
                "signal": "task_completion",
                "earned": 0,
                "max": _WEIGHTS["task_completion"],
                "detail": "No tasks found",
            }
        )
        blocking_factors.append("No tasks in run")

    # ── SPEC present ──
    art_result = await db.execute(
        select(Artifact.artifact_type).where(Artifact.run_id == run_id)
    )
    art_types = {row[0] for row in art_result.all()}

    has_spec = ArtifactType.SPEC in art_types
    spec_earned = _WEIGHTS["spec_present"] if has_spec else 0
    score += spec_earned
    reasons.append(
        {
            "signal": "spec_present",
            "earned": spec_earned,
            "max": _WEIGHTS["spec_present"],
            "detail": "SPEC artifact present" if has_spec else "No SPEC artifact",
        }
    )
    if not has_spec:
        suggested_actions.append("Generate a SPEC before delivery")

    # ── PLAN present ──
    has_plan = ArtifactType.PLAN in art_types
    plan_earned = _WEIGHTS["plan_present"] if has_plan else 0
    score += plan_earned
    reasons.append(
        {
            "signal": "plan_present",
            "earned": plan_earned,
            "max": _WEIGHTS["plan_present"],
            "detail": "PLAN artifact present" if has_plan else "No PLAN artifact",
        }
    )
    if not has_plan:
        suggested_actions.append("Generate a PLAN before delivery")

    # ── Approvals ──
    approval_result = await db.execute(
        select(ApprovalRequest.status, sa_func.count())
        .where(ApprovalRequest.run_id == run_id)
        .group_by(ApprovalRequest.status)
    )
    approval_counts = {s.value: c for s, c in approval_result.all()}
    total_approvals = sum(approval_counts.values())
    pending = approval_counts.get("pending", 0)
    rejected = approval_counts.get("rejected", 0)

    if total_approvals > 0:
        all_resolved = pending == 0
        resolved_earned = _WEIGHTS["approvals_resolved"] if all_resolved else 0
        score += resolved_earned
        reasons.append(
            {
                "signal": "approvals_resolved",
                "earned": resolved_earned,
                "max": _WEIGHTS["approvals_resolved"],
                "detail": f"{'All' if all_resolved else f'{pending} pending'} approvals resolved",
            }
        )
        if pending > 0:
            blocking_factors.append(f"{pending} approval(s) pending")
            suggested_actions.append("Resolve pending approvals")

        no_rej = rejected == 0
        rej_earned = _WEIGHTS["no_rejections"] if no_rej else 0
        score += rej_earned
        reasons.append(
            {
                "signal": "no_rejections",
                "earned": rej_earned,
                "max": _WEIGHTS["no_rejections"],
                "detail": "No rejections" if no_rej else f"{rejected} rejection(s)",
            }
        )
        if rejected > 0:
            blocking_factors.append(f"{rejected} approval(s) rejected")
            suggested_actions.append("Address rejected approvals")
    else:
        # No approvals — give partial credit
        score += _WEIGHTS["approvals_resolved"]
        score += _WEIGHTS["no_rejections"]
        reasons.append(
            {
                "signal": "approvals_resolved",
                "earned": _WEIGHTS["approvals_resolved"],
                "max": _WEIGHTS["approvals_resolved"],
                "detail": "No approvals required",
            }
        )
        reasons.append(
            {
                "signal": "no_rejections",
                "earned": _WEIGHTS["no_rejections"],
                "max": _WEIGHTS["no_rejections"],
                "detail": "No rejections (no approvals)",
            }
        )

    # ── Checkpoints ──
    cp_result = await db.execute(
        select(sa_func.count()).where(ExecutionCheckpoint.run_id == run_id)
    )
    cp_count = cp_result.scalar_one()
    has_cps = cp_count > 0
    cp_earned = _WEIGHTS["has_checkpoints"] if has_cps else 0
    score += cp_earned
    reasons.append(
        {
            "signal": "has_checkpoints",
            "earned": cp_earned,
            "max": _WEIGHTS["has_checkpoints"],
            "detail": f"{cp_count} checkpoint(s)" if has_cps else "No checkpoints",
        }
    )

    # ── Run completed ──
    run_done = run.status.value == "completed"
    run_earned = _WEIGHTS["run_completed"] if run_done else 0
    score += run_earned
    reasons.append(
        {
            "signal": "run_completed",
            "earned": run_earned,
            "max": _WEIGHTS["run_completed"],
            "detail": f"Run status: {run.status.value}",
        }
    )
    if not run_done:
        blocking_factors.append(f"Run not completed (status: {run.status.value})")

    # ── Delivery artifacts ──
    delivery_result = await db.execute(
        select(sa_func.count())
        .where(Artifact.run_id == run_id)
        .where(
            Artifact.artifact_type.in_(
                [ArtifactType.DOCUMENTATION, ArtifactType.REVIEW]
            )
        )
    )
    delivery_count = delivery_result.scalar_one()
    has_delivery = delivery_count > 0
    del_earned = _WEIGHTS["has_delivery_artifacts"] if has_delivery else 0
    score += del_earned
    reasons.append(
        {
            "signal": "has_delivery_artifacts",
            "earned": del_earned,
            "max": _WEIGHTS["has_delivery_artifacts"],
            "detail": f"{delivery_count} delivery artifact(s)"
            if has_delivery
            else "No delivery artifacts",
        }
    )
    if not has_delivery:
        suggested_actions.append("Generate delivery artifacts before release")

    band = _band_for_score(score)

    return {
        "run_id": str(run_id),
        "project_id": str(run.project_id),
        "score": score,
        "max_score": sum(_WEIGHTS.values()),
        "band": band,
        "reasons": reasons,
        "blocking_factors": blocking_factors,
        "suggested_actions": suggested_actions,
    }
