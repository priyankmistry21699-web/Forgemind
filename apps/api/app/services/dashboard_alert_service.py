"""Dashboard, Alert & Reporting services — FM-197/198/199.

FM-197: Custom dashboard CRUD and layout management.
FM-198: Scheduled reports and threshold-based metric alerts.
FM-199: Executive summary generation.
"""

import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analytics_metrics import (
    Dashboard,
    DashboardVisibility,
    ScheduledReport,
    MetricAlert,
    AlertConditionOp,
    AlertTriggerHistory,
)

logger = logging.getLogger(__name__)


# ── FM-197: Dashboard CRUD ───────────────────────────────────────


async def create_dashboard(
    db: AsyncSession,
    *,
    creator_id: uuid.UUID,
    name: str,
    description: str | None = None,
    layout_json: dict | None = None,
    visibility: DashboardVisibility = DashboardVisibility.PRIVATE,
    org_id: uuid.UUID | None = None,
) -> Dashboard:
    """Create a new custom dashboard."""
    dash = Dashboard(
        creator_id=creator_id,
        name=name,
        description=description,
        layout_json=layout_json or {},
        visibility=visibility,
        org_id=org_id,
    )
    db.add(dash)
    await db.flush()
    return dash


async def get_dashboard(
    db: AsyncSession,
    dashboard_id: uuid.UUID,
) -> Dashboard:
    """Get a dashboard by ID."""
    result = await db.execute(
        select(Dashboard).where(Dashboard.id == dashboard_id)
    )
    dash = result.scalar_one_or_none()
    if dash is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dashboard not found",
        )
    return dash


async def list_dashboards(
    db: AsyncSession,
    creator_id: uuid.UUID,
    *,
    include_team: bool = True,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[Dashboard], int]:
    """List dashboards for a user (own + team-visible)."""
    conditions = [Dashboard.creator_id == creator_id]
    if include_team:
        conditions = [
            (Dashboard.creator_id == creator_id)
            | (Dashboard.visibility != DashboardVisibility.PRIVATE)
        ]

    query = select(Dashboard).where(*conditions)
    total = (
        await db.execute(select(sa_func.count()).select_from(query.subquery()))
    ).scalar_one()

    result = await db.execute(
        query.order_by(Dashboard.updated_at.desc()).offset(offset).limit(limit)
    )
    return list(result.scalars().all()), total


async def update_dashboard(
    db: AsyncSession,
    dashboard_id: uuid.UUID,
    **fields: Any,
) -> Dashboard:
    """Update dashboard fields."""
    dash = await get_dashboard(db, dashboard_id)
    for key, value in fields.items():
        if hasattr(dash, key) and value is not None:
            setattr(dash, key, value)
    await db.flush()
    return dash


async def delete_dashboard(
    db: AsyncSession,
    dashboard_id: uuid.UUID,
) -> None:
    """Delete a dashboard."""
    dash = await get_dashboard(db, dashboard_id)
    await db.delete(dash)
    await db.flush()


# ── FM-198: Scheduled Reports ────────────────────────────────────


async def create_scheduled_report(
    db: AsyncSession,
    *,
    name: str,
    metrics: list[str],
    schedule_cron: str,
    recipients: list[str] | None = None,
    org_id: uuid.UUID | None = None,
) -> ScheduledReport:
    """Create an automated report schedule."""
    report = ScheduledReport(
        name=name,
        metrics=metrics,
        schedule_cron=schedule_cron,
        recipients=recipients or [],
        org_id=org_id,
    )
    db.add(report)
    await db.flush()
    return report


async def list_scheduled_reports(
    db: AsyncSession,
    *,
    org_id: uuid.UUID | None = None,
    active_only: bool = True,
) -> list[ScheduledReport]:
    """List scheduled reports."""
    query = select(ScheduledReport)
    if org_id:
        query = query.where(ScheduledReport.org_id == org_id)
    if active_only:
        query = query.where(ScheduledReport.active.is_(True))
    result = await db.execute(query.order_by(ScheduledReport.created_at.desc()))
    return list(result.scalars().all())


async def update_scheduled_report(
    db: AsyncSession,
    report_id: uuid.UUID,
    **fields: Any,
) -> ScheduledReport:
    """Update a scheduled report."""
    result = await db.execute(
        select(ScheduledReport).where(ScheduledReport.id == report_id)
    )
    report = result.scalar_one_or_none()
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scheduled report not found",
        )
    for key, value in fields.items():
        if hasattr(report, key) and value is not None:
            setattr(report, key, value)
    await db.flush()
    return report


# ── FM-198: Metric Alerts ────────────────────────────────────────


async def create_metric_alert(
    db: AsyncSession,
    *,
    name: str,
    metric_type: str,
    condition_op: AlertConditionOp,
    threshold: float,
    recipients: list[str] | None = None,
    cooldown_minutes: int = 60,
    org_id: uuid.UUID | None = None,
    project_id: uuid.UUID | None = None,
) -> MetricAlert:
    """Create a threshold-based metric alert rule."""
    alert = MetricAlert(
        name=name,
        metric_type=metric_type,
        condition_op=condition_op,
        threshold=threshold,
        recipients=recipients or [],
        cooldown_minutes=cooldown_minutes,
        org_id=org_id,
        project_id=project_id,
    )
    db.add(alert)
    await db.flush()
    return alert


async def list_metric_alerts(
    db: AsyncSession,
    *,
    org_id: uuid.UUID | None = None,
    project_id: uuid.UUID | None = None,
    active_only: bool = True,
) -> list[MetricAlert]:
    """List metric alert rules."""
    query = select(MetricAlert)
    if org_id:
        query = query.where(MetricAlert.org_id == org_id)
    if project_id:
        query = query.where(MetricAlert.project_id == project_id)
    if active_only:
        query = query.where(MetricAlert.active.is_(True))
    result = await db.execute(query.order_by(MetricAlert.created_at.desc()))
    return list(result.scalars().all())


async def evaluate_alert(
    alert: MetricAlert,
    current_value: float,
) -> bool:
    """Check if a metric value triggers the alert condition.

    Returns False if the alert is in cooldown (last_triggered_at + cooldown_minutes > now).
    """
    # Cooldown check
    if alert.last_triggered_at is not None:
        cooldown_end = alert.last_triggered_at + timedelta(minutes=alert.cooldown_minutes)
        now = datetime.now(timezone.utc)
        last = alert.last_triggered_at
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        cooldown_end = last + timedelta(minutes=alert.cooldown_minutes)
        if now < cooldown_end:
            return False

    ops = {
        AlertConditionOp.GT: lambda v, t: v > t,
        AlertConditionOp.GTE: lambda v, t: v >= t,
        AlertConditionOp.LT: lambda v, t: v < t,
        AlertConditionOp.LTE: lambda v, t: v <= t,
        AlertConditionOp.EQ: lambda v, t: v == t,
    }
    op_fn = ops.get(alert.condition_op)
    if op_fn is None:
        return False
    return op_fn(current_value, alert.threshold)


async def trigger_alert(
    db: AsyncSession,
    alert_id: uuid.UUID,
    *,
    current_value: float | None = None,
) -> MetricAlert:
    """Mark an alert as triggered, update last_triggered_at, and log to history."""
    result = await db.execute(
        select(MetricAlert).where(MetricAlert.id == alert_id)
    )
    alert = result.scalar_one_or_none()
    if alert is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found",
        )
    now = datetime.now(timezone.utc)
    alert.last_triggered_at = now

    # Log trigger event to history
    if current_value is not None:
        history_entry = AlertTriggerHistory(
            alert_id=alert_id,
            triggered_at=now,
            current_value=current_value,
            threshold=alert.threshold,
            condition_op=alert.condition_op.value if hasattr(alert.condition_op, 'value') else str(alert.condition_op),
        )
        db.add(history_entry)

    await db.flush()
    return alert


async def get_alert_history(
    db: AsyncSession,
    alert_id: uuid.UUID,
    *,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[AlertTriggerHistory], int]:
    """Get trigger history for a specific alert."""
    query = select(AlertTriggerHistory).where(
        AlertTriggerHistory.alert_id == alert_id
    )
    total = (
        await db.execute(select(sa_func.count()).select_from(query.subquery()))
    ).scalar_one()
    result = await db.execute(
        query.order_by(AlertTriggerHistory.triggered_at.desc())
        .offset(offset).limit(limit)
    )
    return list(result.scalars().all()), total


# ── FM-199: Executive Summary ────────────────────────────────────


async def generate_executive_summary(
    db: AsyncSession,
    project_id: uuid.UUID,
) -> dict[str, Any]:
    """Generate a project executive summary combining all analytics."""
    from app.services import execution_health_service
    from app.services import velocity_quality_service

    # Health
    health = await execution_health_service.get_latest_health(db, project_id)
    health_data = None
    if health:
        health_data = {
            "grade": health.grade.value if hasattr(health.grade, 'value') else str(health.grade),
            "composite_score": health.composite_score,
            "dimension_scores": health.dimension_scores,
        }

    # Velocity
    velocity = await velocity_quality_service.compute_velocity(db, project_id)

    # Quality
    quality = await velocity_quality_service.get_latest_quality(db, project_id)
    quality_data = None
    if quality:
        quality_data = {
            "test_pass_rate": quality.test_pass_rate,
            "defect_density": quality.defect_density,
            "rollback_rate": quality.rollback_rate,
            "review_coverage": quality.review_coverage,
        }

    # Execution metrics summary
    exec_summary = await execution_health_service.get_execution_metrics_summary(
        db, project_id
    )

    return {
        "project_id": str(project_id),
        "health": health_data,
        "velocity": velocity,
        "quality": quality_data,
        "execution_metrics": exec_summary.get("metrics", []),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


# ── FM-199: Executive Summary Artifact Storage ───────────────────

# In-memory store for versioned summaries (production: persist to DB table)
_summary_artifacts: dict[str, list[dict[str, Any]]] = {}


async def save_executive_summary(
    db: AsyncSession,
    project_id: uuid.UUID,
) -> dict[str, Any]:
    """Generate and store a versioned executive summary artifact."""
    summary = await generate_executive_summary(db, project_id)
    key = str(project_id)
    if key not in _summary_artifacts:
        _summary_artifacts[key] = []
    version = len(_summary_artifacts[key]) + 1
    artifact = {
        "version": version,
        "summary": summary,
        "stored_at": datetime.now(timezone.utc).isoformat(),
    }
    _summary_artifacts[key].append(artifact)
    return artifact


def get_summary_artifacts(project_id: uuid.UUID) -> list[dict[str, Any]]:
    """Retrieve stored executive summary artifacts for a project."""
    return _summary_artifacts.get(str(project_id), [])


# ── FM-197: Widget Data Resolution ───────────────────────────────

WIDGET_DATA_SOURCES = {
    "health_score": "execution_health_service.get_latest_health",
    "velocity": "velocity_quality_service.compute_velocity",
    "quality": "velocity_quality_service.get_latest_quality",
    "execution_metrics": "execution_health_service.get_execution_metrics_summary",
    "debt_summary": "pattern_debt_service.get_debt_summary",
    "complexity_summary": "flakiness_complexity_service.get_complexity_summary",
    "flakiness_summary": "flakiness_complexity_service.get_test_flakiness_summary",
}


async def resolve_widget_data(
    db: AsyncSession,
    project_id: uuid.UUID,
    widget_type: str,
) -> dict[str, Any]:
    """FM-197: Resolve a widget data source and return real metric data.

    widget_type must be one of the known WIDGET_DATA_SOURCES keys.
    """
    if widget_type not in WIDGET_DATA_SOURCES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown widget type: {widget_type}. "
                   f"Valid: {', '.join(sorted(WIDGET_DATA_SOURCES))}",
        )

    from app.services import execution_health_service as ehs
    from app.services import velocity_quality_service as vqs
    from app.services import pattern_debt_service as pds
    from app.services import flakiness_complexity_service as fcs

    resolvers = {
        "health_score": lambda: ehs.get_latest_health(db, project_id),
        "velocity": lambda: vqs.compute_velocity(db, project_id),
        "quality": lambda: vqs.get_latest_quality(db, project_id),
        "execution_metrics": lambda: ehs.get_execution_metrics_summary(db, project_id),
        "debt_summary": lambda: pds.get_debt_summary(db, project_id),
        "complexity_summary": lambda: fcs.get_complexity_summary(db, project_id),
        "flakiness_summary": lambda: fcs.get_test_flakiness_summary(db, project_id),
    }

    result = await resolvers[widget_type]()

    # Normalize ORM objects to dicts
    if result is None:
        return {"widget_type": widget_type, "data": None}
    if hasattr(result, "__dict__"):
        data = {
            k: v for k, v in result.__dict__.items()
            if not k.startswith("_")
        }
        # Serialize UUIDs and enums
        for k, v in data.items():
            if hasattr(v, "value"):
                data[k] = v.value
            elif isinstance(v, uuid.UUID):
                data[k] = str(v)
    else:
        data = result

    return {"widget_type": widget_type, "project_id": str(project_id), "data": data}
