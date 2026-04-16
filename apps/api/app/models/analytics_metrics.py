"""Analytics & Metrics models — FM-191 through FM-199.

New tables:
- execution_metrics: Per-task/run timing metrics (FM-191)
- health_snapshots: Project health scoring snapshots (FM-192)
- budget_configs: Per-project cost budget settings (FM-193)
- quality_snapshots: Quality metric snapshots (FM-195)
- dashboards: Custom dashboard definitions (FM-197)
- scheduled_reports: Automated report configurations (FM-198)
- metric_alerts: Threshold-based alert rules (FM-198)
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Boolean,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSON as PG_JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base


# ── FM-191: Execution Metrics ────────────────────────────────────


class ExecutionMetricType(str, enum.Enum):
    QUEUE_TIME = "queue_time"
    EXECUTION_TIME = "execution_time"
    REVIEW_TIME = "review_time"
    PLANNING_TIME = "planning_time"
    TOTAL_CYCLE_TIME = "total_cycle_time"


class ExecutionMetric(Base):
    """Timing metric for a specific stage of run/task execution."""

    __tablename__ = "execution_metrics"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    run_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("runs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    task_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="SET NULL"),
        nullable=True,
    )
    metric_type: Mapped[ExecutionMetricType] = mapped_column(
        Enum(ExecutionMetricType, name="execution_metric_type"),
        nullable=False,
    )
    value_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        Index("ix_exec_metric_project_type", "project_id", "metric_type"),
    )


# ── FM-192: Health Scoring ───────────────────────────────────────


class HealthGrade(str, enum.Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    F = "F"


class HealthSnapshot(Base):
    """Point-in-time project health score and dimension breakdown."""

    __tablename__ = "health_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    dimension_scores: Mapped[dict] = mapped_column(PG_JSON, nullable=False)
    composite_score: Mapped[float] = mapped_column(Float, nullable=False)
    grade: Mapped[HealthGrade] = mapped_column(
        Enum(HealthGrade, name="health_grade"), nullable=False
    )
    snapshot_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


# ── FM-193: Cost Budget Configuration ────────────────────────────


class BudgetAction(str, enum.Enum):
    LOG = "log"
    WARN = "warn"
    BLOCK = "block"


class BudgetConfig(Base):
    """Per-project cost budget configuration."""

    __tablename__ = "budget_configs"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    monthly_budget_usd: Mapped[float] = mapped_column(Float, nullable=False)
    warn_threshold_pct: Mapped[float] = mapped_column(
        Float, default=80.0, nullable=False
    )
    action_on_exceed: Mapped[BudgetAction] = mapped_column(
        Enum(BudgetAction, name="budget_action"),
        default=BudgetAction.WARN,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


# ── FM-195: Quality Metrics ──────────────────────────────────────


class QualitySnapshot(Base):
    """Point-in-time quality metric snapshot."""

    __tablename__ = "quality_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    test_pass_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    defect_density: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    rollback_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    review_coverage: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    snapshot_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


# ── FM-197: Custom Dashboards ────────────────────────────────────


class DashboardVisibility(str, enum.Enum):
    PRIVATE = "private"
    TEAM = "team"
    ORG = "org"


class Dashboard(Base):
    """User-created custom dashboard."""

    __tablename__ = "dashboards"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    org_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True, index=True
    )
    creator_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    layout_json: Mapped[dict] = mapped_column(PG_JSON, nullable=False, default=dict)
    visibility: Mapped[DashboardVisibility] = mapped_column(
        Enum(DashboardVisibility, name="dashboard_visibility"),
        default=DashboardVisibility.PRIVATE,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


# ── FM-198: Scheduled Reports & Alerts ───────────────────────────


class ScheduledReport(Base):
    """Automated metric report schedule."""

    __tablename__ = "scheduled_reports"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    org_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    metrics: Mapped[list] = mapped_column(PG_JSON, nullable=False)
    schedule_cron: Mapped[str] = mapped_column(String(100), nullable=False)
    recipients: Mapped[list] = mapped_column(PG_JSON, nullable=False, default=list)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_generated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class AlertConditionOp(str, enum.Enum):
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    EQ = "eq"


class MetricAlert(Base):
    """Threshold-based metric alert rule."""

    __tablename__ = "metric_alerts"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    org_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True, index=True
    )
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    metric_type: Mapped[str] = mapped_column(String(100), nullable=False)
    condition_op: Mapped[AlertConditionOp] = mapped_column(
        Enum(AlertConditionOp, name="alert_condition_op"), nullable=False
    )
    threshold: Mapped[float] = mapped_column(Float, nullable=False)
    recipients: Mapped[list] = mapped_column(PG_JSON, nullable=False, default=list)
    cooldown_minutes: Mapped[int] = mapped_column(
        Integer, default=60, nullable=False
    )
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_triggered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
