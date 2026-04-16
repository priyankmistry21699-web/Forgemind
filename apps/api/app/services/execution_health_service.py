"""Execution Metrics & Health Scoring services — FM-191/192.

FM-191: Record and aggregate timing metrics for runs/tasks.
FM-192: Project health scoring with weighted dimension scoring.
"""

import logging
import uuid
from typing import Any

from sqlalchemy import select, func as sa_func
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
    limit: int = 100,
    offset: int = 0,
) -> tuple[list[ExecutionMetric], int]:
    """List execution metrics with optional filters."""
    query = select(ExecutionMetric).where(
        ExecutionMetric.project_id == project_id
    )
    if metric_type:
        query = query.where(ExecutionMetric.metric_type == metric_type)
    if run_id:
        query = query.where(ExecutionMetric.run_id == run_id)

    total = (
        await db.execute(select(sa_func.count()).select_from(query.subquery()))
    ).scalar_one()

    result = await db.execute(
        query.order_by(ExecutionMetric.recorded_at.desc())
        .offset(offset)
        .limit(limit)
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
                "metric_type": row.metric_type.value if hasattr(row.metric_type, 'value') else str(row.metric_type),
                "count": row.count,
                "avg_ms": round(float(row.avg_ms or 0), 2),
                "min_ms": int(row.min_ms or 0),
                "max_ms": int(row.max_ms or 0),
                "total_ms": int(row.total_ms or 0),
            }
            for row in rows
        ],
    }


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
    """Map a 0-100 score to a letter grade."""
    if score >= 90:
        return HealthGrade.A
    if score >= 80:
        return HealthGrade.B
    if score >= 70:
        return HealthGrade.C
    if score >= 60:
        return HealthGrade.D
    return HealthGrade.F


async def compute_health_snapshot(
    db: AsyncSession,
    project_id: uuid.UUID,
    *,
    dimension_scores: dict[str, float] | None = None,
) -> HealthSnapshot:
    """Compute and persist a project health snapshot.

    If dimension_scores not provided, defaults to neutral (50) for each weight.
    """
    if dimension_scores is None:
        dimension_scores = {k: 50.0 for k in HEALTH_WEIGHTS}

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
            "grade": s.grade.value if hasattr(s.grade, 'value') else str(s.grade),
            "dimension_scores": s.dimension_scores,
            "snapshot_date": s.snapshot_date.isoformat() if s.snapshot_date else None,
        }
        for s in snaps
    ]
