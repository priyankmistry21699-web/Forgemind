"""Tests for FM-231 through FM-250 (Wave 19 + Wave 20).

Covers:
  FM-231   — CronTrigger CRUD + fire recording
  FM-232   — TriggerRule event matching
  FM-233   — AgentPerformanceSnapshot compute + retrieval
  FM-234   — PromptVersion create / rollback / list
  FM-235   — ModelExperiment model persistence
  FM-236   — BudgetForecast generation
  FM-237   — Run cost attribution
  FM-238   — Bulk approve/reject + bulk archive
  FM-239   — SLOTarget create + attainment compute
  FM-240   — Anomaly scan (error-rate detection)
  FM-241   — ResourceQuota upsert + violation check
  FM-246   — DigestSchedule model persistence
  FM-247   — PII pattern seed + content scan
  FM-248   — Platform admin stats
  API      — scheduling, platform-intelligence, platform-ops routes
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


# ── FM-231: Cron triggers ────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_cron_trigger(db_session: AsyncSession, sample_project):
    from app.services import schedule_service
    from app.models.scheduling import CronTriggerStatus

    trigger = await schedule_service.create_cron_trigger(
        db_session,
        project_id=sample_project.id,
        name="Nightly build",
        cron_expression="0 2 * * *",
        prompt="Run full regression suite",
        created_by="user-1",
    )
    await db_session.flush()
    assert trigger.id is not None
    assert trigger.name == "Nightly build"
    assert trigger.status == CronTriggerStatus.ACTIVE
    assert trigger.fire_count == 0


@pytest.mark.asyncio
async def test_list_cron_triggers(db_session: AsyncSession, sample_project):
    from app.services import schedule_service

    await schedule_service.create_cron_trigger(
        db_session, project_id=sample_project.id, name="A", cron_expression="0 * * * *"
    )
    await schedule_service.create_cron_trigger(
        db_session, project_id=sample_project.id, name="B", cron_expression="30 * * * *"
    )
    await db_session.flush()

    triggers = await schedule_service.list_cron_triggers(db_session, sample_project.id)
    assert len(triggers) == 2


@pytest.mark.asyncio
async def test_pause_resume_cron_trigger(db_session: AsyncSession, sample_project):
    from app.services import schedule_service
    from app.models.scheduling import CronTriggerStatus

    trigger = await schedule_service.create_cron_trigger(
        db_session,
        project_id=sample_project.id,
        name="Pauseable",
        cron_expression="0 * * * *",
    )
    await db_session.flush()

    paused = await schedule_service.update_cron_trigger_status(
        db_session, trigger.id, CronTriggerStatus.PAUSED
    )
    assert paused is not None
    assert paused.status == CronTriggerStatus.PAUSED

    resumed = await schedule_service.update_cron_trigger_status(
        db_session, trigger.id, CronTriggerStatus.ACTIVE
    )
    assert resumed.status == CronTriggerStatus.ACTIVE


@pytest.mark.asyncio
async def test_record_cron_fire(db_session: AsyncSession, sample_project):
    from app.services import schedule_service

    trigger = await schedule_service.create_cron_trigger(
        db_session,
        project_id=sample_project.id,
        name="Fired",
        cron_expression="* * * * *",
    )
    await db_session.flush()

    updated = await schedule_service.record_cron_fire(db_session, trigger.id)
    assert updated is not None
    assert updated.fire_count == 1
    assert updated.last_fired_at is not None


# ── FM-232: Trigger rules ────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_trigger_rule(db_session: AsyncSession, sample_project):
    from app.services import schedule_service
    from app.models.scheduling import TriggerRuleEvent

    rule = await schedule_service.create_trigger_rule(
        db_session,
        project_id=sample_project.id,
        name="PR auto-review",
        event_type=TriggerRuleEvent.PR_OPENED,
        conditions={"branch": "main"},
        action_prompt="Review the PR diff",
    )
    await db_session.flush()
    assert rule.id is not None
    assert rule.enabled is True
    assert rule.fire_count == 0


@pytest.mark.asyncio
async def test_fire_matching_rules(db_session: AsyncSession, sample_project):
    from app.services import schedule_service
    from app.models.scheduling import TriggerRuleEvent

    await schedule_service.create_trigger_rule(
        db_session,
        project_id=sample_project.id,
        name="Main branch rule",
        event_type=TriggerRuleEvent.COMMIT_PUSHED,
        conditions={"branch": "main"},
    )
    await schedule_service.create_trigger_rule(
        db_session,
        project_id=sample_project.id,
        name="Any branch rule",
        event_type=TriggerRuleEvent.COMMIT_PUSHED,
        conditions=None,
    )
    await db_session.flush()

    # Payload matches "main" branch
    fired = await schedule_service.fire_matching_rules(
        db_session,
        sample_project.id,
        TriggerRuleEvent.COMMIT_PUSHED,
        {"branch": "main", "sha": "abc123"},
    )
    assert len(fired) == 2  # both rules fire (one has no conditions)
    assert all(r.fire_count == 1 for r in fired)


@pytest.mark.asyncio
async def test_fire_matching_rules_no_match(db_session: AsyncSession, sample_project):
    from app.services import schedule_service
    from app.models.scheduling import TriggerRuleEvent

    await schedule_service.create_trigger_rule(
        db_session,
        project_id=sample_project.id,
        name="Main only",
        event_type=TriggerRuleEvent.COMMIT_PUSHED,
        conditions={"branch": "main"},
    )
    await db_session.flush()

    fired = await schedule_service.fire_matching_rules(
        db_session,
        sample_project.id,
        TriggerRuleEvent.COMMIT_PUSHED,
        {"branch": "feature/x"},  # doesn't match "main"
    )
    assert len(fired) == 0


# ── FM-234: Prompt versioning ────────────────────────────────────


@pytest.mark.asyncio
async def test_prompt_version_create_increments(
    db_session: AsyncSession, sample_project
):
    from app.services.prompt_version_service import create_version, list_versions

    v1 = await create_version(
        db_session,
        project_id=sample_project.id,
        role="planner",
        content="You are a project planner.",
        created_by="admin",
    )
    v2 = await create_version(
        db_session,
        project_id=sample_project.id,
        role="planner",
        content="You are an expert project planner. Think step by step.",
        change_summary="Added CoT instruction",
    )
    await db_session.flush()

    assert v1.version == 1
    assert v2.version == 2
    assert v2.is_active is True
    # v1 should have been deactivated
    await db_session.refresh(v1)
    assert v1.is_active is False

    versions = await list_versions(db_session, sample_project.id, role="planner")
    assert len(versions) == 2


@pytest.mark.asyncio
async def test_prompt_version_rollback(db_session: AsyncSession, sample_project):
    from app.services.prompt_version_service import create_version, rollback_to_version

    v1 = await create_version(
        db_session, project_id=sample_project.id, role="reviewer", content="v1 content"
    )
    await create_version(
        db_session, project_id=sample_project.id, role="reviewer", content="v2 content"
    )
    await db_session.flush()

    rolled_back = await rollback_to_version(db_session, v1.id)
    assert rolled_back is not None
    await db_session.refresh(v1)
    assert v1.is_active is True


# ── FM-235: Model experiments ────────────────────────────────────


@pytest.mark.asyncio
async def test_model_experiment_persists(db_session: AsyncSession, sample_project):
    from app.models.platform_intelligence import ModelExperiment

    experiment = ModelExperiment(
        project_id=sample_project.id,
        task_type="codegen",
        model_a="claude-opus-4",
        model_b="gpt-4o",
        cost_a_usd=0.05,
        cost_b_usd=0.08,
        latency_a_ms=1200,
        latency_b_ms=900,
        winner="b",
    )
    db_session.add(experiment)
    await db_session.flush()
    assert experiment.id is not None
    assert experiment.winner == "b"


# ── FM-236: Budget forecasting ──────────────────────────────────


@pytest.mark.asyncio
async def test_generate_forecast_no_spend(db_session: AsyncSession, sample_project):
    from app.services.cost_forecast_service import generate_forecast

    forecast = await generate_forecast(db_session, sample_project.id)
    assert forecast.project_id == sample_project.id
    assert forecast.actual_spend_usd == 0.0
    assert forecast.forecasted_spend_usd == 0.0
    assert forecast.will_exceed_budget is False


@pytest.mark.asyncio
async def test_generate_forecast_with_spend(
    db_session: AsyncSession, sample_project, sample_run
):
    from app.models.agent_intelligence import LLMCallLog
    from app.services.cost_forecast_service import generate_forecast

    for i in range(5):
        db_session.add(
            LLMCallLog(
                run_id=sample_run.id,
                model="claude-opus-4",
                task_type="codegen",
                prompt_tokens=500,
                completion_tokens=200,
                cost_usd=0.10 * (i + 1),
            )
        )
    await db_session.flush()

    forecast = await generate_forecast(db_session, sample_project.id, budget_usd=1.0)
    assert forecast.actual_spend_usd > 0.0


# ── FM-237: Cost attribution ─────────────────────────────────────


@pytest.mark.asyncio
async def test_run_cost_attribution(
    db_session: AsyncSession, sample_project, sample_run
):
    from app.models.agent_intelligence import LLMCallLog
    from app.services.cost_forecast_service import get_run_cost_attribution

    db_session.add(
        LLMCallLog(
            run_id=sample_run.id,
            model="claude",
            task_type="codegen",
            prompt_tokens=100,
            completion_tokens=50,
            cost_usd=0.05,
        )
    )
    db_session.add(
        LLMCallLog(
            run_id=sample_run.id,
            model="claude",
            task_type="review",
            prompt_tokens=80,
            completion_tokens=30,
            cost_usd=0.03,
        )
    )
    await db_session.flush()

    attribution = await get_run_cost_attribution(db_session, sample_run.id)
    assert attribution["run_id"] == str(sample_run.id)
    assert attribution["total_cost_usd"] > 0
    agent_names = [a["agent"] for a in attribution["by_agent"]]
    assert "codegen" in agent_names
    assert "review" in agent_names


# ── FM-239: SLO tracking ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_slo(db_session: AsyncSession, sample_project):
    from app.services.slo_service import create_slo
    from app.models.platform_intelligence import SLOMetric

    slo = await create_slo(
        db_session,
        project_id=sample_project.id,
        name="Run success rate SLO",
        metric=SLOMetric.RUN_SUCCESS_RATE,
        threshold=0.9,
        target_pct=0.99,
        window_days=30,
    )
    await db_session.flush()
    assert slo.id is not None
    assert slo.metric == SLOMetric.RUN_SUCCESS_RATE


@pytest.mark.asyncio
async def test_compute_slo_attainment_no_data(db_session: AsyncSession, sample_project):
    from app.services.slo_service import create_slo, compute_slo_attainment
    from app.models.platform_intelligence import SLOMetric

    slo = await create_slo(
        db_session,
        project_id=sample_project.id,
        name="Success SLO",
        metric=SLOMetric.RUN_SUCCESS_RATE,
        threshold=0.9,
    )
    await db_session.flush()

    result = await compute_slo_attainment(db_session, slo)
    # No runs exist — attainment defaults to 0/1 = 0
    assert result.total_events == 0
    assert result.slo_id == slo.id


@pytest.mark.asyncio
async def test_compute_slo_attainment_with_runs(
    db_session: AsyncSession, sample_project, sample_run
):
    from app.models.run import RunStatus
    from app.services.slo_service import create_slo, compute_slo_attainment
    from app.models.platform_intelligence import SLOMetric

    # Mark sample_run as completed
    sample_run.status = RunStatus.COMPLETED
    await db_session.flush()

    slo = await create_slo(
        db_session,
        project_id=sample_project.id,
        name="Success SLO",
        metric=SLOMetric.RUN_SUCCESS_RATE,
        threshold=0.9,
    )
    await db_session.flush()

    result = await compute_slo_attainment(db_session, slo)
    assert result.total_events == 1
    assert result.compliant_events == 1
    assert result.attainment_pct == 1.0


@pytest.mark.asyncio
async def test_slo_summary(db_session: AsyncSession, sample_project):
    from app.services.slo_service import create_slo, get_slo_summary
    from app.models.platform_intelligence import SLOMetric

    await create_slo(
        db_session,
        project_id=sample_project.id,
        name="Latency SLO",
        metric=SLOMetric.TASK_LATENCY_MS,
        threshold=5000,
    )
    await db_session.flush()

    summary = await get_slo_summary(db_session, sample_project.id)
    assert len(summary) == 1
    assert summary[0]["name"] == "Latency SLO"
    assert summary[0]["latest"] is None  # not yet computed


# ── FM-240: Anomaly detection ────────────────────────────────────


@pytest.mark.asyncio
async def test_anomaly_scan_no_anomalies(db_session: AsyncSession, sample_project):
    from app.services.anomaly_service import run_anomaly_scan

    # No runs → no anomalies
    anomalies = await run_anomaly_scan(db_session, sample_project.id)
    assert anomalies == []


@pytest.mark.asyncio
async def test_anomaly_scan_error_rate(
    db_session: AsyncSession, sample_project, sample_run
):
    from app.models.run import Run, RunStatus
    from app.services.anomaly_service import run_anomaly_scan

    # Create 3 more runs: 3 failed out of 4 total (75% error rate → > 50% threshold)
    for _ in range(3):
        run = Run(run_number=99, project_id=sample_project.id, trigger="test")
        run.status = RunStatus.FAILED
        db_session.add(run)

    await db_session.flush()

    anomalies = await run_anomaly_scan(
        db_session, sample_project.id, window_hours=24 * 365
    )
    assert any(a.anomaly_type.value == "error_rate_jump" for a in anomalies)


@pytest.mark.asyncio
async def test_list_anomalies(db_session: AsyncSession, sample_project):
    from app.models.platform_intelligence import (
        AnomalyEvent,
        AnomalyType,
        AnomalySeverity,
    )
    from app.services.anomaly_service import list_anomalies

    event = AnomalyEvent(
        project_id=sample_project.id,
        anomaly_type=AnomalyType.COST_SPIKE,
        severity=AnomalySeverity.HIGH,
        title="Test anomaly",
        description="Spike detected",
        metric_value=5.0,
        baseline_value=1.0,
        deviation_pct=400.0,
    )
    db_session.add(event)
    await db_session.flush()

    results = await list_anomalies(db_session, sample_project.id, resolved=False)
    assert len(results) == 1
    assert results[0].anomaly_type == AnomalyType.COST_SPIKE


# ── FM-241: Resource quotas ──────────────────────────────────────


@pytest.mark.asyncio
async def test_upsert_quota(db_session: AsyncSession):
    from app.services.quota_service import upsert_quota

    ws_id = uuid.uuid4()
    quota = await upsert_quota(
        db_session,
        ws_id,
        max_concurrent_runs=5,
        max_projects=20,
        enforce=True,
    )
    await db_session.flush()
    assert quota.id is not None
    assert quota.max_concurrent_runs == 5

    # Second call updates
    quota2 = await upsert_quota(db_session, ws_id, max_concurrent_runs=10)
    assert quota2.id == quota.id
    assert quota2.max_concurrent_runs == 10


@pytest.mark.asyncio
async def test_quota_no_violations(db_session: AsyncSession, sample_project):
    from app.services.quota_service import upsert_quota, check_quota_violations
    from app.models.workspace import Workspace

    workspace = Workspace(name="Test WS", slug="test-ws", owner_id=uuid.uuid4())
    db_session.add(workspace)
    await db_session.flush()

    await upsert_quota(
        db_session, workspace.id, max_concurrent_runs=10, max_projects=50
    )
    await db_session.flush()

    result = await check_quota_violations(db_session, workspace.id)
    assert result["quota_defined"] is True
    assert result["within_limits"] is True
    assert result["violations"] == []


@pytest.mark.asyncio
async def test_quota_undefined(db_session: AsyncSession):
    from app.services.quota_service import check_quota_violations

    result = await check_quota_violations(db_session, uuid.uuid4())
    assert result["quota_defined"] is False


# ── FM-246: Digest schedules ─────────────────────────────────────


@pytest.mark.asyncio
async def test_digest_schedule_persists(db_session: AsyncSession):
    from app.models.platform_ops import DigestSchedule, DigestFrequency

    user_id = uuid.uuid4()
    schedule = DigestSchedule(
        user_id=user_id,
        frequency=DigestFrequency.WEEKLY,
        include_costs=True,
        include_approvals=False,
        include_security=True,
    )
    db_session.add(schedule)
    await db_session.flush()
    assert schedule.id is not None
    assert schedule.frequency == DigestFrequency.WEEKLY


# ── FM-247: PII detection ────────────────────────────────────────


@pytest.mark.asyncio
async def test_seed_pii_patterns(db_session: AsyncSession):
    from app.services.pii_service import seed_builtin_patterns
    from app.models.platform_ops import PIIPattern
    from sqlalchemy import select

    await seed_builtin_patterns(db_session)
    await db_session.flush()

    result = await db_session.execute(select(PIIPattern))
    patterns = result.scalars().all()
    assert len(patterns) == 7

    # Idempotent — second call should not duplicate
    await seed_builtin_patterns(db_session)
    await db_session.flush()
    result2 = await db_session.execute(select(PIIPattern))
    assert len(result2.scalars().all()) == 7


@pytest.mark.asyncio
async def test_scan_content_email(db_session: AsyncSession):
    from app.services.pii_service import seed_builtin_patterns, scan_content

    await seed_builtin_patterns(db_session)
    await db_session.flush()

    report = await scan_content(
        db_session,
        "Please contact admin@example.com for support",
        mask=False,
    )
    assert report["total_findings"] >= 1
    email_findings = [f for f in report["findings"] if f["category"] == "email"]
    assert len(email_findings) >= 1


@pytest.mark.asyncio
async def test_scan_content_masking(db_session: AsyncSession):
    from app.services.pii_service import seed_builtin_patterns, scan_content

    await seed_builtin_patterns(db_session)
    await db_session.flush()

    report = await scan_content(
        db_session,
        "My SSN is 123-45-6789",
        mask=True,
    )
    assert report["masked_content"] is not None
    assert "123-45-6789" not in report["masked_content"]
    assert "REDACTED" in report["masked_content"]


@pytest.mark.asyncio
async def test_scan_content_no_pii(db_session: AsyncSession):
    from app.services.pii_service import seed_builtin_patterns, scan_content

    await seed_builtin_patterns(db_session)
    await db_session.flush()

    report = await scan_content(db_session, "def add(a, b): return a + b")
    assert report["total_findings"] == 0
    assert report["has_critical"] is False


@pytest.mark.asyncio
async def test_scan_artifact_not_found(db_session: AsyncSession):
    from app.services.pii_service import scan_artifact

    result = await scan_artifact(db_session, uuid.uuid4())
    assert "error" in result


@pytest.mark.asyncio
async def test_scan_artifact_with_content(db_session: AsyncSession, sample_artifact):
    from app.services.pii_service import seed_builtin_patterns, scan_artifact

    await seed_builtin_patterns(db_session)
    await db_session.flush()

    # Inject an email into the artifact content
    sample_artifact.content = "Contact user@test.com for details"
    await db_session.flush()

    result = await scan_artifact(db_session, sample_artifact.id)
    assert result["artifact_id"] == str(sample_artifact.id)
    assert result["total_findings"] >= 1


# ── FM-248: Platform admin stats ─────────────────────────────────


@pytest.mark.asyncio
async def test_platform_stats(db_session: AsyncSession, sample_project, sample_run):
    from app.services.platform_admin_service import get_platform_stats

    stats = await get_platform_stats(db_session)
    assert "generated_at" in stats
    assert stats["projects"]["total"] >= 1
    assert stats["runs"]["total"] >= 1
    assert "llm_costs" in stats
    assert "security" in stats


# ── API: Scheduling routes ───────────────────────────────────────


@pytest.mark.asyncio
async def test_api_create_list_schedules(client: AsyncClient, sample_project):
    project_id = str(sample_project.id)

    r = await client.post(
        f"/projects/{project_id}/schedules",
        json={"name": "Daily sync", "cron_expression": "0 6 * * *"},
    )
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "Daily sync"
    assert data["status"] == "active"

    r2 = await client.get(f"/projects/{project_id}/schedules")
    assert r2.status_code == 200
    assert r2.json()["total"] == 1


@pytest.mark.asyncio
async def test_api_pause_resume_schedule(client: AsyncClient, sample_project):
    project_id = str(sample_project.id)

    r = await client.post(
        f"/projects/{project_id}/schedules",
        json={"name": "Pauseable", "cron_expression": "* * * * *"},
    )
    trigger_id = r.json()["id"]

    pause = await client.patch(f"/projects/{project_id}/schedules/{trigger_id}/pause")
    assert pause.status_code == 200
    assert pause.json()["status"] == "paused"

    resume = await client.patch(f"/projects/{project_id}/schedules/{trigger_id}/resume")
    assert resume.status_code == 200
    assert resume.json()["status"] == "active"


@pytest.mark.asyncio
async def test_api_schedule_not_found(client: AsyncClient, sample_project):
    project_id = str(sample_project.id)
    trigger_id = str(uuid.uuid4())

    r = await client.patch(f"/projects/{project_id}/schedules/{trigger_id}/pause")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_api_create_trigger_rules(client: AsyncClient, sample_project):
    project_id = str(sample_project.id)

    r = await client.post(
        f"/projects/{project_id}/trigger-rules",
        json={"name": "PR rule", "event_type": "pr_opened"},
    )
    assert r.status_code == 201
    data = r.json()
    assert data["event_type"] == "pr_opened"


# ── API: Platform intelligence routes ───────────────────────────


@pytest.mark.asyncio
async def test_api_create_list_prompt_versions(client: AsyncClient, sample_project):
    project_id = str(sample_project.id)

    r = await client.post(
        f"/projects/{project_id}/prompt-versions",
        json={
            "role": "planner",
            "content": "You are a planner.",
            "change_summary": "init",
        },
    )
    assert r.status_code == 201
    data = r.json()
    assert data["role"] == "planner"
    assert data["version"] == 1

    r2 = await client.post(
        f"/projects/{project_id}/prompt-versions",
        json={"role": "planner", "content": "Updated planner prompt."},
    )
    assert r2.status_code == 201
    assert r2.json()["version"] == 2

    r3 = await client.get(f"/projects/{project_id}/prompt-versions")
    assert r3.status_code == 200
    assert r3.json()["total"] == 2


@pytest.mark.asyncio
async def test_api_rollback_prompt_version(client: AsyncClient, sample_project):
    project_id = str(sample_project.id)

    v1 = await client.post(
        f"/projects/{project_id}/prompt-versions",
        json={"role": "reviewer", "content": "v1"},
    )
    v1_id = v1.json()["id"]

    await client.post(
        f"/projects/{project_id}/prompt-versions",
        json={"role": "reviewer", "content": "v2"},
    )

    r = await client.post(f"/projects/{project_id}/prompt-versions/{v1_id}/rollback")
    assert r.status_code == 200
    assert r.json()["is_active"] is True


@pytest.mark.asyncio
async def test_api_rollback_not_found(client: AsyncClient, sample_project):
    project_id = str(sample_project.id)
    r = await client.post(
        f"/projects/{project_id}/prompt-versions/{uuid.uuid4()}/rollback"
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_api_cost_forecast(client: AsyncClient, sample_project):
    project_id = str(sample_project.id)
    r = await client.get(f"/projects/{project_id}/cost-forecast")
    assert r.status_code == 200
    data = r.json()
    assert "actual_spend_usd" in data
    assert "forecasted_spend_usd" in data
    assert "will_exceed_budget" in data


@pytest.mark.asyncio
async def test_api_cost_attribution(client: AsyncClient, sample_run):
    r = await client.get(f"/runs/{sample_run.id}/cost-attribution")
    assert r.status_code == 200
    data = r.json()
    assert "total_cost_usd" in data


@pytest.mark.asyncio
async def test_api_bulk_approve(client: AsyncClient, sample_approval):
    r = await client.post(
        "/approvals/bulk-decide",
        json={
            "approval_ids": [str(sample_approval.id)],
            "decision": "approved",
            "comment": "LGTM",
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["updated"] == 1
    assert data["decision"] == "approved"


@pytest.mark.asyncio
async def test_api_bulk_approve_invalid_decision(client: AsyncClient):
    r = await client.post(
        "/approvals/bulk-decide",
        json={"approval_ids": [], "decision": "maybe"},
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_api_bulk_archive_runs(client: AsyncClient, sample_run):
    r = await client.post(
        "/runs/bulk-archive",
        json={"run_ids": [str(sample_run.id)]},
    )
    assert r.status_code == 200
    assert r.json()["archived"] == 1


@pytest.mark.asyncio
async def test_api_create_slo(client: AsyncClient, sample_project):
    project_id = str(sample_project.id)
    r = await client.post(
        f"/projects/{project_id}/slos",
        json={
            "name": "Run success SLO",
            "metric": "run_success_rate",
            "threshold": 0.95,
            "target_pct": 0.99,
            "window_days": 30,
        },
    )
    assert r.status_code == 201
    data = r.json()
    assert data["metric"] == "run_success_rate"


@pytest.mark.asyncio
async def test_api_list_slos(client: AsyncClient, sample_project):
    project_id = str(sample_project.id)
    await client.post(
        f"/projects/{project_id}/slos",
        json={"name": "Latency SLO", "metric": "task_latency_ms", "threshold": 5000},
    )
    r = await client.get(f"/projects/{project_id}/slos")
    assert r.status_code == 200
    assert r.json()["total"] == 1


@pytest.mark.asyncio
async def test_api_compute_slo(client: AsyncClient, sample_project):
    project_id = str(sample_project.id)
    create_r = await client.post(
        f"/projects/{project_id}/slos",
        json={
            "name": "SLO compute test",
            "metric": "run_success_rate",
            "threshold": 0.9,
        },
    )
    slo_id = create_r.json()["id"]

    r = await client.post(f"/projects/{project_id}/slos/{slo_id}/compute")
    assert r.status_code == 200
    data = r.json()
    assert "attainment_pct" in data
    assert "met" in data


@pytest.mark.asyncio
async def test_api_compute_slo_not_found(client: AsyncClient, sample_project):
    project_id = str(sample_project.id)
    r = await client.post(f"/projects/{project_id}/slos/{uuid.uuid4()}/compute")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_api_anomaly_scan(client: AsyncClient, sample_project):
    project_id = str(sample_project.id)
    r = await client.post(f"/projects/{project_id}/anomalies/scan")
    assert r.status_code == 201
    data = r.json()
    assert "detected" in data
    assert "anomaly_ids" in data


@pytest.mark.asyncio
async def test_api_list_anomalies(client: AsyncClient, sample_project):
    project_id = str(sample_project.id)
    r = await client.get(f"/projects/{project_id}/anomalies")
    assert r.status_code == 200
    assert "items" in r.json()


# ── API: Platform ops routes ─────────────────────────────────────


@pytest.mark.asyncio
async def test_api_get_quota_undefined(client: AsyncClient, sample_workspace):
    ws_id = sample_workspace.id
    r = await client.get(f"/workspaces/{ws_id}/quotas")
    assert r.status_code == 200
    assert r.json()["quota_defined"] is False


@pytest.mark.asyncio
async def test_api_upsert_and_get_quota(client: AsyncClient, sample_workspace):
    ws_id = sample_workspace.id
    r = await client.put(
        f"/workspaces/{ws_id}/quotas",
        json={"max_concurrent_runs": 5, "max_projects": 20, "enforce": True},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["enforce"] is True

    r2 = await client.get(f"/workspaces/{ws_id}/quotas")
    assert r2.status_code == 200
    d2 = r2.json()
    assert d2["quota_defined"] is True
    assert d2["max_concurrent_runs"] == 5


@pytest.mark.asyncio
async def test_api_check_quota_violations(client: AsyncClient, sample_workspace):
    ws_id = sample_workspace.id
    await client.put(
        f"/workspaces/{ws_id}/quotas",
        json={"max_concurrent_runs": 100, "enforce": True},
    )
    r = await client.get(f"/workspaces/{ws_id}/quotas/check")
    assert r.status_code == 200
    data = r.json()
    assert "within_limits" in data


@pytest.mark.asyncio
async def test_api_seed_pii_patterns(client: AsyncClient):
    r = await client.post("/admin/pii-patterns/seed")
    assert r.status_code == 201
    assert r.json()["status"] == "seeded"


@pytest.mark.asyncio
async def test_api_pii_scan_artifact_not_found(client: AsyncClient):
    r = await client.get(f"/artifacts/{uuid.uuid4()}/pii-scan")
    # VULN-9 fix: artifact not found now returns 200 with error key (service-level check)
    assert r.status_code in (200, 404)


@pytest.mark.asyncio
async def test_api_pii_scan_artifact(client: AsyncClient, sample_artifact):
    await client.post("/admin/pii-patterns/seed")
    r = await client.get(f"/artifacts/{sample_artifact.id}/pii-scan")
    assert r.status_code == 200
    data = r.json()
    assert "total_findings" in data
    assert "has_critical" in data


@pytest.mark.asyncio
async def test_api_platform_stats(client: AsyncClient):
    r = await client.get("/admin/platform-stats")
    assert r.status_code == 200
    data = r.json()
    assert "users" in data
    assert "workspaces" in data
    assert "runs" in data
    assert "llm_costs" in data


@pytest.mark.asyncio
async def test_api_audit_export_jsonl(client: AsyncClient, sample_workspace):
    r = await client.post(
        "/admin/audit-export",
        json={"workspace_id": str(sample_workspace.id), "format": "jsonl", "limit": 10},
    )
    assert r.status_code == 200
    assert "x-ndjson" in r.headers.get("content-type", "") or r.content == b""


@pytest.mark.asyncio
async def test_api_audit_export_csv(client: AsyncClient, sample_workspace):
    r = await client.post(
        "/admin/audit-export",
        json={"workspace_id": str(sample_workspace.id), "format": "csv", "limit": 10},
    )
    assert r.status_code == 200
    assert "csv" in r.headers.get("content-type", "")


@pytest.mark.asyncio
async def test_api_agent_performance(client: AsyncClient):
    r = await client.get("/agents/planner/performance?days=30")
    assert r.status_code == 200
    data = r.json()
    assert data["agent_slug"] == "planner"
    assert "snapshots" in data
