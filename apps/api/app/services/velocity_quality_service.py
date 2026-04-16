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


# ── FM-196: Portfolio Analytics ──────────────────────────────────


async def get_portfolio_summary(
    db: AsyncSession,
    project_ids: list[uuid.UUID],
) -> dict[str, Any]:
    """Aggregate analytics across multiple projects."""
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

        projects_data.append({
            "project_id": str(pid),
            "total_runs": run_row.total or 0,
            "completed_runs": int(run_row.completed or 0),
            "total_cost_usd": round(cost, 6),
        })
        total_cost += cost
        total_runs += run_row.total or 0

    return {
        "project_count": len(project_ids),
        "total_runs": total_runs,
        "total_cost_usd": round(total_cost, 6),
        "projects": projects_data,
    }
