"""FM-231–250: Wave 19+20 scheduling, platform intelligence, and platform ops tables.

Creates:
  - cron_triggers
  - trigger_rules
  - agent_performance_snapshots
  - prompt_versions
  - model_experiments
  - budget_forecasts
  - slo_targets
  - slo_period_results
  - anomaly_events
  - resource_quotas
  - digest_schedules
  - pii_patterns

Revision ID: wave19_20_platform_intelligence
Revises: wave17_18_agent_intelligence
Create Date: 2026-05-07
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "wave19_20_platform_intelligence"
down_revision = "wave17_18_agent_intelligence"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- FM-231: cron_triggers ---
    op.create_table(
        "cron_triggers",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("cron_expression", sa.String(100), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("fire_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_fired_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.String(36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index("ix_cron_triggers_project_id", "cron_triggers", ["project_id"])

    # --- FM-232: trigger_rules ---
    op.create_table(
        "trigger_rules",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("conditions", sa.JSON(), nullable=True),
        sa.Column("action_prompt", sa.Text(), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("fire_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_fired_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index("ix_trigger_rules_project_id", "trigger_rules", ["project_id"])

    # --- FM-233: agent_performance_snapshots ---
    op.create_table(
        "agent_performance_snapshots",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("agent_slug", sa.String(100), nullable=False),
        sa.Column("project_id", sa.String(36), nullable=True),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("total_tasks", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("successful_tasks", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_tasks", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("avg_latency_ms", sa.Float(), nullable=True),
        sa.Column("total_cost_usd", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("llm_calls", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index("ix_agent_perf_slug_date", "agent_performance_snapshots", ["agent_slug", "snapshot_date"])

    # --- FM-234: prompt_versions ---
    op.create_table(
        "prompt_versions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(100), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("change_summary", sa.Text(), nullable=True),
        sa.Column("created_by", sa.String(36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index("ix_prompt_versions_project_role", "prompt_versions", ["project_id", "role"])

    # --- FM-235: model_experiments ---
    op.create_table(
        "model_experiments",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("model_a", sa.String(100), nullable=False),
        sa.Column("model_b", sa.String(100), nullable=False),
        sa.Column("traffic_split_pct", sa.Float(), nullable=False, server_default="50.0"),
        sa.Column("status", sa.String(20), nullable=False, server_default="running"),
        sa.Column("winner", sa.String(100), nullable=True),
        sa.Column("result_summary", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
    )

    # --- FM-236: budget_forecasts ---
    op.create_table(
        "budget_forecasts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("forecast_month", sa.String(7), nullable=False),
        sa.Column("actual_spend_usd", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("forecasted_spend_usd", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("budget_usd", sa.Float(), nullable=True),
        sa.Column("burn_rate_usd_per_day", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("days_remaining", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("will_exceed_budget", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("breakdown_by_agent", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )

    # --- FM-239: slo_targets ---
    op.create_table(
        "slo_targets",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("metric", sa.String(50), nullable=False),
        sa.Column("threshold", sa.Float(), nullable=False),
        sa.Column("target_pct", sa.Float(), nullable=False, server_default="0.99"),
        sa.Column("window_days", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index("ix_slo_targets_project_id", "slo_targets", ["project_id"])

    # --- FM-239: slo_period_results ---
    op.create_table(
        "slo_period_results",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("slo_id", sa.String(36), sa.ForeignKey("slo_targets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("attainment_pct", sa.Float(), nullable=False),
        sa.Column("met", sa.Boolean(), nullable=False),
        sa.Column("total_events", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("p50", sa.Float(), nullable=True),
        sa.Column("p95", sa.Float(), nullable=True),
        sa.Column("p99", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )

    # --- FM-240: anomaly_events ---
    op.create_table(
        "anomaly_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("anomaly_type", sa.String(50), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("metric_value", sa.Float(), nullable=True),
        sa.Column("baseline_value", sa.Float(), nullable=True),
        sa.Column("deviation_pct", sa.Float(), nullable=True),
        sa.Column("resolved", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("detected_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index("ix_anomaly_events_project_id", "anomaly_events", ["project_id"])

    # --- FM-241: resource_quotas ---
    op.create_table(
        "resource_quotas",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("workspace_id", sa.String(36), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("max_concurrent_runs", sa.Integer(), nullable=True),
        sa.Column("max_projects", sa.Integer(), nullable=True),
        sa.Column("max_monthly_cost_usd", sa.Float(), nullable=True),
        sa.Column("max_api_calls_per_minute", sa.Integer(), nullable=True),
        sa.Column("max_storage_gb", sa.Float(), nullable=True),
        sa.Column("enforce", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )

    # --- FM-246: digest_schedules ---
    op.create_table(
        "digest_schedules",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False, unique=True),
        sa.Column("frequency", sa.String(20), nullable=False, server_default="daily"),
        sa.Column("include_activity", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("include_approvals", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("include_costs", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("include_security", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("last_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )

    # --- FM-247: pii_patterns ---
    op.create_table(
        "pii_patterns",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False, unique=True),
        sa.Column("pattern_type", sa.String(20), nullable=False, server_default="regex"),
        sa.Column("pattern", sa.Text(), nullable=False),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False, server_default="medium"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("pii_patterns")
    op.drop_table("digest_schedules")
    op.drop_table("resource_quotas")
    op.drop_index("ix_anomaly_events_project_id", "anomaly_events")
    op.drop_table("anomaly_events")
    op.drop_table("slo_period_results")
    op.drop_index("ix_slo_targets_project_id", "slo_targets")
    op.drop_table("slo_targets")
    op.drop_table("budget_forecasts")
    op.drop_table("model_experiments")
    op.drop_index("ix_prompt_versions_project_role", "prompt_versions")
    op.drop_table("prompt_versions")
    op.drop_index("ix_agent_perf_slug_date", "agent_performance_snapshots")
    op.drop_table("agent_performance_snapshots")
    op.drop_index("ix_trigger_rules_project_id", "trigger_rules")
    op.drop_table("trigger_rules")
    op.drop_index("ix_cron_triggers_project_id", "cron_triggers")
    op.drop_table("cron_triggers")
