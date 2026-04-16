"""Velocity, Quality & Portfolio services — FM-194/195/196.

FM-194: Team velocity — throughput, cycle time, approval velocity.
FM-195: Quality metrics — test pass rate, defect density, rollback rate.
FM-196: Portfolio analytics — multi-project aggregation.
"""

import logging
import uuid
from typing import Any

from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analytics_metrics import QualitySnapshot

logger = logging.getLogger(__name__)


# ── FM-194: Velocity Metrics ─────────────────────────────────────


async def compute_velocity(
    db: AsyncSession,
    project_id: uuid.UUID,
    *,
    days: int = 30,
) -> dict[str, Any]:
    """Compute velocity metrics for a project over recent N days.

    Uses Run and Task tables directly to compute throughput.
    """
    from app.models.run import Run, RunStatus
    from app.models.task import Task, TaskStatus
    from datetime import datetime, timedelta, timezone

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    # Completed runs in window
    run_q = await db.execute(
        select(sa_func.count(Run.id)).where(
            Run.project_id == project_id,
            Run.status == RunStatus.COMPLETED,
            Run.created_at >= cutoff,
        )
    )
    completed_runs = run_q.scalar_one()

    # Completed tasks in window (join through Run to filter by project)
    task_q = await db.execute(
        select(sa_func.count(Task.id)).where(
            Task.status == TaskStatus.COMPLETED,
            Task.run_id == Run.id,
            Run.project_id == project_id,
        )
    )
    completed_tasks = task_q.scalar_one()

    # Average run cycle time (created_at → updated_at for completed runs)
    cycle_q = await db.execute(
        select(
            sa_func.avg(
                sa_func.extract("epoch", Run.updated_at) -
                sa_func.extract("epoch", Run.created_at)
            ).label("avg_cycle_seconds")
        ).where(
            Run.project_id == project_id,
            Run.status == RunStatus.COMPLETED,
            Run.created_at >= cutoff,
        )
    )
    avg_cycle = cycle_q.scalar_one()

    return {
        "project_id": str(project_id),
        "period_days": days,
        "completed_runs": completed_runs,
        "completed_tasks": completed_tasks,
        "runs_per_day": round(completed_runs / max(days, 1), 2),
        "avg_cycle_time_seconds": round(float(avg_cycle or 0), 2),
    }


async def compute_approval_velocity(
    db: AsyncSession,
    project_id: uuid.UUID,
    *,
    days: int = 30,
) -> dict[str, Any]:
    """Compute approval velocity: request-to-decision duration stats.

    Measures how fast approval requests are processed.
    """
    from app.models.approval_request import ApprovalRequest, ApprovalStatus
    from datetime import datetime, timedelta, timezone

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    # Get decided requests in window
    decided_q = await db.execute(
        select(ApprovalRequest).where(
            ApprovalRequest.project_id == project_id,
            ApprovalRequest.decided_at.isnot(None),
            ApprovalRequest.created_at >= cutoff,
        )
    )
    decided = list(decided_q.scalars().all())

    # Pending count
    pending_q = await db.execute(
        select(sa_func.count(ApprovalRequest.id)).where(
            ApprovalRequest.project_id == project_id,
            ApprovalRequest.status == ApprovalStatus.PENDING,
        )
    )
    pending_count = pending_q.scalar_one()

    if not decided:
        return {
            "project_id": str(project_id),
            "period_days": days,
            "total_decided": 0,
            "pending_count": pending_count,
            "avg_decision_seconds": 0.0,
            "min_decision_seconds": 0.0,
            "max_decision_seconds": 0.0,
            "approval_rate": 0.0,
        }

    # Compute decision durations
    durations = []
    approved = 0
    for req in decided:
        if req.decided_at and req.created_at:
            delta = (req.decided_at - req.created_at).total_seconds()
            durations.append(delta)
        if req.status == ApprovalStatus.APPROVED:
            approved += 1

    avg_dur = sum(durations) / len(durations) if durations else 0.0

    return {
        "project_id": str(project_id),
        "period_days": days,
        "total_decided": len(decided),
        "pending_count": pending_count,
        "avg_decision_seconds": round(avg_dur, 2),
        "min_decision_seconds": round(min(durations), 2) if durations else 0.0,
        "max_decision_seconds": round(max(durations), 2) if durations else 0.0,
        "approval_rate": round(approved / len(decided) * 100, 2),
    }


async def compute_velocity_comparison(
    db: AsyncSession,
    project_id: uuid.UUID,
    *,
    days: int = 30,
) -> dict[str, Any]:
    """Compare current period velocity with previous period.

    Returns both periods' metrics plus % change.
    """
    current = await compute_velocity(db, project_id, days=days)

    # Previous period: offset by 'days'
    from app.models.run import Run, RunStatus
    from datetime import datetime, timedelta, timezone

    now = datetime.now(timezone.utc)
    prev_end = now - timedelta(days=days)
    prev_start = prev_end - timedelta(days=days)

    # Previous completed runs
    prev_run_q = await db.execute(
        select(sa_func.count(Run.id)).where(
            Run.project_id == project_id,
            Run.status == RunStatus.COMPLETED,
            Run.created_at >= prev_start,
            Run.created_at < prev_end,
        )
    )
    prev_completed = prev_run_q.scalar_one()

    prev_rpd = round(prev_completed / max(days, 1), 2)

    def pct_change(current_val: float, prev_val: float) -> float | None:
        if prev_val == 0:
            return None
        return round((current_val - prev_val) / prev_val * 100, 2)

    return {
        "project_id": str(project_id),
        "period_days": days,
        "current": current,
        "previous": {
            "completed_runs": prev_completed,
            "runs_per_day": prev_rpd,
        },
        "change_pct": {
            "completed_runs": pct_change(current["completed_runs"], prev_completed),
            "runs_per_day": pct_change(current["runs_per_day"], prev_rpd),
        },
    }


# ── FM-195: Quality Metrics ──────────────────────────────────────


async def record_quality_snapshot(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    test_pass_rate: float = 0.0,
    defect_density: float = 0.0,
    rollback_rate: float = 0.0,
    review_coverage: float = 0.0,
) -> QualitySnapshot:
    """Record a quality metrics snapshot."""
    snap = QualitySnapshot(
        project_id=project_id,
        test_pass_rate=test_pass_rate,
        defect_density=defect_density,
        rollback_rate=rollback_rate,
        review_coverage=review_coverage,
    )
    db.add(snap)
    await db.flush()
    return snap


async def get_latest_quality(
    db: AsyncSession,
    project_id: uuid.UUID,
) -> QualitySnapshot | None:
    """Get the most recent quality snapshot."""
    result = await db.execute(
        select(QualitySnapshot)
        .where(QualitySnapshot.project_id == project_id)
        .order_by(QualitySnapshot.snapshot_date.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_quality_trend(
    db: AsyncSession,
    project_id: uuid.UUID,
    *,
    limit: int = 30,
) -> list[dict[str, Any]]:
    """Get recent quality snapshots for trend visualization."""
    result = await db.execute(
        select(QualitySnapshot)
        .where(QualitySnapshot.project_id == project_id)
        .order_by(QualitySnapshot.snapshot_date.desc())
        .limit(limit)
    )
    snaps = list(result.scalars().all())
    return [
        {
            "id": str(s.id),
            "test_pass_rate": s.test_pass_rate,
            "defect_density": s.defect_density,
            "rollback_rate": s.rollback_rate,
            "review_coverage": s.review_coverage,
            "snapshot_date": s.snapshot_date.isoformat() if s.snapshot_date else None,
        }
        for s in snaps
    ]


# Default quality gate thresholds
DEFAULT_QUALITY_GATES: dict[str, dict[str, Any]] = {
    "test_pass_rate": {"min": 0.8, "label": "Test pass rate"},
    "defect_density": {"max": 0.05, "label": "Defect density"},
    "rollback_rate": {"max": 0.1, "label": "Rollback rate"},
    "review_coverage": {"min": 0.7, "label": "Review coverage"},
}


async def evaluate_quality_gates(
    db: AsyncSession,
    project_id: uuid.UUID,
    *,
    gates: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Evaluate quality gates against latest snapshot.

    Returns pass/fail status and list of gate violations (warnings).
    gates overrides DEFAULT_QUALITY_GATES with custom thresholds.
    """
    effective_gates = {**DEFAULT_QUALITY_GATES, **(gates or {})}

    snapshot = await get_latest_quality(db, project_id)
    if snapshot is None:
        return {
            "project_id": str(project_id),
            "passed": True,
            "gates_evaluated": 0,
            "violations": [],
            "warnings": [],
            "message": "No quality snapshot available — gates skipped",
        }

    violations: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    for metric_name, gate_cfg in effective_gates.items():
        value = getattr(snapshot, metric_name, None)
        if value is None:
            continue

        label = gate_cfg.get("label", metric_name)

        # Check min threshold
        if "min" in gate_cfg and value < gate_cfg["min"]:
            entry = {
                "metric": metric_name,
                "label": label,
                "value": round(float(value), 4),
                "threshold": gate_cfg["min"],
                "direction": "below_min",
            }
            violations.append(entry)
            warnings.append(f"{label} is {value:.2%}, below minimum {gate_cfg['min']:.2%}")

        # Check max threshold
        if "max" in gate_cfg and value > gate_cfg["max"]:
            entry = {
                "metric": metric_name,
                "label": label,
                "value": round(float(value), 4),
                "threshold": gate_cfg["max"],
                "direction": "above_max",
            }
            violations.append(entry)
            warnings.append(f"{label} is {value:.2%}, above maximum {gate_cfg['max']:.2%}")

    passed = len(violations) == 0

    return {
        "project_id": str(project_id),
        "passed": passed,
        "gates_evaluated": len(effective_gates),
        "violations": violations,
        "warnings": warnings,
    }


# ── FM-196: Portfolio Analytics ──────────────────────────────────


async def get_portfolio_summary(
    db: AsyncSession,
    project_ids: list[uuid.UUID],
    *,
    sort_by: str | None = None,
    sort_order: str = "desc",
    filter_min_runs: int | None = None,
    filter_min_cost: float | None = None,
    filter_max_cost: float | None = None,
) -> dict[str, Any]:
    """Aggregate analytics across multiple projects.

    Sort/filter options (FM-196):
    - sort_by: 'total_runs', 'completed_runs', 'total_cost_usd', 'success_rate'
    - sort_order: 'asc' or 'desc'
    - filter_min_runs: minimum total runs to include
    - filter_min_cost / filter_max_cost: cost range filter
    """
    from app.models.run import Run, RunStatus
    from app.models.cost_record import CostRecord
    from sqlalchemy import case

    projects_data = []
    total_cost = 0.0
    total_runs = 0

    for pid in project_ids:
        # Runs count/status
        run_q = await db.execute(
            select(
                sa_func.count(Run.id).label("total"),
                sa_func.sum(
                    case((Run.status == RunStatus.COMPLETED, 1), else_=0)
                ).label("completed"),
            ).where(Run.project_id == pid)
        )
        run_row = run_q.one()

        # Cost
        cost_q = await db.execute(
            select(
                sa_func.coalesce(sa_func.sum(CostRecord.cost_usd), 0.0)
            ).where(CostRecord.project_id == pid)
        )
        cost = float(cost_q.scalar_one())

        total_r = run_row.total or 0
        completed_r = int(run_row.completed or 0)
        success_rate = round(completed_r / total_r * 100, 2) if total_r > 0 else 0.0

        entry = {
            "project_id": str(pid),
            "total_runs": total_r,
            "completed_runs": completed_r,
            "total_cost_usd": round(cost, 6),
            "success_rate": success_rate,
        }

        # Apply filters
        if filter_min_runs is not None and total_r < filter_min_runs:
            continue
        if filter_min_cost is not None and cost < filter_min_cost:
            continue
        if filter_max_cost is not None and cost > filter_max_cost:
            continue

        projects_data.append(entry)
        total_cost += cost
        total_runs += total_r

    # Apply sorting
    if sort_by and sort_by in ("total_runs", "completed_runs", "total_cost_usd", "success_rate"):
        reverse = sort_order != "asc"
        projects_data.sort(key=lambda p: p.get(sort_by, 0), reverse=reverse)

    return {
        "project_count": len(projects_data),
        "total_runs": total_runs,
        "total_cost_usd": round(total_cost, 6),
        "projects": projects_data,
    }
