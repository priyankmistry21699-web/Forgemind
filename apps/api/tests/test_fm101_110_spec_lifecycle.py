"""FM-101–110: Comprehensive tests for the SPEC-driven lifecycle block.

Covers:
  FM-101: SPEC/PLAN artifact types, SPECIFYING status, lifecycle gating
  FM-102: Constitution CRUD, prompt injection
  FM-103: Governance audit events
  FM-104: Slash command parsing
  FM-105: Structured SPEC generation
  FM-106: PLAN artifact creation, SPEC→PLAN linking, export
  FM-107: ADR-aware enrichment
  FM-108: Spec-to-plan validation rules
  FM-109: Approval integration for SPEC/PLAN
  FM-110: End-to-end lifecycle hardening
"""


import pytest
from sqlalchemy import select



# ── Helpers ──────────────────────────────────────────────────────


async def _make_run(db, project, *, status=None, prompt=None):
    from app.models.run import Run

    run = Run(
        run_number=100,
        project_id=project.id,
        trigger="test",
    )
    if status:
        run.status = status
    db.add(run)
    await db.flush()
    await db.refresh(run)
    return run


async def _make_spec(db, run):
    from app.models.artifact import Artifact, ArtifactType

    spec = Artifact(
        run_id=run.id,
        project_id=run.project_id,
        artifact_type=ArtifactType.SPEC,
        title="Test SPEC",
        content=(
            "# Specification\n\n"
            "## Problem / Objective\nBuild a todo app\n\n"
            "## Scope\nWeb application\n\n"
            "## Constraints\n- Must use Python\n\n"
            "## Assumptions\n- Requirements stable\n\n"
            "## Acceptance Criteria\n- All tests pass\n- UI renders correctly\n\n"
            "## Risks / Unknowns\n- LLM availability\n\n"
            "## Architecture Summary\nFastAPI + React\n"
        ),
    )
    db.add(spec)
    await db.flush()
    await db.refresh(spec)
    return spec


async def _make_plan(db, run, spec):
    from app.models.artifact import Artifact, ArtifactType

    plan = Artifact(
        run_id=run.id,
        project_id=run.project_id,
        artifact_type=ArtifactType.PLAN,
        title="Test PLAN",
        spec_artifact_id=spec.id,
        content=(
            "# Execution Plan\n\n"
            "## Overview\nBuild a todo web application with Python backend.\n\n"
            "## Phase 1: Setup\n- Set up project structure\n- Install dependencies\n\n"
            "## Phase 2: Implementation\n- Build backend API\n- Build frontend UI renders\n\n"
            "## Phase 3: Testing\n- All tests pass\n- Integration tests\n"
        ),
    )
    db.add(plan)
    await db.flush()
    await db.refresh(plan)
    return plan


# ═══════════════════════════════════════════════════════════════════
# FM-101: SPEC/PLAN artifact types and lifecycle gating
# ═══════════════════════════════════════════════════════════════════


class TestFM101_ArtifactTypes:
    async def test_spec_artifact_type_exists(self):
        from app.models.artifact import ArtifactType

        assert ArtifactType.SPEC.value == "spec"

    async def test_plan_artifact_type_exists(self):
        from app.models.artifact import ArtifactType

        assert ArtifactType.PLAN.value == "plan"

    async def test_specifying_run_status_exists(self):
        from app.models.run import RunStatus

        assert RunStatus.SPECIFYING.value == "specifying"

    async def test_spec_artifact_creation(self, db_session, sample_project):
        from app.models.artifact import Artifact, ArtifactType

        run = await _make_run(db_session, sample_project)
        spec = Artifact(
            run_id=run.id,
            project_id=sample_project.id,
            artifact_type=ArtifactType.SPEC,
            title="My SPEC",
            content="# Specification\nHello",
        )
        db_session.add(spec)
        await db_session.flush()
        assert spec.id is not None
        assert spec.artifact_type == ArtifactType.SPEC

    async def test_spec_artifact_id_fk(self, db_session, sample_project):
        from app.models.artifact import Artifact, ArtifactType

        run = await _make_run(db_session, sample_project)
        spec = await _make_spec(db_session, run)
        plan = Artifact(
            run_id=run.id,
            project_id=sample_project.id,
            artifact_type=ArtifactType.PLAN,
            title="My PLAN",
            content="# Plan",
            spec_artifact_id=spec.id,
        )
        db_session.add(plan)
        await db_session.flush()
        assert plan.spec_artifact_id == spec.id


class TestFM101_LifecycleGating:
    async def test_valid_transitions_dict(self):
        from app.services.run_lifecycle_service import VALID_TRANSITIONS
        from app.models.run import RunStatus

        assert RunStatus.PLANNING in VALID_TRANSITIONS[RunStatus.SPECIFYING]
        assert RunStatus.RUNNING in VALID_TRANSITIONS[RunStatus.PLANNING]

    async def test_has_spec_artifact(self, db_session, sample_project):
        from app.services.run_lifecycle_service import has_spec_artifact

        run = await _make_run(db_session, sample_project)
        assert not await has_spec_artifact(db_session, run_id=run.id)
        await _make_spec(db_session, run)
        assert await has_spec_artifact(db_session, run_id=run.id)

    async def test_has_plan_artifact(self, db_session, sample_project):
        from app.services.run_lifecycle_service import has_plan_artifact

        run = await _make_run(db_session, sample_project)
        assert not await has_plan_artifact(db_session, run_id=run.id)
        spec = await _make_spec(db_session, run)
        await _make_plan(db_session, run, spec)
        assert await has_plan_artifact(db_session, run_id=run.id)

    async def test_specifying_to_planning_blocked_without_spec(
        self, db_session, sample_project
    ):
        from app.services.run_lifecycle_service import validate_transition
        from app.models.run import RunStatus

        run = await _make_run(db_session, sample_project, status=RunStatus.SPECIFYING)
        result = await validate_transition(db_session, run.id, RunStatus.PLANNING)
        assert not result["allowed"]

    async def test_specifying_to_planning_allowed_with_spec(
        self, db_session, sample_project
    ):
        from app.services.run_lifecycle_service import validate_transition
        from app.models.run import RunStatus

        run = await _make_run(db_session, sample_project, status=RunStatus.SPECIFYING)
        await _make_spec(db_session, run)
        result = await validate_transition(db_session, run.id, RunStatus.PLANNING)
        assert result["allowed"]


# ═══════════════════════════════════════════════════════════════════
# FM-102: Constitution CRUD
# ═══════════════════════════════════════════════════════════════════


class TestFM102_Constitution:
    async def test_create_constitution(self, db_session, sample_project):
        from app.services.constitution_service import create_or_update_constitution
        from app.schemas.constitution import ConstitutionCreate

        data = ConstitutionCreate(
            content="Always write tests first.",
            title="TDD Constitution",
        )
        const = await create_or_update_constitution(
            db_session, sample_project.id, data
        )
        assert const.content == "Always write tests first."
        assert const.version == 1

    async def test_update_constitution_bumps_version(
        self, db_session, sample_project
    ):
        from app.services.constitution_service import create_or_update_constitution
        from app.schemas.constitution import ConstitutionCreate

        data1 = ConstitutionCreate(content="V1 content")
        await create_or_update_constitution(db_session, sample_project.id, data1)

        data2 = ConstitutionCreate(content="V2 content")
        const = await create_or_update_constitution(
            db_session, sample_project.id, data2
        )
        assert const.version == 2
        assert const.content == "V2 content"

    async def test_get_constitution(self, db_session, sample_project):
        from app.services.constitution_service import (
            create_or_update_constitution,
            get_constitution,
        )
        from app.schemas.constitution import ConstitutionCreate

        data = ConstitutionCreate(content="Test constitution")
        await create_or_update_constitution(db_session, sample_project.id, data)

        const = await get_constitution(db_session, sample_project.id)
        assert const is not None
        assert const.content == "Test constitution"

    async def test_delete_constitution(self, db_session, sample_project):
        from app.services.constitution_service import (
            create_or_update_constitution,
            delete_constitution,
            get_constitution,
        )
        from app.schemas.constitution import ConstitutionCreate

        data = ConstitutionCreate(content="To be deleted")
        await create_or_update_constitution(db_session, sample_project.id, data)

        deleted = await delete_constitution(db_session, sample_project.id)
        assert deleted is True

        const = await get_constitution(db_session, sample_project.id)
        assert const is None

    async def test_get_constitution_for_prompt(self, db_session, sample_project):
        from app.services.constitution_service import (
            create_or_update_constitution,
            get_constitution_for_prompt,
        )
        from app.schemas.constitution import ConstitutionCreate

        data = ConstitutionCreate(
            content="Always TDD",
            title="TDD Rules",
            summary="TDD summary",
        )
        await create_or_update_constitution(db_session, sample_project.id, data)

        prompt = await get_constitution_for_prompt(db_session, sample_project.id)
        assert prompt is not None
        assert "Always TDD" in prompt

    async def test_get_constitution_for_prompt_returns_none(
        self, db_session, sample_project
    ):
        from app.services.constitution_service import get_constitution_for_prompt

        prompt = await get_constitution_for_prompt(db_session, sample_project.id)
        assert prompt is None


# ═══════════════════════════════════════════════════════════════════
# FM-104: Slash command parsing
# ═══════════════════════════════════════════════════════════════════


class TestFM104_SlashCommands:
    def test_parse_specify(self):
        from app.services.slash_command_service import parse_command

        result = parse_command("/fm.specify Build a todo app")
        assert result is not None
        assert result.command == "specify"
        assert result.args == "Build a todo app"

    def test_parse_plan(self):
        from app.services.slash_command_service import parse_command

        result = parse_command("/fm.plan")
        assert result is not None
        assert result.command == "plan"
        assert result.args == ""

    def test_parse_tasks(self):
        from app.services.slash_command_service import parse_command

        result = parse_command("/fm.tasks")
        assert result is not None
        assert result.command == "tasks"

    def test_parse_implement(self):
        from app.services.slash_command_service import parse_command

        result = parse_command("/fm.implement")
        assert result is not None
        assert result.command == "implement"

    def test_parse_unknown_returns_none(self):
        from app.services.slash_command_service import parse_command

        result = parse_command("hello world")
        assert result is None

    def test_parse_unknown_command_returns_none(self):
        from app.services.slash_command_service import parse_command

        result = parse_command("/fm.unknown")
        assert result is None

    def test_is_slash_command(self):
        from app.services.slash_command_service import is_slash_command

        assert is_slash_command("/fm.specify something")
        assert not is_slash_command("just a normal message")

    def test_list_commands(self):
        from app.services.slash_command_service import list_commands

        cmds = list_commands()
        assert len(cmds) == 4
        names = [c["command"] for c in cmds]
        assert "/fm.specify" in names
        assert "/fm.plan" in names

    def test_case_insensitive_parsing(self):
        from app.services.slash_command_service import parse_command

        result = parse_command("/FM.SPECIFY  my app")
        assert result is not None
        assert result.command == "specify"


# ═══════════════════════════════════════════════════════════════════
# FM-105: Structured SPEC generation
# ═══════════════════════════════════════════════════════════════════


class TestFM105_SpecGeneration:
    async def test_generate_spec_stub(self, db_session, sample_project):
        from app.services.spec_service import generate_spec
        from app.models.run import RunStatus

        run = await _make_run(
            db_session, sample_project, status=RunStatus.PENDING
        )
        spec = await generate_spec(
            db_session,
            run_id=run.id,
            project_id=sample_project.id,
            user_prompt="Build a chat app",
        )
        assert spec.artifact_type.value == "spec"
        assert "Specification" in spec.content
        assert "Build a chat app" in spec.content
        # Run should transition to SPECIFYING
        await db_session.refresh(run)
        assert run.status == RunStatus.SPECIFYING

    async def test_generate_spec_with_prompt(self, db_session, sample_project):
        from app.services.spec_service import generate_spec

        run = await _make_run(db_session, sample_project)
        spec = await generate_spec(
            db_session,
            run_id=run.id,
            project_id=sample_project.id,
            user_prompt="Custom: build an API",
        )
        assert "Custom: build an API" in spec.content

    async def test_get_spec_for_run(self, db_session, sample_project):
        from app.services.spec_service import generate_spec, get_spec_for_run

        run = await _make_run(db_session, sample_project)
        await generate_spec(
            db_session, run_id=run.id, project_id=sample_project.id
        )
        found = await get_spec_for_run(db_session, run.id)
        assert found is not None
        assert found.artifact_type.value == "spec"

    async def test_get_spec_for_run_none(self, db_session, sample_project):
        from app.services.spec_service import get_spec_for_run

        run = await _make_run(db_session, sample_project)
        found = await get_spec_for_run(db_session, run.id)
        assert found is None


# ═══════════════════════════════════════════════════════════════════
# FM-106: PLAN artifact creation, linking, export
# ═══════════════════════════════════════════════════════════════════


class TestFM106_PlanArtifact:
    async def test_generate_plan_requires_spec(self, db_session, sample_project):
        from app.services.plan_artifact_service import generate_plan_artifact

        run = await _make_run(db_session, sample_project)

        with pytest.raises(ValueError, match="no SPEC"):
            await generate_plan_artifact(
                db_session, run_id=run.id, project_id=sample_project.id
            )

    async def test_generate_plan_links_to_spec(self, db_session, sample_project):
        from app.services.plan_artifact_service import generate_plan_artifact
        from app.models.run import RunStatus

        run = await _make_run(
            db_session, sample_project, status=RunStatus.SPECIFYING
        )
        spec = await _make_spec(db_session, run)

        plan = await generate_plan_artifact(
            db_session, run_id=run.id, project_id=sample_project.id
        )
        assert plan.spec_artifact_id == spec.id
        assert plan.artifact_type.value == "plan"
        # Run should transition to PLANNING
        await db_session.refresh(run)
        assert run.status == RunStatus.PLANNING

    async def test_export_plan_markdown(self, db_session, sample_project):
        from app.services.plan_artifact_service import export_plan_markdown

        run = await _make_run(db_session, sample_project)
        spec = await _make_spec(db_session, run)
        await _make_plan(db_session, run, spec)

        md = await export_plan_markdown(db_session, run.id)
        assert md is not None
        assert "PLAN" in md
        assert "SPEC" in md
        assert str(run.id) in md

    async def test_export_plan_returns_none_without_plan(
        self, db_session, sample_project
    ):
        from app.services.plan_artifact_service import export_plan_markdown

        run = await _make_run(db_session, sample_project)
        md = await export_plan_markdown(db_session, run.id)
        assert md is None


# ═══════════════════════════════════════════════════════════════════
# FM-108: Spec-to-plan validation
# ═══════════════════════════════════════════════════════════════════


class TestFM108_SpecPlanValidation:
    async def test_validation_fails_without_spec(self, db_session, sample_project):
        from app.services.spec_plan_validation_service import validate_spec_plan

        run = await _make_run(db_session, sample_project)
        result = await validate_spec_plan(db_session, run.id)
        assert not result.valid
        assert any(i.rule == "spec_exists" for i in result.issues)

    async def test_validation_fails_without_plan(self, db_session, sample_project):
        from app.services.spec_plan_validation_service import validate_spec_plan

        run = await _make_run(db_session, sample_project)
        await _make_spec(db_session, run)
        result = await validate_spec_plan(db_session, run.id)
        assert not result.valid
        assert any(i.rule == "plan_exists" for i in result.issues)

    async def test_validation_passes_with_good_plan(
        self, db_session, sample_project
    ):
        from app.services.spec_plan_validation_service import validate_spec_plan

        run = await _make_run(db_session, sample_project)
        spec = await _make_spec(db_session, run)
        await _make_plan(db_session, run, spec)
        result = await validate_spec_plan(db_session, run.id)
        assert result.valid

    async def test_validation_checks_plan_link(self, db_session, sample_project):
        from app.services.spec_plan_validation_service import validate_spec_plan
        from app.models.artifact import Artifact, ArtifactType

        run = await _make_run(db_session, sample_project)
        await _make_spec(db_session, run)
        # Create unlinked plan
        plan = Artifact(
            run_id=run.id,
            project_id=sample_project.id,
            artifact_type=ArtifactType.PLAN,
            title="Unlinked PLAN",
            content=(
                "# Execution Plan\n\n## Overview\nSome plan overview text.\n\n"
                "## Phase 1: Build\n- Build things\n"
            ),
        )
        db_session.add(plan)
        await db_session.flush()

        result = await validate_spec_plan(db_session, run.id)
        assert any(i.rule == "plan_linked_to_spec" for i in result.issues)

    async def test_to_dict(self, db_session, sample_project):
        from app.services.spec_plan_validation_service import validate_spec_plan

        run = await _make_run(db_session, sample_project)
        spec = await _make_spec(db_session, run)
        await _make_plan(db_session, run, spec)
        result = await validate_spec_plan(db_session, run.id)
        d = result.to_dict()
        assert "run_id" in d
        assert "valid" in d
        assert isinstance(d["issues"], list)
        assert isinstance(d["coverage"], dict)


# ═══════════════════════════════════════════════════════════════════
# FM-109: Approval integration for SPEC/PLAN
# ═══════════════════════════════════════════════════════════════════


class TestFM109_SpecPlanApproval:
    async def test_spec_approved_by_default(self, db_session, sample_project):
        from app.services.spec_plan_approval_service import is_spec_approved

        run = await _make_run(db_session, sample_project)
        assert await is_spec_approved(db_session, run.id)

    async def test_plan_approved_by_default(self, db_session, sample_project):
        from app.services.spec_plan_approval_service import is_plan_approved

        run = await _make_run(db_session, sample_project)
        assert await is_plan_approved(db_session, run.id)

    async def test_request_spec_approval(self, db_session, sample_project):
        from app.services.spec_plan_approval_service import (
            request_spec_approval,
            is_spec_approved,
        )

        run = await _make_run(db_session, sample_project)
        await _make_spec(db_session, run)

        approval = await request_spec_approval(
            db_session, run_id=run.id, project_id=sample_project.id
        )
        assert approval is not None
        assert approval.status.value == "pending"
        # Now spec should NOT be approved
        assert not await is_spec_approved(db_session, run.id)

    async def test_request_spec_approval_no_spec(self, db_session, sample_project):
        from app.services.spec_plan_approval_service import request_spec_approval

        run = await _make_run(db_session, sample_project)
        result = await request_spec_approval(
            db_session, run_id=run.id, project_id=sample_project.id
        )
        assert result is None

    async def test_approval_idempotent(self, db_session, sample_project):
        from app.services.spec_plan_approval_service import request_spec_approval

        run = await _make_run(db_session, sample_project)
        await _make_spec(db_session, run)

        a1 = await request_spec_approval(
            db_session, run_id=run.id, project_id=sample_project.id
        )
        a2 = await request_spec_approval(
            db_session, run_id=run.id, project_id=sample_project.id
        )
        assert a1.id == a2.id

    async def test_spec_approved_after_resolve(self, db_session, sample_project):
        from app.services.spec_plan_approval_service import (
            request_spec_approval,
            is_spec_approved,
        )
        from app.services.approval_service import resolve_approval
        from app.schemas.approval import ApprovalDecision
        from app.models.approval_request import ApprovalStatus

        run = await _make_run(db_session, sample_project)
        await _make_spec(db_session, run)

        approval = await request_spec_approval(
            db_session, run_id=run.id, project_id=sample_project.id
        )
        await resolve_approval(
            db_session,
            approval.id,
            ApprovalDecision(
                status=ApprovalStatus.APPROVED,
                comment="Looks good",
            ),
        )
        assert await is_spec_approved(db_session, run.id)

    async def test_get_artifact_approval_status(self, db_session, sample_project):
        from app.services.spec_plan_approval_service import get_artifact_approval_status

        run = await _make_run(db_session, sample_project)
        await _make_spec(db_session, run)

        status_data = await get_artifact_approval_status(db_session, run.id)
        assert "spec" in status_data
        assert "plan" in status_data
        assert status_data["spec"]["exists"] is True
        assert status_data["plan"]["exists"] is False


# ═══════════════════════════════════════════════════════════════════
# FM-110: End-to-end lifecycle hardening
# ═══════════════════════════════════════════════════════════════════


class TestFM110_E2E:
    async def test_full_lifecycle_spec_plan_run(self, db_session, sample_project):
        """Walk through PENDING → SPECIFYING → PLANNING → RUNNING with proper gating."""
        from app.services.run_lifecycle_service import transition_run, validate_transition
        from app.services.spec_service import generate_spec
        from app.services.plan_artifact_service import generate_plan_artifact
        from app.models.run import RunStatus

        # Create run
        run = await _make_run(db_session, sample_project)
        assert run.status == RunStatus.PENDING

        # Generate SPEC → transitions to SPECIFYING
        spec = await generate_spec(
            db_session,
            run_id=run.id,
            project_id=sample_project.id,
            user_prompt="Build a REST API",
        )
        await db_session.refresh(run)
        assert run.status == RunStatus.SPECIFYING

        # Validate: can now go to PLANNING
        v = await validate_transition(db_session, run.id, RunStatus.PLANNING)
        assert v["allowed"]

        # Transition to PLANNING
        result = await transition_run(db_session, run.id, RunStatus.PLANNING)
        assert result["transitioned"]
        await db_session.refresh(run)
        assert run.status == RunStatus.PLANNING

        # Generate PLAN → should stay in PLANNING (already there)
        plan = await generate_plan_artifact(
            db_session, run_id=run.id, project_id=sample_project.id
        )
        assert plan.spec_artifact_id == spec.id

        # Validate: can now go to RUNNING
        v = await validate_transition(db_session, run.id, RunStatus.RUNNING)
        assert v["allowed"]

        # Transition to RUNNING
        result = await transition_run(db_session, run.id, RunStatus.RUNNING)
        assert result["transitioned"]
        await db_session.refresh(run)
        assert run.status == RunStatus.RUNNING

    async def test_cannot_skip_spec(self, db_session, sample_project):
        """Cannot go from PENDING to PLANNING directly."""
        from app.services.run_lifecycle_service import validate_transition
        from app.models.run import RunStatus

        run = await _make_run(
            db_session, sample_project, status=RunStatus.PENDING
        )
        v = await validate_transition(db_session, run.id, RunStatus.PLANNING)
        assert not v["allowed"]

    async def test_cannot_skip_plan(self, db_session, sample_project):
        """Cannot go from SPECIFYING to RUNNING directly."""
        from app.services.run_lifecycle_service import validate_transition
        from app.models.run import RunStatus

        run = await _make_run(
            db_session, sample_project, status=RunStatus.SPECIFYING
        )
        v = await validate_transition(db_session, run.id, RunStatus.RUNNING)
        assert not v["allowed"]

    async def test_planning_to_running_blocked_without_plan(
        self, db_session, sample_project
    ):
        from app.services.run_lifecycle_service import validate_transition
        from app.models.run import RunStatus

        run = await _make_run(
            db_session, sample_project, status=RunStatus.PLANNING
        )
        await _make_spec(db_session, run)
        v = await validate_transition(db_session, run.id, RunStatus.RUNNING)
        assert not v["allowed"]


# ═══════════════════════════════════════════════════════════════════
# HTTP route integration tests
# ═══════════════════════════════════════════════════════════════════


class TestFM_Routes:
    async def test_chat_slash_command(self, client, sample_run):
        """POST /runs/{id}/chat with /fm.tasks returns command result."""
        resp = await client.post(
            f"/runs/{sample_run.id}/chat",
            json={"message": "/fm.tasks"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["command_result"] is not None
        assert data["command_result"]["command"] == "tasks"

    async def test_chat_normal_message(self, client, sample_run):
        """Regular chat still works."""
        resp = await client.post(
            f"/runs/{sample_run.id}/chat",
            json={"message": "What is blocked?"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["command_result"] is None
        assert data["reply"]

    async def test_list_slash_commands(self, client):
        """GET /chat/commands returns available commands."""
        resp = await client.get("/chat/commands")
        assert resp.status_code == 200
        data = resp.json()
        assert "commands" in data
        assert len(data["commands"]) == 4

    async def test_constitution_crud_via_api(self, client, sample_project):
        """PUT then GET constitution via API."""
        pid = str(sample_project.id)
        # PUT
        resp = await client.put(
            f"/projects/{pid}/constitution",
            json={"content": "Always TDD", "title": "TDD Rules"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["content"] == "Always TDD"

        # GET
        resp = await client.get(f"/projects/{pid}/constitution")
        assert resp.status_code == 200
        assert resp.json()["content"] == "Always TDD"

        # DELETE
        resp = await client.delete(f"/projects/{pid}/constitution")
        assert resp.status_code == 204

    async def test_spec_plan_validate_endpoint(self, client, sample_run):
        """GET /lifecycle/runs/{id}/spec-plan/validate."""
        resp = await client.get(
            f"/lifecycle/runs/{sample_run.id}/spec-plan/validate"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "valid" in data
        assert "issues" in data


# ═══════════════════════════════════════════════════════════════════
# FM-103: Governance events for constitution mutations
# ═══════════════════════════════════════════════════════════════════


class TestFM103_GovernanceEvents:
    async def test_constitution_create_emits_event(self, db_session, sample_project):
        """Creating a constitution emits CONSTITUTION_UPDATED event."""
        from app.models.execution_event import ExecutionEvent, EventType
        from app.services import constitution_service
        from app.schemas.constitution import ConstitutionCreate

        data = ConstitutionCreate(
            title="Governance Rules",
            content="Always write tests first",
        )
        await constitution_service.create_or_update_constitution(
            db_session, project_id=sample_project.id, data=data
        )
        await db_session.flush()

        result = await db_session.execute(
            select(ExecutionEvent).where(
                ExecutionEvent.project_id == sample_project.id,
                ExecutionEvent.event_type == EventType.CONSTITUTION_UPDATED,
            )
        )
        events = list(result.scalars().all())
        assert len(events) >= 1

    async def test_constitution_update_emits_event(self, db_session, sample_project):
        """Updating a constitution emits another CONSTITUTION_UPDATED event."""
        from app.models.execution_event import ExecutionEvent, EventType
        from app.services import constitution_service
        from app.schemas.constitution import ConstitutionCreate

        data = ConstitutionCreate(title="V1", content="Rule 1")
        await constitution_service.create_or_update_constitution(
            db_session, project_id=sample_project.id, data=data
        )
        await db_session.flush()

        data2 = ConstitutionCreate(title="V2", content="Rule 1 updated")
        await constitution_service.create_or_update_constitution(
            db_session, project_id=sample_project.id, data=data2
        )
        await db_session.flush()

        result = await db_session.execute(
            select(ExecutionEvent).where(
                ExecutionEvent.project_id == sample_project.id,
                ExecutionEvent.event_type == EventType.CONSTITUTION_UPDATED,
            )
        )
        events = list(result.scalars().all())
        assert len(events) >= 2

    async def test_constitution_delete_emits_event(self, db_session, sample_project):
        """Deleting a constitution emits CONSTITUTION_UPDATED event."""
        from app.models.execution_event import ExecutionEvent, EventType
        from app.services import constitution_service
        from app.schemas.constitution import ConstitutionCreate

        data = ConstitutionCreate(title="Delete me", content="Temporary")
        await constitution_service.create_or_update_constitution(
            db_session, project_id=sample_project.id, data=data
        )
        await db_session.flush()

        await constitution_service.delete_constitution(
            db_session, project_id=sample_project.id
        )
        await db_session.flush()

        result = await db_session.execute(
            select(ExecutionEvent).where(
                ExecutionEvent.project_id == sample_project.id,
                ExecutionEvent.event_type == EventType.CONSTITUTION_UPDATED,
            )
        )
        events = list(result.scalars().all())
        # At least 2: one for create, one for delete
        assert len(events) >= 2


# ═══════════════════════════════════════════════════════════════════
# FM-107: ADR-aware enrichment
# ═══════════════════════════════════════════════════════════════════


class TestFM107_ADREnrichment:
    async def test_build_adr_section_no_data(self, db_session, sample_project):
        """build_adr_section returns None when project has no architecture data."""
        from app.services import adr_service

        result = await adr_service.build_adr_section(
            db_session, project_id=sample_project.id
        )
        assert result is None

    async def test_build_adr_section_with_nodes(self, db_session, sample_project):
        """build_adr_section returns ADR markdown when architecture nodes exist."""
        from app.models.architecture import (
            ArchitectureNode, NodeType, SourceType,
        )
        from app.services import adr_service

        node = ArchitectureNode(
            project_id=sample_project.id,
            node_type=NodeType.SERVICE,
            key="api-service",
            name="API Service",
            path="apps/api",
            source_type=SourceType.DECLARED,
        )
        db_session.add(node)
        await db_session.flush()

        result = await adr_service.build_adr_section(
            db_session, project_id=sample_project.id
        )
        assert result is not None
        assert "Architecture Decision Records" in result
        assert "ADR-001" in result
        assert "1 service(s)" in result

    async def test_enrich_plan_with_adr_appends(self, db_session, sample_project):
        """enrich_plan_with_adr appends ADR section to plan content."""
        from app.models.architecture import (
            ArchitectureNode, NodeType, SourceType,
        )
        from app.services import adr_service

        node = ArchitectureNode(
            project_id=sample_project.id,
            node_type=NodeType.MODULE,
            key="core-module",
            name="Core Module",
            path="apps/core",
            source_type=SourceType.DECLARED,
        )
        db_session.add(node)
        await db_session.flush()

        plan = "# Execution Plan\n\nBuild stuff."
        enriched = await adr_service.enrich_plan_with_adr(
            db_session, project_id=sample_project.id, plan_content=plan
        )
        assert enriched.startswith(plan)
        assert "Architecture Decision Records" in enriched
