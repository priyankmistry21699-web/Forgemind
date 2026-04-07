"""FM-133: Environment-aware deployment readiness evaluation.

Evaluates whether a release package is ready for deployment to a given environment
by checking real signals: confidence score, approval state, task completion,
checkpoint coverage, and environment-specific required gates.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.approval_request import ApprovalRequest
from app.models.artifact import Artifact, ArtifactType
from app.models.execution_checkpoint import ExecutionCheckpoint
from app.models.release_ops import (
    DeploymentEnvironment,
    EnvironmentTier,
    ReleasePackage,
)
from app.models.run import Run, RunStatus
from app.models.task import Task, TaskStatus

logger = logging.getLogger(__name__)

# Minimum confidence thresholds per tier
_TIER_THRESHOLDS: dict[EnvironmentTier, int] = {
    EnvironmentTier.DEVELOPMENT: 30,
    EnvironmentTier.STAGING: 50,
    EnvironmentTier.CANARY: 65,
    EnvironmentTier.PRODUCTION: 80,
}


async def evaluate_readiness(
    db: AsyncSession,
    *,
    release_package_id: uuid.UUID,
    environment_id: uuid.UUID,
) -> dict[str, Any]:
    """Evaluate deployment readiness for a release package against an environment.

    Returns an explainable readiness report with per-check results, overall
    readiness status, and blocking reasons.
    """
    pkg_result = await db.execute(
        select(ReleasePackage).where(ReleasePackage.id == release_package_id)
    )
    pkg = pkg_result.scalar_one_or_none()
    if pkg is None:
        return {"error": "release_package_not_found"}

    env_result = await db.execute(
        select(DeploymentEnvironment).where(DeploymentEnvironment.id == environment_id)
    )
    env = env_result.scalar_one_or_none()
    if env is None:
        return {"error": "environment_not_found"}

    checks: list[dict[str, Any]] = []
    blockers: list[str] = []

    # Check 1: Run status
    run_result = await db.execute(select(Run).where(Run.id == pkg.run_id))
    run = run_result.scalar_one_or_none()
    run_completed = run is not None and run.status == RunStatus.COMPLETED
    checks.append({
        "check": "run_completed",
        "passed": run_completed,
        "detail": f"Run status: {run.status.value if run else 'not found'}",
    })
    if not run_completed:
        blockers.append("Run has not completed successfully")

    # Check 2: Task completion
    task_result = await db.execute(
        select(Task).where(Task.run_id == pkg.run_id)
    )
    tasks = list(task_result.scalars().all())
    total = len(tasks)
    completed = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED)
    failed = sum(1 for t in tasks if t.status == TaskStatus.FAILED)
    all_terminal = all(
        t.status in (TaskStatus.COMPLETED, TaskStatus.SKIPPED) for t in tasks
    ) if tasks else False

    checks.append({
        "check": "tasks_terminal",
        "passed": all_terminal,
        "detail": f"{completed}/{total} completed, {failed} failed",
    })
    if failed > 0:
        blockers.append(f"{failed} task(s) in FAILED state")

    # Check 3: Approval state
    approval_result = await db.execute(
        select(ApprovalRequest).where(ApprovalRequest.run_id == pkg.run_id)
    )
    approvals = list(approval_result.scalars().all())
    pending = sum(1 for a in approvals if a.status == "pending")
    rejected = sum(1 for a in approvals if a.status == "rejected")
    approvals_clear = pending == 0 and rejected == 0
    checks.append({
        "check": "approvals_resolved",
        "passed": approvals_clear,
        "detail": f"{len(approvals)} total, {pending} pending, {rejected} rejected",
    })
    if pending > 0:
        blockers.append(f"{pending} approval(s) still pending")
    if rejected > 0:
        blockers.append(f"{rejected} approval(s) rejected")

    # Check 4: Confidence threshold for tier
    threshold = _TIER_THRESHOLDS.get(env.tier, 50)
    confidence = pkg.confidence_snapshot or {}
    score = confidence.get("score", 0)
    meets_threshold = score >= threshold
    checks.append({
        "check": "confidence_threshold",
        "passed": meets_threshold,
        "detail": f"Score {score}/100 vs threshold {threshold} ({env.tier.value})",
    })
    if not meets_threshold:
        blockers.append(
            f"Confidence {score} below {env.tier.value} threshold ({threshold})"
        )

    # Check 5: Checkpoint coverage
    cp_result = await db.execute(
        select(ExecutionCheckpoint).where(ExecutionCheckpoint.run_id == pkg.run_id)
    )
    checkpoints = list(cp_result.scalars().all())
    has_checkpoints = len(checkpoints) > 0
    checks.append({
        "check": "has_checkpoints",
        "passed": has_checkpoints,
        "detail": f"{len(checkpoints)} checkpoint(s) recorded",
    })

    # Check 6: Required artifacts
    artifact_result = await db.execute(
        select(Artifact).where(Artifact.run_id == pkg.run_id)
    )
    artifacts = list(artifact_result.scalars().all())
    artifact_types = {a.artifact_type for a in artifacts}
    has_spec = ArtifactType.SPEC in artifact_types
    has_plan = ArtifactType.PLAN in artifact_types
    checks.append({
        "check": "required_artifacts",
        "passed": has_spec and has_plan,
        "detail": f"SPEC: {'yes' if has_spec else 'no'}, PLAN: {'yes' if has_plan else 'no'}",
    })

    # Check 7: Environment-specific required gates
    required_gates = env.required_gates or {}
    gate_names = required_gates.get("gates", [])
    if gate_names:
        checks.append({
            "check": "environment_gates",
            "passed": True,  # gates evaluated separately via FM-134
            "detail": f"{len(gate_names)} gate(s) configured (evaluated separately)",
        })

    # Overall
    all_passed = all(c["passed"] for c in checks)
    is_ready = all_passed and len(blockers) == 0

    return {
        "release_package_id": str(release_package_id),
        "environment_id": str(environment_id),
        "environment_name": env.name,
        "environment_tier": env.tier.value,
        "is_ready": is_ready,
        "checks": checks,
        "blockers": blockers,
        "confidence_score": score,
        "confidence_threshold": threshold,
        "total_checks": len(checks),
        "passed_checks": sum(1 for c in checks if c["passed"]),
    }
