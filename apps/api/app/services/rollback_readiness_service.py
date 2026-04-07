"""FM-135: Rollback readiness and recovery metadata.

Evaluates rollback readiness by examining checkpoint history, artifact
state, and previous releases to determine recovery options.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.execution_checkpoint import CheckpointType, ExecutionCheckpoint
from app.models.release_ops import ReleasePackage, ReleaseStatus

logger = logging.getLogger(__name__)


async def evaluate_rollback_readiness(
    db: AsyncSession,
    *,
    release_package_id: uuid.UUID,
) -> dict[str, Any]:
    """Evaluate rollback readiness for a release package.

    Returns recovery points, rollback strategies, and risk assessment.
    """
    pkg_result = await db.execute(
        select(ReleasePackage).where(ReleasePackage.id == release_package_id)
    )
    pkg = pkg_result.scalar_one_or_none()
    if pkg is None:
        return {"error": "release_package_not_found"}

    # Gather checkpoints for the run
    cp_result = await db.execute(
        select(ExecutionCheckpoint)
        .where(ExecutionCheckpoint.run_id == pkg.run_id)
        .order_by(ExecutionCheckpoint.sequence_number.desc())
    )
    checkpoints = list(cp_result.scalars().all())

    # Find previous releases for the same project
    prev_result = await db.execute(
        select(ReleasePackage)
        .where(
            ReleasePackage.project_id == pkg.project_id,
            ReleasePackage.id != pkg.id,
            ReleasePackage.status.in_([
                ReleaseStatus.DEPLOYED,
                ReleaseStatus.APPROVED,
                ReleaseStatus.READY,
            ]),
        )
        .order_by(ReleasePackage.created_at.desc())
        .limit(5)
    )
    prev_releases = list(prev_result.scalars().all())

    # Build recovery points
    recovery_points: list[dict[str, Any]] = []

    # 1. Checkpoint-based recovery
    for cp in checkpoints:
        recovery_points.append({
            "type": "checkpoint",
            "id": str(cp.id),
            "label": f"Checkpoint #{cp.sequence_number}: {cp.summary}",
            "checkpoint_type": cp.checkpoint_type.value,
            "sequence": cp.sequence_number,
            "has_status_snapshot": cp.status_snapshot is not None,
            "has_artifact_refs": cp.artifact_refs is not None,
            "created_at": cp.created_at.isoformat() if cp.created_at else None,
        })

    # 2. Previous release recovery
    for prev in prev_releases:
        recovery_points.append({
            "type": "previous_release",
            "id": str(prev.id),
            "label": f"Release v{prev.version} ({prev.status.value})",
            "version": prev.version,
            "status": prev.status.value,
            "created_at": prev.created_at.isoformat() if prev.created_at else None,
        })

    # Rollback strategies
    strategies: list[dict[str, str]] = []
    if checkpoints:
        strategies.append({
            "strategy": "checkpoint_resume",
            "description": "Resume from the latest checkpoint to restore run state",
            "available": "yes",
        })
    if prev_releases:
        strategies.append({
            "strategy": "version_rollback",
            "description": f"Roll back to previous release v{prev_releases[0].version}",
            "available": "yes",
        })
    strategies.append({
        "strategy": "manual_intervention",
        "description": "Manually restore state — always available as last resort",
        "available": "yes",
    })

    # Risk assessment
    has_pre_delivery = any(
        cp.checkpoint_type == CheckpointType.PRE_DELIVERY for cp in checkpoints
    )
    has_pre_approval = any(
        cp.checkpoint_type == CheckpointType.PRE_APPROVAL for cp in checkpoints
    )
    risk_signals: list[dict[str, Any]] = []

    if not checkpoints:
        risk_signals.append({
            "signal": "no_checkpoints",
            "level": "high",
            "detail": "No checkpoints — rollback requires manual state reconstruction",
        })
    elif not has_pre_delivery:
        risk_signals.append({
            "signal": "no_pre_delivery_checkpoint",
            "level": "medium",
            "detail": "No PRE_DELIVERY checkpoint — may not capture final state",
        })

    if not prev_releases:
        risk_signals.append({
            "signal": "no_previous_releases",
            "level": "medium",
            "detail": "No previous releases to fall back to",
        })

    if has_pre_delivery and has_pre_approval:
        risk_signals.append({
            "signal": "full_checkpoint_coverage",
            "level": "low",
            "detail": "Both PRE_APPROVAL and PRE_DELIVERY checkpoints available",
        })

    # Overall readiness
    high_risks = sum(1 for r in risk_signals if r["level"] == "high")
    is_rollback_ready = len(checkpoints) > 0 or len(prev_releases) > 0

    return {
        "release_package_id": str(release_package_id),
        "is_rollback_ready": is_rollback_ready,
        "recovery_points": recovery_points,
        "recovery_point_count": len(recovery_points),
        "strategies": strategies,
        "risk_signals": risk_signals,
        "risk_level": "high" if high_risks else "medium" if risk_signals else "low",
    }
