"""Tests for FM-046 through FM-050 features.

FM-046: Run Lifecycle Manager (health checks, auto-complete, auto-fail)
FM-047: Cost & Token Tracking
FM-048: Governance Policy Engine
FM-049: Audit Trail Export & Compliance
FM-050: Trust Scoring & Risk Assessment
"""

import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.run import Run, RunStatus
from app.models.task import Task, TaskStatus
from app.models.execution_event import ExecutionEvent, EventType
from app.models.cost_record import CostRecord
from app.models.governance_policy import GovernancePolicy, PolicyTrigger, PolicyAction
from app.models.trust_score import TrustScore, RiskLevel, EntityType


# ══════════════════════════════════════════════════════════════════
# FM-046: Run Lifecycle Manager
# ══════════════════════════════════════════════════════════════════


class TestRunHealthCheck:
    """Test run health computation."""

    @pytest.mark.asyncio
    async def test_healthy_running_run(
        self, db_session: AsyncSession, sample_project
    ):
        """A running run with no failures should be healthy."""
        from app.services import run_lifecycle_service

        run = Run(run_number=10, project_id=sample_project.id, status=RunStatus.RUNNING)
        db_session.add(run)
        await db_session.flush()

        task = Task(
            title="Build feature", task_type="coding",
            status=TaskStatus.RUNNING, run_id=run.id,
        )
        db_session.add(task)
        await db_session.flush()

        # Add a recent event so it's not "stuck"
        event = ExecutionEvent(
            event_type=EventType.TASK_CLAIMED,
            summary="Task claimed",
            project_id=sample_project.id,
            run_id=run.id,
        )
        db_session.add(event)
        await db_session.flush()

        health = await run_lifecycle_service.get_run_health(db_session, run.id)
        assert health["health"] == "healthy"
        assert health["status"] == "running"
        assert health["progress"] == 0.0

    @pytest.mark.asyncio
    async def test_completed_run_health(
        self, db_session: AsyncSession, sample_project
    ):
        """A completed run should return completed health."""
        from app.services import run_lifecycle_service

        run = Run(run_number=11, project_id=sample_project.id, status=RunStatus.COMPLETED)
        db_session.add(run)
        await db_session.flush()

        health = await run_lifecycle_service.get_run_health(db_session, run.id)
        assert health["health"] == "completed"
        assert health["progress"] == 1.0

    @pytest.mark.asyncio
    async def test_degraded_run_with_failures(
        self, db_session: AsyncSession, sample_project
    ):
        """A run with some failures but active tasks should be degraded."""
        from app.services import run_lifecycle_service

        run = Run(run_number=12, project_id=sample_project.id, status=RunStatus.RUNNING)
        db_session.add(run)
        await db_session.flush()

        t1 = Task(title="T1", task_type="coding", status=TaskStatus.COMPLETED, run_id=run.id)
        t2 = Task(title="T2", task_type="coding", status=TaskStatus.FAILED, run_id=run.id)
        t3 = Task(title="T3", task_type="coding", status=TaskStatus.RUNNING, run_id=run.id)
        db_session.add_all([t1, t2, t3])
        await db_session.flush()

        event = ExecutionEvent(
            event_type=EventType.TASK_COMPLETED, summary="T1 done",
            project_id=sample_project.id, run_id=run.id,
        )
        db_session.add(event)
        await db_session.flush()

        health = await run_lifecycle_service.get_run_health(db_session, run.id)
        assert health["health"] == "degraded"

    @pytest.mark.asyncio
    async def test_not_found_run(self, db_session: AsyncSession):
        """Health check for nonexistent run returns error."""
        from app.services import run_lifecycle_service

        health = await run_lifecycle_service.get_run_health(
            db_session, uuid.uuid4()
        )
        assert "error" in health


class TestAutoComplete:
    """Test run auto-completion logic."""

    @pytest.mark.asyncio
    async def test_auto_complete_all_completed(
        self, db_session: AsyncSession, sample_project
    ):
        """Run with all completed tasks should auto-complete."""
        from app.services import run_lifecycle_service

        run = Run(run_number=20, project_id=sample_project.id, status=RunStatus.RUNNING)
        db_session.add(run)
        await db_session.flush()

        for i in range(3):
            db_session.add(Task(
                title=f"Task {i}", task_type="coding",
                status=TaskStatus.COMPLETED, run_id=run.id,
            ))
        await db_session.flush()

        result = await run_lifecycle_service.try_auto_complete_run(db_session, run.id)
        assert result["completed"] is True
        await db_session.refresh(run)
        assert run.status == RunStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_no_auto_complete_with_running(
        self, db_session: AsyncSession, sample_project
    ):
        """Run with running tasks should not auto-complete."""
        from app.services import run_lifecycle_service

        run = Run(run_number=21, project_id=sample_project.id, status=RunStatus.RUNNING)
        db_session.add(run)
        await db_session.flush()

        db_session.add(Task(
            title="Done", task_type="coding",
            status=TaskStatus.COMPLETED, run_id=run.id,
        ))
        db_session.add(Task(
            title="Still going", task_type="coding",
            status=TaskStatus.RUNNING, run_id=run.id,
        ))
        await db_session.flush()

        result = await run_lifecycle_service.try_auto_complete_run(db_session, run.id)
        assert result["completed"] is False


class TestAutoFail:
    """Test run auto-fail logic."""

    @pytest.mark.asyncio
    async def test_auto_fail_exhausted_blocking(
        self, db_session: AsyncSession, sample_project
    ):
        """Run with exhausted-retry blocking failure should auto-fail."""
        from app.services import run_lifecycle_service

        run = Run(run_number=30, project_id=sample_project.id, status=RunStatus.RUNNING)
        db_session.add(run)
        await db_session.flush()

        t1 = Task(
            title="Failed blocker", task_type="coding",
            status=TaskStatus.FAILED, run_id=run.id,
            retry_count=3, max_retries=3,
        )
        db_session.add(t1)
        await db_session.flush()

        t2 = Task(
            title="Blocked downstream", task_type="coding",
            status=TaskStatus.BLOCKED, run_id=run.id,
            depends_on=[str(t1.id)],
        )
        db_session.add(t2)
        await db_session.flush()

        result = await run_lifecycle_service.try_auto_fail_run(db_session, run.id)
        assert result["failed"] is True
        await db_session.refresh(run)
        assert run.status == RunStatus.FAILED

    @pytest.mark.asyncio
    async def test_no_auto_fail_with_active_tasks(
        self, db_session: AsyncSession, sample_project
    ):
        """Run with active tasks should not auto-fail."""
        from app.services import run_lifecycle_service

        run = Run(run_number=31, project_id=sample_project.id, status=RunStatus.RUNNING)
        db_session.add(run)
        await db_session.flush()

        db_session.add(Task(
            title="Active", task_type="coding",
            status=TaskStatus.RUNNING, run_id=run.id,
        ))
        await db_session.flush()

        result = await run_lifecycle_service.try_auto_fail_run(db_session, run.id)
        assert result["failed"] is False


class TestLifecycleAPI:
    """Test lifecycle API endpoints."""

    @pytest.mark.asyncio
    async def test_health_endpoint(
        self, client: AsyncClient, sample_run
    ):
        resp = await client.get(f"/lifecycle/runs/{sample_run.id}/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "health" in data
        assert "progress" in data

    @pytest.mark.asyncio
    async def test_health_not_found(self, client: AsyncClient):
        resp = await client.get(f"/lifecycle/runs/{uuid.uuid4()}/health")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_scan_all_runs(self, client: AsyncClient):
        resp = await client.get("/lifecycle/runs/health/scan")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


# ══════════════════════════════════════════════════════════════════
# FM-047: Cost & Token Tracking
# ══════════════════════════════════════════════════════════════════


class TestCostTracking:
    """Test cost recording and aggregation."""

    @pytest.mark.asyncio
    async def test_record_usage(
        self, db_session: AsyncSession, sample_project, sample_run
    ):
        from app.services import cost_tracking_service

        record = await cost_tracking_service.record_usage(
            db_session,
            model_name="gpt-4o",
            prompt_tokens=1000,
            completion_tokens=500,
            project_id=sample_project.id,
            run_id=sample_run.id,
            caller="planner",
        )
        assert record.total_tokens == 1500
        assert record.cost_usd > 0

    @pytest.mark.asyncio
    async def test_estimate_cost_known_model(self):
        from app.services.cost_tracking_service import estimate_cost

        cost = estimate_cost("gpt-4o", 1000, 500)
        assert cost > 0
        # gpt-4o: 1000 * 2.5/1M + 500 * 10/1M = 0.0025 + 0.005 = 0.0075
        assert abs(cost - 0.0075) < 0.001

    @pytest.mark.asyncio
    async def test_estimate_cost_unknown_model(self):
        from app.services.cost_tracking_service import estimate_cost

        cost = estimate_cost("unknown-model", 1000, 500)
        assert cost > 0  # Falls back to default rates

    @pytest.mark.asyncio
    async def test_run_cost_summary(
        self, db_session: AsyncSession, sample_project, sample_run
    ):
        from app.services import cost_tracking_service

        await cost_tracking_service.record_usage(
            db_session, model_name="gpt-4o",
            prompt_tokens=500, completion_tokens=200,
            run_id=sample_run.id, project_id=sample_project.id,
            caller="planner",
        )
        await cost_tracking_service.record_usage(
            db_session, model_name="gpt-4o",
            prompt_tokens=300, completion_tokens=100,
            run_id=sample_run.id, project_id=sample_project.id,
            caller="chat",
        )

        summary = await cost_tracking_service.get_run_cost_summary(
            db_session, sample_run.id
        )
        assert summary["call_count"] == 2
        assert summary["total_tokens"] == 1100
        assert summary["total_cost_usd"] > 0

    @pytest.mark.asyncio
    async def test_cost_breakdown_by_model(
        self, db_session: AsyncSession, sample_project, sample_run
    ):
        from app.services import cost_tracking_service

        await cost_tracking_service.record_usage(
            db_session, model_name="gpt-4o",
            prompt_tokens=100, completion_tokens=50,
            run_id=sample_run.id, caller="planner",
        )
        await cost_tracking_service.record_usage(
            db_session, model_name="gpt-4o-mini",
            prompt_tokens=200, completion_tokens=100,
            run_id=sample_run.id, caller="chat",
        )

        breakdown = await cost_tracking_service.get_cost_breakdown_by_model(
            db_session, run_id=sample_run.id
        )
        assert len(breakdown) == 2
        models = {b["model_name"] for b in breakdown}
        assert "gpt-4o" in models
        assert "gpt-4o-mini" in models


class TestCostAPI:
    """Test cost API endpoints."""

    @pytest.mark.asyncio
    async def test_run_cost_summary_endpoint(
        self, client: AsyncClient, sample_run
    ):
        resp = await client.get(f"/costs/runs/{sample_run.id}/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_cost_usd" in data

    @pytest.mark.asyncio
    async def test_list_cost_records(self, client: AsyncClient):
        resp = await client.get("/costs")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_cost_breakdown_endpoint(self, client: AsyncClient):
        resp = await client.get("/costs/breakdown")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


# ══════════════════════════════════════════════════════════════════
# FM-048: Governance Policy Engine
# ══════════════════════════════════════════════════════════════════


class TestGovernanceService:
    """Test governance policy CRUD and evaluation."""

    @pytest.mark.asyncio
    async def test_create_policy(
        self, db_session: AsyncSession, sample_project
    ):
        from app.services import governance_service

        policy = await governance_service.create_policy(
            db_session,
            name="Architecture Approval",
            trigger=PolicyTrigger.TASK_TYPE,
            action=PolicyAction.REQUIRE_APPROVAL,
            rules={"task_types": ["architecture"]},
            project_id=sample_project.id,
        )
        assert policy.name == "Architecture Approval"
        assert policy.enabled is True

    @pytest.mark.asyncio
    async def test_evaluate_matching_policy(
        self, db_session: AsyncSession, sample_project
    ):
        from app.services import governance_service

        await governance_service.create_policy(
            db_session,
            name="Arch Gate",
            trigger=PolicyTrigger.TASK_TYPE,
            action=PolicyAction.REQUIRE_APPROVAL,
            rules={"task_types": ["architecture"]},
            project_id=sample_project.id,
        )

        action = await governance_service.evaluate_task_approval(
            db_session, task_type="architecture", project_id=sample_project.id
        )
        assert action == PolicyAction.REQUIRE_APPROVAL

    @pytest.mark.asyncio
    async def test_evaluate_no_matching_policy(
        self, db_session: AsyncSession, sample_project
    ):
        from app.services import governance_service

        action = await governance_service.evaluate_task_approval(
            db_session, task_type="coding", project_id=sample_project.id
        )
        assert action == PolicyAction.AUTO_APPROVE

    @pytest.mark.asyncio
    async def test_cost_threshold_policy(
        self, db_session: AsyncSession, sample_project
    ):
        from app.services import governance_service

        await governance_service.create_policy(
            db_session,
            name="Budget Guard",
            trigger=PolicyTrigger.COST_THRESHOLD,
            action=PolicyAction.REQUIRE_APPROVAL,
            rules={"cost_threshold_usd": 10.0},
            project_id=sample_project.id,
        )

        action = await governance_service.evaluate_cost_threshold(
            db_session, current_cost_usd=15.0, project_id=sample_project.id
        )
        assert action == PolicyAction.REQUIRE_APPROVAL

        action2 = await governance_service.evaluate_cost_threshold(
            db_session, current_cost_usd=5.0, project_id=sample_project.id
        )
        assert action2 == PolicyAction.AUTO_APPROVE

    @pytest.mark.asyncio
    async def test_delete_policy(
        self, db_session: AsyncSession, sample_project
    ):
        from app.services import governance_service

        policy = await governance_service.create_policy(
            db_session,
            name="Temp Policy",
            trigger=PolicyTrigger.TASK_TYPE,
            action=PolicyAction.NOTIFY,
            rules={"task_types": ["testing"]},
        )
        deleted = await governance_service.delete_policy(db_session, policy.id)
        assert deleted is True

    @pytest.mark.asyncio
    async def test_seed_default_policies(
        self, db_session: AsyncSession
    ):
        from app.services import governance_service

        policies = await governance_service.seed_default_policies(db_session)
        assert len(policies) == 2
        names = {p.name for p in policies}
        assert "Architecture Review Gate" in names
        assert "Code Review Gate" in names


class TestGovernanceAPI:
    """Test governance API endpoints."""

    @pytest.mark.asyncio
    async def test_create_policy_endpoint(
        self, client: AsyncClient, sample_project
    ):
        resp = await client.post("/governance/policies", json={
            "name": "Test Policy",
            "trigger": "task_type",
            "action": "require_approval",
            "rules": {"task_types": ["deploy"]},
            "project_id": str(sample_project.id),
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Test Policy"

    @pytest.mark.asyncio
    async def test_list_policies_endpoint(self, client: AsyncClient):
        resp = await client.get("/governance/policies")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data

    @pytest.mark.asyncio
    async def test_evaluate_task_endpoint(
        self, client: AsyncClient, sample_project
    ):
        resp = await client.get(
            "/governance/evaluate/task",
            params={"task_type": "coding", "project_id": str(sample_project.id)},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "action" in data

    @pytest.mark.asyncio
    async def test_seed_defaults_endpoint(self, client: AsyncClient):
        resp = await client.post("/governance/seed-defaults")
        assert resp.status_code == 200
        data = resp.json()
        assert data["seeded"] >= 0


# ══════════════════════════════════════════════════════════════════
# FM-049: Audit Trail Export & Compliance
# ══════════════════════════════════════════════════════════════════


class TestAuditExport:
    """Test audit export service."""

    @pytest.mark.asyncio
    async def test_export_json_empty(self, db_session: AsyncSession):
        from app.services import audit_export_service

        result = await audit_export_service.export_events_json(db_session)
        assert result["export_metadata"]["total_events"] == 0
        assert result["events"] == []

    @pytest.mark.asyncio
    async def test_export_json_with_events(
        self, db_session: AsyncSession, sample_project, sample_run
    ):
        from app.services import audit_export_service, event_service

        await event_service.emit_event(
            db_session,
            event_type=EventType.RUN_STARTED,
            summary="Run started",
            project_id=sample_project.id,
            run_id=sample_run.id,
        )
        await event_service.emit_event(
            db_session,
            event_type=EventType.TASK_CLAIMED,
            summary="Task claimed",
            project_id=sample_project.id,
            run_id=sample_run.id,
        )

        result = await audit_export_service.export_events_json(
            db_session, run_id=sample_run.id
        )
        assert result["export_metadata"]["total_events"] == 2
        assert len(result["events"]) == 2

    @pytest.mark.asyncio
    async def test_export_csv(
        self, db_session: AsyncSession, sample_project, sample_run
    ):
        from app.services import audit_export_service, event_service

        await event_service.emit_event(
            db_session,
            event_type=EventType.RUN_STARTED,
            summary="Run started",
            project_id=sample_project.id,
            run_id=sample_run.id,
        )

        csv_content = await audit_export_service.export_events_csv(
            db_session, run_id=sample_run.id
        )
        assert "id,event_type,summary" in csv_content
        assert "run_started" in csv_content

    @pytest.mark.asyncio
    async def test_audit_summary(
        self, db_session: AsyncSession, sample_project, sample_run
    ):
        from app.services import audit_export_service, event_service

        await event_service.emit_event(
            db_session,
            event_type=EventType.RUN_STARTED,
            summary="Run started",
            project_id=sample_project.id,
            run_id=sample_run.id,
        )
        await event_service.emit_event(
            db_session,
            event_type=EventType.TASK_CLAIMED,
            summary="Claimed",
            project_id=sample_project.id,
            run_id=sample_run.id,
        )

        summary = await audit_export_service.get_audit_summary(
            db_session, run_id=sample_run.id
        )
        assert summary["total_events"] == 2
        assert "run_started" in summary["event_type_breakdown"]


class TestAuditAPI:
    """Test audit export API endpoints."""

    @pytest.mark.asyncio
    async def test_export_json_endpoint(self, client: AsyncClient):
        resp = await client.get("/audit/export/json")
        assert resp.status_code == 200
        data = resp.json()
        assert "export_metadata" in data
        assert "events" in data

    @pytest.mark.asyncio
    async def test_export_csv_endpoint(self, client: AsyncClient):
        resp = await client.get("/audit/export/csv")
        assert resp.status_code == 200
        assert "text/csv" in resp.headers.get("content-type", "")

    @pytest.mark.asyncio
    async def test_audit_summary_endpoint(self, client: AsyncClient):
        resp = await client.get("/audit/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_events" in data


# ══════════════════════════════════════════════════════════════════
# FM-050: Trust Scoring & Risk Assessment
# ══════════════════════════════════════════════════════════════════


class TestTrustScoring:
    """Test trust scoring heuristics."""

    @pytest.mark.asyncio
    async def test_assess_completed_task(
        self, db_session: AsyncSession, sample_run
    ):
        from app.services import trust_scoring_service

        task = Task(
            title="Complete task", task_type="coding",
            status=TaskStatus.COMPLETED, run_id=sample_run.id,
            assigned_agent_slug="coder",
        )
        db_session.add(task)
        await db_session.flush()

        ts = await trust_scoring_service.assess_task(db_session, task.id)
        assert ts.trust_score > 0.7
        assert ts.risk_level == RiskLevel.LOW

    @pytest.mark.asyncio
    async def test_assess_failed_task_high_retries(
        self, db_session: AsyncSession, sample_run
    ):
        from app.services import trust_scoring_service

        task = Task(
            title="Failed task", task_type="coding",
            status=TaskStatus.FAILED, run_id=sample_run.id,
            retry_count=3, max_retries=3,
            error_message="Something went wrong",
        )
        db_session.add(task)
        await db_session.flush()

        ts = await trust_scoring_service.assess_task(db_session, task.id)
        assert ts.trust_score < 0.3
        assert ts.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL)

    @pytest.mark.asyncio
    async def test_assess_run(
        self, db_session: AsyncSession, sample_project
    ):
        from app.services import trust_scoring_service

        run = Run(run_number=50, project_id=sample_project.id, status=RunStatus.RUNNING)
        db_session.add(run)
        await db_session.flush()

        for i in range(4):
            db_session.add(Task(
                title=f"Task {i}", task_type="coding",
                status=TaskStatus.COMPLETED, run_id=run.id,
            ))
        db_session.add(Task(
            title="Failed task", task_type="coding",
            status=TaskStatus.FAILED, run_id=run.id,
        ))
        await db_session.flush()

        ts = await trust_scoring_service.assess_run(db_session, run.id)
        assert 0.3 < ts.trust_score < 0.9  # Mixed: mostly complete but has failure

    @pytest.mark.asyncio
    async def test_risk_summary(
        self, db_session: AsyncSession, sample_project
    ):
        from app.services import trust_scoring_service

        run = Run(run_number=51, project_id=sample_project.id, status=RunStatus.RUNNING)
        db_session.add(run)
        await db_session.flush()

        db_session.add(Task(
            title="Good task", task_type="coding",
            status=TaskStatus.COMPLETED, run_id=run.id,
            assigned_agent_slug="coder",
        ))
        db_session.add(Task(
            title="Bad task", task_type="coding",
            status=TaskStatus.FAILED, run_id=run.id,
            error_message="Crash",
        ))
        await db_session.flush()

        summary = await trust_scoring_service.get_run_risk_summary(db_session, run.id)
        assert "run_trust_score" in summary
        assert "task_scores" in summary
        assert len(summary["task_scores"]) == 2
        assert "task_risk_distribution" in summary

    @pytest.mark.asyncio
    async def test_upsert_task_score(
        self, db_session: AsyncSession, sample_run
    ):
        """Assessing the same task twice should update, not duplicate."""
        from app.services import trust_scoring_service

        task = Task(
            title="Evolving task", task_type="coding",
            status=TaskStatus.RUNNING, run_id=sample_run.id,
        )
        db_session.add(task)
        await db_session.flush()

        ts1 = await trust_scoring_service.assess_task(db_session, task.id)
        score1 = ts1.trust_score

        task.status = TaskStatus.COMPLETED
        await db_session.flush()

        ts2 = await trust_scoring_service.assess_task(db_session, task.id)
        assert ts2.trust_score > score1  # Completion should increase trust
        assert ts1.id == ts2.id  # Same record, updated

    @pytest.mark.asyncio
    async def test_classify_risk_levels(self):
        from app.services.trust_scoring_service import _classify_risk

        assert _classify_risk(0.9) == RiskLevel.LOW
        assert _classify_risk(0.6) == RiskLevel.MEDIUM
        assert _classify_risk(0.4) == RiskLevel.HIGH
        assert _classify_risk(0.2) == RiskLevel.CRITICAL


class TestTrustAPI:
    """Test trust scoring API endpoints."""

    @pytest.mark.asyncio
    async def test_assess_task_endpoint(
        self, client: AsyncClient, sample_task
    ):
        resp = await client.post(f"/trust/tasks/{sample_task.id}/assess")
        assert resp.status_code == 200
        data = resp.json()
        assert "trust_score" in data
        assert "risk_level" in data

    @pytest.mark.asyncio
    async def test_assess_run_endpoint(
        self, client: AsyncClient, sample_run
    ):
        resp = await client.post(f"/trust/runs/{sample_run.id}/assess")
        assert resp.status_code == 200
        data = resp.json()
        assert "trust_score" in data

    @pytest.mark.asyncio
    async def test_list_scores_endpoint(self, client: AsyncClient):
        resp = await client.get("/trust/scores")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data

    @pytest.mark.asyncio
    async def test_assess_nonexistent_task(self, client: AsyncClient):
        resp = await client.post(f"/trust/tasks/{uuid.uuid4()}/assess")
        assert resp.status_code == 404
