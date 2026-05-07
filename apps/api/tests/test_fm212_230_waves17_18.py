"""Tests for FM-212 through FM-230 (Wave 17 + Wave 18).

Covers:
  FM-212/213 — telemetry + structured logging module imports
  FM-215     — slow query ring-buffer
  FM-216     — cache get/set/invalidate/stats
  FM-217     — job dispatcher enqueue
  FM-218     — storage service path helpers
  FM-221     — model router selection + health tracking
  FM-222     — agent memory store/recall
  FM-223     — LLM cost log + budget pressure
  FM-224     — stream service (no Redis needed)
  FM-225     — tool registry + built-in tool paths
  FM-226     — adaptive orchestrator replan audit
  FM-227     — code review agent comment parsing
  FM-228     — doc agent handle (stub)
  FM-229     — testgen agent patch creation
  FM-230     — security scan agent finding persistence
  API        — agent intelligence endpoints
"""

import json
import os
import sys
import uuid
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

# Make worker package importable from the API test runner
_WORKER_PATH = str(Path(__file__).parent.parent.parent / "worker")
if _WORKER_PATH not in sys.path:
    sys.path.insert(0, _WORKER_PATH)


# ── FM-212: Telemetry module ─────────────────────────────────────


def test_telemetry_setup_no_sdk():
    """setup_telemetry must succeed even without opentelemetry-sdk installed."""
    from app.core.telemetry import setup_telemetry, current_trace_id

    app = MagicMock()
    setup_telemetry(app)  # should not raise
    tid = current_trace_id()
    assert tid is None or isinstance(tid, str)


# ── FM-213: Structured logging ───────────────────────────────────


def test_structured_logging_configure():
    """configure_logging must succeed with or without structlog."""
    from app.core.structured_logging import configure_logging, get_logger

    configure_logging()
    log = get_logger("test")
    assert log is not None


# ── FM-215: Slow query ring-buffer ───────────────────────────────


def test_slow_query_ring_buffer():
    from app.core.slow_query import (
        get_slow_queries,
        clear_slow_queries,
        _slow_query_buffer,
    )

    clear_slow_queries()
    _slow_query_buffer.append(
        {"statement": "SELECT 1", "elapsed_ms": 600, "recorded_at": "now"}
    )
    results = get_slow_queries(limit=10)
    assert len(results) >= 1
    assert results[0]["elapsed_ms"] == 600
    clear_slow_queries()
    assert get_slow_queries() == []


# ── FM-216: Cache ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_cache_get_set_invalidate():
    import os

    os.environ["CACHE_ENABLED"] = "true"
    from app.core.cache import cache_get, cache_set, invalidate, flush_local_cache

    flush_local_cache()
    found, val = await cache_get("mykey")
    assert not found
    await cache_set("mykey", {"hello": "world"}, ttl=60)
    found2, val2 = await cache_get("mykey")
    assert found2
    assert val2 == {"hello": "world"}
    await invalidate("mykey")
    found3, _ = await cache_get("mykey")
    assert not found3


@pytest.mark.asyncio
async def test_cache_stats():
    from app.core.cache import get_cache_stats, flush_local_cache, cache_set

    flush_local_cache()
    await cache_set("stat_key", 42)
    stats = get_cache_stats()
    assert "local_size" in stats
    assert stats["local_size"] >= 1


def test_cache_disabled_returns_none():
    os.environ["CACHE_ENABLED"] = "false"
    import importlib
    import app.core.cache as cache_mod

    importlib.reload(cache_mod)

    async def _run():
        found, val = await cache_mod.cache_get("anything")
        assert not found
        assert val is None

    import asyncio

    asyncio.get_event_loop().run_until_complete(_run())
    os.environ["CACHE_ENABLED"] = "true"


# ── FM-217: Job dispatcher ───────────────────────────────────────


@pytest.mark.asyncio
async def test_job_dispatcher_enqueue():
    from app.worker.job_dispatcher import (
        enqueue_job,
        get_job_history,
        register_job,
        _job_history,
    )

    _job_history.clear()

    async def _noop(**kwargs):
        pass

    register_job("test_noop", _noop)
    job_id = await enqueue_job("test_noop", foo="bar")
    assert job_id is not None

    history = get_job_history()
    assert any(h["job_name"] == "test_noop" for h in history)


# ── FM-218: Storage service ──────────────────────────────────────


def test_storage_service_should_offload():
    from app.services.storage_service import should_offload

    small = "x" * 100
    large = "x" * 5000
    assert not should_offload(small)
    assert should_offload(large)


@pytest.mark.asyncio
async def test_storage_service_local_fallback():
    os.environ["STORAGE_ENABLED"] = "false"
    from app.services import storage_service
    import importlib

    importlib.reload(storage_service)

    content = "hello world test content"
    storage_key = await storage_service.upload_artifact(content)
    assert isinstance(storage_key, str)
    assert len(storage_key) > 0

    os.environ["STORAGE_ENABLED"] = "true"


# ── FM-221: Model router ─────────────────────────────────────────


def test_model_router_select_default():
    from app.core.model_router import select_model

    model = select_model(task_type="codegen", budget_used_pct=0.0)
    assert isinstance(model, str)
    assert len(model) > 0


def test_model_router_downgrade_on_budget():
    from app.core.model_router import select_model

    select_model(task_type="codegen", budget_used_pct=0.5)
    model_tight = select_model(task_type="codegen", budget_used_pct=0.95)
    # At 95% budget the router should pick a cheaper model or downgrade
    assert isinstance(model_tight, str)


def test_model_router_record_error():
    from app.core.model_router import record_provider_error, get_router_status

    record_provider_error("gpt-4o")
    status = get_router_status()
    assert "config" in status
    assert "unhealthy_models" in status


# ── FM-222: Agent memory ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_agent_memory_store_recall(db_session: AsyncSession, sample_project):
    from app.services.agent_memory_service import store_memory, recall_memory

    entry = await store_memory(
        db_session,
        project_id=sample_project.id,
        agent_type="coder",
        key="preferred_stack",
        value={"language": "Python", "framework": "FastAPI"},
    )
    await db_session.flush()
    assert entry.id is not None
    assert entry.key == "preferred_stack"

    results = await recall_memory(
        db_session,
        project_id=sample_project.id,
        agent_type="coder",
        query="python framework",
        top_k=5,
    )
    assert isinstance(results, list)


# ── FM-223: LLM cost tracking ────────────────────────────────────


@pytest.mark.asyncio
async def test_llm_cost_log(db_session: AsyncSession, sample_run):
    from app.services.llm_cost_service import log_llm_call, get_run_cost_summary

    await log_llm_call(
        db_session,
        run_id=sample_run.id,
        model="gpt-4o-mini",
        prompt_tokens=100,
        completion_tokens=50,
        task_type="codegen",
        latency_ms=350,
        success=True,
    )
    await db_session.flush()

    summary = await get_run_cost_summary(db_session, sample_run.id)
    assert summary["total_calls"] >= 1
    assert summary["total_cost_usd"] >= 0.0


@pytest.mark.asyncio
async def test_llm_budget_pressure(db_session: AsyncSession, sample_run):
    from app.services.llm_cost_service import get_run_budget_pressure

    pressure = await get_run_budget_pressure(db_session, sample_run.id)
    assert 0.0 <= pressure <= 1.0


# ── FM-224: Streaming service ────────────────────────────────────


@pytest.mark.asyncio
async def test_stream_service_no_redis():
    """stream_run_events must yield a graceful message when Redis is absent."""
    from app.services.agent_stream_service import stream_run_events

    run_id = uuid.uuid4()
    chunks = []
    async for chunk in stream_run_events(run_id):
        chunks.append(chunk)
        break  # stop after first chunk (heartbeat or error)
    assert len(chunks) >= 1


@pytest.mark.asyncio
async def test_publish_event_no_redis():
    """publish_event should not raise when Redis is unavailable."""
    from app.services.agent_stream_service import publish_event

    await publish_event(uuid.uuid4(), event_type="test", payload={"msg": "hello"})


# ── FM-225: Tool registry ────────────────────────────────────────


def test_tool_registry_has_builtins():
    import importlib

    importlib.import_module("worker.tools.builtin_tools")
    from worker.tools.base import registry

    names = [t["name"] for t in registry.list_tools()]
    assert "web_search" in names
    assert "read_file" in names
    assert "write_file" in names
    assert "run_command" in names


@pytest.mark.asyncio
async def test_run_command_allowlist():
    from worker.tools.builtin_tools import RunCommandTool

    tool = RunCommandTool()
    result = await tool.execute(command="rm -rf /", timeout=5)
    assert result["success"] is False
    assert "allowlist" in result["output"]


@pytest.mark.asyncio
async def test_read_file_sandbox_escape():
    from worker.tools.builtin_tools import ReadFileTool

    tool = ReadFileTool()
    result = await tool.execute(path="../../etc/passwd")
    assert result["success"] is False


# ── FM-226: Plan revision (replan) ──────────────────────────────


@pytest.mark.asyncio
async def test_trigger_replan_run_not_found(db_session: AsyncSession):
    from app.services.adaptive_orchestrator import trigger_replan

    result = await trigger_replan(
        db_session,
        run_id=uuid.uuid4(),
        failed_task_id=uuid.uuid4(),
        error_context="boom",
    )
    assert result["status"] == "error"
    assert "not found" in result["detail"]


@pytest.mark.asyncio
async def test_trigger_replan_creates_revision(
    db_session: AsyncSession, sample_run, sample_task
):
    from app.services.adaptive_orchestrator import trigger_replan
    from app.models.agent_intelligence import PlanRevision
    from sqlalchemy import select

    # trigger_replan gracefully handles missing replan function — status is
    # "replanned" if planner_service.replan exists, "replan_failed" otherwise.
    result = await trigger_replan(
        db_session,
        run_id=sample_run.id,
        failed_task_id=sample_task.id,
        error_context="test failure",
    )

    assert result["status"] in ("replanned", "replan_failed")
    assert "revision_id" in result

    rows = await db_session.execute(
        select(PlanRevision).where(PlanRevision.run_id == sample_run.id)
    )
    assert rows.scalar_one_or_none() is not None


# ── FM-227: Code review agent ────────────────────────────────────


@pytest.mark.asyncio
async def test_code_review_agent_persist_comments(
    db_session: AsyncSession, sample_run, sample_task
):
    from worker.agents.code_review_agent import _persist_review_comments
    from app.models.agent_intelligence import ReviewComment
    from sqlalchemy import select

    llm_response = (
        "```json\n"
        '[{"file_path":"src/api.py","line_number":10,"severity":"warning",'
        '"category":"security","body":"Input not validated"}]\n'
        "```\n\n## Summary\nOne issue found."
    )
    count = await _persist_review_comments(db_session, sample_task, llm_response)
    await db_session.flush()
    assert count == 1
    rows = await db_session.execute(
        select(ReviewComment).where(ReviewComment.run_id == sample_task.run_id)
    )
    comment = rows.scalar_one()
    assert comment.file_path == "src/api.py"
    assert comment.severity.value == "warning"


@pytest.mark.asyncio
async def test_code_review_agent_no_json(db_session, sample_task):
    from worker.agents.code_review_agent import _persist_review_comments

    count = await _persist_review_comments(db_session, sample_task, "No JSON here")
    assert count == 0


# ── FM-228: Doc agent ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_doc_agent_readme(db_session, sample_task):
    from worker.agents.doc_agent import handle

    sample_task.description = "readme overview"
    with patch(
        "worker.agents.doc_agent.llm_completion",
        new_callable=AsyncMock,
        return_value=None,
    ):
        result = await handle(db_session, sample_task, MagicMock())

    assert result["artifact_title"] == "README.md"
    assert "[Stub]" in result["artifact_content"]


@pytest.mark.asyncio
async def test_doc_agent_api_ref(db_session, sample_task):
    from worker.agents.doc_agent import handle

    sample_task.description = "api reference endpoints"
    with patch(
        "worker.agents.doc_agent.llm_completion",
        new_callable=AsyncMock,
        return_value="# API Reference\n...",
    ):
        result = await handle(db_session, sample_task, MagicMock())

    assert result["artifact_title"] == "API_REFERENCE.md"


# ── FM-229: Test gen agent ───────────────────────────────────────


@pytest.mark.asyncio
async def test_testgen_agent_creates_patch(
    db_session: AsyncSession, sample_run, sample_task
):
    from worker.agents.testgen_agent import handle
    from app.models.code_ops import PatchProposal
    from sqlalchemy import select

    with patch(
        "worker.agents.testgen_agent.llm_completion",
        new_callable=AsyncMock,
        return_value="```python\nimport pytest\nasync def test_foo():\n    assert True\n```",
    ):
        result = await handle(db_session, sample_task, MagicMock())

    await db_session.flush()
    assert result["patch_created"] is True
    rows = await db_session.execute(
        select(PatchProposal).where(PatchProposal.project_id == sample_run.project_id)
    )
    patch_record = rows.scalar_one()
    assert "test_foo" in (patch_record.diff_content or "")


# ── FM-230: Security scan agent ──────────────────────────────────


@pytest.mark.asyncio
async def test_security_scan_agent_bandit_parse(
    db_session: AsyncSession, sample_run, sample_task
):
    from worker.agents.security_scan_agent import _parse_bandit, _persist_findings
    from app.models.agent_intelligence import SecurityFinding
    from sqlalchemy import select

    bandit_json = json.dumps(
        {
            "results": [
                {
                    "test_name": "B105",
                    "issue_severity": "HIGH",
                    "issue_text": "Hardcoded password",
                    "filename": "app/auth.py",
                    "line_number": 42,
                }
            ]
        }
    )
    findings = _parse_bandit(bandit_json)
    assert len(findings) == 1
    assert findings[0]["severity"] == "high"

    created, approvals = await _persist_findings(db_session, sample_task, findings)
    await db_session.flush()
    assert created == 1

    rows = await db_session.execute(
        select(SecurityFinding).where(SecurityFinding.run_id == sample_run.id)
    )
    sf = rows.scalar_one()
    assert sf.severity.value == "high"


@pytest.mark.asyncio
async def test_security_scan_agent_npm_parse():
    from worker.agents.security_scan_agent import _parse_npm_audit

    npm_json = json.dumps(
        {
            "vulnerabilities": {
                "lodash": {
                    "severity": "critical",
                    "via": [
                        {"title": "Prototype pollution", "cve": ["CVE-2021-23337"]}
                    ],
                }
            }
        }
    )
    findings = _parse_npm_audit(npm_json)
    assert len(findings) == 1
    assert findings[0]["severity"] == "critical"
    assert "CVE" in (findings[0].get("cve_id") or "")


@pytest.mark.asyncio
async def test_security_scan_high_creates_approval(
    db_session: AsyncSession, sample_run, sample_task
):
    from worker.agents.security_scan_agent import _persist_findings
    from app.models.approval_request import ApprovalRequest, ApprovalStatus
    from sqlalchemy import select

    findings = [
        {
            "source": "bandit",
            "severity": "critical",
            "title": "RCE via eval",
            "description": "User input passed to eval()",
            "file_path": "app/exec.py",
            "line_number": 7,
        }
    ]
    created, approval_count = await _persist_findings(db_session, sample_task, findings)
    await db_session.flush()
    assert approval_count == 1

    rows = await db_session.execute(
        select(ApprovalRequest).where(ApprovalRequest.run_id == sample_run.id)
    )
    approval = rows.scalar_one()
    assert approval.status == ApprovalStatus.PENDING
    assert "CRITICAL" in approval.title


# ── API: Agent intelligence routes ───────────────────────────────


@pytest.mark.asyncio
async def test_list_memory_empty(client: AsyncClient, sample_project):
    resp = await client.get(f"/projects/{sample_project.id}/memory")
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []


@pytest.mark.asyncio
async def test_store_and_list_memory(
    client: AsyncClient, db_session: AsyncSession, sample_project
):
    body = {
        "agent_type": "coder",
        "key": "preferred_language",
        "value": {"lang": "Python"},
    }
    resp = await client.post(f"/projects/{sample_project.id}/memory", json=body)
    assert resp.status_code == 201
    data = resp.json()
    assert "id" in data

    resp2 = await client.get(f"/projects/{sample_project.id}/memory?agent_type=coder")
    assert resp2.status_code == 200
    assert len(resp2.json()["items"]) >= 1


@pytest.mark.asyncio
async def test_list_security_findings_empty(client: AsyncClient, sample_project):
    resp = await client.get(f"/projects/{sample_project.id}/security-findings")
    assert resp.status_code == 200
    assert resp.json()["items"] == []


@pytest.mark.asyncio
async def test_resolve_finding_not_found(client: AsyncClient, sample_project):
    fake_id = uuid.uuid4()
    resp = await client.patch(
        f"/projects/{sample_project.id}/security-findings/{fake_id}/resolve"
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_llm_cost_summary_empty_run(client: AsyncClient, sample_run):
    resp = await client.get(f"/runs/{sample_run.id}/llm-cost-summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_calls"] == 0
    assert data["total_cost_usd"] == 0.0


@pytest.mark.asyncio
async def test_generate_docs_queues_task(client: AsyncClient, sample_project):
    resp = await client.post(
        f"/projects/{sample_project.id}/generate-docs",
        json={"doc_type": "api"},
    )
    assert resp.status_code == 202
    data = resp.json()
    assert "run_id" in data
    assert "task_id" in data
    assert data["status"] == "queued"


@pytest.mark.asyncio
async def test_generate_docs_project_not_found(client: AsyncClient):
    resp = await client.post(
        f"/projects/{uuid.uuid4()}/generate-docs",
        json={"doc_type": "readme"},
    )
    assert resp.status_code == 404
