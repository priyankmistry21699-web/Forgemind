"""Analytics & Metrics routes — FM-191 through FM-199.

Execution metrics, health scoring, cost budgets, velocity, quality,
portfolio, dashboards, alerts, scheduled reports, executive summaries.
"""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user_id
from app.db.session import get_db
from app.services.authz_service import check_project_permission, Action
from app.services import execution_health_service
from app.services import velocity_quality_service
from app.services import dashboard_alert_service

router = APIRouter(prefix="/analytics")


# ── Inline Schemas ───────────────────────────────────────────────


class RecordMetricRequest(BaseModel):
    metric_type: str
    value_ms: int
    run_id: uuid.UUID | None = None
    task_id: uuid.UUID | None = None


class HealthScoreRequest(BaseModel):
    dimension_scores: dict[str, float] | None = None


class BudgetConfigRequest(BaseModel):
    monthly_budget_usd: float
    warn_threshold_pct: float = 80.0
    action_on_exceed: str = "warn"


class QualitySnapshotRequest(BaseModel):
    test_pass_rate: float = 0.0
    defect_density: float = 0.0
    rollback_rate: float = 0.0
    review_coverage: float = 0.0


class PortfolioRequest(BaseModel):
    project_ids: list[uuid.UUID]


class DashboardCreateRequest(BaseModel):
    name: str
    description: str | None = None
    layout_json: dict | None = None
    visibility: str = "private"
    org_id: uuid.UUID | None = None


class DashboardUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    layout_json: dict | None = None
    visibility: str | None = None


class ScheduledReportRequest(BaseModel):
    name: str
    metrics: list[str]
    schedule_cron: str
    recipients: list[str] | None = None
    org_id: uuid.UUID | None = None


class MetricAlertRequest(BaseModel):
    name: str
    metric_type: str
    condition_op: str
    threshold: float
    recipients: list[str] | None = None
    cooldown_minutes: int = 60
    org_id: uuid.UUID | None = None
    project_id: uuid.UUID | None = None


# ── FM-191: Execution Metrics ────────────────────────────────────


@router.post("/projects/{project_id}/execution-metrics")
async def record_execution_metric(
    project_id: uuid.UUID,
    data: RecordMetricRequest,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Record an execution timing metric."""
    await check_project_permission(db, project_id, user_id, Action.PROJECT_EDIT)
    from app.models.analytics_metrics import ExecutionMetricType
    m = await execution_health_service.record_execution_metric(
        db, project_id=project_id, metric_type=ExecutionMetricType(data.metric_type),
        value_ms=data.value_ms, run_id=data.run_id, task_id=data.task_id,
    )
    return {"id": str(m.id), "metric_type": data.metric_type, "value_ms": data.value_ms}


@router.get("/projects/{project_id}/execution-metrics")
async def get_execution_metrics(
    project_id: uuid.UUID,
    metric_type: str | None = Query(None),
    run_id: uuid.UUID | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """List execution metrics with optional filters."""
    await check_project_permission(db, project_id, user_id, Action.PROJECT_VIEW)
    mt = None
    if metric_type:
        from app.models.analytics_metrics import ExecutionMetricType
        mt = ExecutionMetricType(metric_type)
    items, total = await execution_health_service.get_execution_metrics(
        db, project_id, metric_type=mt, run_id=run_id, limit=limit, offset=offset,
    )
    return {
        "total": total,
        "items": [
            {"id": str(i.id), "metric_type": i.metric_type.value if i.metric_type else None,
             "value_ms": i.value_ms, "run_id": str(i.run_id) if i.run_id else None,
             "recorded_at": i.recorded_at.isoformat() if i.recorded_at else None}
            for i in items
        ],
    }


@router.get("/projects/{project_id}/execution-metrics/summary")
async def get_execution_metrics_summary(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Get aggregated execution metric stats."""
    await check_project_permission(db, project_id, user_id, Action.PROJECT_VIEW)
    return await execution_health_service.get_execution_metrics_summary(db, project_id)


# ── FM-192: Health Scoring ───────────────────────────────────────


@router.post("/projects/{project_id}/health")
async def compute_health(
    project_id: uuid.UUID,
    data: HealthScoreRequest,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Compute and store a health snapshot for the project."""
    await check_project_permission(db, project_id, user_id, Action.PROJECT_EDIT)
    snap = await execution_health_service.compute_health_snapshot(
        db, project_id, dimension_scores=data.dimension_scores,
    )
    return {
        "id": str(snap.id), "composite_score": snap.composite_score,
        "grade": snap.grade.value if hasattr(snap.grade, 'value') else str(snap.grade),
    }


@router.get("/projects/{project_id}/health")
async def get_health(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Get the latest health snapshot."""
    await check_project_permission(db, project_id, user_id, Action.PROJECT_VIEW)
    snap = await execution_health_service.get_latest_health(db, project_id)
    if snap is None:
        return {"health": None}
    return {
        "id": str(snap.id), "composite_score": snap.composite_score,
        "grade": snap.grade.value if hasattr(snap.grade, 'value') else str(snap.grade),
        "dimension_scores": snap.dimension_scores,
    }


@router.get("/projects/{project_id}/health/trend")
async def get_health_trend(
    project_id: uuid.UUID,
    limit: int = Query(30, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Get health score trend over time."""
    await check_project_permission(db, project_id, user_id, Action.PROJECT_VIEW)
    return await execution_health_service.get_health_trend(db, project_id, limit=limit)


# ── FM-193: Cost Budget Config ───────────────────────────────────


@router.post("/projects/{project_id}/budget")
async def set_budget(
    project_id: uuid.UUID,
    data: BudgetConfigRequest,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Set or update cost budget configuration for a project."""
    await check_project_permission(db, project_id, user_id, Action.PROJECT_EDIT)
    from app.models.analytics_metrics import BudgetConfig, BudgetAction
    from sqlalchemy import select

    result = await db.execute(
        select(BudgetConfig).where(BudgetConfig.project_id == project_id)
    )
    existing = result.scalar_one_or_none()
    if existing:
        existing.monthly_budget_usd = data.monthly_budget_usd
        existing.warn_threshold_pct = data.warn_threshold_pct
        existing.action_on_exceed = BudgetAction(data.action_on_exceed)
        await db.flush()
        return {"id": str(existing.id), "monthly_budget_usd": data.monthly_budget_usd}

    config = BudgetConfig(
        project_id=project_id,
        monthly_budget_usd=data.monthly_budget_usd,
        warn_threshold_pct=data.warn_threshold_pct,
        action_on_exceed=BudgetAction(data.action_on_exceed),
    )
    db.add(config)
    await db.flush()
    return {"id": str(config.id), "monthly_budget_usd": data.monthly_budget_usd}


@router.get("/projects/{project_id}/budget")
async def get_budget(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Get budget configuration and current spend."""
    await check_project_permission(db, project_id, user_id, Action.PROJECT_VIEW)
    from app.models.analytics_metrics import BudgetConfig
    from app.services import cost_tracking_service
    from sqlalchemy import select

    result = await db.execute(
        select(BudgetConfig).where(BudgetConfig.project_id == project_id)
    )
    config = result.scalar_one_or_none()
    cost_summary = await cost_tracking_service.get_project_cost_summary(db, project_id)

    budget_data = None
    if config:
        budget_data = {
            "monthly_budget_usd": config.monthly_budget_usd,
            "warn_threshold_pct": config.warn_threshold_pct,
            "action_on_exceed": config.action_on_exceed.value if config.action_on_exceed else None,
        }

    return {
        "budget": budget_data,
        "current_spend": cost_summary,
    }


# ── FM-194: Velocity ─────────────────────────────────────────────


@router.get("/projects/{project_id}/velocity")
async def get_velocity(
    project_id: uuid.UUID,
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Get velocity metrics for a project."""
    await check_project_permission(db, project_id, user_id, Action.PROJECT_VIEW)
    return await velocity_quality_service.compute_velocity(db, project_id, days=days)


# ── FM-195: Quality Metrics ──────────────────────────────────────


@router.post("/projects/{project_id}/quality")
async def record_quality(
    project_id: uuid.UUID,
    data: QualitySnapshotRequest,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Record a quality metrics snapshot."""
    await check_project_permission(db, project_id, user_id, Action.PROJECT_EDIT)
    snap = await velocity_quality_service.record_quality_snapshot(
        db, project_id=project_id,
        test_pass_rate=data.test_pass_rate,
        defect_density=data.defect_density,
        rollback_rate=data.rollback_rate,
        review_coverage=data.review_coverage,
    )
    return {"id": str(snap.id), "test_pass_rate": snap.test_pass_rate}


@router.get("/projects/{project_id}/quality")
async def get_quality(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Get the latest quality snapshot."""
    await check_project_permission(db, project_id, user_id, Action.PROJECT_VIEW)
    snap = await velocity_quality_service.get_latest_quality(db, project_id)
    if snap is None:
        return {"quality": None}
    return {
        "test_pass_rate": snap.test_pass_rate,
        "defect_density": snap.defect_density,
        "rollback_rate": snap.rollback_rate,
        "review_coverage": snap.review_coverage,
    }


@router.get("/projects/{project_id}/quality/trend")
async def get_quality_trend(
    project_id: uuid.UUID,
    limit: int = Query(30, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Get quality trend over time."""
    await check_project_permission(db, project_id, user_id, Action.PROJECT_VIEW)
    return await velocity_quality_service.get_quality_trend(db, project_id, limit=limit)


# ── FM-196: Portfolio ────────────────────────────────────────────


@router.post("/portfolio")
async def get_portfolio(
    data: PortfolioRequest,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Get aggregate analytics across multiple projects."""
    return await velocity_quality_service.get_portfolio_summary(db, data.project_ids)


# ── FM-197: Dashboards ───────────────────────────────────────────


@router.post("/dashboards")
async def create_dashboard(
    data: DashboardCreateRequest,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Create a custom dashboard."""
    from app.models.analytics_metrics import DashboardVisibility
    dash = await dashboard_alert_service.create_dashboard(
        db, creator_id=user_id, name=data.name, description=data.description,
        layout_json=data.layout_json, visibility=DashboardVisibility(data.visibility),
        org_id=data.org_id,
    )
    return {"id": str(dash.id), "name": dash.name}


@router.get("/dashboards")
async def list_dashboards(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """List dashboards for the current user."""
    dashboards, total = await dashboard_alert_service.list_dashboards(
        db, user_id, limit=limit, offset=offset,
    )
    return {
        "total": total,
        "items": [
            {"id": str(d.id), "name": d.name, "visibility": d.visibility.value if d.visibility else None}
            for d in dashboards
        ],
    }


@router.get("/dashboards/{dashboard_id}")
async def get_dashboard(
    dashboard_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Get a dashboard by ID."""
    dash = await dashboard_alert_service.get_dashboard(db, dashboard_id)
    return {
        "id": str(dash.id), "name": dash.name, "description": dash.description,
        "layout_json": dash.layout_json,
        "visibility": dash.visibility.value if dash.visibility else None,
    }


@router.put("/dashboards/{dashboard_id}")
async def update_dashboard(
    dashboard_id: uuid.UUID,
    data: DashboardUpdateRequest,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Update a dashboard."""
    dash = await dashboard_alert_service.update_dashboard(
        db, dashboard_id, **data.model_dump(exclude_unset=True),
    )
    return {"id": str(dash.id), "name": dash.name}


@router.delete("/dashboards/{dashboard_id}")
async def delete_dashboard(
    dashboard_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Delete a dashboard."""
    await dashboard_alert_service.delete_dashboard(db, dashboard_id)
    return {"deleted": True}


# ── FM-198: Scheduled Reports & Alerts ───────────────────────────


@router.post("/scheduled-reports")
async def create_report(
    data: ScheduledReportRequest,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Create a scheduled report."""
    report = await dashboard_alert_service.create_scheduled_report(
        db, name=data.name, metrics=data.metrics,
        schedule_cron=data.schedule_cron, recipients=data.recipients,
        org_id=data.org_id,
    )
    return {"id": str(report.id), "name": report.name}


@router.get("/scheduled-reports")
async def list_reports(
    org_id: uuid.UUID | None = Query(None),
    active_only: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """List scheduled reports."""
    reports = await dashboard_alert_service.list_scheduled_reports(
        db, org_id=org_id, active_only=active_only,
    )
    return {
        "items": [
            {"id": str(r.id), "name": r.name, "schedule_cron": r.schedule_cron, "active": r.active}
            for r in reports
        ]
    }


@router.post("/alerts")
async def create_alert(
    data: MetricAlertRequest,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Create a metric alert rule."""
    from app.models.analytics_metrics import AlertConditionOp
    alert = await dashboard_alert_service.create_metric_alert(
        db, name=data.name, metric_type=data.metric_type,
        condition_op=AlertConditionOp(data.condition_op),
        threshold=data.threshold, recipients=data.recipients,
        cooldown_minutes=data.cooldown_minutes, org_id=data.org_id,
        project_id=data.project_id,
    )
    return {"id": str(alert.id), "name": alert.name}


@router.get("/alerts")
async def list_alerts(
    org_id: uuid.UUID | None = Query(None),
    project_id: uuid.UUID | None = Query(None),
    active_only: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """List metric alert rules."""
    alerts = await dashboard_alert_service.list_metric_alerts(
        db, org_id=org_id, project_id=project_id, active_only=active_only,
    )
    return {
        "items": [
            {"id": str(a.id), "name": a.name, "metric_type": a.metric_type,
             "threshold": a.threshold, "active": a.active}
            for a in alerts
        ]
    }


# ── FM-199: Executive Summary ────────────────────────────────────


@router.get("/projects/{project_id}/executive-summary")
async def get_executive_summary(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Generate a comprehensive executive summary for a project."""
    await check_project_permission(db, project_id, user_id, Action.PROJECT_VIEW)
    return await dashboard_alert_service.generate_executive_summary(db, project_id)
