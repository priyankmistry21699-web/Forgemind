"""FM-111–120: Comprehensive tests for Phase Routing, Templates, and Project Bootstrapping.

Covers:
  FM-111: PhaseAgentProfile CRUD
  FM-112: resolve_agent_for_phase routing
  FM-113: Phase profile API endpoints (tested via HTTP)
  FM-114: ProjectTemplate CRUD and built-in seeding
  FM-115: Template-based project creation
  FM-116: Template inheritance resolution
  FM-117: Constitution suggestion generation and resolution
  FM-118: Template influence on spec/plan context
  FM-119: Local config template_slug / phase_profiles
  FM-120: Integration hardening
"""

import uuid
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import STUB_USER_ID


# ── Helpers ──────────────────────────────────────────────────────


async def _seed_agent(db: AsyncSession, *, slug: str = "test-agent", name: str = "Test Agent", capabilities: list | None = None):
    from app.models.agent import Agent, AgentStatus

    agent = Agent(
        name=name,
        slug=slug,
        description="Agent for testing",
        status=AgentStatus.ACTIVE,
        capabilities=capabilities or ["coding", "architecture"],
        supported_task_types=["coding", "architecture"],
    )
    db.add(agent)
    await db.flush()
    await db.refresh(agent)
    return agent


async def _seed_project(db: AsyncSession, **kwargs):
    from app.models.project import Project
    from app.models.membership import ProjectMember, ProjectRole

    project = Project(
        name=kwargs.get("name", "Template Test Project"),
        description=kwargs.get("description", "Testing templates"),
        owner_id=STUB_USER_ID,
        template_id=kwargs.get("template_id"),
    )
    db.add(project)
    await db.flush()
    await db.refresh(project)
    lead = ProjectMember(
        project_id=project.id,
        user_id=STUB_USER_ID,
        role=ProjectRole.LEAD,
    )
    db.add(lead)
    await db.flush()
    return project


# ═════════════════════════════════════════════════════════════════
# FM-111: PhaseAgentProfile model & service
# ═════════════════════════════════════════════════════════════════


class TestPhaseAgentProfileService:
    """FM-111: CRUD operations for phase-agent profiles."""

    @pytest.mark.asyncio
    async def test_upsert_creates_profile(self, db_session):
        from app.services import phase_agent_profile_service
        from app.schemas.phase_agent_profile import PhaseAgentProfileCreate
        from app.models.phase_agent_profile import WorkflowPhase

        agent = await _seed_agent(db_session, slug="spec-agent")
        project = await _seed_project(db_session)

        data = PhaseAgentProfileCreate(
            phase=WorkflowPhase.SPECIFY,
            agent_id=agent.id,
        )
        profile = await phase_agent_profile_service.upsert_profile(
            db_session, project.id, data
        )

        assert profile is not None
        assert profile.phase == WorkflowPhase.SPECIFY
        assert profile.agent_id == agent.id
        assert profile.project_id == project.id

    @pytest.mark.asyncio
    async def test_upsert_updates_existing(self, db_session):
        from app.services import phase_agent_profile_service
        from app.schemas.phase_agent_profile import PhaseAgentProfileCreate
        from app.models.phase_agent_profile import WorkflowPhase

        agent1 = await _seed_agent(db_session, slug="agent-a")
        agent2 = await _seed_agent(db_session, slug="agent-b", name="Agent B")
        project = await _seed_project(db_session)

        data1 = PhaseAgentProfileCreate(phase=WorkflowPhase.PLAN, agent_id=agent1.id)
        await phase_agent_profile_service.upsert_profile(db_session, project.id, data1)

        data2 = PhaseAgentProfileCreate(phase=WorkflowPhase.PLAN, agent_id=agent2.id)
        profile = await phase_agent_profile_service.upsert_profile(
            db_session, project.id, data2
        )

        assert profile.agent_id == agent2.id

    @pytest.mark.asyncio
    async def test_upsert_rejects_nonexistent_agent(self, db_session):
        from app.services import phase_agent_profile_service
        from app.schemas.phase_agent_profile import PhaseAgentProfileCreate
        from app.models.phase_agent_profile import WorkflowPhase

        project = await _seed_project(db_session)
        data = PhaseAgentProfileCreate(
            phase=WorkflowPhase.REVIEW,
            agent_id=uuid.uuid4(),
        )
        with pytest.raises(ValueError, match="not found"):
            await phase_agent_profile_service.upsert_profile(
                db_session, project.id, data
            )

    @pytest.mark.asyncio
    async def test_list_profiles(self, db_session):
        from app.services import phase_agent_profile_service
        from app.schemas.phase_agent_profile import PhaseAgentProfileCreate
        from app.models.phase_agent_profile import WorkflowPhase

        agent = await _seed_agent(db_session, slug="list-agent")
        project = await _seed_project(db_session)

        for phase in [WorkflowPhase.SPECIFY, WorkflowPhase.PLAN]:
            data = PhaseAgentProfileCreate(phase=phase, agent_id=agent.id)
            await phase_agent_profile_service.upsert_profile(
                db_session, project.id, data
            )

        items, total = await phase_agent_profile_service.list_profiles(
            db_session, project.id
        )
        assert total == 2
        assert len(items) == 2

    @pytest.mark.asyncio
    async def test_delete_profile(self, db_session):
        from app.services import phase_agent_profile_service
        from app.schemas.phase_agent_profile import PhaseAgentProfileCreate
        from app.models.phase_agent_profile import WorkflowPhase

        agent = await _seed_agent(db_session, slug="del-agent")
        project = await _seed_project(db_session)

        data = PhaseAgentProfileCreate(
            phase=WorkflowPhase.IMPLEMENT, agent_id=agent.id
        )
        await phase_agent_profile_service.upsert_profile(
            db_session, project.id, data
        )

        deleted = await phase_agent_profile_service.delete_profile(
            db_session, project.id, WorkflowPhase.IMPLEMENT
        )
        assert deleted is True

        deleted_again = await phase_agent_profile_service.delete_profile(
            db_session, project.id, WorkflowPhase.IMPLEMENT
        )
        assert deleted_again is False

    @pytest.mark.asyncio
    async def test_get_agent_slug_for_phase(self, db_session):
        from app.services import phase_agent_profile_service
        from app.schemas.phase_agent_profile import PhaseAgentProfileCreate
        from app.models.phase_agent_profile import WorkflowPhase

        agent = await _seed_agent(db_session, slug="slug-agent")
        project = await _seed_project(db_session)

        data = PhaseAgentProfileCreate(
            phase=WorkflowPhase.VALIDATE, agent_id=agent.id
        )
        await phase_agent_profile_service.upsert_profile(
            db_session, project.id, data
        )

        slug = await phase_agent_profile_service.get_agent_slug_for_phase(
            db_session, project.id, WorkflowPhase.VALIDATE
        )
        assert slug == "slug-agent"

    @pytest.mark.asyncio
    async def test_get_agent_slug_returns_none_if_missing(self, db_session):
        from app.services import phase_agent_profile_service
        from app.models.phase_agent_profile import WorkflowPhase

        project = await _seed_project(db_session)
        slug = await phase_agent_profile_service.get_agent_slug_for_phase(
            db_session, project.id, WorkflowPhase.REVIEW
        )
        assert slug is None


# ═════════════════════════════════════════════════════════════════
# FM-112: resolve_agent_for_phase via composition_service
# ═════════════════════════════════════════════════════════════════


class TestResolveAgentForPhase:
    """FM-112: Phase-aware agent routing in composition_service."""

    @pytest.mark.asyncio
    async def test_routes_via_profile(self, db_session):
        from app.services import phase_agent_profile_service, composition_service
        from app.schemas.phase_agent_profile import PhaseAgentProfileCreate
        from app.models.phase_agent_profile import WorkflowPhase

        agent = await _seed_agent(db_session, slug="routed-agent")
        project = await _seed_project(db_session)

        data = PhaseAgentProfileCreate(
            phase=WorkflowPhase.SPECIFY, agent_id=agent.id
        )
        await phase_agent_profile_service.upsert_profile(
            db_session, project.id, data
        )

        slug, source = await composition_service.resolve_agent_for_phase(
            db_session, project.id, "specify"
        )
        assert slug == "routed-agent"
        assert source == "phase_profile"

    @pytest.mark.asyncio
    async def test_fallback_to_capability_scoring(self, db_session):
        from app.services import composition_service

        await _seed_agent(db_session, slug="fallback-agent", capabilities=["coding"])
        project = await _seed_project(db_session)

        slug, source = await composition_service.resolve_agent_for_phase(
            db_session,
            project.id,
            "implement",
            fallback_task_type="coding",
        )
        # Might resolve or not depending on capability scoring
        assert source in ("phase_profile", "capability_fallback")


# ═════════════════════════════════════════════════════════════════
# FM-114: ProjectTemplate CRUD and seeding
# ═════════════════════════════════════════════════════════════════


class TestProjectTemplateService:
    """FM-114: Template management and built-in seeding."""

    @pytest.mark.asyncio
    async def test_seed_builtin_templates(self, db_session):
        from app.services import project_template_service

        await project_template_service.seed_builtin_templates(db_session)
        await db_session.commit()

        items, total = await project_template_service.list_templates(db_session)
        assert total >= 4  # rest-api, frontend-app, data-pipeline, cli-tool
        slugs = {t.slug for t in items}
        assert "rest-api" in slugs
        assert "frontend-app" in slugs
        assert "data-pipeline" in slugs
        assert "cli-tool" in slugs

    @pytest.mark.asyncio
    async def test_idempotent_seeding(self, db_session):
        from app.services import project_template_service

        await project_template_service.seed_builtin_templates(db_session)
        await db_session.commit()
        items1, total1 = await project_template_service.list_templates(db_session)

        await project_template_service.seed_builtin_templates(db_session)
        await db_session.commit()
        items2, total2 = await project_template_service.list_templates(db_session)

        assert total1 == total2

    @pytest.mark.asyncio
    async def test_get_template_by_slug(self, db_session):
        from app.services import project_template_service

        await project_template_service.seed_builtin_templates(db_session)
        await db_session.commit()

        template = await project_template_service.get_template_by_slug(
            db_session, "rest-api"
        )
        assert template is not None
        assert template.name == "REST API Service"
        assert template.is_builtin is True

    @pytest.mark.asyncio
    async def test_create_custom_template(self, db_session):
        from app.services import project_template_service
        from app.schemas.project_template import ProjectTemplateCreate

        data = ProjectTemplateCreate(
            slug="my-custom",
            name="My Custom Template",
            description="Custom template",
            category="custom",
        )
        template = await project_template_service.create_template(db_session, data)
        assert template.slug == "my-custom"
        assert template.is_builtin is False

    @pytest.mark.asyncio
    async def test_filter_by_category(self, db_session):
        from app.services import project_template_service

        await project_template_service.seed_builtin_templates(db_session)
        await db_session.commit()

        items, total = await project_template_service.list_templates(
            db_session, category="backend"
        )
        assert total >= 1
        assert all(t.category == "backend" for t in items)


# ═════════════════════════════════════════════════════════════════
# FM-115: Template-based project creation
# ═════════════════════════════════════════════════════════════════


class TestTemplateProjectCreation:
    """FM-115: Creating a project from a template."""

    @pytest.mark.asyncio
    async def test_create_project_with_template(self, db_session):
        from app.services import project_template_service, project_service
        from app.schemas.project import ProjectCreate

        await project_template_service.seed_builtin_templates(db_session)
        await db_session.commit()

        template = await project_template_service.get_template_by_slug(
            db_session, "rest-api"
        )
        assert template is not None

        data = ProjectCreate(
            name="My REST API",
            description="A new REST API project",
            template_id=template.id,
        )
        project = await project_service.create_project(
            db_session, data, owner_id=STUB_USER_ID
        )

        assert project.template_id == template.id

    @pytest.mark.asyncio
    async def test_create_project_without_template(self, db_session):
        from app.services import project_service
        from app.schemas.project import ProjectCreate

        data = ProjectCreate(name="Blank Project")
        project = await project_service.create_project(
            db_session, data, owner_id=STUB_USER_ID
        )
        assert project.template_id is None


# ═════════════════════════════════════════════════════════════════
# FM-116: Template inheritance resolution
# ═════════════════════════════════════════════════════════════════


class TestTemplateInheritance:
    """FM-116: Governance config inheritance (system → template → project)."""

    @pytest.mark.asyncio
    async def test_system_defaults(self):
        from app.services.template_inheritance_service import (
            resolve_governance_config,
            SYSTEM_DEFAULTS,
        )

        result = resolve_governance_config(template=None, project_override=None)
        assert result == SYSTEM_DEFAULTS["governance"]

    @pytest.mark.asyncio
    async def test_template_overrides_system(self, db_session):
        from app.services import project_template_service
        from app.services.template_inheritance_service import (
            resolve_governance_config,
        )

        await project_template_service.seed_builtin_templates(db_session)
        await db_session.commit()
        template = await project_template_service.get_template_by_slug(
            db_session, "rest-api"
        )

        result = resolve_governance_config(
            template=template, project_override=None
        )
        # rest-api template requires both spec + plan approval
        assert result["require_spec_approval"] is True
        assert result["require_plan_approval"] is True

    @pytest.mark.asyncio
    async def test_project_overrides_template(self, db_session):
        from app.services import project_template_service
        from app.services.template_inheritance_service import (
            resolve_governance_config,
        )

        await project_template_service.seed_builtin_templates(db_session)
        await db_session.commit()
        template = await project_template_service.get_template_by_slug(
            db_session, "rest-api"
        )

        override = {"require_plan_approval": False}
        result = resolve_governance_config(
            template=template, project_override=override
        )
        assert result["require_spec_approval"] is True  # from template
        assert result["require_plan_approval"] is False  # from project override


# ═════════════════════════════════════════════════════════════════
# FM-117: Constitution suggestions
# ═════════════════════════════════════════════════════════════════


class TestConstitutionSuggestions:
    """FM-117: Generate, list, and resolve constitution suggestions."""

    @pytest.mark.asyncio
    async def test_generate_with_no_history(self, db_session):
        from app.services import constitution_suggestion_service

        project = await _seed_project(db_session)
        await db_session.commit()

        suggestions = await constitution_suggestion_service.generate_suggestions(
            db_session, project.id
        )
        # With no run history, few or no suggestions should fire
        assert isinstance(suggestions, list)

    @pytest.mark.asyncio
    async def test_list_suggestions_empty(self, db_session):
        from app.services import constitution_suggestion_service

        project = await _seed_project(db_session)
        await db_session.commit()

        items, total = await constitution_suggestion_service.list_suggestions(
            db_session, project.id
        )
        assert total == 0
        assert items == []

    @pytest.mark.asyncio
    async def test_resolve_suggestion_accept(self, db_session):
        from app.services import constitution_suggestion_service
        from app.models.constitution_suggestion import (
            ConstitutionSuggestion,
            SuggestionStatus,
        )
        from app.models.project_constitution import ProjectConstitution

        project = await _seed_project(db_session)

        # Create constitution
        constitution = ProjectConstitution(
            project_id=project.id,
            content="# Constitution\nExisting rules.",
        )
        db_session.add(constitution)

        # Create suggestion manually
        suggestion = ConstitutionSuggestion(
            project_id=project.id,
            title="Add testing rule",
            rationale="Tests improve quality",
            suggested_text="All PRs must have tests.",
            category="testing",
            status=SuggestionStatus.PENDING,
        )
        db_session.add(suggestion)
        await db_session.flush()
        await db_session.refresh(suggestion)

        resolved = await constitution_suggestion_service.resolve_suggestion(
            db_session, suggestion.id, "accept"
        )
        assert resolved.status == SuggestionStatus.ACCEPTED

        # Constitution should be updated
        await db_session.refresh(constitution)
        assert "All PRs must have tests." in constitution.content

    @pytest.mark.asyncio
    async def test_resolve_suggestion_reject(self, db_session):
        from app.services import constitution_suggestion_service
        from app.models.constitution_suggestion import (
            ConstitutionSuggestion,
            SuggestionStatus,
        )

        project = await _seed_project(db_session)
        suggestion = ConstitutionSuggestion(
            project_id=project.id,
            title="Rejected rule",
            rationale="Not applicable",
            suggested_text="Should not appear.",
            category="misc",
            status=SuggestionStatus.PENDING,
        )
        db_session.add(suggestion)
        await db_session.flush()
        await db_session.refresh(suggestion)

        resolved = await constitution_suggestion_service.resolve_suggestion(
            db_session, suggestion.id, "reject"
        )
        assert resolved.status == SuggestionStatus.REJECTED

    @pytest.mark.asyncio
    async def test_resolve_already_resolved(self, db_session):
        from app.services import constitution_suggestion_service
        from app.models.constitution_suggestion import (
            ConstitutionSuggestion,
            SuggestionStatus,
        )

        project = await _seed_project(db_session)
        suggestion = ConstitutionSuggestion(
            project_id=project.id,
            title="Already done",
            rationale="Not relevant",
            suggested_text="...",
            status=SuggestionStatus.ACCEPTED,
        )
        db_session.add(suggestion)
        await db_session.flush()
        await db_session.refresh(suggestion)

        with pytest.raises(ValueError, match="already"):
            await constitution_suggestion_service.resolve_suggestion(
                db_session, suggestion.id, "reject"
            )


# ═════════════════════════════════════════════════════════════════
# FM-118: Template influence on spec/plan context
# ═════════════════════════════════════════════════════════════════


class TestTemplateSpecPlanInfluence:
    """FM-118: Template defaults enrich spec/plan generation prompts."""

    @pytest.mark.asyncio
    async def test_spec_context_from_template(self, db_session):
        from app.services.spec_service import _get_template_spec_context
        from app.services import project_template_service

        await project_template_service.seed_builtin_templates(db_session)
        await db_session.commit()

        template = await project_template_service.get_template_by_slug(
            db_session, "rest-api"
        )
        project = await _seed_project(db_session, template_id=template.id)
        await db_session.commit()

        context = await _get_template_spec_context(db_session, project.id)
        assert context is not None
        assert "SPEC sections" in context or "spec sections" in context.lower()

    @pytest.mark.asyncio
    async def test_spec_context_none_without_template(self, db_session):
        from app.services.spec_service import _get_template_spec_context

        project = await _seed_project(db_session)
        await db_session.commit()

        context = await _get_template_spec_context(db_session, project.id)
        assert context is None

    @pytest.mark.asyncio
    async def test_plan_context_from_template(self, db_session):
        from app.services.plan_artifact_service import _get_template_plan_context
        from app.services import project_template_service

        await project_template_service.seed_builtin_templates(db_session)
        await db_session.commit()

        template = await project_template_service.get_template_by_slug(
            db_session, "rest-api"
        )
        project = await _seed_project(db_session, template_id=template.id)
        await db_session.commit()

        context = await _get_template_plan_context(db_session, project.id)
        assert context is not None
        assert "workstream" in context.lower() or "checklist" in context.lower()

    @pytest.mark.asyncio
    async def test_plan_context_none_without_template(self, db_session):
        from app.services.plan_artifact_service import _get_template_plan_context

        project = await _seed_project(db_session)
        await db_session.commit()

        context = await _get_template_plan_context(db_session, project.id)
        assert context is None


# ═════════════════════════════════════════════════════════════════
# FM-119: Local mode template/phase awareness
# ═════════════════════════════════════════════════════════════════


class TestLocalModeConfig:
    """FM-119: LocalConfig carries template slug and phase profiles."""

    @pytest.fixture(autouse=True)
    def _add_local_to_path(self):
        import sys
        local_root = str(Path(__file__).resolve().parents[2] / "local")
        sys.path.insert(0, local_root)
        yield
        sys.path.remove(local_root)

    def test_default_config_has_template_fields(self, tmp_path):
        from forgemind_local.config import LocalConfig

        cfg = LocalConfig.default(str(tmp_path))
        assert cfg.template_slug == ""
        assert cfg.phase_profiles == {}

    def test_round_trip_with_template_fields(self, tmp_path):
        from forgemind_local.config import (
            LocalConfig,
            save_config,
            load_config,
        )

        cfg = LocalConfig.default(str(tmp_path))
        cfg.template_slug = "rest-api"
        cfg.phase_profiles = {"specify": "spec-agent", "plan": "plan-agent"}
        save_config(cfg)

        loaded = load_config(str(tmp_path))
        assert loaded is not None
        assert loaded.template_slug == "rest-api"
        assert loaded.phase_profiles == {
            "specify": "spec-agent",
            "plan": "plan-agent",
        }

    def test_serialization_includes_template_fields(self):
        from forgemind_local.config import LocalConfig

        cfg = LocalConfig(template_slug="cli-tool", phase_profiles={"review": "review-bot"})
        d = cfg.to_dict()
        assert d["template_slug"] == "cli-tool"
        assert d["phase_profiles"] == {"review": "review-bot"}


# ═════════════════════════════════════════════════════════════════
# FM-113/120: HTTP endpoint smoke tests
# ═════════════════════════════════════════════════════════════════


class TestPhaseProfileEndpoints:
    """FM-113: Phase profile CRUD via HTTP."""

    @pytest.mark.asyncio
    async def test_list_profiles_empty(self, client, sample_project):
        resp = await client.get(
            f"/projects/{sample_project.id}/phase-agent-profiles"
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["items"] == []
        assert body["total"] == 0

    @pytest.mark.asyncio
    async def test_put_delete_profile(self, client, sample_project, db_session):
        agent = await _seed_agent(db_session, slug="http-agent")
        await db_session.commit()

        # PUT to create
        resp = await client.put(
            f"/projects/{sample_project.id}/phase-agent-profiles/specify",
            json={
                "phase": "specify",
                "agent_id": str(agent.id),
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["phase"] == "specify"

        # GET to verify
        resp = await client.get(
            f"/projects/{sample_project.id}/phase-agent-profiles/specify"
        )
        assert resp.status_code == 200

        # DELETE
        resp = await client.delete(
            f"/projects/{sample_project.id}/phase-agent-profiles/specify"
        )
        assert resp.status_code == 204


class TestTemplateEndpoints:
    """FM-114: Template listing via HTTP."""

    @pytest.mark.asyncio
    async def test_list_templates(self, client, db_session):
        from app.services import project_template_service

        await project_template_service.seed_builtin_templates(db_session)
        await db_session.commit()

        resp = await client.get("/templates")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] >= 4

    @pytest.mark.asyncio
    async def test_get_template_not_found(self, client):
        fake_id = str(uuid.uuid4())
        resp = await client.get(f"/templates/{fake_id}")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_create_custom_template_endpoint(self, client):
        resp = await client.post(
            "/templates",
            json={
                "slug": "e2e-custom",
                "name": "E2E Custom",
                "category": "testing",
            },
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["slug"] == "e2e-custom"


class TestConstitutionSuggestionEndpoints:
    """FM-117: Constitution suggestion endpoints via HTTP."""

    @pytest.mark.asyncio
    async def test_generate_suggestions_endpoint(self, client, sample_project):
        resp = await client.post(
            f"/projects/{sample_project.id}/constitution-suggestions/generate"
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body

    @pytest.mark.asyncio
    async def test_list_suggestions_endpoint(self, client, sample_project):
        resp = await client.get(
            f"/projects/{sample_project.id}/constitution-suggestions"
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 0
