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
    ExecutiveSummaryArtifact,
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


async def execute_scheduled_report(
    db: AsyncSession,
    report_id: uuid.UUID,
    *,
    project_id: uuid.UUID,
) -> dict[str, Any]:
    """FM-198: Execute a scheduled report — generate current metric values.

    Collects the metric values specified in the report's ``metrics`` list
    for the given project and returns a snapshot result.
    """
    result = await db.execute(
        select(ScheduledReport).where(ScheduledReport.id == report_id)
    )
    report = result.scalar_one_or_none()
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scheduled report not found",
        )

    from app.services import execution_health_service as ehs
    from app.services import velocity_quality_service as vqs

    resolvers: dict[str, Any] = {
        "health": lambda: ehs.get_latest_health(db, project_id),
        "velocity": lambda: vqs.compute_velocity(db, project_id),
        "quality": lambda: vqs.get_latest_quality(db, project_id),
        "execution_metrics": lambda: ehs.get_execution_metrics_summary(db, project_id),
    }

    collected: dict[str, Any] = {}
    for metric_name in report.metrics:
        resolver = resolvers.get(metric_name)
        if resolver:
            raw = await resolver()
            if raw is None:
                collected[metric_name] = None
            elif hasattr(raw, "__dict__"):
                collected[metric_name] = {
                    k: (v.value if hasattr(v, "value") else str(v) if isinstance(v, uuid.UUID) else v)
                    for k, v in raw.__dict__.items()
                    if not k.startswith("_")
                }
            else:
                collected[metric_name] = raw
        else:
            collected[metric_name] = None

    # Update last_generated_at
    report.last_generated_at = datetime.now(timezone.utc)
    await db.flush()

    return {
        "report_id": str(report_id),
        "report_name": report.name,
        "project_id": str(project_id),
        "metrics_collected": collected,
        "generated_at": report.last_generated_at.isoformat(),
    }


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
        "narrative": _generate_narrative(health_data, velocity, quality_data),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def _generate_narrative(
    health: dict | None,
    velocity: dict | None,
    quality: dict | None,
) -> str:
    """FM-199: Produce a non-technical, human-readable summary paragraph.

    Uses simple template sentences so stakeholders without engineering
    context can understand the project status at a glance.
    """
    parts: list[str] = []

    # Health narrative
    if health:
        grade = health.get("grade", "N/A")
        score = health.get("composite_score")
        if score is not None:
            parts.append(
                f"Overall project health is rated {grade} "
                f"with a composite score of {score:.1f} out of 100."
            )
        else:
            parts.append(f"Overall project health is rated {grade}.")

        # Dimension color commentary
        dims = health.get("dimension_scores") or {}
        weak = [k for k, v in dims.items() if isinstance(v, (int, float)) and v < 60]
        strong = [k for k, v in dims.items() if isinstance(v, (int, float)) and v >= 85]
        if strong:
            parts.append(
                f"Strong areas include {', '.join(strong)}."
            )
        if weak:
            parts.append(
                f"Areas needing attention: {', '.join(weak)}."
            )
    else:
        parts.append("No health data is available yet for this project.")

    # Velocity narrative
    if velocity:
        runs = velocity.get("completed_runs", 0)
        rpd = velocity.get("runs_per_day")
        if rpd is not None:
            parts.append(
                f"The team has completed {runs} runs "
                f"at a pace of {rpd:.1f} runs per day."
            )
        elif runs:
            parts.append(f"The team has completed {runs} runs so far.")

    # Quality narrative
    if quality:
        pass_rate = quality.get("test_pass_rate")
        if pass_rate is not None:
            pct = pass_rate * 100 if pass_rate <= 1.0 else pass_rate
            if pct >= 95:
                parts.append(f"Test quality is excellent with a {pct:.1f}% pass rate.")
            elif pct >= 80:
                parts.append(f"Test quality is good at {pct:.1f}% pass rate, with room for improvement.")
            else:
                parts.append(f"Test pass rate is {pct:.1f}% — this needs immediate attention.")

        defect = quality.get("defect_density")
        if defect is not None and defect > 0.05:
            parts.append(
                f"Defect density is elevated at {defect:.2f}; "
                "consider prioritizing bug-fix sprints."
            )

    if not parts:
        return "Insufficient data to generate an executive summary at this time."

    return " ".join(parts)


# ── FM-199: Executive Summary Artifact Storage ───────────────────


async def save_executive_summary(
    db: AsyncSession,
    project_id: uuid.UUID,
) -> dict[str, Any]:
    """Generate and store a versioned executive summary artifact (DB-persisted)."""
    summary = await generate_executive_summary(db, project_id)

    # Determine next version number
    result = await db.execute(
        select(sa_func.coalesce(sa_func.max(ExecutiveSummaryArtifact.version), 0))
        .where(ExecutiveSummaryArtifact.project_id == project_id)
    )
    version = result.scalar_one() + 1

    artifact = ExecutiveSummaryArtifact(
        project_id=project_id,
        version=version,
        summary_json=summary,
    )
    db.add(artifact)
    await db.flush()

    return {
        "version": version,
        "summary": summary,
        "stored_at": artifact.stored_at.isoformat() if artifact.stored_at else datetime.now(timezone.utc).isoformat(),
    }


async def get_summary_artifacts(
    db: AsyncSession,
    project_id: uuid.UUID,
) -> list[dict[str, Any]]:
    """Retrieve stored executive summary artifacts for a project (DB-persisted)."""
    result = await db.execute(
        select(ExecutiveSummaryArtifact)
        .where(ExecutiveSummaryArtifact.project_id == project_id)
        .order_by(ExecutiveSummaryArtifact.version.asc())
    )
    artifacts = result.scalars().all()
    return [
        {
            "version": a.version,
            "summary": a.summary_json,
            "stored_at": a.stored_at.isoformat() if a.stored_at else None,
        }
        for a in artifacts
    ]


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

# Chart types that the frontend should support for each widget
WIDGET_CHART_TYPES = frozenset({
    "line", "bar", "pie", "table", "number", "gauge",
})


def validate_widget_config(widget: dict[str, Any]) -> list[str]:
    """FM-197: Validate a widget configuration dict before persistence.

    Returns a list of validation error strings (empty = valid).
    Validates: widget_type, chart_type, position, size, data_source.
    """
    errors: list[str] = []

    wtype = widget.get("widget_type")
    if not wtype:
        errors.append("widget_type is required")
    elif wtype not in WIDGET_DATA_SOURCES:
        errors.append(
            f"Unknown widget_type '{wtype}'. "
            f"Valid: {', '.join(sorted(WIDGET_DATA_SOURCES))}"
        )

    chart = widget.get("chart_type")
    if chart and chart not in WIDGET_CHART_TYPES:
        errors.append(
            f"Unknown chart_type '{chart}'. "
            f"Valid: {', '.join(sorted(WIDGET_CHART_TYPES))}"
        )

    position = widget.get("position")
    if position is not None:
        if not isinstance(position, dict):
            errors.append("position must be a dict with 'x' and 'y' keys")
        else:
            if "x" not in position or "y" not in position:
                errors.append("position must contain 'x' and 'y' keys")

    size = widget.get("size")
    if size is not None:
        if not isinstance(size, dict):
            errors.append("size must be a dict with 'w' and 'h' keys")
        else:
            if "w" not in size or "h" not in size:
                errors.append("size must contain 'w' and 'h' keys")

    return errors


def validate_dashboard_layout(layout_json: list[dict[str, Any]]) -> list[str]:
    """FM-197: Validate an entire dashboard layout (list of widget configs).

    Returns aggregated validation errors across all widgets.
    """
    if not isinstance(layout_json, list):
        return ["layout_json must be a list of widget configurations"]

    all_errors: list[str] = []
    for idx, widget in enumerate(layout_json):
        widget_errors = validate_widget_config(widget)
        for e in widget_errors:
            all_errors.append(f"Widget [{idx}]: {e}")
    return all_errors


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
