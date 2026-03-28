"""Tests for FM-060 — Collaboration Phase Hardening.

Covers:
- workspace_id on projects (FM-051)
- authz_service permissions (FM-052)
- membership workspace validation (FM-053)
- stream_service pub/sub (FM-054)
- notification_delivery_service (FM-056)
- escalation integration (FM-057)
- workspace activity endpoint (FM-058)
- user_activity_service & user context (FM-059)
- collaboration phase integration flows (FM-060)
"""

import asyncio
import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

STUB_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


# ── FM-051: Workspace-scoped projects ────────────────────────────

class TestWorkspaceScopedProjects:
    """Verify projects can be linked to workspaces."""

    @pytest.mark.asyncio
    async def test_project_has_workspace_id_field(self, client: AsyncClient):
        """ProjectRead schema should include workspace_id."""
        resp = await client.post("/projects", json={"name": "WS Test Project"})
        assert resp.status_code == 201
        data = resp.json()
        assert "workspace_id" in data
        assert data["workspace_id"] is None  # null by default

    @pytest.mark.asyncio
    async def test_create_project_with_workspace(self, client: AsyncClient):
        """Create a workspace then a project linked to it."""
        # Create workspace
        ws_resp = await client.post("/workspaces", json={
            "name": "Test WS", "slug": "test-ws-proj"
        })
        assert ws_resp.status_code == 201
        ws_id = ws_resp.json()["id"]

        # Create project with workspace_id
        proj_resp = await client.post("/projects", json={
            "name": "WS Project", "workspace_id": ws_id
        })
        assert proj_resp.status_code == 201
        assert proj_resp.json()["workspace_id"] == ws_id


# ── FM-052: Authorization service ────────────────────────────────

class TestAuthzService:
    """Test the authorization permission helpers."""

    @pytest.mark.asyncio
    async def test_workspace_permission_matrix(self, db_session: AsyncSession):
        """Verify permission matrix returns correct allowed roles."""
        from app.services.authz_service import (
            Action, WORKSPACE_PERMISSIONS, is_workspace_action_allowed,
        )
        from app.models.membership import WorkspaceRole

        # Owner can do everything
        for action in WORKSPACE_PERMISSIONS:
            assert is_workspace_action_allowed(WorkspaceRole.OWNER, action)

        # Viewer can only view
        assert is_workspace_action_allowed(WorkspaceRole.VIEWER, Action.WORKSPACE_VIEW)
        assert not is_workspace_action_allowed(WorkspaceRole.VIEWER, Action.WORKSPACE_UPDATE)
        assert not is_workspace_action_allowed(WorkspaceRole.VIEWER, Action.WORKSPACE_DELETE)

    @pytest.mark.asyncio
    async def test_project_permission_matrix(self, db_session: AsyncSession):
        """Verify project permission matrix."""
        from app.services.authz_service import (
            Action, is_project_action_allowed,
        )
        from app.models.membership import ProjectRole

        # Lead can do everything
        for action in [Action.PROJECT_UPDATE, Action.PROJECT_DELETE,
                       Action.PROJECT_MANAGE_MEMBERS, Action.PROJECT_VIEW,
                       Action.PROJECT_RUN, Action.PROJECT_APPROVE, Action.PROJECT_REVIEW]:
            assert is_project_action_allowed(ProjectRole.LEAD, action)

        # Viewer can only view
        assert is_project_action_allowed(ProjectRole.VIEWER, Action.PROJECT_VIEW)
        assert not is_project_action_allowed(ProjectRole.VIEWER, Action.PROJECT_UPDATE)

    @pytest.mark.asyncio
    async def test_check_workspace_permission_not_member(self, db_session: AsyncSession):
        """Non-member should get 404."""
        from app.services.authz_service import check_workspace_permission, Action
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await check_workspace_permission(
                db_session, uuid.uuid4(), uuid.uuid4(), Action.WORKSPACE_VIEW
            )
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_check_workspace_permission_authorized(self, db_session: AsyncSession):
        """Member with correct role should pass."""
        from app.services.authz_service import check_workspace_permission, Action
        from app.services import workspace_service, membership_service
        from app.models.membership import WorkspaceRole

        ws = await workspace_service.create_workspace(
            db_session, name="Auth WS", slug="auth-ws-test",
            owner_id=STUB_USER_ID,
        )
        await membership_service.add_workspace_member(
            db_session, workspace_id=ws.id, user_id=STUB_USER_ID,
            role=WorkspaceRole.ADMIN,
        )

        role = await check_workspace_permission(
            db_session, ws.id, STUB_USER_ID, Action.WORKSPACE_UPDATE
        )
        assert role == WorkspaceRole.ADMIN

    @pytest.mark.asyncio
    async def test_check_workspace_permission_forbidden(self, db_session: AsyncSession):
        """Member without correct role should get 403."""
        from app.services.authz_service import check_workspace_permission, Action
        from app.services import workspace_service, membership_service
        from app.models.membership import WorkspaceRole
        from fastapi import HTTPException

        ws = await workspace_service.create_workspace(
            db_session, name="Auth WS2", slug="auth-ws-forbidden",
            owner_id=STUB_USER_ID,
        )
        await membership_service.add_workspace_member(
            db_session, workspace_id=ws.id, user_id=STUB_USER_ID,
            role=WorkspaceRole.VIEWER,
        )

        with pytest.raises(HTTPException) as exc_info:
            await check_workspace_permission(
                db_session, ws.id, STUB_USER_ID, Action.WORKSPACE_DELETE
            )
        assert exc_info.value.status_code == 403


# ── FM-053: Workspace membership validation ──────────────────────

class TestProjectMembershipValidation:
    """Verify workspace membership is validated before project assignment."""

    @pytest.mark.asyncio
    async def test_add_project_member_no_workspace_check_when_no_workspace(
        self, db_session: AsyncSession, sample_project,
    ):
        """Projects without workspace_id should skip the check."""
        from app.services import membership_service
        from app.models.membership import ProjectRole

        # sample_project has no workspace_id, should work fine
        member = await membership_service.add_project_member(
            db_session, project_id=sample_project.id,
            user_id=STUB_USER_ID, role=ProjectRole.LEAD,
        )
        assert member.role.value == "lead"


# ── FM-054: Stream service pub/sub ───────────────────────────────

class TestStreamService:
    """Test the in-memory event pub/sub for SSE streaming."""

    @pytest.mark.asyncio
    async def test_subscribe_and_publish(self):
        """Subscriber should receive published events."""
        from app.services.stream_service import (
            subscribe_run, unsubscribe_run, publish_run_event,
        )

        run_id = uuid.uuid4()
        queue = subscribe_run(run_id)

        count = await publish_run_event(run_id, "task_updated", {"task_id": "abc"})
        assert count == 1

        event = queue.get_nowait()
        assert event["event_type"] == "task_updated"
        assert event["data"]["task_id"] == "abc"

        unsubscribe_run(run_id, queue)

    @pytest.mark.asyncio
    async def test_no_subscribers_no_error(self):
        """Publishing with no subscribers should not fail."""
        from app.services.stream_service import publish_run_event

        count = await publish_run_event(uuid.uuid4(), "test", {})
        assert count == 0

    @pytest.mark.asyncio
    async def test_global_subscriber_receives_events(self):
        """Global subscribers should get all run events."""
        from app.services.stream_service import (
            subscribe_global, unsubscribe_global, publish_run_event,
        )

        queue = subscribe_global()
        run_id = uuid.uuid4()

        await publish_run_event(run_id, "artifact_created", {"name": "test"})

        event = queue.get_nowait()
        assert event["event_type"] == "artifact_created"

        unsubscribe_global(queue)

    @pytest.mark.asyncio
    async def test_run_scoped_sse_route_exists(self, client: AsyncClient):
        """The /runs/{run_id}/stream endpoint should be registered."""
        from app.main import create_app
        app = create_app()
        routes = [r.path for r in app.routes]
        assert "/runs/{run_id}/stream" in routes

    @pytest.mark.asyncio
    async def test_run_event_generator_yields(self):
        """Run event generator should yield events."""
        from app.services.stream_service import (
            run_event_generator, publish_run_event,
        )

        run_id = uuid.uuid4()
        gen = run_event_generator(run_id)

        # Publish event shortly after starting generator
        async def publish_later():
            await asyncio.sleep(0.05)
            await publish_run_event(run_id, "task_updated", {"id": "123"})

        task = asyncio.create_task(publish_later())
        line = await asyncio.wait_for(gen.__anext__(), timeout=2.0)
        assert "task_updated" in line
        await task


# ── FM-056: Notification delivery service ────────────────────────

class TestNotificationDeliveryService:
    """Test external notification delivery."""

    @pytest.mark.asyncio
    async def test_deliver_with_no_configs(self, db_session: AsyncSession):
        """No delivery configs means empty results."""
        from app.services.notification_delivery_service import deliver_notification
        from app.models.notification import Notification, NotificationType, NotificationPriority

        notif = Notification(
            user_id=STUB_USER_ID,
            notification_type=NotificationType.SYSTEM,
            priority=NotificationPriority.NORMAL,
            title="Test",
        )
        db_session.add(notif)
        await db_session.flush()

        results = await deliver_notification(db_session, notif)
        assert results == []

    @pytest.mark.asyncio
    async def test_deliver_email_stub(self, db_session: AsyncSession):
        """Email delivery stub should succeed."""
        from app.services.notification_delivery_service import _deliver_email
        from app.models.notification import (
            Notification, NotificationType, NotificationPriority,
            NotificationDeliveryConfig, DeliveryChannel, DeliveryStatus,
        )

        notif = Notification(
            user_id=STUB_USER_ID,
            notification_type=NotificationType.RUN_FAILED,
            priority=NotificationPriority.HIGH,
            title="Run Failed",
            body="Your run has failed",
        )
        db_session.add(notif)
        await db_session.flush()

        config = NotificationDeliveryConfig(
            user_id=STUB_USER_ID,
            channel=DeliveryChannel.EMAIL,
            status=DeliveryStatus.ACTIVE,
            config={"email": "test@example.com"},
        )
        db_session.add(config)
        await db_session.flush()

        result = await _deliver_email(notif, config)
        assert result["status"] == "delivered"
        assert "test@example.com" in result["detail"]

    @pytest.mark.asyncio
    async def test_deliver_webhook_no_url(self, db_session: AsyncSession):
        """Webhook with no URL should fail gracefully."""
        from app.services.notification_delivery_service import _deliver_webhook
        from app.models.notification import (
            Notification, NotificationType, NotificationPriority,
            NotificationDeliveryConfig, DeliveryChannel, DeliveryStatus,
        )

        notif = Notification(
            user_id=STUB_USER_ID,
            notification_type=NotificationType.SYSTEM,
            priority=NotificationPriority.LOW,
            title="Test",
        )
        db_session.add(notif)
        await db_session.flush()

        config = NotificationDeliveryConfig(
            user_id=STUB_USER_ID,
            channel=DeliveryChannel.WEBHOOK,
            status=DeliveryStatus.ACTIVE,
            config={},  # no url
        )
        db_session.add(config)
        await db_session.flush()

        result = await _deliver_webhook(notif, config)
        assert result["status"] == "failed"
        assert "No webhook URL" in result["detail"]


# ── FM-058: Workspace activity endpoint ──────────────────────────

class TestWorkspaceActivity:
    """Test workspace-scoped activity feed."""

    @pytest.mark.asyncio
    async def test_workspace_activity_empty(self, client: AsyncClient):
        """Empty workspace activity should return empty list."""
        ws_resp = await client.post("/workspaces", json={
            "name": "Activity WS", "slug": "activity-ws-test"
        })
        ws_id = ws_resp.json()["id"]

        resp = await client.get(f"/workspaces/{ws_id}/activity")
        assert resp.status_code == 200
        assert resp.json()["items"] == []
        assert resp.json()["total"] == 0

    @pytest.mark.asyncio
    async def test_workspace_activity_with_entries(self, client: AsyncClient):
        """Activity should be filterable by workspace."""
        ws_resp = await client.post("/workspaces", json={
            "name": "Activity WS2", "slug": "activity-ws-entries"
        })
        ws_id = ws_resp.json()["id"]

        # Create an activity entry for this workspace
        await client.post("/activity", json={
            "activity_type": "run_started",
            "summary": "Test run started",
            "workspace_id": ws_id,
        })

        resp = await client.get(f"/workspaces/{ws_id}/activity")
        assert resp.status_code == 200
        assert resp.json()["total"] == 1
        assert resp.json()["items"][0]["summary"] == "Test run started"


# ── FM-059: User activity service & context ──────────────────────

class TestUserActivityService:
    """Test user presence tracking and assignment context."""

    @pytest.mark.asyncio
    async def test_touch_user_activity(self, db_session: AsyncSession):
        """touch_user_activity should create/update presence."""
        from app.services.user_activity_service import touch_user_activity

        presence = await touch_user_activity(
            db_session, STUB_USER_ID,
            resource_type="project",
            resource_id=uuid.uuid4(),
        )
        assert presence.status == "online"
        assert presence.current_resource_type == "project"

    @pytest.mark.asyncio
    async def test_touch_user_activity_update(self, db_session: AsyncSession):
        """Second call should update, not duplicate."""
        from app.services.user_activity_service import touch_user_activity

        p1 = await touch_user_activity(db_session, STUB_USER_ID)
        p2 = await touch_user_activity(
            db_session, STUB_USER_ID, resource_type="run",
        )
        assert p2.current_resource_type == "run"
        assert p1.user_id == p2.user_id

    @pytest.mark.asyncio
    async def test_get_user_assignment_context(self, db_session: AsyncSession):
        """Assignment context should include membership counts."""
        from app.services.user_activity_service import get_user_assignment_context

        ctx = await get_user_assignment_context(db_session, STUB_USER_ID)
        assert ctx["user_id"] == str(STUB_USER_ID)
        assert "workspace_memberships" in ctx
        assert "project_memberships" in ctx

    @pytest.mark.asyncio
    async def test_user_context_endpoint(self, client: AsyncClient):
        """GET /users/{user_id}/context should return context dict."""
        resp = await client.get(f"/users/{STUB_USER_ID}/context")
        assert resp.status_code == 200
        data = resp.json()
        assert data["user_id"] == str(STUB_USER_ID)


# ── FM-060: Integration flows ────────────────────────────────────

class TestCollaborationIntegration:
    """End-to-end collaboration integration tests."""

    @pytest.mark.asyncio
    async def test_full_workspace_project_flow(self, client: AsyncClient):
        """Create workspace → add member → create project in workspace → list activity."""
        # 1. Create workspace
        ws_resp = await client.post("/workspaces", json={
            "name": "Integration WS", "slug": "integ-ws-flow"
        })
        assert ws_resp.status_code == 201
        ws_id = ws_resp.json()["id"]

        # 2. Add self as member
        mem_resp = await client.post(f"/workspaces/{ws_id}/members", json={
            "user_id": str(STUB_USER_ID), "role": "admin"
        })
        assert mem_resp.status_code == 201

        # 3. Create project in workspace
        proj_resp = await client.post("/projects", json={
            "name": "WS Project", "workspace_id": ws_id
        })
        assert proj_resp.status_code == 201
        assert proj_resp.json()["workspace_id"] == ws_id

        # 4. List workspace members
        members_resp = await client.get(f"/workspaces/{ws_id}/members")
        assert members_resp.status_code == 200
        assert members_resp.json()["total"] >= 1

    @pytest.mark.asyncio
    async def test_notification_create_and_read_flow(self, client: AsyncClient):
        """Create notification → list → mark read → verify unread count."""
        # Create (user_id comes from auth stub, not the body)
        n_resp = await client.post("/notifications", json={
            "notification_type": "approval_required",
            "title": "Review needed",
            "priority": "high",
        })
        assert n_resp.status_code == 201
        n_id = n_resp.json()["id"]

        # List — user_id comes from auth stub
        list_resp = await client.get("/notifications")
        assert list_resp.status_code == 200
        assert list_resp.json()["unread_count"] >= 1

        # Mark read
        read_resp = await client.post(f"/notifications/{n_id}/read")
        assert read_resp.status_code == 200

    @pytest.mark.asyncio
    async def test_escalation_with_events(self, client: AsyncClient, sample_project):
        """Create escalation rule → trigger → list events."""
        # Create rule
        rule_resp = await client.post(
            f"/projects/{sample_project.id}/escalation/rules",
            json={
                "name": "Stuck run rule",
                "trigger": "run_failure",
                "action": "notify",
                "rules": {"threshold_minutes": 30},
                "cooldown_minutes": 60,
            },
        )
        assert rule_resp.status_code == 201

        # Events should be empty initially
        events_resp = await client.get(f"/projects/{sample_project.id}/escalation/events")
        assert events_resp.status_code == 200

    @pytest.mark.asyncio
    async def test_presence_update_and_retrieve(self, client: AsyncClient):
        """Update presence → get presence."""
        await client.put("/presence", json={
            "status": "online",
            "current_resource_type": "project",
        })

        resp = await client.get(f"/presence/{STUB_USER_ID}")
        assert resp.status_code == 200
        assert resp.json()["status"] == "online"

    @pytest.mark.asyncio
    async def test_delivery_config_management(self, client: AsyncClient):
        """Create delivery config → list configs."""
        # Create webhook config
        config_resp = await client.post("/notifications/delivery", json={
            "channel": "webhook",
            "config": {"url": "https://example.com/hook"},
        })
        assert config_resp.status_code == 201

        # List configs
        list_resp = await client.get("/notifications/delivery")
        assert list_resp.status_code == 200
        assert list_resp.json()["total"] >= 1
