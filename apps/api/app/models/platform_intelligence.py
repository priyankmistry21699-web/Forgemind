"""FM-233–240: Platform intelligence models.

AgentPerformanceSnapshot — FM-233: per-agent success/latency/cost rollup
PromptVersion           — FM-234: versioned prompt templates per project
ModelExperiment         — FM-235: A/B model experiment result
BudgetForecast          — FM-236: projected spend for a project
SLOTarget               — FM-239: SLO definition (metric, threshold, window)
SLOPeriodResult         — FM-239: measured attainment for a calendar window
AnomalyEvent            — FM-240: detected anomaly in execution patterns
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base


# ---------------------------------------------------------------------------
# FM-233: Agent performance snapshots
# ---------------------------------------------------------------------------

class AgentPerformanceSnapshot(Base):
    """Rolling daily performance rollup per agent slug."""

    __tablename__ = "agent_performance_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_slug: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, index=True
    )
    period_date: Mapped[str] = mapped_column(String(10), nullable=False)  # YYYY-MM-DD
    tasks_completed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tasks_failed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    avg_latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    p95_latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_cost_usd: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    success_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<AgentPerfSnapshot {self.agent_slug} {self.period_date}>"


# ---------------------------------------------------------------------------
# FM-234: Prompt versioning
# ---------------------------------------------------------------------------

class PromptVersion(Base):
    """Versioned prompt template for a project agent role."""

    __tablename__ = "prompt_versions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    change_summary: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<PromptVersion {self.role} v{self.version}>"


# ---------------------------------------------------------------------------
# FM-235: Model experiment A/B tracking
# ---------------------------------------------------------------------------

class ModelExperiment(Base):
    """Records an A/B comparison between two models on the same task."""

    __tablename__ = "model_experiments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, index=True
    )
    run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("runs.id", ondelete="SET NULL"), nullable=True
    )
    task_type: Mapped[str] = mapped_column(String(100), nullable=False)
    model_a: Mapped[str] = mapped_column(String(200), nullable=False)
    model_b: Mapped[str] = mapped_column(String(200), nullable=False)
    cost_a_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    cost_b_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    latency_a_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latency_b_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    quality_score_a: Mapped[float | None] = mapped_column(Float, nullable=True)
    quality_score_b: Mapped[float | None] = mapped_column(Float, nullable=True)
    winner: Mapped[str | None] = mapped_column(String(10), nullable=True)  # "a" | "b" | "tie"
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<ModelExperiment {self.model_a} vs {self.model_b}>"


# ---------------------------------------------------------------------------
# FM-236: Budget forecasting
# ---------------------------------------------------------------------------

class BudgetForecast(Base):
    """Monthly budget forecast generated for a project."""

    __tablename__ = "budget_forecasts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    forecast_month: Mapped[str] = mapped_column(String(7), nullable=False)  # YYYY-MM
    actual_spend_usd: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    forecasted_spend_usd: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    budget_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    burn_rate_usd_per_day: Mapped[float | None] = mapped_column(Float, nullable=True)
    days_remaining: Mapped[int | None] = mapped_column(Integer, nullable=True)
    will_exceed_budget: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)  # 0.0–1.0
    breakdown_by_agent: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<BudgetForecast {self.project_id} {self.forecast_month}>"


# ---------------------------------------------------------------------------
# FM-239: SLO tracking
# ---------------------------------------------------------------------------

class SLOMetric(str, enum.Enum):
    PLAN_LATENCY_MS = "plan_latency_ms"
    TASK_LATENCY_MS = "task_latency_ms"
    APPROVAL_WAIT_MS = "approval_wait_ms"
    RUN_SUCCESS_RATE = "run_success_rate"
    COST_PER_RUN_USD = "cost_per_run_usd"


class SLOTarget(Base):
    """SLO definition — what metric, threshold, and window to measure."""

    __tablename__ = "slo_targets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    metric: Mapped[SLOMetric] = mapped_column(Enum(SLOMetric, name="slo_metric"), nullable=False)
    threshold: Mapped[float] = mapped_column(Float, nullable=False)
    target_pct: Mapped[float] = mapped_column(Float, default=0.99, nullable=False)
    window_days: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<SLOTarget {self.name} {self.metric.value}<={self.threshold}>"


class SLOPeriodResult(Base):
    """Measured SLO attainment for a calendar window."""

    __tablename__ = "slo_period_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slo_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("slo_targets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    total_events: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    compliant_events: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    attainment_pct: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    met: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    p50: Mapped[float | None] = mapped_column(Float, nullable=True)
    p95: Mapped[float | None] = mapped_column(Float, nullable=True)
    p99: Mapped[float | None] = mapped_column(Float, nullable=True)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<SLOPeriodResult slo={self.slo_id} att={self.attainment_pct:.2%}>"


# ---------------------------------------------------------------------------
# FM-240: Anomaly detection
# ---------------------------------------------------------------------------

class AnomalySeverity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class AnomalyType(str, enum.Enum):
    COST_SPIKE = "cost_spike"
    LATENCY_SPIKE = "latency_spike"
    ERROR_RATE_JUMP = "error_rate_jump"
    UNUSUAL_TASK_VOLUME = "unusual_task_volume"
    SECURITY_FINDING_SURGE = "security_finding_surge"
    APPROVAL_REJECTION_SURGE = "approval_rejection_surge"


class AnomalyEvent(Base):
    """Detected anomaly in execution patterns."""

    __tablename__ = "anomaly_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    anomaly_type: Mapped[AnomalyType] = mapped_column(
        Enum(AnomalyType, name="anomaly_type"), nullable=False, index=True
    )
    severity: Mapped[AnomalySeverity] = mapped_column(
        Enum(AnomalySeverity, name="anomaly_severity"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    metric_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    baseline_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    deviation_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    raw_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<AnomalyEvent {self.anomaly_type.value} {self.severity.value}>"
