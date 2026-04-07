"""FM-134: Release gates and operational policy checks.

Evaluates a configurable set of release gates against real run signals.
Gate definitions come from the target environment's required_gates config.
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
    GateStatus,
    ReleaseGateResult,
    ReleasePackage,
    ReleaseStatus,
)
from app.models.run import Run, RunStatus
from app.models.task import Task, TaskStatus

logger = logging.getLogger(__name__)

# Built-in gate evaluators
_BUILTIN_GATES = {
    "run_completed",
    "all_tasks_terminal",
    "no_failed_tasks",
    "approvals_clear",
    "confidence_minimum",
    "has_spec_artifact",
    "has_plan_artifact",
    "has_checkpoints",
    "no_rejections",
}


async def evaluate_gates(
    db: AsyncSession,
    *,
    release_package_id: uuid.UUID,
    environment_id: uuid.UUID | None = None,
) -> dict[str, Any]:
    """Evaluate all release gates for a package.

    Uses the target environment's required_gates config if provided,
    otherwise evaluates all built-in gates.

    Persists ReleaseGateResult rows and returns a summary.
    """
    pkg_result = await db.execute(
        select(ReleasePackage).where(ReleasePackage.id == release_package_id)
    )
    pkg = pkg_result.scalar_one_or_none()
    if pkg is None:
        return {"error": "release_package_not_found"}

    # Determine which gates to check
    gate_names: list[str] = list(_BUILTIN_GATES)
    if environment_id:
        env_result = await db.execute(
            select(DeploymentEnvironment).where(DeploymentEnvironment.id == environment_id)
        )
        env = env_result.scalar_one_or_none()
        if env and env.required_gates:
            configured = env.required_gates.get("gates", [])
            if configured:
                gate_names = configured

    # Gather context once
    ctx = await _gather_gate_context(db, pkg)

    # Evaluate each gate
    results: list[dict[str, Any]] = []
    for gate_name in gate_names:
        evaluator = _GATE_EVALUATORS.get(gate_name)
        if evaluator is None:
            result = GateResult(GateStatus.SKIPPED, f"Unknown gate: {gate_name}")
        else:
            result = evaluator(ctx)

        # Persist
        gate_row = ReleaseGateResult(
            release_package_id=pkg.id,
            gate_name=gate_name,
            gate_status=result.status,
            detail=result.detail,
        )
        db.add(gate_row)

        results.append({
            "gate": gate_name,
            "status": result.status.value,
            "detail": result.detail,
        })

    await db.flush()

    # Determine overall status
    failed_gates = [r for r in results if r["status"] == "failed"]
    pending_gates = [r for r in results if r["status"] == "pending"]
    all_passed = len(failed_gates) == 0 and len(pending_gates) == 0

    # Update package status if all gates passed
    if all_passed and pkg.status == ReleaseStatus.DRAFT:
        pkg.status = ReleaseStatus.READY
        await db.flush()
    elif failed_gates:
        pkg.status = ReleaseStatus.GATED
        await db.flush()

    return {
        "release_package_id": str(release_package_id),
        "total_gates": len(results),
        "passed": sum(1 for r in results if r["status"] == "passed"),
        "failed": len(failed_gates),
        "skipped": sum(1 for r in results if r["status"] == "skipped"),
        "all_passed": all_passed,
        "gate_results": results,
        "package_status": pkg.status.value,
    }


async def list_gate_results(
    db: AsyncSession,
    release_package_id: uuid.UUID,
) -> list[ReleaseGateResult]:
    result = await db.execute(
        select(ReleaseGateResult)
        .where(ReleaseGateResult.release_package_id == release_package_id)
        .order_by(ReleaseGateResult.evaluated_at)
    )
    return list(result.scalars().all())


# ---------------------------------------------------------------------------
# Internal gate evaluation
# ---------------------------------------------------------------------------


class GateResult:
    __slots__ = ("status", "detail")

    def __init__(self, status: GateStatus, detail: str) -> None:
        self.status = status
        self.detail = detail


class _GateContext:
    """Pre-fetched context for gate evaluation."""

    __slots__ = (
        "run", "tasks", "approvals", "artifacts", "checkpoints",
        "confidence", "artifact_types",
    )

    def __init__(self) -> None:
        self.run: Run | None = None
        self.tasks: list[Task] = []
        self.approvals: list[ApprovalRequest] = []
        self.artifacts: list[Artifact] = []
        self.checkpoints: list[ExecutionCheckpoint] = []
        self.confidence: dict[str, Any] = {}
        self.artifact_types: set[ArtifactType] = set()


async def _gather_gate_context(
    db: AsyncSession,
    pkg: ReleasePackage,
) -> _GateContext:
    ctx = _GateContext()

    run_result = await db.execute(select(Run).where(Run.id == pkg.run_id))
    ctx.run = run_result.scalar_one_or_none()

    task_result = await db.execute(select(Task).where(Task.run_id == pkg.run_id))
    ctx.tasks = list(task_result.scalars().all())

    approval_result = await db.execute(
        select(ApprovalRequest).where(ApprovalRequest.run_id == pkg.run_id)
    )
    ctx.approvals = list(approval_result.scalars().all())

    artifact_result = await db.execute(
        select(Artifact).where(Artifact.run_id == pkg.run_id)
    )
    ctx.artifacts = list(artifact_result.scalars().all())
    ctx.artifact_types = {a.artifact_type for a in ctx.artifacts}

    cp_result = await db.execute(
        select(ExecutionCheckpoint).where(ExecutionCheckpoint.run_id == pkg.run_id)
    )
    ctx.checkpoints = list(cp_result.scalars().all())

    ctx.confidence = pkg.confidence_snapshot or {}

    return ctx


def _gate_run_completed(ctx: _GateContext) -> GateResult:
    if ctx.run and ctx.run.status == RunStatus.COMPLETED:
        return GateResult(GateStatus.PASSED, "Run completed successfully")
    status = ctx.run.status.value if ctx.run else "not found"
    return GateResult(GateStatus.FAILED, f"Run status is {status}")


def _gate_all_tasks_terminal(ctx: _GateContext) -> GateResult:
    if not ctx.tasks:
        return GateResult(GateStatus.SKIPPED, "No tasks in run")
    terminal = {TaskStatus.COMPLETED, TaskStatus.SKIPPED}
    non_terminal = [t for t in ctx.tasks if t.status not in terminal]
    if not non_terminal:
        return GateResult(GateStatus.PASSED, f"All {len(ctx.tasks)} tasks terminal")
    return GateResult(GateStatus.FAILED, f"{len(non_terminal)} non-terminal tasks")


def _gate_no_failed_tasks(ctx: _GateContext) -> GateResult:
    failed = [t for t in ctx.tasks if t.status == TaskStatus.FAILED]
    if not failed:
        return GateResult(GateStatus.PASSED, "No failed tasks")
    return GateResult(GateStatus.FAILED, f"{len(failed)} task(s) failed")


def _gate_approvals_clear(ctx: _GateContext) -> GateResult:
    pending = sum(1 for a in ctx.approvals if a.status == "pending")
    rejected = sum(1 for a in ctx.approvals if a.status == "rejected")
    if pending == 0 and rejected == 0:
        return GateResult(GateStatus.PASSED, "All approvals resolved")
    parts = []
    if pending:
        parts.append(f"{pending} pending")
    if rejected:
        parts.append(f"{rejected} rejected")
    return GateResult(GateStatus.FAILED, ", ".join(parts))


def _gate_confidence_minimum(ctx: _GateContext) -> GateResult:
    score = ctx.confidence.get("score", 0)
    if score >= 50:
        return GateResult(GateStatus.PASSED, f"Confidence {score}/100")
    return GateResult(GateStatus.FAILED, f"Confidence {score}/100 (minimum: 50)")


def _gate_has_spec(ctx: _GateContext) -> GateResult:
    if ArtifactType.SPEC in ctx.artifact_types:
        return GateResult(GateStatus.PASSED, "SPEC artifact present")
    return GateResult(GateStatus.FAILED, "No SPEC artifact")


def _gate_has_plan(ctx: _GateContext) -> GateResult:
    if ArtifactType.PLAN in ctx.artifact_types:
        return GateResult(GateStatus.PASSED, "PLAN artifact present")
    return GateResult(GateStatus.FAILED, "No PLAN artifact")


def _gate_has_checkpoints(ctx: _GateContext) -> GateResult:
    if ctx.checkpoints:
        return GateResult(GateStatus.PASSED, f"{len(ctx.checkpoints)} checkpoint(s)")
    return GateResult(GateStatus.FAILED, "No checkpoints recorded")


def _gate_no_rejections(ctx: _GateContext) -> GateResult:
    rejected = sum(1 for a in ctx.approvals if a.status == "rejected")
    if rejected == 0:
        return GateResult(GateStatus.PASSED, "No rejections")
    return GateResult(GateStatus.FAILED, f"{rejected} rejection(s)")


_GATE_EVALUATORS = {
    "run_completed": _gate_run_completed,
    "all_tasks_terminal": _gate_all_tasks_terminal,
    "no_failed_tasks": _gate_no_failed_tasks,
    "approvals_clear": _gate_approvals_clear,
    "confidence_minimum": _gate_confidence_minimum,
    "has_spec_artifact": _gate_has_spec,
    "has_plan_artifact": _gate_has_plan,
    "has_checkpoints": _gate_has_checkpoints,
    "no_rejections": _gate_no_rejections,
}
