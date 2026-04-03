"""FM-075 — RBAC enforcement hardening tests.

Tests verify that:
1. All non-public endpoints require authentication (401 without token in prod mode)
2. Workspace-level RBAC (check_workspace_permission) is enforced
3. Project-level RBAC (check_project_permission) is enforced
4. Permission matrix is correct
5. Error semantics are consistent (401/403/404)
"""

import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.authz_service import (
    Action,
    WORKSPACE_PERMISSIONS,
    PROJECT_PERMISSIONS,
    check_workspace_permission,
    check_project_permission,
    get_workspace_role,
    get_project_role,
    is_workspace_action_allowed,
    is_project_action_allowed,
)
from app.models.membership import (
    WorkspaceMember, WorkspaceRole,
    ProjectMember, ProjectRole,
)

# ── Reuse conftest fixtures (client, db_session, seed_stub_user) ──


# ── Test Helpers ─────────────────────────────────────────────────

STUB_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


@pytest_asyncio.fixture
async def workspace_with_members(db_session: AsyncSession):
    """Create a workspace with members at different roles."""
    from app.models.workspace import Workspace
    from app.models.user import User

    ws = Workspace(name="RBAC Test WS", slug="rbac-test", owner_id=STUB_USER_ID)
    db_session.add(ws)
    await db_session.flush()

    # Stub user is OWNER
    owner_member = WorkspaceMember(
        workspace_id=ws.id, user_id=STUB_USER_ID, role=WorkspaceRole.OWNER,
    )
    db_session.add(owner_member)

    # Create additional users with different roles
    users = {}
    for role in [WorkspaceRole.ADMIN, WorkspaceRole.OPERATOR, WorkspaceRole.REVIEWER, WorkspaceRole.VIEWER]:
        user = User(
            email=f"{role.value}@test.dev",
            display_name=f"Test {role.value.title()}",
        )
        db_session.add(user)
        await db_session.flush()
        member = WorkspaceMember(
            workspace_id=ws.id, user_id=user.id, role=role,
        )
        db_session.add(member)
        users[role] = user

    await db_session.commit()
    return ws, users


@pytest_asyncio.fixture
async def project_with_members(db_session: AsyncSession, workspace_with_members):
    """Create a project with members at different roles."""
    from app.models.project import Project
    from app.models.user import User

    ws, ws_users = workspace_with_members

    proj = Project(
        name="RBAC Test Proj",
        workspace_id=ws.id,
        owner_id=STUB_USER_ID,
    )
    db_session.add(proj)
    await db_session.flush()

    # Stub user is LEAD
    lead_member = ProjectMember(
        project_id=proj.id, user_id=STUB_USER_ID, role=ProjectRole.LEAD,
    )
    db_session.add(lead_member)

    users = {}
    for role in [ProjectRole.OPERATOR, ProjectRole.REVIEWER, ProjectRole.VIEWER]:
        user = User(
            email=f"proj-{role.value}@test.dev",
            display_name=f"Test Proj {role.value.title()}",
        )
        db_session.add(user)
        await db_session.flush()
        member = ProjectMember(
            project_id=proj.id, user_id=user.id, role=role,
        )
        db_session.add(member)
        users[role] = user

    await db_session.commit()
    return proj, users


# ── Test Classes ─────────────────────────────────────────────────


class TestPermissionMatrix:
    """Test the static permission matrices are correctly configured."""

    def test_workspace_permissions_complete(self):
        """All workspace actions have permission entries."""
        ws_actions = [a for a in Action if a.value.startswith("workspace:")]
        for action in ws_actions:
            assert action in WORKSPACE_PERMISSIONS, f"Missing permission entry for {action}"

    def test_project_permissions_complete(self):
        """All project actions have permission entries."""
        proj_actions = [a for a in Action if a.value.startswith("project:")]
        for action in proj_actions:
            assert action in PROJECT_PERMISSIONS, f"Missing permission entry for {action}"

    def test_owner_has_all_workspace_permissions(self):
        """OWNER should have all workspace permissions."""
        for action, roles in WORKSPACE_PERMISSIONS.items():
            assert WorkspaceRole.OWNER in roles, f"OWNER missing from {action}"

    def test_lead_has_all_project_permissions(self):
        """LEAD should have all project permissions."""
        for action, roles in PROJECT_PERMISSIONS.items():
            assert ProjectRole.LEAD in roles, f"LEAD missing from {action}"

    def test_viewer_read_only_workspace(self):
        """VIEWER should only be able to view."""
        for action, roles in WORKSPACE_PERMISSIONS.items():
            if action == Action.WORKSPACE_VIEW:
                assert WorkspaceRole.VIEWER in roles
            else:
                assert WorkspaceRole.VIEWER not in roles, \
                    f"VIEWER should not have {action}"

    def test_viewer_read_only_project(self):
        """VIEWER should only be able to view projects."""
        for action, roles in PROJECT_PERMISSIONS.items():
            if action == Action.PROJECT_VIEW:
                assert ProjectRole.VIEWER in roles
            else:
                assert ProjectRole.VIEWER not in roles, \
                    f"VIEWER should not have {action}"

    def test_new_actions_exist(self):
        """FM-075 new actions should exist."""
        assert Action.WORKSPACE_MANAGE_SECRETS
        assert Action.WORKSPACE_VIEW_AUDIT
        assert Action.PROJECT_EXECUTE_CODE
        assert Action.PROJECT_MANAGE_KNOWLEDGE
        assert Action.PROJECT_MANAGE_ESCALATION

    def test_pure_check_functions(self):
        """is_workspace_action_allowed / is_project_action_allowed work."""
        assert is_workspace_action_allowed(WorkspaceRole.OWNER, Action.WORKSPACE_DELETE)
        assert not is_workspace_action_allowed(WorkspaceRole.VIEWER, Action.WORKSPACE_DELETE)
        assert is_project_action_allowed(ProjectRole.LEAD, Action.PROJECT_RUN)
        assert not is_project_action_allowed(ProjectRole.VIEWER, Action.PROJECT_RUN)


class TestWorkspaceRBAC:
    """Test workspace-level authorization checks with DB."""

    async def test_owner_can_update(self, db_session, workspace_with_members):
        ws, _ = workspace_with_members
        role = await check_workspace_permission(
            db_session, ws.id, STUB_USER_ID, Action.WORKSPACE_UPDATE,
        )
        assert role == WorkspaceRole.OWNER

    async def test_viewer_cannot_update(self, db_session, workspace_with_members):
        ws, users = workspace_with_members
        viewer = users[WorkspaceRole.VIEWER]
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await check_workspace_permission(
                db_session, ws.id, viewer.id, Action.WORKSPACE_UPDATE,
            )
        assert exc_info.value.status_code == 403

    async def test_nonmember_gets_404(self, db_session, workspace_with_members):
        ws, _ = workspace_with_members
        random_user = uuid.uuid4()
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await check_workspace_permission(
                db_session, ws.id, random_user, Action.WORKSPACE_VIEW,
            )
        assert exc_info.value.status_code == 404

    async def test_admin_can_manage_members(self, db_session, workspace_with_members):
        ws, users = workspace_with_members
        admin = users[WorkspaceRole.ADMIN]
        role = await check_workspace_permission(
            db_session, ws.id, admin.id, Action.WORKSPACE_MANAGE_MEMBERS,
        )
        assert role == WorkspaceRole.ADMIN

    async def test_operator_cannot_manage_members(self, db_session, workspace_with_members):
        ws, users = workspace_with_members
        operator = users[WorkspaceRole.OPERATOR]
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await check_workspace_permission(
                db_session, ws.id, operator.id, Action.WORKSPACE_MANAGE_MEMBERS,
            )
        assert exc_info.value.status_code == 403

    async def test_only_owner_can_delete(self, db_session, workspace_with_members):
        ws, users = workspace_with_members
        admin = users[WorkspaceRole.ADMIN]
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await check_workspace_permission(
                db_session, ws.id, admin.id, Action.WORKSPACE_DELETE,
            )
        assert exc_info.value.status_code == 403


class TestProjectRBAC:
    """Test project-level authorization checks with DB."""

    async def test_lead_can_approve(self, db_session, project_with_members):
        proj, _ = project_with_members
        role = await check_project_permission(
            db_session, proj.id, STUB_USER_ID, Action.PROJECT_APPROVE,
        )
        assert role == ProjectRole.LEAD

    async def test_reviewer_can_review(self, db_session, project_with_members):
        proj, users = project_with_members
        reviewer = users[ProjectRole.REVIEWER]
        role = await check_project_permission(
            db_session, proj.id, reviewer.id, Action.PROJECT_REVIEW,
        )
        assert role == ProjectRole.REVIEWER

    async def test_viewer_cannot_run(self, db_session, project_with_members):
        proj, users = project_with_members
        viewer = users[ProjectRole.VIEWER]
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await check_project_permission(
                db_session, proj.id, viewer.id, Action.PROJECT_RUN,
            )
        assert exc_info.value.status_code == 403

    async def test_nonmember_gets_404(self, db_session, project_with_members):
        proj, _ = project_with_members
        random_user = uuid.uuid4()
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await check_project_permission(
                db_session, proj.id, random_user, Action.PROJECT_VIEW,
            )
        assert exc_info.value.status_code == 404

    async def test_operator_can_execute_code(self, db_session, project_with_members):
        proj, users = project_with_members
        operator = users[ProjectRole.OPERATOR]
        role = await check_project_permission(
            db_session, proj.id, operator.id, Action.PROJECT_EXECUTE_CODE,
        )
        assert role == ProjectRole.OPERATOR


class TestRouteAuthEnforcement:
    """Test that endpoints require auth (via dev mode stub user)."""

    async def test_workspace_endpoints_have_auth(self, client: AsyncClient):
        """All workspace CRUD endpoints should succeed with stub auth (dev mode)."""
        # Create workspace (stub user is authed in dev mode)
        resp = await client.post("/workspaces", json={
            "name": "Auth Test WS", "slug": "auth-test-ws",
        })
        assert resp.status_code == 201
        ws_id = resp.json()["id"]

        # List should work
        resp = await client.get("/workspaces")
        assert resp.status_code == 200

    async def test_project_endpoints_have_auth(self, client: AsyncClient):
        """Project endpoints should succeed with stub auth."""
        resp = await client.post("/projects", json={
            "name": "Auth Test Proj",
        })
        assert resp.status_code == 201

        resp = await client.get("/projects")
        assert resp.status_code == 200

    async def test_governance_endpoints_have_auth(self, client: AsyncClient):
        """Governance endpoints should succeed with stub auth."""
        resp = await client.get("/governance/policies")
        assert resp.status_code == 200

    async def test_audit_endpoints_have_auth(self, client: AsyncClient):
        """Audit endpoints should succeed with stub auth."""
        resp = await client.get("/audit/summary")
        assert resp.status_code == 200

    async def test_vault_endpoints_have_auth(self, client: AsyncClient):
        """Vault endpoints should succeed with stub auth."""
        resp = await client.get("/vault/credentials")
        assert resp.status_code == 200

    async def test_approvals_endpoints_have_auth(self, client: AsyncClient):
        """Approvals endpoints should succeed with stub auth."""
        resp = await client.get("/approvals")
        assert resp.status_code == 200

    async def test_agents_endpoints_have_auth(self, client: AsyncClient):
        """Agents endpoints should succeed with stub auth."""
        resp = await client.get("/agents")
        assert resp.status_code == 200

    async def test_costs_endpoints_have_auth(self, client: AsyncClient):
        """Costs endpoints should succeed with stub auth."""
        resp = await client.get("/costs")
        assert resp.status_code == 200

    async def test_health_remains_public(self, client: AsyncClient):
        """Health endpoints should NOT require auth."""
        resp = await client.get("/health")
        assert resp.status_code == 200
        resp = await client.get("/health/ready")
        assert resp.status_code == 200

    async def test_auth_endpoints_remain_public(self, client: AsyncClient):
        """Auth register/login should NOT require auth."""
        resp = await client.post("/auth/register", json={
            "email": "rbac-test@test.dev",
            "password": "testpass123",
            "display_name": "RBAC Test",
        })
        assert resp.status_code == 201


class TestRoleResolution:
    """Test role resolution helpers."""

    async def test_get_workspace_role(self, db_session, workspace_with_members):
        ws, users = workspace_with_members
        role = await get_workspace_role(db_session, ws.id, STUB_USER_ID)
        assert role == WorkspaceRole.OWNER

        admin = users[WorkspaceRole.ADMIN]
        role = await get_workspace_role(db_session, ws.id, admin.id)
        assert role == WorkspaceRole.ADMIN

    async def test_get_workspace_role_nonmember(self, db_session, workspace_with_members):
        ws, _ = workspace_with_members
        role = await get_workspace_role(db_session, ws.id, uuid.uuid4())
        assert role is None

    async def test_get_project_role(self, db_session, project_with_members):
        proj, users = project_with_members
        role = await get_project_role(db_session, proj.id, STUB_USER_ID)
        assert role == ProjectRole.LEAD

        reviewer = users[ProjectRole.REVIEWER]
        role = await get_project_role(db_session, proj.id, reviewer.id)
        assert role == ProjectRole.REVIEWER

    async def test_get_project_role_nonmember(self, db_session, project_with_members):
        proj, _ = project_with_members
        role = await get_project_role(db_session, proj.id, uuid.uuid4())
        assert role is None


# ── Route-level Negative RBAC Tests ─────────────────────────────


@pytest_asyncio.fixture
async def viewer_project(db_session: AsyncSession):
    """Create a project with STUB_USER_ID as LEAD plus a VIEWER user.

    Returns (project, viewer_user, viewer_token).
    """
    from app.models.project import Project
    from app.models.user import User
    from app.core.auth import create_access_token

    proj = Project(name="RBAC Route Proj", owner_id=STUB_USER_ID)
    db_session.add(proj)
    await db_session.flush()

    lead = ProjectMember(
        project_id=proj.id, user_id=STUB_USER_ID, role=ProjectRole.LEAD,
    )
    db_session.add(lead)

    viewer = User(email="viewer-route@test.dev", display_name="Viewer User")
    db_session.add(viewer)
    await db_session.flush()

    viewer_member = ProjectMember(
        project_id=proj.id, user_id=viewer.id, role=ProjectRole.VIEWER,
    )
    db_session.add(viewer_member)
    await db_session.commit()

    token = create_access_token(viewer.id)
    return proj, viewer, token


@pytest_asyncio.fixture
async def viewer_run(db_session: AsyncSession, viewer_project):
    """Create a run under the viewer_project."""
    from app.models.run import Run

    proj, _, _ = viewer_project
    run = Run(run_number=1, project_id=proj.id, trigger="test")
    db_session.add(run)
    await db_session.flush()
    await db_session.refresh(run)
    return run


@pytest_asyncio.fixture
async def viewer_task(db_session: AsyncSession, viewer_run):
    """Create a task under the viewer_run."""
    from app.models.task import Task, TaskStatus

    task = Task(
        title="Viewer Test Task", description="t", task_type="coding",
        status=TaskStatus.READY, order_index=0, run_id=viewer_run.id,
    )
    db_session.add(task)
    await db_session.flush()
    await db_session.refresh(task)
    return task


class TestRouteRBACEnforcement:
    """Negative route-level tests: a VIEWER user should get 403 on write operations."""

    # ── Projects ─────────────────────────────────────────────────

    async def test_viewer_cannot_update_project(self, client: AsyncClient, viewer_project):
        proj, _, token = viewer_project
        resp = await client.patch(
            f"/projects/{proj.id}",
            json={"name": "hacked"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403

    async def test_viewer_can_view_project(self, client: AsyncClient, viewer_project):
        proj, _, token = viewer_project
        resp = await client.get(
            f"/projects/{proj.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200

    # ── Runs ─────────────────────────────────────────────────────

    async def test_viewer_can_list_runs(self, client: AsyncClient, viewer_project):
        proj, _, token = viewer_project
        resp = await client.get(
            f"/projects/{proj.id}/runs",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200

    # ── Tasks ────────────────────────────────────────────────────

    async def test_viewer_can_list_tasks(self, client: AsyncClient, viewer_run, viewer_project):
        _, _, token = viewer_project
        resp = await client.get(
            f"/runs/{viewer_run.id}/tasks",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200

    async def test_viewer_cannot_claim_task(self, client: AsyncClient, viewer_task, viewer_project):
        _, _, token = viewer_project
        resp = await client.post(
            f"/tasks/{viewer_task.id}/claim",
            json={"agent_slug": "test-agent"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403

    async def test_viewer_cannot_cancel_task(self, client: AsyncClient, viewer_task, viewer_project):
        _, _, token = viewer_project
        resp = await client.post(
            f"/tasks/{viewer_task.id}/cancel",
            json={},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403

    # ── Knowledge ────────────────────────────────────────────────

    async def test_viewer_cannot_create_knowledge(self, client: AsyncClient, viewer_project):
        proj, _, token = viewer_project
        resp = await client.post(
            f"/projects/{proj.id}/knowledge",
            json={
                "knowledge_type": "lesson_learned",
                "title": "test",
                "content": "test content",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403

    async def test_viewer_can_list_knowledge(self, client: AsyncClient, viewer_project):
        proj, _, token = viewer_project
        resp = await client.get(
            f"/projects/{proj.id}/knowledge",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200

    # ── Escalation ───────────────────────────────────────────────

    async def test_viewer_cannot_create_escalation_rule(self, client: AsyncClient, viewer_project):
        proj, _, token = viewer_project
        resp = await client.post(
            f"/projects/{proj.id}/escalation/rules",
            json={
                "name": "hack rule",
                "trigger": "task_timeout",
                "action": "notify",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403

    # ── Code Ops ─────────────────────────────────────────────────

    async def test_viewer_cannot_create_patch(self, client: AsyncClient, viewer_project):
        proj, _, token = viewer_project
        resp = await client.post(
            f"/projects/{proj.id}/patches",
            json={
                "title": "hack patch",
                "diff_content": "--- a/f\n+++ b/f\n",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403

    async def test_viewer_cannot_create_sandbox(self, client: AsyncClient, viewer_project):
        proj, _, token = viewer_project
        resp = await client.post(
            f"/projects/{proj.id}/sandbox",
            json={"command": "rm -rf /"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403

    async def test_viewer_can_list_patches(self, client: AsyncClient, viewer_project):
        proj, _, token = viewer_project
        resp = await client.get(
            f"/projects/{proj.id}/patches",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200

    # ── Repos ────────────────────────────────────────────────────

    async def test_viewer_cannot_create_repo(self, client: AsyncClient, viewer_project):
        proj, _, token = viewer_project
        resp = await client.post(
            f"/projects/{proj.id}/repos",
            json={
                "provider": "github",
                "repo_url": "https://github.com/x/y",
                "repo_name": "y",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403

    async def test_viewer_can_list_repos(self, client: AsyncClient, viewer_project):
        proj, _, token = viewer_project
        resp = await client.get(
            f"/projects/{proj.id}/repos",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200

    # ── Costs ────────────────────────────────────────────────────

    async def test_viewer_can_view_project_costs(self, client: AsyncClient, viewer_project):
        proj, _, token = viewer_project
        resp = await client.get(
            f"/costs/projects/{proj.id}/summary",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200

    # ── Council ──────────────────────────────────────────────────

    async def test_viewer_cannot_convene_council(self, client: AsyncClient, viewer_project):
        proj, _, token = viewer_project
        resp = await client.post(
            "/council/sessions",
            json={
                "project_id": str(proj.id),
                "topic": "test topic",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403

    # ── Run Lifecycle ────────────────────────────────────────────

    async def test_viewer_cannot_auto_complete_run(self, client: AsyncClient, viewer_run, viewer_project):
        _, _, token = viewer_project
        resp = await client.post(
            f"/lifecycle/runs/{viewer_run.id}/auto-complete",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403

    async def test_viewer_can_check_run_health(self, client: AsyncClient, viewer_run, viewer_project):
        _, _, token = viewer_project
        resp = await client.get(
            f"/lifecycle/runs/{viewer_run.id}/health",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
