"""FM-233: Agent performance snapshot service."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import func as sa_func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.platform_intelligence import AgentPerformanceSnapshot
from app.models.agent_intelligence import LLMCallLog
from app.models.task import Task, TaskStatus


async def compute_snapshot(
    db: AsyncSession,
    *,
    agent_slug: str,
    project_id: uuid.UUID | None = None,
    period_date: date | None = None,
) -> AgentPerformanceSnapshot:
    """Compute and upsert a daily performance snapshot for an agent."""
    target_date = period_date or date.today()
    period_str = target_date.isoformat()

    # Task counts
    q = select(
        sa_func.count(Task.id).label("total"),
        sa_func.sum(
            sa_func.cast(Task.status == TaskStatus.COMPLETED, "integer")
        ).label("completed"),
        sa_func.sum(
            sa_func.cast(Task.status == TaskStatus.FAILED, "integer")
        ).label("failed"),
    ).where(Task.assigned_agent_slug == agent_slug)
    if project_id:
        from app.models.run import Run
        q = q.join(Run, Task.run_id == Run.id).where(Run.project_id == project_id)

    result = await db.execute(q)
    row = result.one()
    completed = int(row.completed or 0)
    failed = int(row.failed or 0)
    success_rate = completed / max(completed + failed, 1)

    # Cost from LLM call logs
    cost_q = select(sa_func.sum(LLMCallLog.cost_usd)).where(
        LLMCallLog.task_type == agent_slug
    )
    cost_result = await db.execute(cost_q)
    total_cost = float(cost_result.scalar_one() or 0.0)

    # Upsert snapshot
    existing = await db.execute(
        select(AgentPerformanceSnapshot).where(
            AgentPerformanceSnapshot.agent_slug == agent_slug,
            AgentPerformanceSnapshot.period_date == period_str,
            AgentPerformanceSnapshot.project_id == project_id,
        )
    )
    snap = existing.scalar_one_or_none()
    if snap is None:
        snap = AgentPerformanceSnapshot(
            agent_slug=agent_slug,
            project_id=project_id,
            period_date=period_str,
        )
        db.add(snap)

    snap.tasks_completed = completed
    snap.tasks_failed = failed
    snap.success_rate = success_rate
    snap.total_cost_usd = total_cost
    await db.flush()
    return snap


async def get_agent_performance(
    db: AsyncSession,
    agent_slug: str,
    *,
    project_id: uuid.UUID | None = None,
    days: int = 30,
) -> list[dict[str, Any]]:
    q = (
        select(AgentPerformanceSnapshot)
        .where(AgentPerformanceSnapshot.agent_slug == agent_slug)
        .order_by(AgentPerformanceSnapshot.period_date.desc())
        .limit(days)
    )
    if project_id:
        q = q.where(AgentPerformanceSnapshot.project_id == project_id)
    result = await db.execute(q)
    snaps = result.scalars().all()
    return [
        {
            "period_date": s.period_date,
            "tasks_completed": s.tasks_completed,
            "tasks_failed": s.tasks_failed,
            "success_rate": s.success_rate,
            "total_cost_usd": s.total_cost_usd,
            "avg_latency_ms": s.avg_latency_ms,
            "p95_latency_ms": s.p95_latency_ms,
        }
        for s in snaps
    ]
