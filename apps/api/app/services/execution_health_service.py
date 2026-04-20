"""Execution Metrics & Health Scoring services — FM-191/192.

FM-191: Record and aggregate timing metrics for runs/tasks.
FM-192: Project health scoring with weighted dimension scoring.
"""

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select, func as sa_func, case as sa_case
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analytics_metrics import (
    ExecutionMetric,
    ExecutionMetricType,
    HealthSnapshot,
    HealthGrade,
)

logger = logging.getLogger(__name__)


# ── FM-191: Execution Metrics ────────────────────────────────────


async def record_execution_metric(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    metric_type: ExecutionMetricType,
    value_ms: int,
    run_id: uuid.UUID | None = None,
    task_id: uuid.UUID | None = None,
) -> ExecutionMetric:
    """Record a single execution timing metric."""
    m = ExecutionMetric(
        project_id=project_id,
        run_id=run_id,
        task_id=task_id,
        metric_type=metric_type,
        value_ms=value_ms,
    )
    db.add(m)
    await db.flush()
    return m


async def get_execution_metrics(
    db: AsyncSession,
    project_id: uuid.UUID,
    *,
    metric_type: ExecutionMetricType | None = None,
    run_id: uuid.UUID | None = None,
    since_days: int | None = None,
    limit: int = 100,
    offset: int = 0,
) -> tuple[list[ExecutionMetric], int]:
    """List execution metrics with optional filters.

    FM-191: since_days provides time-window preset filtering (e.g. 1, 7, 30, 90).
    """
    query = select(ExecutionMetric).where(ExecutionMetric.project_id == project_id)
    if metric_type:
        query = query.where(ExecutionMetric.metric_type == metric_type)
    if run_id:
        query = query.where(ExecutionMetric.run_id == run_id)
    if since_days is not None:
        cutoff = datetime.now(timezone.utc) - timedelta(days=since_days)
        query = query.where(ExecutionMetric.recorded_at >= cutoff)

    total = (
        await db.execute(select(sa_func.count()).select_from(query.subquery()))
    ).scalar_one()

    result = await db.execute(
        query.order_by(ExecutionMetric.recorded_at.desc()).offset(offset).limit(limit)
    )
    return list(result.scalars().all()), total


async def get_execution_metrics_summary(
    db: AsyncSession,
    project_id: uuid.UUID,
) -> dict[str, Any]:
    """Aggregate execution metric stats by type."""
    result = await db.execute(
        select(
            ExecutionMetric.metric_type,
            sa_func.count(ExecutionMetric.id).label("count"),
            sa_func.avg(ExecutionMetric.value_ms).label("avg_ms"),
            sa_func.min(ExecutionMetric.value_ms).label("min_ms"),
            sa_func.max(ExecutionMetric.value_ms).label("max_ms"),
            sa_func.sum(ExecutionMetric.value_ms).label("total_ms"),
        )
        .where(ExecutionMetric.project_id == project_id)
        .group_by(ExecutionMetric.metric_type)
    )
    rows = result.all()
    return {
        "project_id": str(project_id),
        "metrics": [
            {
                "metric_type": row.metric_type.value
                if hasattr(row.metric_type, "value")
                else str(row.metric_type),
                "count": row.count,
                "avg_ms": round(float(row.avg_ms or 0), 2),
                "min_ms": int(row.min_ms or 0),
                "max_ms": int(row.max_ms or 0),
                "total_ms": int(row.total_ms or 0),
            }
            for row in rows
        ],
    }


# Status-transition mapping for auto-capture (FM-191).
_STATUS_METRIC_MAP: dict[tuple[str, str], ExecutionMetricType] = {
    ("queued", "in_progress"): ExecutionMetricType.QUEUE_TIME,
    ("in_progress", "review"): ExecutionMetricType.EXECUTION_TIME,
    ("review", "approved"): ExecutionMetricType.REVIEW_TIME,
    ("review", "completed"): ExecutionMetricType.REVIEW_TIME,
    ("planning", "in_progress"): ExecutionMetricType.PLANNING_TIME,
    ("queued", "completed"): ExecutionMetricType.TOTAL_CYCLE_TIME,
}


async def auto_record_from_status_transition(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    run_id: uuid.UUID | None = None,
    task_id: uuid.UUID | None = None,
    old_status: str,
    new_status: str,
    duration_ms: int,
) -> ExecutionMetric | None:
    """FM-191: Auto-capture timing metric from a status transition.

    Called by the run/task lifecycle when status changes. Returns the
    recorded metric or None if the transition has no mapping.
    """
    metric_type = _STATUS_METRIC_MAP.get((old_status, new_status))
    if metric_type is None:
        return None
    return await record_execution_metric(
        db,
        project_id=project_id,
        metric_type=metric_type,
        value_ms=duration_ms,
        run_id=run_id,
        task_id=task_id,
    )


# ── FM-192: Health Scoring ───────────────────────────────────────

HEALTH_WEIGHTS: dict[str, float] = {
    "success_rate": 0.25,
    "velocity": 0.20,
    "cost_efficiency": 0.15,
    "quality": 0.20,
    "coverage": 0.10,
    "complexity": 0.10,
}


def _compute_grade(score: float) -> HealthGrade:
    """Map a 0-100 score to a letter grade.

    Thresholds per roadmap: A ≥ 90, B ≥ 75, C ≥ 60, D ≥ 45, F < 45.
    """
    if score >= 90:
        return HealthGrade.A
    if score >= 75:
        return HealthGrade.B
    if score >= 60:
        return HealthGrade.C
    if score >= 45:
        return HealthGrade.D
    return HealthGrade.F


async def auto_compute_health_dimensions(
    db: AsyncSession,
    project_id: uuid.UUID,
    *,
    days: int = 30,
) -> dict[str, float]:
    """Auto-compute all health dimension scores from real project data.

    Dimensions:
    - success_rate: % of completed runs out of total finished runs (0-100)
    - velocity: normalized runs/day score (higher = better, capped at 100)
    - cost_efficiency: inverse of avg cost per run (lower cost = higher score)
    - quality: from latest QualitySnapshot test_pass_rate (0-100)
    - coverage: from latest QualitySnapshot review_coverage (0-100)
    - complexity: inverse of avg complexity (lower complexity = higher score)
    """
    from app.models.run import Run, RunStatus
    from app.models.analytics_metrics import QualitySnapshot
    from app.models.code_intelligence import ComplexityMetric, MetricType
    from app.models.cost_record import CostRecord

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    scores: dict[str, float] = {}

    # ── success_rate: completed / (completed + failed) ──
    run_q = await db.execute(
        select(
            sa_func.count(Run.id).label("total"),
            sa_func.sum(sa_case((Run.status == RunStatus.COMPLETED, 1), else_=0)).label(
                "completed"
            ),
            sa_func.sum(sa_case((Run.status == RunStatus.FAILED, 1), else_=0)).label(
                "failed"
            ),
        ).where(
            Run.project_id == project_id,
            Run.created_at >= cutoff,
        )
    )
    run_row = run_q.one()
    finished = (run_row.completed or 0) + (run_row.failed or 0)
    scores["success_rate"] = round(
        ((run_row.completed or 0) / finished * 100) if finished > 0 else 50.0, 2
    )

    # ── velocity: runs per day normalized (1 run/day = 80, 3+/day = 100) ──
    runs_per_day = (run_row.completed or 0) / max(days, 1)
    scores["velocity"] = round(min(runs_per_day * 33.33, 100.0), 2)

    # ── cost_efficiency: lower avg cost = higher score ──
    cost_q = await db.execute(
        select(
            sa_func.avg(CostRecord.cost_usd).label("avg_cost"),
        ).where(
            CostRecord.project_id == project_id,
            CostRecord.created_at >= cutoff,
        )
    )
    avg_cost = float(cost_q.scalar_one() or 0)
    # Scale: $0 = 100, $1 = 50, $5+ = 10
    if avg_cost <= 0:
        scores["cost_efficiency"] = 80.0  # No costs recorded = decent
    else:
        scores["cost_efficiency"] = round(max(100 - avg_cost * 50, 10.0), 2)

    # ── quality: from latest QualitySnapshot ──
    quality_q = await db.execute(
        select(QualitySnapshot)
        .where(QualitySnapshot.project_id == project_id)
        .order_by(QualitySnapshot.snapshot_date.desc())
        .limit(1)
    )
    quality_snap = quality_q.scalar_one_or_none()
    if quality_snap:
        scores["quality"] = round(quality_snap.test_pass_rate * 100, 2)
        scores["coverage"] = round(quality_snap.review_coverage * 100, 2)
    else:
        scores["quality"] = 50.0
        scores["coverage"] = 50.0

    # ── complexity: inverse of avg cyclomatic (lower = better) ──
    cx_q = await db.execute(
        select(sa_func.avg(ComplexityMetric.value)).where(
            ComplexityMetric.project_id == project_id,
            ComplexityMetric.metric_type == MetricType.CYCLOMATIC,
        )
    )
    avg_cx = float(cx_q.scalar_one() or 0)
    # Scale: complexity 1 = 100, 5 = 70, 15+ = 20
    if avg_cx <= 0:
        scores["complexity"] = 70.0
    else:
        scores["complexity"] = round(max(100 - avg_cx * 5, 20.0), 2)

    return scores


async def compute_health_snapshot(
    db: AsyncSession,
    project_id: uuid.UUID,
    *,
    dimension_scores: dict[str, float] | None = None,
) -> HealthSnapshot:
    """Compute and persist a project health snapshot.

    If dimension_scores not provided, auto-computes from real project data.
    """
    if dimension_scores is None:
        dimension_scores = await auto_compute_health_dimensions(db, project_id)

    composite = 0.0
    for dim, weight in HEALTH_WEIGHTS.items():
        score = dimension_scores.get(dim, 50.0)
        composite += score * weight

    composite = round(composite, 2)
    grade = _compute_grade(composite)

    snap = HealthSnapshot(
        project_id=project_id,
        dimension_scores=dimension_scores,
        composite_score=composite,
        grade=grade,
    )
    db.add(snap)
    await db.flush()
    return snap


async def get_latest_health(
    db: AsyncSession,
    project_id: uuid.UUID,
) -> HealthSnapshot | None:
    """Get the most recent health snapshot."""
    result = await db.execute(
        select(HealthSnapshot)
        .where(HealthSnapshot.project_id == project_id)
        .order_by(HealthSnapshot.snapshot_date.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_health_trend(
    db: AsyncSession,
    project_id: uuid.UUID,
    *,
    limit: int = 30,
) -> list[dict[str, Any]]:
    """Get recent health snapshots for trend visualization."""
    result = await db.execute(
        select(HealthSnapshot)
        .where(HealthSnapshot.project_id == project_id)
        .order_by(HealthSnapshot.snapshot_date.desc())
        .limit(limit)
    )
    snaps = list(result.scalars().all())
    return [
        {
            "id": str(s.id),
            "composite_score": s.composite_score,
            "grade": s.grade.value if hasattr(s.grade, "value") else str(s.grade),
            "dimension_scores": s.dimension_scores,
            "snapshot_date": s.snapshot_date.isoformat() if s.snapshot_date else None,
        }
        for s in snaps
    ]


# ── FM-193: Budget enforcement ────────────────────────────────────────────


async def check_budget(
    db: AsyncSession,
    project_id: uuid.UUID,
) -> dict[str, Any]:
    """Check project spend against BudgetConfig and enforce thresholds.

    Returns dict with: spent_usd, budget_usd, pct_used, action, exceeded.
    Raises HTTPException(403) when action is BLOCK and threshold exceeded.
    """
    from app.models.analytics_metrics import BudgetConfig, BudgetAction
    from app.models.cost_record import CostRecord

    # Fetch budget config
    cfg_q = await db.execute(
        select(BudgetConfig).where(BudgetConfig.project_id == project_id)
    )
    config = cfg_q.scalar_one_or_none()

    if config is None:
        return {
            "spent_usd": 0.0,
            "budget_usd": None,
            "pct_used": 0.0,
            "action": "none",
            "exceeded": False,
        }

    # Sum current month's spend
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    spend_q = await db.execute(
        select(sa_func.coalesce(sa_func.sum(CostRecord.cost_usd), 0.0)).where(
            CostRecord.project_id == project_id,
            CostRecord.created_at >= month_start,
        )
    )
    spent = float(spend_q.scalar_one())

    budget = float(config.monthly_budget_usd)
    pct_used = round((spent / budget * 100) if budget > 0 else 0, 2)
    threshold = float(config.warn_threshold_pct)
    exceeded = pct_used >= threshold
    action_str = (
        config.action_on_exceed.value
        if hasattr(config.action_on_exceed, "value")
        else str(config.action_on_exceed)
    )

    result = {
        "spent_usd": round(spent, 4),
        "budget_usd": budget,
        "pct_used": pct_used,
        "action": action_str if exceeded else "none",
        "exceeded": exceeded,
    }

    if exceeded and config.action_on_exceed == BudgetAction.BLOCK:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=403,
            detail=f"Budget exceeded: {pct_used:.1f}% of ${budget:.2f} used. Action: BLOCK",
        )

    if exceeded:
        logger.warning(
            "Budget warning for project %s: %.1f%% used ($%.4f / $%.2f). Action: %s",
            project_id,
            pct_used,
            spent,
            budget,
            action_str,
        )

    return result
