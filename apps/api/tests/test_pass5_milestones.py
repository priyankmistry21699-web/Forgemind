"""Pass 5 milestone tests — FM-142, FM-147, FM-148, FM-152, FM-155, FM-156,
FM-158, FM-163, FM-164, FM-165, FM-166, FM-172, FM-176.

Tests all new service functions, models, and route endpoints added in Pass 5.
"""

import uuid
from datetime import datetime, timezone, timedelta

import pytest
import pytest_asyncio
from tests.conftest import STUB_USER_ID


# ═══════════════════════════════════════════════════════════════════
# FM-147: Task Assignment Events
# ═══════════════════════════════════════════════════════════════════


class TestFM147AssignmentEvents:
    """Test that task assign/unassign emits execution events."""

    async def test_assign_task_emits_event(self, db_session, sample_task):
        from app.services import task_assignment_service
        from app.models.execution_event import EventType

        task = await task_assignment_service.assign_task(
            db_session,
            sample_task.id,
            STUB_USER_ID,
        )
        assert task.assignee_id == STUB_USER_ID

        # Check for emitted event
        from sqlalchemy import select
        from app.models.execution_event import ExecutionEvent

        result = await db_session.execute(
            select(ExecutionEvent).where(
                ExecutionEvent.event_type == EventType.TASK_ASSIGNED,
            )
        )
        events = list(result.scalars().all())
        assert len(events) >= 1
        ev = events[-1]
        assert ev.metadata_["assignee_id"] == str(STUB_USER_ID)

    async def test_reassign_task_emits_reassigned_event(
        self,
        db_session,
        sample_task,
    ):
        from app.services import task_assignment_service
        from app.models.execution_event import EventType, ExecutionEvent
        from sqlalchemy import select

        user2 = uuid.uuid4()
        await task_assignment_service.assign_task(
            db_session,
            sample_task.id,
            STUB_USER_ID,
        )
        await task_assignment_service.assign_task(
            db_session,
            sample_task.id,
            user2,
        )

        result = await db_session.execute(
            select(ExecutionEvent).where(
                ExecutionEvent.event_type == EventType.TASK_REASSIGNED,
            )
        )
        events = list(result.scalars().all())
        assert len(events) >= 1
        ev = events[-1]
        assert ev.metadata_["previous_assignee_id"] == str(STUB_USER_ID)
        assert ev.metadata_["assignee_id"] == str(user2)

    async def test_unassign_task_emits_event(self, db_session, sample_task):
        from app.services import task_assignment_service
        from app.models.execution_event import EventType, ExecutionEvent
        from sqlalchemy import select

        await task_assignment_service.assign_task(
            db_session,
            sample_task.id,
            STUB_USER_ID,
        )
        await task_assignment_service.unassign_task(db_session, sample_task.id)

        result = await db_session.execute(
            select(ExecutionEvent).where(
                ExecutionEvent.event_type == EventType.TASK_UNASSIGNED,
            )
        )
        events = list(result.scalars().all())
        assert len(events) >= 1


# ═══════════════════════════════════════════════════════════════════
# FM-142: Notification Preferences
# ═══════════════════════════════════════════════════════════════════


class TestFM142NotificationPreferences:
    """Test NotificationPreference model, service, and routes."""

    async def test_preference_model_creation(self, db_session):
        from app.models.notification import NotificationPreference

        pref = NotificationPreference(
            user_id=STUB_USER_ID,
            notification_type="task_assigned",
            enabled=False,
        )
        db_session.add(pref)
        await db_session.flush()
        await db_session.refresh(pref)
        assert pref.id is not None
        assert pref.enabled is False

    async def test_upsert_preference(self, db_session):
        from app.services.notification_service import upsert_preference

        pref = await upsert_preference(
            db_session,
            user_id=STUB_USER_ID,
            notification_type="run_completed",
            enabled=False,
        )
        assert pref.enabled is False

        # Upsert again should update, not create duplicate
        pref2 = await upsert_preference(
            db_session,
            user_id=STUB_USER_ID,
            notification_type="run_completed",
            enabled=True,
        )
        assert pref2.id == pref.id
        assert pref2.enabled is True

    async def test_is_notification_allowed(self, db_session):
        from app.services.notification_service import (
            upsert_preference,
            is_notification_allowed,
        )

        # Default: allowed
        assert await is_notification_allowed(db_session, STUB_USER_ID, "system") is True

        # Disabled
        await upsert_preference(
            db_session,
            user_id=STUB_USER_ID,
            notification_type="system",
            enabled=False,
        )
        assert (
            await is_notification_allowed(db_session, STUB_USER_ID, "system") is False
        )

    async def test_muted_until(self, db_session):
        from app.services.notification_service import (
            upsert_preference,
            is_notification_allowed,
        )

        future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        await upsert_preference(
            db_session,
            user_id=STUB_USER_ID,
            notification_type="escalation",
            enabled=True,
            muted_until=future,
        )
        assert (
            await is_notification_allowed(db_session, STUB_USER_ID, "escalation")
            is False
        )

    async def test_preferences_route_get(self, client):
        resp = await client.get("/notifications/preferences")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data

    async def test_preferences_route_put(self, client):
        resp = await client.put(
            "/notifications/preferences",
            json={"notification_type": "run_failed", "enabled": False},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["enabled"] is False


# ═══════════════════════════════════════════════════════════════════
# FM-148: Cross-Project Dashboard
# ═══════════════════════════════════════════════════════════════════


class TestFM148CrossProjectDashboard:
    """Test cross-project aggregated dashboard."""

    async def test_cross_project_dashboard_service(
        self,
        db_session,
        sample_project,
    ):
        from app.services.project_overview_service import get_cross_project_dashboard

        result = await get_cross_project_dashboard(db_session, STUB_USER_ID)
        assert "projects" in result
        assert "totals" in result
        assert result["totals"]["project_count"] >= 1

    async def test_cross_project_dashboard_route(self, client, sample_project):
        resp = await client.get("/dashboard")
        assert resp.status_code == 200
        data = resp.json()
        assert "projects" in data
        assert "totals" in data

    async def test_cross_project_empty_user(self, db_session):
        from app.services.project_overview_service import get_cross_project_dashboard

        empty_user = uuid.uuid4()
        result = await get_cross_project_dashboard(db_session, empty_user)
        assert result["totals"]["project_count"] == 0


# ═══════════════════════════════════════════════════════════════════
# FM-152: Webhook Event Processing
# ═══════════════════════════════════════════════════════════════════


class TestFM152WebhookEvents:
    """Test new webhook event processors (push, release, check_run)."""

    async def _create_event(self, db_session, event_type, payload):
        from app.models.github_integration import ExternalEvent

        event = ExternalEvent(
            event_type=event_type,
            delivery_id=str(uuid.uuid4()),
            payload=payload,
        )
        db_session.add(event)
        await db_session.flush()
        await db_session.refresh(event)
        return event

    async def test_process_push_event(self, db_session):
        from app.services.webhook_service import process_push_event

        event = await self._create_event(
            db_session,
            "push",
            {
                "ref": "refs/heads/main",
                "pusher": {"name": "octocat"},
                "commits": [1, 2, 3],
                "head_commit": {"id": "abc123"},
            },
        )
        result = await process_push_event(db_session, event)
        assert result["branch"] == "main"
        assert result["pusher"] == "octocat"
        assert result["commits_count"] == 3

    async def test_process_release_event(self, db_session):
        from app.services.webhook_service import process_release_event

        event = await self._create_event(
            db_session,
            "release",
            {
                "release": {
                    "tag_name": "v1.0.0",
                    "name": "First Release",
                    "prerelease": False,
                    "draft": False,
                    "author": {"login": "octocat"},
                },
                "action": "published",
            },
        )
        result = await process_release_event(db_session, event)
        assert result["tag_name"] == "v1.0.0"
        assert result["action"] == "published"

    async def test_process_check_run_event(self, db_session, sample_project):
        from app.services.webhook_service import process_check_run_event
        from app.models.github_integration import (
            GitHubInstallation,
            RepositoryLink,
        )

        # Create installation + repo link
        installation = GitHubInstallation(
            installation_id=54321,
            account_login="test-org",
            connected_by=STUB_USER_ID,
        )
        db_session.add(installation)
        await db_session.flush()

        repo_link = RepositoryLink(
            installation_id=installation.id,
            full_name="owner/repo",
            github_repo_id=12345,
            default_branch="main",
            project_id=sample_project.id,
        )
        db_session.add(repo_link)
        await db_session.flush()

        event = await self._create_event(
            db_session,
            "check_run",
            {
                "check_run": {
                    "name": "test-suite",
                    "head_sha": "abc123",
                    "status": "completed",
                    "conclusion": "success",
                },
            },
        )
        event.repository_link_id = repo_link.id
        await db_session.flush()

        result = await process_check_run_event(db_session, event)
        assert result is not None


# ═══════════════════════════════════════════════════════════════════
# FM-155: Issue Export Direction
# ═══════════════════════════════════════════════════════════════════


class TestFM155IssueExport:
    """Test issue export service functions."""

    async def _make_repo_link(self, db_session, project_id):
        """Helper to create a valid RepositoryLink with required installation."""
        from app.models.github_integration import GitHubInstallation, RepositoryLink

        installation = GitHubInstallation(
            installation_id=12345,
            account_login="test-org",
            connected_by=STUB_USER_ID,
        )
        db_session.add(installation)
        await db_session.flush()

        repo_link = RepositoryLink(
            installation_id=installation.id,
            full_name="owner/repo",
            github_repo_id=99999,
            default_branch="main",
            project_id=project_id,
        )
        db_session.add(repo_link)
        await db_session.flush()
        await db_session.refresh(repo_link)
        return repo_link

    async def test_export_issue_to_github(self, db_session, sample_project):
        from app.services.issue_sync_service import export_issue_to_github

        await self._make_repo_link(db_session, sample_project.id)

        link = await export_issue_to_github(
            db_session,
            project_id=sample_project.id,
            title="Bug: failing test",
            body="Details here",
        )
        assert link is not None
        assert link.issue_number == 0  # Pending sync

    async def test_list_exportable_issues(self, db_session, sample_project):
        from app.services.issue_sync_service import (
            export_issue_to_github,
            list_exportable_issues,
        )

        await self._make_repo_link(db_session, sample_project.id)

        await export_issue_to_github(
            db_session,
            project_id=sample_project.id,
            title="Export test",
        )
        issues = await list_exportable_issues(db_session, sample_project.id)
        assert len(issues) >= 1


# ═══════════════════════════════════════════════════════════════════
# FM-156: Auto-Create Branch
# ═══════════════════════════════════════════════════════════════════


class TestFM156AutoBranch:
    """Test branch name slug generation."""

    def test_slugify_branch_name(self):
        from app.services.github_client import slugify_branch_name

        name = slugify_branch_name("Fix login page bug", "abcd1234-5678")
        assert name.startswith("task/")
        assert "fix-login-page-bug" in name
        assert "abcd1234" in name

    def test_slugify_special_chars(self):
        from app.services.github_client import slugify_branch_name

        name = slugify_branch_name("Add feature: @user/login (v2)", "1111-2222")
        assert "/" not in name.split("/", 1)[1] or "task/" in name
        # Should not have special chars other than -
        slug_part = name.replace("task/", "")
        assert all(c.isalnum() or c == "-" for c in slug_part)


# ═══════════════════════════════════════════════════════════════════
# FM-158: Diff Intelligence — Risk Rules
# ═══════════════════════════════════════════════════════════════════


class TestFM158DiffRiskRules:
    """Test risk rule evaluation for diffs."""

    def test_evaluate_risk_rules_large_file(self):
        from app.services.diff_intelligence_service import evaluate_risk_rules

        # Generate a large diff with proper header
        lines = ["+added line\n" for _ in range(400)]
        diff = (
            "diff --git a/big_file.py b/big_file.py\n--- a/big_file.py\n+++ b/big_file.py\n"
            + "".join(lines)
        )
        result = evaluate_risk_rules(diff)
        assert result["risk_score"] > 0
        assert any(
            r["rule_id"] == "LARGE_FILE_CHANGE" for r in result["triggered_rules"]
        )

    def test_evaluate_risk_rules_secret(self):
        from app.services.diff_intelligence_service import evaluate_risk_rules

        diff = "diff --git a/config.py b/config.py\n--- a/config.py\n+++ b/config.py\n+API_KEY = 'sk-leaked-key-12345'"
        result = evaluate_risk_rules(diff)
        assert any(r["rule_id"] == "SECRET_PATTERN" for r in result["triggered_rules"])

    def test_evaluate_risk_rules_migration(self):
        from app.services.diff_intelligence_service import evaluate_risk_rules

        diff = "diff --git a/migrations/001_init.py b/migrations/001_init.py\n--- a/migrations/001_init.py\n+++ b/migrations/001_init.py\n+ALTER TABLE"
        result = evaluate_risk_rules(diff)
        assert any(
            r["rule_id"] == "MIGRATION_DETECTED" for r in result["triggered_rules"]
        )

    def test_evaluate_risk_rules_clean_diff(self):
        from app.services.diff_intelligence_service import evaluate_risk_rules

        diff = "+# just a comment"
        result = evaluate_risk_rules(diff)
        assert result["risk_level"] == "low"

    def test_get_risk_rules(self):
        from app.services.diff_intelligence_service import get_risk_rules

        rules = get_risk_rules()
        assert len(rules) >= 8
        assert all("id" in r and "severity" in r for r in rules)

    async def test_risk_route(self, client):
        resp = await client.post(
            "/github/diffs/risk",
            json={"diff_text": "+AWS_SECRET_ACCESS_KEY=leaked"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "risk_score" in data

    async def test_rules_list_route(self, client):
        resp = await client.get("/github/diffs/rules")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 8


# ═══════════════════════════════════════════════════════════════════
# FM-163: Knowledge Auto-Suggestion
# ═══════════════════════════════════════════════════════════════════


class TestFM163KnowledgeSuggestion:
    """Test knowledge auto-suggestion service."""

    async def test_suggest_knowledge_for_task(self, db_session, sample_project):
        from app.services.knowledge_service import (
            create_knowledge,
            suggest_knowledge_for_task,
        )
        from app.models.project_knowledge import KnowledgeType

        # Create some knowledge entries
        await create_knowledge(
            db_session,
            project_id=sample_project.id,
            knowledge_type=KnowledgeType.PATTERN,
            title="Architecture Review Patterns",
            content="Best practices for code review",
            tags=["architecture", "review"],
        )
        await create_knowledge(
            db_session,
            project_id=sample_project.id,
            knowledge_type=KnowledgeType.BEST_PRACTICE,
            title="Testing Guidelines",
            content="How to write tests",
            tags=["testing", "quality"],
        )

        suggestions = await suggest_knowledge_for_task(
            db_session,
            project_id=sample_project.id,
            task_type="architecture",
            task_title="Review the architecture document",
        )
        assert len(suggestions) >= 1

    async def test_suggest_knowledge_route(self, client, sample_project):
        resp = await client.get(
            f"/projects/{sample_project.id}/knowledge/suggest",
            params={"task_type": "review", "task_title": "Code review"},
        )
        assert resp.status_code == 200


# ═══════════════════════════════════════════════════════════════════
# FM-164: Deep Clone & Template Versioning
# ═══════════════════════════════════════════════════════════════════


class TestFM164TemplateCloneVersion:
    """Test deep clone and versioning of templates."""

    @pytest_asyncio.fixture
    async def sample_template(self, db_session):
        from app.models.project_template import ProjectTemplate

        tpl = ProjectTemplate(
            slug="test-template",
            name="Test Template",
            description="A template for testing",
            category="general",
            constitution_template={"content": "Be safe.", "title": "Safety First"},
            default_governance_config={"require_spec_approval": True},
            default_phase_profiles=[{"phase": "specifying", "agent_slug": "spec"}],
        )
        db_session.add(tpl)
        await db_session.flush()
        await db_session.refresh(tpl)
        return tpl

    async def test_clone_template(self, db_session, sample_template):
        from app.services.template_inheritance_service import clone_template

        clone = await clone_template(
            db_session,
            sample_template.id,
            new_slug="cloned-template",
            new_name="Cloned Template",
        )
        assert clone.slug == "cloned-template"
        assert clone.version == sample_template.version + 1
        assert clone.parent_template_id == sample_template.id
        assert clone.constitution_template == sample_template.constitution_template
        assert (
            clone.default_governance_config == sample_template.default_governance_config
        )

    async def test_create_template_version(self, db_session, sample_template):
        from app.services.template_inheritance_service import create_template_version

        versioned = await create_template_version(
            db_session,
            sample_template.id,
            updates={"name": "Updated Template", "description": "V2"},
        )
        assert versioned.name == "Updated Template"
        assert versioned.version == sample_template.version + 1
        assert versioned.parent_template_id == sample_template.id
        # Inherited fields should carry over
        assert versioned.constitution_template == sample_template.constitution_template

    async def test_clone_template_not_found(self, db_session):
        from app.services.template_inheritance_service import clone_template

        with pytest.raises(ValueError, match="not found"):
            await clone_template(db_session, uuid.uuid4(), new_slug="nope")

    async def test_version_schema_fields(self):
        from app.schemas.project_template import ProjectTemplateRead

        # Verify version field exists
        fields = ProjectTemplateRead.model_fields
        assert "version" in fields
        assert "parent_template_id" in fields


# ═══════════════════════════════════════════════════════════════════
# FM-165: Project Directory & Related Suggestions
# ═══════════════════════════════════════════════════════════════════


class TestFM165ProjectDirectory:
    """Test project directory and related suggestions."""

    async def test_get_project_directory(self, db_session, sample_project):
        from app.services.search_service import get_project_directory

        items, total = await get_project_directory(db_session, STUB_USER_ID)
        assert total >= 1
        assert len(items) >= 1
        entry = items[0]
        assert "project_id" in entry
        assert "health_grade" in entry
        assert "success_rate" in entry

    async def test_get_project_directory_empty(self, db_session):
        from app.services.search_service import get_project_directory

        items, total = await get_project_directory(db_session, uuid.uuid4())
        assert total == 0
        assert items == []

    async def test_get_related_projects(self, db_session, sample_project):
        from app.services.search_service import get_related_projects

        related = await get_related_projects(
            db_session,
            sample_project.id,
            STUB_USER_ID,
        )
        assert isinstance(related, list)

    async def test_directory_route(self, client, sample_project):
        resp = await client.get("/project-directory")
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "items" in data
        assert "total" in data

    async def test_related_route(self, client, sample_project):
        resp = await client.get(f"/projects/{sample_project.id}/related")
        assert resp.status_code == 200
        data = resp.json()
        assert "related" in data


# ═══════════════════════════════════════════════════════════════════
# FM-166: Replay Run
# ═══════════════════════════════════════════════════════════════════


class TestFM166ReplayRun:
    """Test replay_run service function."""

    async def test_replay_run_no_snapshots(self, db_session, sample_run):
        from app.services.replay_service import replay_run

        result = await replay_run(db_session, sample_run.id)
        assert "error" in result

    async def test_replay_run_with_snapshots(
        self,
        db_session,
        sample_project,
        sample_run,
        sample_task,
    ):
        from app.services.replay_service import capture_snapshot, replay_run

        await capture_snapshot(
            db_session,
            task_id=sample_task.id,
            run_id=sample_run.id,
            project_id=sample_project.id,
            agent_slug="test-agent",
            input_snapshot={"prompt": "hello"},
            prompt_snapshot="hello world",
            model_used="gpt-4",
            temperature=0.7,
            output_snapshot={"result": "response"},
        )
        await db_session.flush()

        result = await replay_run(db_session, sample_run.id)
        assert result["run_id"] == str(sample_run.id)
        assert result["total_steps"] == 1
        assert result["replayed_steps"] == 1
        assert result["all_match"] is True


# ═══════════════════════════════════════════════════════════════════
# FM-172: Custom Roles
# ═══════════════════════════════════════════════════════════════════


class TestFM172CustomRoles:
    """Test custom role model and CRUD."""

    async def test_custom_role_model(self, db_session):
        from app.models.enterprise_governance import CustomRole

        role = CustomRole(
            workspace_id=uuid.uuid4(),
            name="Tester",
            scope="project",
            permissions=["project:view", "project:run"],
            created_by=STUB_USER_ID,
        )
        db_session.add(role)
        await db_session.flush()
        await db_session.refresh(role)
        assert role.id is not None
        assert role.is_active is True

    async def test_create_custom_role_service(self, db_session):
        from app.services.authz_service import create_custom_role

        ws_id = uuid.uuid4()
        role = await create_custom_role(
            db_session,
            workspace_id=ws_id,
            name="QA Lead",
            permissions=["project:view", "project:review"],
            created_by=STUB_USER_ID,
        )
        assert role.name == "QA Lead"
        assert "project:view" in role.permissions

    async def test_create_custom_role_invalid_permission(self, db_session):
        from app.services.authz_service import create_custom_role

        with pytest.raises(ValueError, match="Invalid permissions"):
            await create_custom_role(
                db_session,
                workspace_id=uuid.uuid4(),
                name="Bad Role",
                permissions=["totally:invalid"],
                created_by=STUB_USER_ID,
            )

    async def test_list_custom_roles(self, db_session):
        from app.services.authz_service import create_custom_role, list_custom_roles

        ws_id = uuid.uuid4()
        await create_custom_role(
            db_session,
            workspace_id=ws_id,
            name="Role A",
            permissions=["project:view"],
            created_by=STUB_USER_ID,
        )
        await create_custom_role(
            db_session,
            workspace_id=ws_id,
            name="Role B",
            permissions=["project:run"],
            created_by=STUB_USER_ID,
        )

        roles = await list_custom_roles(db_session, ws_id)
        assert len(roles) == 2

    async def test_update_custom_role(self, db_session):
        from app.services.authz_service import create_custom_role, update_custom_role

        role = await create_custom_role(
            db_session,
            workspace_id=uuid.uuid4(),
            name="Old Name",
            permissions=["project:view"],
            created_by=STUB_USER_ID,
        )
        updated = await update_custom_role(
            db_session,
            role.id,
            name="New Name",
            permissions=["project:view", "project:run"],
        )
        assert updated.name == "New Name"
        assert len(updated.permissions) == 2


# ═══════════════════════════════════════════════════════════════════
# FM-176: Retention Archive Exclusion
# ═══════════════════════════════════════════════════════════════════


class TestFM176ArchiveExclusion:
    """Test that archived_at column exists and retention sets it."""

    async def test_run_has_archived_at(self, db_session, sample_run):
        assert sample_run.archived_at is None

    async def test_artifact_has_archived_at(self, db_session, sample_artifact):
        assert sample_artifact.archived_at is None

    async def test_archive_sets_archived_at(self, db_session, sample_project):
        """Create old runs, apply archive policy, verify archived_at is set."""
        from app.models.run import Run
        from app.models.workspace import Workspace
        from app.models.enterprise_governance import RetentionPolicy, RetentionAction
        from app.services.retention_policy_service import evaluate_retention

        # Create a workspace
        ws = Workspace(name="Test WS", slug="test-ws", owner_id=STUB_USER_ID)
        db_session.add(ws)
        await db_session.flush()

        # Update project's workspace
        from app.models.project import Project

        proj = await db_session.get(Project, sample_project.id)
        proj.workspace_id = ws.id
        await db_session.flush()

        # Create an old run
        old_run = Run(
            run_number=99,
            project_id=sample_project.id,
            trigger="test",
        )
        db_session.add(old_run)
        await db_session.flush()

        # Backdate it
        from sqlalchemy import update

        await db_session.execute(
            update(Run)
            .where(Run.id == old_run.id)
            .values(created_at=datetime.now(timezone.utc) - timedelta(days=400))
        )
        await db_session.flush()

        # Create archive policy
        policy = RetentionPolicy(
            workspace_id=ws.id,
            entity_type="run",
            retention_days=30,
            action=RetentionAction.ARCHIVE,
            created_by=STUB_USER_ID,
        )
        db_session.add(policy)
        await db_session.flush()

        # Evaluate with dry_run=False to actually archive
        await evaluate_retention(db_session, ws.id, dry_run=False)
        await db_session.flush()

        # Check archived_at was set
        await db_session.refresh(old_run)
        assert old_run.archived_at is not None

    async def test_version_field_on_template(self, db_session):
        """Verify ProjectTemplate has version and parent_template_id fields."""
        from app.models.project_template import ProjectTemplate

        tpl = ProjectTemplate(
            slug="version-test",
            name="Version Test",
            category="test",
        )
        db_session.add(tpl)
        await db_session.flush()
        await db_session.refresh(tpl)
        assert tpl.version == 1
        assert tpl.parent_template_id is None
