"""FM-239: SLO tracking service."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func as sa_func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.platform_intelligence import SLOMetric, SLOPeriodResult, SLOTarget
from app.models.task import Task, TaskStatus
from app.models.run import Run, RunStatus
from app.models.approval_request import ApprovalRequest


async def create_slo(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    name: str,
    metric: SLOMetric,
    threshold: float,
    target_pct: float = 0.99,
    window_days: int = 30,
) -> SLOTarget:
    slo = SLOTarget(
        project_id=project_id,
        name=name,
        metric=metric,
        threshold=threshold,
        target_pct=target_pct,
        window_days=window_days,
    )
    db.add(slo)
    await db.flush()
    return slo


async def list_slos(
    db: AsyncSession,
    project_id: uuid.UUID,
) -> list[SLOTarget]:
    result = await db.execute(
        select(SLOTarget)
        .where(SLOTarget.project_id == project_id, SLOTarget.enabled.is_(True))
        .order_by(SLOTarget.created_at.desc())
    )
    return list(result.scalars().all())


async def compute_slo_attainment(
    db: AsyncSession,
    slo: SLOTarget,
) -> SLOPeriodResult:
    """Compute attainment for the SLO over its configured window."""
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(days=slo.window_days)

    total_events = 0
    compliant_events = 0
    values: list[float] = []

    if slo.metric == SLOMetric.RUN_SUCCESS_RATE:
        run_ids_q = select(Run.id).where(
            Run.project_id == slo.project_id,
            Run.created_at >= window_start,
        )
        run_ids = list((await db.execute(run_ids_q)).scalars().all())
        total_events = len(run_ids)
        if run_ids:
            ok_q = select(sa_func.count(Run.id)).where(
                Run.id.in_(run_ids),
                Run.status == RunStatus.COMPLETED,
            )
            compliant_events = int((await db.execute(ok_q)).scalar_one() or 0)
            values = [1.0] * compliant_events + [0.0] * (
                total_events - compliant_events
            )

    elif slo.metric == SLOMetric.TASK_LATENCY_MS:
        from app.models.run import Run as R

        tasks_q = (
            select(Task)
            .join(R, Task.run_id == R.id)
            .where(
                R.project_id == slo.project_id,
                Task.created_at >= window_start,
                Task.status == TaskStatus.COMPLETED,
            )
        )
        result = await db.execute(tasks_q)
        tasks = result.scalars().all()
        total_events = len(tasks)
        for t in tasks:
            if t.updated_at and t.created_at:
                latency = (t.updated_at - t.created_at).total_seconds() * 1000
                values.append(latency)
                if latency <= slo.threshold:
                    compliant_events += 1

    elif slo.metric == SLOMetric.APPROVAL_WAIT_MS:
        approvals_q = select(ApprovalRequest).where(
            ApprovalRequest.project_id == slo.project_id,
            ApprovalRequest.created_at >= window_start,
            ApprovalRequest.decided_at.isnot(None),
        )
        result = await db.execute(approvals_q)
        approvals = result.scalars().all()
        total_events = len(approvals)
        for a in approvals:
            if a.decided_at and a.created_at:
                wait = (a.decided_at - a.created_at).total_seconds() * 1000
                values.append(wait)
                if wait <= slo.threshold:
                    compliant_events += 1

    attainment = compliant_events / max(total_events, 1)
    met = attainment >= slo.target_pct

    sorted_vals = sorted(values)
    n = len(sorted_vals)

    def percentile(p: float) -> float | None:
        if not sorted_vals:
            return None
        idx = int(n * p / 100)
        return sorted_vals[min(idx, n - 1)]

    period_result = SLOPeriodResult(
        slo_id=slo.id,
        period_start=window_start,
        period_end=now,
        total_events=total_events,
        compliant_events=compliant_events,
        attainment_pct=round(attainment, 4),
        met=met,
        p50=percentile(50),
        p95=percentile(95),
        p99=percentile(99),
    )
    db.add(period_result)
    await db.flush()
    return period_result


async def get_slo_summary(
    db: AsyncSession,
    project_id: uuid.UUID,
) -> list[dict[str, Any]]:
    slos = await list_slos(db, project_id)
    summary = []
    for slo in slos:
        result_q = (
            select(SLOPeriodResult)
            .where(SLOPeriodResult.slo_id == slo.id)
            .order_by(SLOPeriodResult.computed_at.desc())
            .limit(1)
        )
        result = await db.execute(result_q)
        latest = result.scalar_one_or_none()
        summary.append(
            {
                "id": str(slo.id),
                "name": slo.name,
                "metric": slo.metric.value,
                "threshold": slo.threshold,
                "target_pct": slo.target_pct,
                "window_days": slo.window_days,
                "latest": {
                    "attainment_pct": latest.attainment_pct if latest else None,
                    "met": latest.met if latest else None,
                    "total_events": latest.total_events if latest else 0,
                    "p50": latest.p50 if latest else None,
                    "p95": latest.p95 if latest else None,
                }
                if latest
                else None,
            }
        )
    return summary
