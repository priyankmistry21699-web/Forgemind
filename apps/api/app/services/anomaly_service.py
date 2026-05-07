"""FM-240: Anomaly detection service.

Detects statistical anomalies in execution patterns by comparing
the current window against a rolling baseline.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func as sa_func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_intelligence import LLMCallLog, SecurityFinding
from app.models.platform_intelligence import AnomalyEvent, AnomalySeverity, AnomalyType
from app.models.run import Run, RunStatus
from app.models.approval_request import ApprovalRequest, ApprovalStatus


async def run_anomaly_scan(
    db: AsyncSession,
    project_id: uuid.UUID,
    *,
    window_hours: int = 24,
    baseline_days: int = 7,
) -> list[AnomalyEvent]:
    """Scan a project for anomalies. Returns newly created AnomalyEvent records."""
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(hours=window_hours)
    baseline_start = now - timedelta(days=baseline_days)

    anomalies: list[AnomalyEvent] = []

    # Get run IDs for context
    run_ids_q = select(Run.id).where(Run.project_id == project_id)
    run_ids = list((await db.execute(run_ids_q)).scalars().all())

    if not run_ids:
        return anomalies

    # --- Cost spike ---
    current_cost = await _sum_cost(db, run_ids, window_start, now)
    baseline_cost = await _sum_cost(db, run_ids, baseline_start, window_start)
    baseline_avg_cost = baseline_cost / max(baseline_days, 1)
    window_avg_cost = current_cost / max(window_hours / 24, 1)
    if baseline_avg_cost > 0 and window_avg_cost > 0:
        deviation = (window_avg_cost - baseline_avg_cost) / baseline_avg_cost
        if deviation > 2.0:
            anomalies.append(_make_anomaly(
                project_id=project_id,
                anomaly_type=AnomalyType.COST_SPIKE,
                severity=AnomalySeverity.HIGH if deviation > 5 else AnomalySeverity.MEDIUM,
                title=f"Cost spike: {deviation:.0%} above baseline",
                description=f"Daily spend ${window_avg_cost:.2f} vs baseline ${baseline_avg_cost:.2f}",
                metric_value=window_avg_cost,
                baseline_value=baseline_avg_cost,
                deviation_pct=deviation * 100,
            ))

    # --- Error rate jump ---
    current_run_q = select(sa_func.count(Run.id)).where(
        Run.id.in_(run_ids), Run.created_at >= window_start
    )
    current_failed_q = select(sa_func.count(Run.id)).where(
        Run.id.in_(run_ids),
        Run.created_at >= window_start,
        Run.status == RunStatus.FAILED,
    )
    current_total = int((await db.execute(current_run_q)).scalar_one() or 0)
    current_failed = int((await db.execute(current_failed_q)).scalar_one() or 0)
    if current_total > 2:
        error_rate = current_failed / current_total
        if error_rate > 0.5:
            anomalies.append(_make_anomaly(
                project_id=project_id,
                anomaly_type=AnomalyType.ERROR_RATE_JUMP,
                severity=AnomalySeverity.HIGH if error_rate > 0.8 else AnomalySeverity.MEDIUM,
                title=f"High run error rate: {error_rate:.0%}",
                description=f"{current_failed}/{current_total} runs failed in last {window_hours}h",
                metric_value=error_rate,
                baseline_value=None,
                deviation_pct=None,
            ))

    # --- Security finding surge ---
    recent_findings_q = select(sa_func.count(SecurityFinding.id)).where(
        SecurityFinding.project_id == project_id,
        SecurityFinding.created_at >= window_start,
    )
    recent_findings = int((await db.execute(recent_findings_q)).scalar_one() or 0)
    if recent_findings >= 10:
        anomalies.append(_make_anomaly(
            project_id=project_id,
            anomaly_type=AnomalyType.SECURITY_FINDING_SURGE,
            severity=AnomalySeverity.HIGH,
            title=f"Security finding surge: {recent_findings} in {window_hours}h",
            description="Unusually high number of security findings detected",
            metric_value=float(recent_findings),
            baseline_value=None,
            deviation_pct=None,
        ))

    # --- Approval rejection surge ---
    rejection_q = select(sa_func.count(ApprovalRequest.id)).where(
        ApprovalRequest.project_id == project_id,
        ApprovalRequest.created_at >= window_start,
        ApprovalRequest.status == ApprovalStatus.REJECTED,
    )
    rejections = int((await db.execute(rejection_q)).scalar_one() or 0)
    if rejections >= 5:
        anomalies.append(_make_anomaly(
            project_id=project_id,
            anomaly_type=AnomalyType.APPROVAL_REJECTION_SURGE,
            severity=AnomalySeverity.MEDIUM,
            title=f"Approval rejection surge: {rejections} in {window_hours}h",
            description="Multiple approvals have been rejected recently",
            metric_value=float(rejections),
            baseline_value=None,
            deviation_pct=None,
        ))

    for a in anomalies:
        db.add(a)
    if anomalies:
        await db.flush()
    return anomalies


async def list_anomalies(
    db: AsyncSession,
    project_id: uuid.UUID,
    *,
    resolved: bool | None = None,
    limit: int = 50,
) -> list[AnomalyEvent]:
    q = (
        select(AnomalyEvent)
        .where(AnomalyEvent.project_id == project_id)
        .order_by(AnomalyEvent.detected_at.desc())
        .limit(limit)
    )
    if resolved is not None:
        q = q.where(AnomalyEvent.resolved == resolved)
    result = await db.execute(q)
    return list(result.scalars().all())


async def _sum_cost(
    db: AsyncSession,
    run_ids: list,
    start: datetime,
    end: datetime,
) -> float:
    if not run_ids:
        return 0.0
    result = await db.execute(
        select(sa_func.sum(LLMCallLog.cost_usd)).where(
            LLMCallLog.run_id.in_(run_ids),
            LLMCallLog.created_at >= start,
            LLMCallLog.created_at <= end,
        )
    )
    return float(result.scalar_one() or 0.0)


def _make_anomaly(
    *,
    project_id: uuid.UUID,
    anomaly_type: AnomalyType,
    severity: AnomalySeverity,
    title: str,
    description: str,
    metric_value: float | None,
    baseline_value: float | None,
    deviation_pct: float | None,
) -> AnomalyEvent:
    return AnomalyEvent(
        project_id=project_id,
        anomaly_type=anomaly_type,
        severity=severity,
        title=title,
        description=description,
        metric_value=metric_value,
        baseline_value=baseline_value,
        deviation_pct=deviation_pct,
    )
