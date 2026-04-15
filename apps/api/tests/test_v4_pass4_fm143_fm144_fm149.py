"""Pass 4 tests — FM-143 cursor pagination, FM-144 default view seeding,
FM-149 dismiss/grouping/digest routes.

Targets:
  FM-143: Cursor-based pagination on unified activity feed
  FM-144: Default views seeded on project creation
  FM-149: Dismiss route, grouped notifications, digest preview route
"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import STUB_USER_ID


# ── Helpers ──────────────────────────────────────────────────────


async def _seed_project(db: AsyncSession):
    from app.models.project import Project
    from app.models.membership import ProjectMember, ProjectRole

    project = Project(
        name="Pass4 Test Project",
        description="For Pass-4 tests",
        owner_id=STUB_USER_ID,
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


async def _seed_workspace(db: AsyncSession):
    from app.models.workspace import Workspace
    from app.models.membership import WorkspaceMember, WorkspaceRole

    ws = Workspace(name="Pass4 WS", slug="pass4-ws", owner_id=STUB_USER_ID)
    db.add(ws)
    await db.flush()
    await db.refresh(ws)
    wm = WorkspaceMember(
        workspace_id=ws.id,
        user_id=STUB_USER_ID,
        role=WorkspaceRole.OWNER,
    )
    db.add(wm)
    await db.flush()
    return ws


# =====================================================================
# FM-144: Default View Seeding
# =====================================================================


class TestDefaultViewSeeding:
    @pytest.mark.asyncio
    async def test_seed_creates_three_defaults(self, db_session: AsyncSession):
        """seed_default_views creates 'My tasks', 'Pending approvals', 'Failed runs'."""
        from app.services.saved_view_service import seed_default_views

        project = await _seed_project(db_session)
        views = await seed_default_views(db_session, project.id, STUB_USER_ID)
        assert len(views) == 3
        names = {v.name for v in views}
        assert names == {"My tasks", "Pending approvals", "Failed runs"}

    @pytest.mark.asyncio
    async def test_seeded_views_are_team_visible(self, db_session: AsyncSession):
        from app.services.saved_view_service import seed_default_views
        from app.models.saved_view import ViewVisibility

        project = await _seed_project(db_session)
        views = await seed_default_views(db_session, project.id, STUB_USER_ID)
        for v in views:
            assert v.visibility == ViewVisibility.TEAM

    @pytest.mark.asyncio
    async def test_seeded_views_have_correct_entity_types(self, db_session: AsyncSession):
        from app.services.saved_view_service import seed_default_views

        project = await _seed_project(db_session)
        views = await seed_default_views(db_session, project.id, STUB_USER_ID)
        entity_types = {v.name: v.entity_type for v in views}
        assert entity_types["My tasks"] == "task"
        assert entity_types["Pending approvals"] == "approval"
        assert entity_types["Failed runs"] == "run"

    @pytest.mark.asyncio
    async def test_project_create_seeds_views(self, db_session: AsyncSession):
        """create_project now auto-seeds default views."""
        from app.services.project_service import create_project
        from app.schemas.project import ProjectCreate
        from app.services.saved_view_service import list_saved_views

        ws = await _seed_workspace(db_session)
        data = ProjectCreate(
            name="AutoSeed Project",
            description="Tests auto-seeding",
            workspace_id=ws.id,
        )
        project = await create_project(db_session, data, STUB_USER_ID)
        views, total = await list_saved_views(db_session, project.id, STUB_USER_ID)
        assert total == 3
        assert {v.name for v in views} == {
            "My tasks",
            "Pending approvals",
            "Failed runs",
        }


# =====================================================================
# FM-149: Dismiss, Grouped Notifications, Digest
# =====================================================================


class TestNotificationDismiss:
    @pytest.mark.asyncio
    async def test_dismiss_sets_dismissed_at(self, db_session: AsyncSession):
        from app.models.notification import Notification, NotificationType, NotificationPriority
        from app.services.notification_digest_service import dismiss_notification

        n = Notification(
            user_id=STUB_USER_ID,
            notification_type=NotificationType.SYSTEM,
            priority=NotificationPriority.NORMAL,
            title="Dismiss me",
        )
        db_session.add(n)
        await db_session.flush()
        await db_session.refresh(n)

        result = await dismiss_notification(db_session, n.id, STUB_USER_ID)
        assert result is not None
        assert result.dismissed_at is not None

    @pytest.mark.asyncio
    async def test_dismiss_wrong_user_returns_none(self, db_session: AsyncSession):
        from app.models.notification import Notification, NotificationType, NotificationPriority
        from app.services.notification_digest_service import dismiss_notification

        n = Notification(
            user_id=STUB_USER_ID,
            notification_type=NotificationType.SYSTEM,
            priority=NotificationPriority.NORMAL,
            title="Not yours",
        )
        db_session.add(n)
        await db_session.flush()
        await db_session.refresh(n)

        other_user = uuid.uuid4()
        result = await dismiss_notification(db_session, n.id, other_user)
        assert result is None

    @pytest.mark.asyncio
    async def test_dismissed_excluded_from_list(self, db_session: AsyncSession):
        from app.models.notification import Notification, NotificationType, NotificationPriority
        from app.services.notification_digest_service import (
            dismiss_notification,
            list_notifications,
        )

        n = Notification(
            user_id=STUB_USER_ID,
            notification_type=NotificationType.SYSTEM,
            priority=NotificationPriority.NORMAL,
            title="Will dismiss",
        )
        db_session.add(n)
        await db_session.flush()
        await db_session.refresh(n)

        await dismiss_notification(db_session, n.id, STUB_USER_ID)
        items, total = await list_notifications(db_session, STUB_USER_ID)
        assert all(i.id != n.id for i in items)


class TestGroupedNotifications:
    @pytest.mark.asyncio
    async def test_grouped_collapses_same_key(self, db_session: AsyncSession):
        from app.models.notification import Notification, NotificationType, NotificationPriority
        from app.services.notification_digest_service import get_grouped_notifications

        for i in range(3):
            db_session.add(
                Notification(
                    user_id=STUB_USER_ID,
                    notification_type=NotificationType.TASK_COMPLETED,
                    priority=NotificationPriority.NORMAL,
                    title=f"Task #{i} done",
                    group_key="run:42",
                    is_read=False,
                )
            )
        await db_session.flush()

        groups = await get_grouped_notifications(db_session, STUB_USER_ID)
        grouped = [g for g in groups if g["group_key"] == "run:42"]
        assert len(grouped) == 1
        assert grouped[0]["count"] == 3

    @pytest.mark.asyncio
    async def test_ungrouped_appear_individually(self, db_session: AsyncSession):
        from app.models.notification import Notification, NotificationType, NotificationPriority
        from app.services.notification_digest_service import get_grouped_notifications

        for i in range(2):
            db_session.add(
                Notification(
                    user_id=STUB_USER_ID,
                    notification_type=NotificationType.SYSTEM,
                    priority=NotificationPriority.NORMAL,
                    title=f"Standalone {i}",
                    group_key=None,
                    is_read=False,
                )
            )
        await db_session.flush()

        groups = await get_grouped_notifications(db_session, STUB_USER_ID)
        ungrouped = [g for g in groups if g["group_key"] is None]
        assert len(ungrouped) == 2
        for g in ungrouped:
            assert g["count"] == 1

    @pytest.mark.asyncio
    async def test_read_notifications_excluded_from_groups(self, db_session: AsyncSession):
        from app.models.notification import Notification, NotificationType, NotificationPriority
        from app.services.notification_digest_service import get_grouped_notifications

        db_session.add(
            Notification(
                user_id=STUB_USER_ID,
                notification_type=NotificationType.SYSTEM,
                priority=NotificationPriority.NORMAL,
                title="Already read",
                group_key="run:99",
                is_read=True,
            )
        )
        await db_session.flush()

        groups = await get_grouped_notifications(db_session, STUB_USER_ID)
        run99 = [g for g in groups if g["group_key"] == "run:99"]
        assert len(run99) == 0


class TestDigestPreview:
    @pytest.mark.asyncio
    async def test_digest_returns_unread_undismissed(self, db_session: AsyncSession):
        from app.models.notification import Notification, NotificationType, NotificationPriority
        from app.services.notification_digest_service import get_digest_preview

        for i in range(3):
            db_session.add(
                Notification(
                    user_id=STUB_USER_ID,
                    notification_type=NotificationType.SYSTEM,
                    priority=NotificationPriority.NORMAL,
                    title=f"Digest {i}",
                    is_read=False,
                )
            )
        db_session.add(
            Notification(
                user_id=STUB_USER_ID,
                notification_type=NotificationType.SYSTEM,
                priority=NotificationPriority.NORMAL,
                title="Read item",
                is_read=True,
            )
        )
        await db_session.flush()

        digest = await get_digest_preview(db_session, STUB_USER_ID)
        assert len(digest) == 3
        assert all(not n.is_read for n in digest)

    @pytest.mark.asyncio
    async def test_digest_excludes_dismissed(self, db_session: AsyncSession):
        from app.models.notification import Notification, NotificationType, NotificationPriority
        from app.services.notification_digest_service import (
            get_digest_preview,
            dismiss_notification,
        )

        n = Notification(
            user_id=STUB_USER_ID,
            notification_type=NotificationType.SYSTEM,
            priority=NotificationPriority.NORMAL,
            title="Dismissed",
            is_read=False,
        )
        db_session.add(n)
        await db_session.flush()
        await db_session.refresh(n)

        await dismiss_notification(db_session, n.id, STUB_USER_ID)
        digest = await get_digest_preview(db_session, STUB_USER_ID)
        assert all(d.id != n.id for d in digest)


# =====================================================================
# FM-143: Cursor-Based Pagination
# =====================================================================


class TestCursorPagination:
    @pytest.mark.asyncio
    async def test_cursor_returns_older_entries(self, db_session: AsyncSession):
        from app.models.activity import ActivityFeedEntry, ActivityType
        from app.services.unified_activity_service import get_unified_activity

        project = await _seed_project(db_session)
        now = datetime.now(timezone.utc)
        for i in range(5):
            db_session.add(
                ActivityFeedEntry(
                    project_id=project.id,
                    actor_id=STUB_USER_ID,
                    activity_type=ActivityType.RUN_STARTED,
                    summary=f"Entry {i}",
                    created_at=now - timedelta(minutes=i),
                )
            )
        await db_session.flush()

        # First page (no cursor) — get the 3 newest
        items, total, cursor = await get_unified_activity(
            db_session, project_id=project.id, limit=3,
        )
        assert len(items) == 3
        assert total == 5
        assert cursor is not None

        # Second page (with cursor) — get the 2 remaining
        cursor_dt = datetime.fromisoformat(cursor)
        items2, total2, cursor2 = await get_unified_activity(
            db_session, project_id=project.id, limit=3, cursor=cursor_dt,
        )
        assert len(items2) == 2
        # No next cursor since this is the last page
        assert cursor2 is None

    @pytest.mark.asyncio
    async def test_cursor_no_overlap(self, db_session: AsyncSession):
        from app.models.activity import ActivityFeedEntry, ActivityType
        from app.services.unified_activity_service import get_unified_activity

        project = await _seed_project(db_session)
        now = datetime.now(timezone.utc)
        for i in range(6):
            db_session.add(
                ActivityFeedEntry(
                    project_id=project.id,
                    actor_id=STUB_USER_ID,
                    activity_type=ActivityType.TASK_COMPLETED,
                    summary=f"Item {i}",
                    created_at=now - timedelta(minutes=i * 2),
                )
            )
        await db_session.flush()

        page1, _, c1 = await get_unified_activity(
            db_session, project_id=project.id, limit=3,
        )
        page2, _, _ = await get_unified_activity(
            db_session,
            project_id=project.id,
            limit=3,
            cursor=datetime.fromisoformat(c1),
        )
        page1_ids = {i["id"] for i in page1}
        page2_ids = {i["id"] for i in page2}
        assert page1_ids.isdisjoint(page2_ids)

    @pytest.mark.asyncio
    async def test_cursor_none_when_all_returned(self, db_session: AsyncSession):
        from app.models.activity import ActivityFeedEntry, ActivityType
        from app.services.unified_activity_service import get_unified_activity

        project = await _seed_project(db_session)
        db_session.add(
            ActivityFeedEntry(
                project_id=project.id,
                actor_id=STUB_USER_ID,
                activity_type=ActivityType.COMMENT,
                summary="Only one",
            )
        )
        await db_session.flush()

        items, total, cursor = await get_unified_activity(
            db_session, project_id=project.id, limit=50,
        )
        assert len(items) == 1
        assert cursor is None

    @pytest.mark.asyncio
    async def test_empty_feed_cursor_none(self, db_session: AsyncSession):
        from app.services.unified_activity_service import get_unified_activity

        project = await _seed_project(db_session)
        items, total, cursor = await get_unified_activity(
            db_session, project_id=project.id,
        )
        assert items == []
        assert cursor is None
