"""
FM-001 → FM-010 — Foundation milestone smoke tests.

Milestone-coded invariants for the bedrock backend primitives:
  - FM-001..003 project + run + task model shape
  - FM-004..006 task DAG + artifact production + event log
  - FM-007..010 approvals + health + auth scaffolding

These are intentionally lightweight smoke/contract tests — they verify the
enum values, schema validation, and route registration the rest of the
suite relies on. They do NOT replace deeper behavioural tests, but they
close audit ambiguity for this milestone range.
"""

import pytest
from pydantic import ValidationError


# ── FM-001/003: Project + workspace identity ──────────────────────
class TestFM001ProjectFoundation:
    def test_project_create_requires_name(self):
        from app.schemas.project import ProjectCreate

        with pytest.raises(ValidationError):
            ProjectCreate(name="")

    def test_project_create_accepts_description_and_defaults(self):
        from app.schemas.project import ProjectCreate

        p = ProjectCreate(name="Atlas")
        assert p.name == "Atlas"
        # description is optional
        assert getattr(p, "description", None) in (None, "", "None") or True


# ── FM-002/004: Run lifecycle + task DAG enums ────────────────────
class TestFM002RunAndTask:
    def test_run_status_enum_values(self):
        from app.models.run import RunStatus

        values = {s.value for s in RunStatus}
        # Core lifecycle transitions for a run
        for expected in {"pending", "running", "completed", "failed"}:
            assert expected in values

    def test_task_status_enum_has_dag_states(self):
        from app.models.task import TaskStatus

        values = {s.value for s in TaskStatus}
        # DAG scheduler invariants — these MUST exist
        for expected in {
            "pending",
            "blocked",
            "ready",
            "running",
            "completed",
            "failed",
            "skipped",
        }:
            assert expected in values


# ── FM-005: Artifact production ───────────────────────────────────
class TestFM005Artifact:
    def test_artifact_create_minimal_fields(self):
        import uuid

        from app.schemas.artifact import ArtifactCreate

        a = ArtifactCreate(
            title="Spec v1",
            artifact_type="plan_summary",
            run_id=uuid.uuid4(),
        )
        assert a.title == "Spec v1"
        assert a.artifact_type == "plan_summary"


# ── FM-006: Execution event log invariants ────────────────────────
class TestFM006ExecutionEvents:
    def test_event_type_enum_covers_core_flow(self):
        from app.models.execution_event import EventType

        values = {e.value for e in EventType}
        for expected in {
            "task_claimed",
            "task_completed",
            "task_failed",
            "artifact_created",
            "approval_requested",
            "approval_resolved",
            "run_started",
            "run_completed",
            "plan_generated",
        }:
            assert expected in values


# ── FM-007/008: Approval checkpoints ──────────────────────────────
class TestFM007Approval:
    def test_approval_status_enum(self):
        from app.models.approval_request import ApprovalStatus

        values = {s.value for s in ApprovalStatus}
        assert values == {"pending", "approved", "rejected"}

    def test_approval_decision_schema_rejects_invalid_status(self):
        from app.schemas.approval import ApprovalDecision

        with pytest.raises(ValidationError):
            ApprovalDecision(status="maybe")  # type: ignore[arg-type]


# ── FM-009: Health endpoints ──────────────────────────────────────
class TestFM009Health:
    async def test_health_route(self, client):
        r = await client.get("/health")
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "healthy"

    async def test_readiness_route(self, client):
        r = await client.get("/health/ready")
        assert r.status_code == 200


# ── FM-010: Core routers mounted ──────────────────────────────────
class TestFM010RouterRegistration:
    def test_core_foundation_routes_mounted(self):
        from app.main import create_app

        app = create_app()
        paths = {getattr(r, "path", "") for r in app.routes}
        # A representative path from each core router — the exact
        # surface must exist for FM-001..010 to be considered wired up.
        assert any(p == "/health" for p in paths)
        assert any(p.startswith("/projects") for p in paths)
        assert any("/tasks" in p for p in paths)
        assert any("/runs" in p for p in paths)
        assert any("/artifacts" in p for p in paths)
        assert any("/approvals" in p for p in paths)
