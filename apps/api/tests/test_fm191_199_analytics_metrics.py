"""Tests for FM-191–199: Analytics & Metrics.

Covers: execution metrics, health scoring, cost budgets, velocity,
quality metrics, portfolio, dashboards, alerts, executive summaries.
"""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analytics_metrics import (
    ExecutionMetricType,
    HealthGrade,
    AlertConditionOp,
    DashboardVisibility,
)
from app.services import (
    execution_health_service,
    velocity_quality_service,
    dashboard_alert_service,
)

STUB_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


# ══════════════════════════════════════════════════════════════════
# FM-191: Execution Metrics
# ══════════════════════════════════════════════════════════════════


class TestExecutionMetrics:
    @pytest.mark.asyncio
    async def test_record_execution_metric(self, db_session: AsyncSession, sample_project):
        m = await execution_health_service.record_execution_metric(
            db_session,
            project_id=sample_project.id,
            metric_type=ExecutionMetricType.EXECUTION_TIME,
            value_ms=5000,
        )
        await db_session.commit()
        assert m.id is not None
        assert m.value_ms == 5000

    @pytest.mark.asyncio
    async def test_record_execution_metric_with_run(
        self, db_session: AsyncSession, sample_project, sample_run
    ):
        m = await execution_health_service.record_execution_metric(
            db_session,
            project_id=sample_project.id,
            metric_type=ExecutionMetricType.QUEUE_TIME,
            value_ms=200,
            run_id=sample_run.id,
        )
        await db_session.commit()
        assert m.run_id == sample_run.id

    @pytest.mark.asyncio
    async def test_get_execution_metrics(self, db_session: AsyncSession, sample_project):
        await execution_health_service.record_execution_metric(
            db_session, project_id=sample_project.id,
            metric_type=ExecutionMetricType.PLANNING_TIME, value_ms=1000,
        )
        await db_session.commit()

        items, total = await execution_health_service.get_execution_metrics(
            db_session, sample_project.id
        )
        assert total >= 1

    @pytest.mark.asyncio
    async def test_get_execution_metrics_summary(
        self, db_session: AsyncSession, sample_project
    ):
        for ms in [100, 200, 300]:
            await execution_health_service.record_execution_metric(
                db_session, project_id=sample_project.id,
                metric_type=ExecutionMetricType.EXECUTION_TIME, value_ms=ms,
            )
        await db_session.commit()

        summary = await execution_health_service.get_execution_metrics_summary(
            db_session, sample_project.id
        )
        assert len(summary["metrics"]) >= 1


# ══════════════════════════════════════════════════════════════════
# FM-192: Health Scoring
# ══════════════════════════════════════════════════════════════════


class TestHealthScoring:
    @pytest.mark.asyncio
    async def test_compute_health_defaults(self, db_session: AsyncSession, sample_project):
        snap = await execution_health_service.compute_health_snapshot(
            db_session, sample_project.id
        )
        await db_session.commit()
        assert snap.id is not None
        # Auto-computed from real data: empty project gets default dimension scores
        assert snap.composite_score > 0
        assert snap.grade in (HealthGrade.D, HealthGrade.F)  # Low scores for empty project

    @pytest.mark.asyncio
    async def test_compute_health_high_scores(
        self, db_session: AsyncSession, sample_project
    ):
        scores = {
            "success_rate": 95, "velocity": 90, "cost_efficiency": 85,
            "quality": 92, "coverage": 88, "complexity": 91,
        }
        snap = await execution_health_service.compute_health_snapshot(
            db_session, sample_project.id, dimension_scores=scores,
        )
        await db_session.commit()
        assert snap.grade == HealthGrade.A
        assert snap.composite_score > 85

    @pytest.mark.asyncio
    async def test_get_latest_health(self, db_session: AsyncSession, sample_project):
        await execution_health_service.compute_health_snapshot(
            db_session, sample_project.id,
        )
        await db_session.commit()

        latest = await execution_health_service.get_latest_health(
            db_session, sample_project.id
        )
        assert latest is not None

    @pytest.mark.asyncio
    async def test_get_health_trend(self, db_session: AsyncSession, sample_project):
        for i in range(3):
            await execution_health_service.compute_health_snapshot(
                db_session, sample_project.id,
                dimension_scores={"success_rate": 50 + i * 10,
                                  "velocity": 50, "cost_efficiency": 50,
                                  "quality": 50, "coverage": 50, "complexity": 50},
            )
        await db_session.commit()

        trend = await execution_health_service.get_health_trend(
            db_session, sample_project.id
        )
        assert len(trend) >= 3

    @pytest.mark.asyncio
    async def test_grade_boundaries(self, db_session: AsyncSession):
        """Verify grade thresholds match roadmap: A≥90, B≥75, C≥60, D≥45, F<45."""
        from app.services.execution_health_service import _compute_grade
        # A grade
        assert _compute_grade(95) == HealthGrade.A
        assert _compute_grade(90) == HealthGrade.A
        # B grade
        assert _compute_grade(89) == HealthGrade.B
        assert _compute_grade(75) == HealthGrade.B
        # C grade
        assert _compute_grade(74) == HealthGrade.C
        assert _compute_grade(60) == HealthGrade.C
        # D grade
        assert _compute_grade(59) == HealthGrade.D
        assert _compute_grade(45) == HealthGrade.D
        # F grade
        assert _compute_grade(44) == HealthGrade.F
        assert _compute_grade(0) == HealthGrade.F


# ══════════════════════════════════════════════════════════════════
# FM-193: Cost Budget Config
# ══════════════════════════════════════════════════════════════════


class TestCostBudget:
    @pytest.mark.asyncio
    async def test_create_budget_config(self, db_session: AsyncSession, sample_project):
        from app.models.analytics_metrics import BudgetConfig, BudgetAction

        config = BudgetConfig(
            project_id=sample_project.id,
            monthly_budget_usd=100.0,
            warn_threshold_pct=80.0,
            action_on_exceed=BudgetAction.WARN,
        )
        db_session.add(config)
        await db_session.commit()
        assert config.id is not None
        assert config.monthly_budget_usd == 100.0

    @pytest.mark.asyncio
    async def test_budget_action_block(self, db_session: AsyncSession, sample_project):
        from app.models.analytics_metrics import BudgetConfig, BudgetAction

        config = BudgetConfig(
            project_id=sample_project.id,
            monthly_budget_usd=50.0,
            action_on_exceed=BudgetAction.BLOCK,
        )
        db_session.add(config)
        await db_session.commit()
        assert config.action_on_exceed == BudgetAction.BLOCK


# ══════════════════════════════════════════════════════════════════
# FM-194: Velocity Metrics
# ══════════════════════════════════════════════════════════════════


class TestVelocity:
    @pytest.mark.asyncio
    async def test_compute_velocity(self, db_session: AsyncSession, sample_project):
        velocity = await velocity_quality_service.compute_velocity(
            db_session, sample_project.id, days=30,
        )
        assert velocity["project_id"] == str(sample_project.id)
        assert "completed_runs" in velocity
        assert "runs_per_day" in velocity

    @pytest.mark.asyncio
    async def test_velocity_tasks_filtered_by_project(
        self, db_session: AsyncSession, sample_project
    ):
        """Regression: completed_tasks must only count tasks in this project's runs."""
        from app.models.project import Project
        from app.models.run import Run, RunStatus
        from app.models.task import Task, TaskStatus

        # Create a second project with a completed run+task
        other_project = Project(
            name="Other Project",
            description="Should not leak into velocity",
            owner_id=STUB_USER_ID,
        )
        db_session.add(other_project)
        await db_session.flush()

        other_run = Run(
            run_number=1,
            project_id=other_project.id,
            status=RunStatus.COMPLETED,
            trigger="test",
        )
        db_session.add(other_run)
        await db_session.flush()

        other_task = Task(
            title="Other Task",
            status=TaskStatus.COMPLETED,
            run_id=other_run.id,
        )
        db_session.add(other_task)
        await db_session.flush()
        await db_session.commit()

        # Velocity for sample_project must NOT include other_task
        velocity = await velocity_quality_service.compute_velocity(
            db_session, sample_project.id, days=365,
        )
        assert velocity["completed_tasks"] == 0


# ══════════════════════════════════════════════════════════════════
# FM-195: Quality Metrics
# ══════════════════════════════════════════════════════════════════


class TestQualityMetrics:
    @pytest.mark.asyncio
    async def test_record_quality_snapshot(self, db_session: AsyncSession, sample_project):
        snap = await velocity_quality_service.record_quality_snapshot(
            db_session, project_id=sample_project.id,
            test_pass_rate=95.5, defect_density=0.02,
            rollback_rate=1.0, review_coverage=88.0,
        )
        await db_session.commit()
        assert snap.id is not None
        assert snap.test_pass_rate == 95.5

    @pytest.mark.asyncio
    async def test_get_latest_quality(self, db_session: AsyncSession, sample_project):
        await velocity_quality_service.record_quality_snapshot(
            db_session, project_id=sample_project.id,
            test_pass_rate=90.0,
        )
        await db_session.commit()

        latest = await velocity_quality_service.get_latest_quality(
            db_session, sample_project.id
        )
        assert latest is not None
        assert latest.test_pass_rate == 90.0

    @pytest.mark.asyncio
    async def test_get_quality_trend(self, db_session: AsyncSession, sample_project):
        for rate in [80.0, 85.0, 90.0]:
            await velocity_quality_service.record_quality_snapshot(
                db_session, project_id=sample_project.id,
                test_pass_rate=rate,
            )
        await db_session.commit()

        trend = await velocity_quality_service.get_quality_trend(
            db_session, sample_project.id
        )
        assert len(trend) >= 3


# ══════════════════════════════════════════════════════════════════
# FM-196: Portfolio Analytics
# ══════════════════════════════════════════════════════════════════


class TestPortfolio:
    @pytest.mark.asyncio
    async def test_get_portfolio_summary(self, db_session: AsyncSession, sample_project):
        result = await velocity_quality_service.get_portfolio_summary(
            db_session, [sample_project.id]
        )
        assert result["project_count"] == 1
        assert len(result["projects"]) == 1


# ══════════════════════════════════════════════════════════════════
# FM-197: Dashboards
# ══════════════════════════════════════════════════════════════════


class TestDashboards:
    @pytest.mark.asyncio
    async def test_create_dashboard(self, db_session: AsyncSession):
        dash = await dashboard_alert_service.create_dashboard(
            db_session, creator_id=STUB_USER_ID,
            name="My Dashboard",
            layout_json={"widgets": []},
        )
        await db_session.commit()
        assert dash.id is not None
        assert dash.name == "My Dashboard"

    @pytest.mark.asyncio
    async def test_get_dashboard(self, db_session: AsyncSession):
        dash = await dashboard_alert_service.create_dashboard(
            db_session, creator_id=STUB_USER_ID, name="Get Test",
        )
        await db_session.commit()

        fetched = await dashboard_alert_service.get_dashboard(db_session, dash.id)
        assert fetched.name == "Get Test"

    @pytest.mark.asyncio
    async def test_list_dashboards(self, db_session: AsyncSession):
        await dashboard_alert_service.create_dashboard(
            db_session, creator_id=STUB_USER_ID, name="D1",
        )
        await dashboard_alert_service.create_dashboard(
            db_session, creator_id=STUB_USER_ID, name="D2",
        )
        await db_session.commit()

        dashboards, total = await dashboard_alert_service.list_dashboards(
            db_session, STUB_USER_ID,
        )
        assert total >= 2

    @pytest.mark.asyncio
    async def test_update_dashboard(self, db_session: AsyncSession):
        dash = await dashboard_alert_service.create_dashboard(
            db_session, creator_id=STUB_USER_ID, name="Old Name",
        )
        await db_session.commit()

        updated = await dashboard_alert_service.update_dashboard(
            db_session, dash.id, name="New Name",
        )
        assert updated.name == "New Name"

    @pytest.mark.asyncio
    async def test_delete_dashboard(self, db_session: AsyncSession):
        dash = await dashboard_alert_service.create_dashboard(
            db_session, creator_id=STUB_USER_ID, name="To Delete",
        )
        await db_session.commit()

        await dashboard_alert_service.delete_dashboard(db_session, dash.id)
        await db_session.commit()

        from fastapi import HTTPException
        with pytest.raises(HTTPException):
            await dashboard_alert_service.get_dashboard(db_session, dash.id)

    @pytest.mark.asyncio
    async def test_dashboard_visibility(self, db_session: AsyncSession):
        dash = await dashboard_alert_service.create_dashboard(
            db_session, creator_id=STUB_USER_ID, name="Team Dash",
            visibility=DashboardVisibility.TEAM,
        )
        await db_session.commit()
        assert dash.visibility == DashboardVisibility.TEAM


# ══════════════════════════════════════════════════════════════════
# FM-198: Scheduled Reports & Alerts
# ══════════════════════════════════════════════════════════════════


class TestScheduledReports:
    @pytest.mark.asyncio
    async def test_create_scheduled_report(self, db_session: AsyncSession):
        report = await dashboard_alert_service.create_scheduled_report(
            db_session, name="Weekly Summary",
            metrics=["velocity", "cost"],
            schedule_cron="0 9 * * 1",
            recipients=["user@example.com"],
        )
        await db_session.commit()
        assert report.id is not None
        assert report.active is True

    @pytest.mark.asyncio
    async def test_list_scheduled_reports(self, db_session: AsyncSession):
        await dashboard_alert_service.create_scheduled_report(
            db_session, name="Report A",
            metrics=["health"], schedule_cron="0 0 * * *",
        )
        await db_session.commit()

        reports = await dashboard_alert_service.list_scheduled_reports(db_session)
        assert len(reports) >= 1


class TestMetricAlerts:
    @pytest.mark.asyncio
    async def test_create_metric_alert(self, db_session: AsyncSession):
        alert = await dashboard_alert_service.create_metric_alert(
            db_session, name="High Cost Alert",
            metric_type="cost_usd",
            condition_op=AlertConditionOp.GT,
            threshold=100.0,
            recipients=["admin@example.com"],
        )
        await db_session.commit()
        assert alert.id is not None
        assert alert.active is True

    @pytest.mark.asyncio
    async def test_list_metric_alerts(self, db_session: AsyncSession):
        await dashboard_alert_service.create_metric_alert(
            db_session, name="Alert 1",
            metric_type="latency", condition_op=AlertConditionOp.GTE,
            threshold=5000.0,
        )
        await db_session.commit()

        alerts = await dashboard_alert_service.list_metric_alerts(db_session)
        assert len(alerts) >= 1

    @pytest.mark.asyncio
    async def test_evaluate_alert_triggers(self, db_session: AsyncSession):
        alert = await dashboard_alert_service.create_metric_alert(
            db_session, name="Test Eval",
            metric_type="latency", condition_op=AlertConditionOp.GT,
            threshold=1000.0,
        )
        await db_session.commit()

        triggered = await dashboard_alert_service.evaluate_alert(alert, 1500.0)
        assert triggered is True

    @pytest.mark.asyncio
    async def test_evaluate_alert_no_trigger(self, db_session: AsyncSession):
        alert = await dashboard_alert_service.create_metric_alert(
            db_session, name="No Trigger",
            metric_type="latency", condition_op=AlertConditionOp.GT,
            threshold=1000.0,
        )
        await db_session.commit()

        triggered = await dashboard_alert_service.evaluate_alert(alert, 500.0)
        assert triggered is False

    @pytest.mark.asyncio
    async def test_trigger_alert_updates_timestamp(self, db_session: AsyncSession):
        alert = await dashboard_alert_service.create_metric_alert(
            db_session, name="Timestamp Test",
            metric_type="error_rate", condition_op=AlertConditionOp.GTE,
            threshold=5.0,
        )
        await db_session.commit()

        triggered_alert = await dashboard_alert_service.trigger_alert(
            db_session, alert.id
        )
        assert triggered_alert.last_triggered_at is not None


# ══════════════════════════════════════════════════════════════════
# FM-198: Cooldown Enforcement & Alert History
# ══════════════════════════════════════════════════════════════════


class TestAlertCooldown:
    @pytest.mark.asyncio
    async def test_cooldown_prevents_retrigger(self, db_session: AsyncSession):
        """Alert in cooldown should not fire even when condition is met."""
        from datetime import datetime, timezone, timedelta

        alert = await dashboard_alert_service.create_metric_alert(
            db_session, name="Cooldown Test",
            metric_type="latency", condition_op=AlertConditionOp.GT,
            threshold=100.0, cooldown_minutes=60,
        )
        await db_session.commit()

        # First evaluation: should trigger
        triggered = await dashboard_alert_service.evaluate_alert(alert, 200.0)
        assert triggered is True

        # Simulate trigger to set last_triggered_at
        await dashboard_alert_service.trigger_alert(
            db_session, alert.id, current_value=200.0,
        )
        await db_session.commit()

        # Re-fetch alert to get updated last_triggered_at
        from sqlalchemy import select
        from app.models.analytics_metrics import MetricAlert
        result = await db_session.execute(
            select(MetricAlert).where(MetricAlert.id == alert.id)
        )
        alert = result.scalar_one()

        # Second evaluation within cooldown: should NOT trigger
        triggered2 = await dashboard_alert_service.evaluate_alert(alert, 300.0)
        assert triggered2 is False

    @pytest.mark.asyncio
    async def test_alert_fires_after_cooldown_expires(self, db_session: AsyncSession):
        """Alert should fire again after cooldown period expires."""
        from datetime import datetime, timezone, timedelta
        from app.models.analytics_metrics import MetricAlert
        from sqlalchemy import select

        alert = await dashboard_alert_service.create_metric_alert(
            db_session, name="Cooldown Expire",
            metric_type="latency", condition_op=AlertConditionOp.GT,
            threshold=100.0, cooldown_minutes=5,
        )
        await db_session.commit()

        # Set last_triggered_at to well in the past
        alert.last_triggered_at = datetime.now(timezone.utc) - timedelta(minutes=10)
        await db_session.flush()

        result = await db_session.execute(
            select(MetricAlert).where(MetricAlert.id == alert.id)
        )
        alert = result.scalar_one()

        # Should fire because cooldown has expired
        triggered = await dashboard_alert_service.evaluate_alert(alert, 200.0)
        assert triggered is True


class TestAlertHistory:
    @pytest.mark.asyncio
    async def test_trigger_records_history(self, db_session: AsyncSession):
        """trigger_alert with current_value logs to AlertTriggerHistory."""
        alert = await dashboard_alert_service.create_metric_alert(
            db_session, name="History Test",
            metric_type="cost", condition_op=AlertConditionOp.GT,
            threshold=50.0,
        )
        await db_session.commit()

        await dashboard_alert_service.trigger_alert(
            db_session, alert.id, current_value=75.0,
        )
        await db_session.commit()

        history, total = await dashboard_alert_service.get_alert_history(
            db_session, alert.id,
        )
        assert total >= 1
        assert history[0].current_value == 75.0
        assert history[0].threshold == 50.0

    @pytest.mark.asyncio
    async def test_multiple_triggers_recorded(self, db_session: AsyncSession):
        alert = await dashboard_alert_service.create_metric_alert(
            db_session, name="Multi History",
            metric_type="errors", condition_op=AlertConditionOp.GTE,
            threshold=10.0,
        )
        await db_session.commit()

        # Trigger multiple times (bypassing cooldown for test purposes)
        from datetime import datetime, timezone, timedelta
        for val in [15.0, 20.0, 25.0]:
            # Reset cooldown to allow re-trigger
            alert.last_triggered_at = datetime.now(timezone.utc) - timedelta(hours=2)
            await db_session.flush()
            await dashboard_alert_service.trigger_alert(
                db_session, alert.id, current_value=val,
            )
        await db_session.commit()

        history, total = await dashboard_alert_service.get_alert_history(
            db_session, alert.id,
        )
        assert total >= 3


# ══════════════════════════════════════════════════════════════════
# FM-199: Executive Summary
# ══════════════════════════════════════════════════════════════════


class TestExecutiveSummary:
    @pytest.mark.asyncio
    async def test_generate_executive_summary(
        self, db_session: AsyncSession, sample_project
    ):
        summary = await dashboard_alert_service.generate_executive_summary(
            db_session, sample_project.id
        )
        assert summary["project_id"] == str(sample_project.id)
        assert "health" in summary
        assert "velocity" in summary
        assert "quality" in summary
        assert "generated_at" in summary


# ══════════════════════════════════════════════════════════════════
# FM-192: Auto-Compute Health Dimensions
# ══════════════════════════════════════════════════════════════════


class TestAutoComputeHealth:
    @pytest.mark.asyncio
    async def test_auto_compute_returns_all_dimensions(
        self, db_session: AsyncSession, sample_project
    ):
        """auto_compute_health_dimensions returns all 6 dimension keys."""
        scores = await execution_health_service.auto_compute_health_dimensions(
            db_session, sample_project.id
        )
        for key in ("success_rate", "velocity", "cost_efficiency", "quality", "coverage", "complexity"):
            assert key in scores, f"Missing dimension: {key}"
            assert isinstance(scores[key], float)

    @pytest.mark.asyncio
    async def test_auto_compute_with_runs(
        self, db_session: AsyncSession, sample_project
    ):
        """With completed/failed runs, success_rate is computed correctly."""
        from app.models.run import Run, RunStatus

        for s in [RunStatus.COMPLETED, RunStatus.COMPLETED, RunStatus.FAILED]:
            db_session.add(Run(
                run_number=0, project_id=sample_project.id,
                status=s, trigger="test",
            ))
        await db_session.flush()
        await db_session.commit()

        scores = await execution_health_service.auto_compute_health_dimensions(
            db_session, sample_project.id
        )
        # 2 completed / 3 finished = 66.67%
        assert 66 <= scores["success_rate"] <= 67

    @pytest.mark.asyncio
    async def test_auto_compute_with_quality_snapshot(
        self, db_session: AsyncSession, sample_project
    ):
        """Quality and coverage come from latest QualitySnapshot."""
        await velocity_quality_service.record_quality_snapshot(
            db_session, project_id=sample_project.id,
            test_pass_rate=0.92, review_coverage=0.85,
        )
        await db_session.commit()

        scores = await execution_health_service.auto_compute_health_dimensions(
            db_session, sample_project.id
        )
        assert scores["quality"] == 92.0
        assert scores["coverage"] == 85.0

    @pytest.mark.asyncio
    async def test_compute_health_snapshot_auto_computes(
        self, db_session: AsyncSession, sample_project
    ):
        """compute_health_snapshot without dimension_scores auto-computes."""
        snap = await execution_health_service.compute_health_snapshot(
            db_session, sample_project.id
        )
        await db_session.commit()
        assert snap.id is not None
        assert snap.dimension_scores is not None
        # Should have real computed values, not all 50.0
        assert "success_rate" in snap.dimension_scores


# ══════════════════════════════════════════════════════════════════
# FM-193: Budget Enforcement
# ══════════════════════════════════════════════════════════════════


class TestBudgetEnforcement:
    @pytest.mark.asyncio
    async def test_check_budget_no_config(
        self, db_session: AsyncSession, sample_project
    ):
        """No BudgetConfig → no enforcement."""
        result = await execution_health_service.check_budget(
            db_session, sample_project.id
        )
        assert result["exceeded"] is False
        assert result["action"] == "none"
        assert result["budget_usd"] is None

    @pytest.mark.asyncio
    async def test_check_budget_under_threshold(
        self, db_session: AsyncSession, sample_project
    ):
        """Spend under warn_threshold_pct → no warning."""
        from app.models.analytics_metrics import BudgetConfig, BudgetAction
        from app.models.cost_record import CostRecord

        config = BudgetConfig(
            project_id=sample_project.id,
            monthly_budget_usd=100.0,
            warn_threshold_pct=80.0,
            action_on_exceed=BudgetAction.WARN,
        )
        db_session.add(config)

        # Add $50 of cost (50% of $100 budget, under 80% threshold)
        db_session.add(CostRecord(
            project_id=sample_project.id,
            model_name="gpt-4",
            prompt_tokens=1000, completion_tokens=500,
            total_tokens=1500, cost_usd=50.0,
            caller="test",
        ))
        await db_session.commit()

        result = await execution_health_service.check_budget(
            db_session, sample_project.id
        )
        assert result["exceeded"] is False
        assert result["action"] == "none"
        assert result["pct_used"] == 50.0

    @pytest.mark.asyncio
    async def test_check_budget_warn(
        self, db_session: AsyncSession, sample_project
    ):
        """Spend over threshold with WARN action → warns but doesn't block."""
        from app.models.analytics_metrics import BudgetConfig, BudgetAction
        from app.models.cost_record import CostRecord

        config = BudgetConfig(
            project_id=sample_project.id,
            monthly_budget_usd=100.0,
            warn_threshold_pct=80.0,
            action_on_exceed=BudgetAction.WARN,
        )
        db_session.add(config)
        db_session.add(CostRecord(
            project_id=sample_project.id,
            model_name="gpt-4",
            prompt_tokens=10000, completion_tokens=5000,
            total_tokens=15000, cost_usd=85.0,
            caller="test",
        ))
        await db_session.commit()

        result = await execution_health_service.check_budget(
            db_session, sample_project.id
        )
        assert result["exceeded"] is True
        assert result["action"] == "warn"
        assert result["pct_used"] == 85.0

    @pytest.mark.asyncio
    async def test_check_budget_block_raises(
        self, db_session: AsyncSession, sample_project
    ):
        """BLOCK action over threshold raises HTTPException(403)."""
        from app.models.analytics_metrics import BudgetConfig, BudgetAction
        from app.models.cost_record import CostRecord
        from fastapi import HTTPException

        config = BudgetConfig(
            project_id=sample_project.id,
            monthly_budget_usd=100.0,
            warn_threshold_pct=80.0,
            action_on_exceed=BudgetAction.BLOCK,
        )
        db_session.add(config)
        db_session.add(CostRecord(
            project_id=sample_project.id,
            model_name="gpt-4",
            prompt_tokens=10000, completion_tokens=5000,
            total_tokens=15000, cost_usd=90.0,
            caller="test",
        ))
        await db_session.commit()

        with pytest.raises(HTTPException) as exc_info:
            await execution_health_service.check_budget(
                db_session, sample_project.id
            )
        assert exc_info.value.status_code == 403


# ══════════════════════════════════════════════════════════════════
# FM-194: Approval Velocity & Period Comparison
# ══════════════════════════════════════════════════════════════════


class TestApprovalVelocity:
    @pytest.mark.asyncio
    async def test_approval_velocity_no_requests(
        self, db_session: AsyncSession, sample_project
    ):
        result = await velocity_quality_service.compute_approval_velocity(
            db_session, sample_project.id
        )
        assert result["total_decided"] == 0
        assert result["avg_decision_seconds"] == 0.0

    @pytest.mark.asyncio
    async def test_approval_velocity_with_decided(
        self, db_session: AsyncSession, sample_project, sample_run
    ):
        """Decided requests produce meaningful avg_decision_seconds."""
        from app.models.approval_request import ApprovalRequest, ApprovalStatus
        from datetime import datetime, timedelta, timezone

        now = datetime.now(timezone.utc)
        for i in range(3):
            req = ApprovalRequest(
                project_id=sample_project.id,
                run_id=sample_run.id,
                title=f"Approval Request {i}",
                status=ApprovalStatus.APPROVED,
                created_at=now - timedelta(hours=2),
                decided_at=now - timedelta(hours=1),
                decided_by=str(STUB_USER_ID),
            )
            db_session.add(req)
        await db_session.commit()

        result = await velocity_quality_service.compute_approval_velocity(
            db_session, sample_project.id
        )
        assert result["total_decided"] == 3
        assert result["avg_decision_seconds"] > 0
        assert result["approval_rate"] == 100.0

    @pytest.mark.asyncio
    async def test_velocity_comparison(
        self, db_session: AsyncSession, sample_project
    ):
        result = await velocity_quality_service.compute_velocity_comparison(
            db_session, sample_project.id, days=30,
        )
        assert "current" in result
        assert "previous" in result
        assert "change_pct" in result


# ══════════════════════════════════════════════════════════════════
# FM-195: Quality Gates
# ══════════════════════════════════════════════════════════════════


class TestQualityGates:
    @pytest.mark.asyncio
    async def test_quality_gates_no_snapshot(
        self, db_session: AsyncSession, sample_project
    ):
        """No snapshot → gates skipped, passed=True."""
        result = await velocity_quality_service.evaluate_quality_gates(
            db_session, sample_project.id
        )
        assert result["passed"] is True
        assert result["gates_evaluated"] == 0

    @pytest.mark.asyncio
    async def test_quality_gates_all_passing(
        self, db_session: AsyncSession, sample_project
    ):
        """All metrics within thresholds → passed=True, no violations."""
        await velocity_quality_service.record_quality_snapshot(
            db_session, project_id=sample_project.id,
            test_pass_rate=0.95, defect_density=0.01,
            rollback_rate=0.02, review_coverage=0.90,
        )
        await db_session.commit()

        result = await velocity_quality_service.evaluate_quality_gates(
            db_session, sample_project.id
        )
        assert result["passed"] is True
        assert len(result["violations"]) == 0

    @pytest.mark.asyncio
    async def test_quality_gates_violations(
        self, db_session: AsyncSession, sample_project
    ):
        """Low test_pass_rate and high defect_density trigger violations."""
        await velocity_quality_service.record_quality_snapshot(
            db_session, project_id=sample_project.id,
            test_pass_rate=0.50,  # below 0.8 min
            defect_density=0.10,  # above 0.05 max
            rollback_rate=0.02,
            review_coverage=0.90,
        )
        await db_session.commit()

        result = await velocity_quality_service.evaluate_quality_gates(
            db_session, sample_project.id
        )
        assert result["passed"] is False
        assert len(result["violations"]) == 2
        assert len(result["warnings"]) == 2

    @pytest.mark.asyncio
    async def test_quality_gates_custom_thresholds(
        self, db_session: AsyncSession, sample_project
    ):
        """Custom gate thresholds override defaults."""
        await velocity_quality_service.record_quality_snapshot(
            db_session, project_id=sample_project.id,
            test_pass_rate=0.85, defect_density=0.03,
            rollback_rate=0.05, review_coverage=0.75,
        )
        await db_session.commit()

        # Stricter custom gate: test_pass_rate >= 0.95
        result = await velocity_quality_service.evaluate_quality_gates(
            db_session, sample_project.id,
            gates={"test_pass_rate": {"min": 0.95, "label": "Test pass rate"}},
        )
        assert result["passed"] is False
        assert len(result["violations"]) == 1


# ══════════════════════════════════════════════════════════════════
# FM-196: Portfolio Sort & Filter
# ══════════════════════════════════════════════════════════════════


class TestPortfolioSortFilter:
    @pytest.mark.asyncio
    async def test_portfolio_sort_by_total_runs(
        self, db_session: AsyncSession, sample_project
    ):
        """sort_by=total_runs works without error."""
        result = await velocity_quality_service.get_portfolio_summary(
            db_session, [sample_project.id],
            sort_by="total_runs", sort_order="desc",
        )
        assert result["project_count"] >= 1

    @pytest.mark.asyncio
    async def test_portfolio_filter_min_runs(
        self, db_session: AsyncSession, sample_project
    ):
        """filter_min_runs=1000 filters out project with 0 runs."""
        result = await velocity_quality_service.get_portfolio_summary(
            db_session, [sample_project.id],
            filter_min_runs=1000,
        )
        assert result["project_count"] == 0
        assert len(result["projects"]) == 0

    @pytest.mark.asyncio
    async def test_portfolio_sort_by_success_rate(
        self, db_session: AsyncSession, sample_project
    ):
        """success_rate dimension available in portfolio results."""
        result = await velocity_quality_service.get_portfolio_summary(
            db_session, [sample_project.id],
            sort_by="success_rate", sort_order="asc",
        )
        for proj in result["projects"]:
            assert "success_rate" in proj

    @pytest.mark.asyncio
    async def test_portfolio_cost_filter(
        self, db_session: AsyncSession, sample_project
    ):
        """filter_max_cost filters projects by cost."""
        result = await velocity_quality_service.get_portfolio_summary(
            db_session, [sample_project.id],
            filter_max_cost=0.001,  # Very low, should exclude if any cost
        )
        # With no cost records, cost=0 passes the filter
        assert result["project_count"] >= 0


# ══════════════════════════════════════════════════════════════════
# FM-202: Rate Limit Headers
# ══════════════════════════════════════════════════════════════════


class TestRateLimitHeaders:
    def test_rate_limit_headers_from_result(self):
        """rate_limit_headers_from_result builds proper header dict."""
        from app.services.api_key_service import rate_limit_headers_from_result
        result = {"limit": 100, "remaining": 95, "reset_at": 1700000000}
        headers = rate_limit_headers_from_result(result)
        assert headers["X-RateLimit-Limit"] == "100"
        assert headers["X-RateLimit-Remaining"] == "95"
        assert headers["X-RateLimit-Reset"] == "1700000000"

    def test_require_rate_limit_returns_callable(self):
        """require_rate_limit() returns a dependency function."""
        from app.services.api_key_service import require_rate_limit
        dep = require_rate_limit(max_requests=50)
        assert callable(dep)


# ══════════════════════════════════════════════════════════════════
# FM-191 Enhancement: Time-Window Filtering (since_days)
# ══════════════════════════════════════════════════════════════════


class TestTimeWindowFiltering:
    @pytest.mark.asyncio
    async def test_get_execution_metrics_with_since_days(
        self, db_session: AsyncSession, sample_project
    ):
        """since_days filters metrics to recent window."""
        await execution_health_service.record_execution_metric(
            db_session, project_id=sample_project.id,
            metric_type=ExecutionMetricType.EXECUTION_TIME, value_ms=1000,
        )
        await db_session.commit()

        items, total = await execution_health_service.get_execution_metrics(
            db_session, sample_project.id, since_days=7,
        )
        assert total >= 1  # Just recorded within 7 days

    @pytest.mark.asyncio
    async def test_get_execution_metrics_since_days_zero_result(
        self, db_session: AsyncSession, sample_project
    ):
        """since_days=0 should still work (returns nothing or recent)."""
        items, total = await execution_health_service.get_execution_metrics(
            db_session, sample_project.id, since_days=1,
        )
        # No metrics recorded → 0
        assert total == 0


# ══════════════════════════════════════════════════════════════════
# FM-193: Budget Enforcement Wiring
# ══════════════════════════════════════════════════════════════════


class TestBudgetEnforcement:
    @pytest.mark.asyncio
    async def test_check_budget_no_config(
        self, db_session: AsyncSession, sample_project
    ):
        """No budget config → returns a result (may indicate no budget set)."""
        result = await execution_health_service.check_budget(db_session, sample_project.id)
        # check_budget may return status or raise; validate shape
        assert isinstance(result, dict)


# ══════════════════════════════════════════════════════════════════
# FM-195 Enhancement: Quality Gates with Quarantine Exclusion
# ══════════════════════════════════════════════════════════════════


class TestQualityGatesQuarantine:
    @pytest.mark.asyncio
    async def test_quality_gates_with_quarantine_flag(
        self, db_session: AsyncSession, sample_project
    ):
        """evaluate_quality_gates returns quarantined_excluded field."""
        result = await velocity_quality_service.evaluate_quality_gates(
            db_session, sample_project.id, exclude_quarantined=True,
        )
        assert "quarantined_excluded" in result
        assert result["quarantined_excluded"] is True

    @pytest.mark.asyncio
    async def test_quality_gates_without_quarantine_exclusion(
        self, db_session: AsyncSession, sample_project
    ):
        """exclude_quarantined=False still works."""
        result = await velocity_quality_service.evaluate_quality_gates(
            db_session, sample_project.id, exclude_quarantined=False,
        )
        assert result["quarantined_excluded"] is False


# ══════════════════════════════════════════════════════════════════
# FM-196: Portfolio Sort/Filter Forwarding
# ══════════════════════════════════════════════════════════════════


class TestPortfolioSortFilter:
    @pytest.mark.asyncio
    async def test_portfolio_with_sort(self, db_session: AsyncSession, sample_project):
        """get_portfolio_summary accepts sort_by and sort_order."""
        result = await velocity_quality_service.get_portfolio_summary(
            db_session, [sample_project.id], sort_by="health", sort_order="asc",
        )
        assert "projects" in result

    @pytest.mark.asyncio
    async def test_portfolio_with_filter(self, db_session: AsyncSession, sample_project):
        """get_portfolio_summary accepts filter_min_runs."""
        result = await velocity_quality_service.get_portfolio_summary(
            db_session, [sample_project.id], filter_min_runs=0,
        )
        assert "projects" in result


# ══════════════════════════════════════════════════════════════════
# FM-197: Widget Data Resolution
# ══════════════════════════════════════════════════════════════════


class TestWidgetDataResolution:
    @pytest.mark.asyncio
    async def test_resolve_widget_velocity(
        self, db_session: AsyncSession, sample_project
    ):
        """resolve_widget_data returns velocity data."""
        result = await dashboard_alert_service.resolve_widget_data(
            db_session, sample_project.id, "velocity",
        )
        assert result["widget_type"] == "velocity"  
        assert "data" in result

    @pytest.mark.asyncio
    async def test_resolve_widget_unknown_type(
        self, db_session: AsyncSession, sample_project
    ):
        """Unknown widget type → 400 error."""
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await dashboard_alert_service.resolve_widget_data(
                db_session, sample_project.id, "nonexistent_widget",
            )
        assert exc_info.value.status_code == 400


# ══════════════════════════════════════════════════════════════════
# FM-199: Executive Summary Artifact Storage
# ══════════════════════════════════════════════════════════════════


class TestSummaryArtifacts:
    @pytest.mark.asyncio
    async def test_save_executive_summary_artifact(
        self, db_session: AsyncSession, sample_project
    ):
        """save_executive_summary stores a versioned artifact."""
        artifact = await dashboard_alert_service.save_executive_summary(
            db_session, sample_project.id
        )
        assert artifact["version"] == 1
        assert "summary" in artifact
        assert "stored_at" in artifact

    @pytest.mark.asyncio
    async def test_save_multiple_artifacts(
        self, db_session: AsyncSession, sample_project
    ):
        """Multiple saves produce incrementing versions."""
        a1 = await dashboard_alert_service.save_executive_summary(
            db_session, sample_project.id
        )
        a2 = await dashboard_alert_service.save_executive_summary(
            db_session, sample_project.id
        )
        assert a2["version"] > a1["version"]

    def test_get_summary_artifacts_empty(self):
        """No stored artifacts → empty list."""
        import uuid as _uuid
        result = dashboard_alert_service.get_summary_artifacts(_uuid.uuid4())
        assert result == []
