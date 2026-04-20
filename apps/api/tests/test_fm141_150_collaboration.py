"""FM-141–150: Comprehensive tests for Wave 10 — Collaboration & UX.

Covers:
  FM-141: Threaded comments (model + service + routes)
  FM-142: @Mentions & notification routing
  FM-143: Unified activity feed
  FM-144: Saved views & filters
  FM-146: Run annotations
  FM-147: Task assignment & workload
  FM-148: Approval delegation & batch decisions
  FM-149: Notification digest & center
  FM-150: Project overview / dashboard
"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import STUB_USER_ID


# ── Helpers ──────────────────────────────────────────────────────


async def _seed_project(db: AsyncSession):
    from app.models.project import Project
    from app.models.membership import ProjectMember, ProjectRole

    project = Project(
        name="Collab Test Project",
        description="For FM-141–150 tests",
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


async def _seed_run(db: AsyncSession, project_id: uuid.UUID):
    from app.models.run import Run

    run = Run(project_id=project_id, run_number=1, trigger="test")
    db.add(run)
    await db.flush()
    await db.refresh(run)
    return run


async def _seed_task(db: AsyncSession, run_id: uuid.UUID):
    from app.models.task import Task, TaskStatus

    task = Task(
        title="Test Task",
        task_type="architecture",
        status=TaskStatus.READY,
        order_index=0,
        run_id=run_id,
    )
    db.add(task)
    await db.flush()
    await db.refresh(task)
    return task


# =====================================================================
# FM-141: Threaded Comments
# =====================================================================


class TestComments:
    @pytest.mark.asyncio
    async def test_create_comment(self, db_session: AsyncSession):
        project = await _seed_project(db_session)
        run = await _seed_run(db_session, project.id)

        from app.schemas.comment import CommentCreate
        from app.services.comment_service import create_comment

        data = CommentCreate(entity_type="run", entity_id=run.id, body="First comment")
        comment = await create_comment(db_session, data, author_id=STUB_USER_ID)
        assert comment.id is not None
        assert comment.body == "First comment"
        assert comment.parent_id is None

    @pytest.mark.asyncio
    async def test_thread_reply(self, db_session: AsyncSession):
        project = await _seed_project(db_session)
        run = await _seed_run(db_session, project.id)

        from app.schemas.comment import CommentCreate
        from app.services.comment_service import create_comment

        parent_data = CommentCreate(entity_type="run", entity_id=run.id, body="Parent")
        parent = await create_comment(db_session, parent_data, STUB_USER_ID)
        reply_data = CommentCreate(
            entity_type="run", entity_id=run.id, body="Reply", parent_id=parent.id
        )
        reply = await create_comment(db_session, reply_data, STUB_USER_ID)
        assert reply.parent_id == parent.id

    @pytest.mark.asyncio
    async def test_list_comments(self, db_session: AsyncSession):
        project = await _seed_project(db_session)
        run = await _seed_run(db_session, project.id)

        from app.models.comment import CommentEntityType
        from app.schemas.comment import CommentCreate
        from app.services.comment_service import create_comment, list_comments

        d1 = CommentCreate(entity_type="run", entity_id=run.id, body="One")
        d2 = CommentCreate(entity_type="run", entity_id=run.id, body="Two")
        await create_comment(db_session, d1, STUB_USER_ID)
        await create_comment(db_session, d2, STUB_USER_ID)

        items, total = await list_comments(db_session, CommentEntityType.RUN, run.id)
        assert total >= 2

    @pytest.mark.asyncio
    async def test_soft_delete(self, db_session: AsyncSession):
        project = await _seed_project(db_session)
        run = await _seed_run(db_session, project.id)

        from app.schemas.comment import CommentCreate
        from app.services.comment_service import create_comment, delete_comment

        data = CommentCreate(entity_type="run", entity_id=run.id, body="To delete")
        comment = await create_comment(db_session, data, STUB_USER_ID)
        await delete_comment(db_session, comment.id, STUB_USER_ID)
        assert comment.deleted_at is not None

    @pytest.mark.asyncio
    async def test_update_author_only(self, db_session: AsyncSession):
        project = await _seed_project(db_session)
        run = await _seed_run(db_session, project.id)

        from app.schemas.comment import CommentCreate, CommentUpdate
        from app.services.comment_service import create_comment, update_comment
        from fastapi import HTTPException

        data = CommentCreate(entity_type="run", entity_id=run.id, body="Original")
        comment = await create_comment(db_session, data, STUB_USER_ID)
        updated = await update_comment(
            db_session, comment.id, CommentUpdate(body="Updated"), STUB_USER_ID
        )
        assert updated.body == "Updated"

        other_user = uuid.uuid4()
        with pytest.raises(HTTPException) as exc:
            await update_comment(
                db_session, comment.id, CommentUpdate(body="Nope"), other_user
            )
        assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_comment_http_routes(self, client: AsyncClient, sample_run):
        # Create
        resp = await client.post(
            "/comments",
            json={
                "entity_type": "run",
                "entity_id": str(sample_run.id),
                "body": "HTTP comment",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        comment_id = data["id"]

        # Get
        resp = await client.get(f"/comments/{comment_id}")
        assert resp.status_code == 200

        # List
        resp = await client.get(f"/comments?entity_type=run&entity_id={sample_run.id}")
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

        # Update
        resp = await client.patch(
            f"/comments/{comment_id}",
            json={"body": "Updated via HTTP"},
        )
        assert resp.status_code == 200

        # Delete (soft — route returns 200 with body)
        resp = await client.delete(f"/comments/{comment_id}")
        assert resp.status_code == 200


# =====================================================================
# FM-142: @Mentions
# =====================================================================


class TestMentions:
    @pytest.mark.asyncio
    async def test_extract_mentions(self):
        from app.services.mention_service import extract_mentions

        text = "Hey @alice and @bob, check this out @alice"
        mentions = extract_mentions(text)
        # Returns list (deduped, preserves order)
        assert "alice" in mentions
        assert "bob" in mentions

    @pytest.mark.asyncio
    async def test_resolve_mentions(self, db_session: AsyncSession):
        from app.services.mention_service import resolve_mentions

        mapping = await resolve_mentions(db_session, ["nonexistent_user"])
        assert "nonexistent_user" not in mapping

    @pytest.mark.asyncio
    async def test_create_mention_notifications(self, db_session: AsyncSession):
        from app.services.mention_service import (
            extract_mentions,
            resolve_mentions,
            create_mention_notifications,
        )
        from app.models.user import User

        other = User(id=uuid.uuid4(), email="other@test.dev", display_name="other_user")
        db_session.add(other)
        await db_session.flush()

        text = "CC @other_user"
        mentions = extract_mentions(text)
        mapping = await resolve_mentions(db_session, mentions)

        comment_id = uuid.uuid4()
        entity_id = uuid.uuid4()
        notifs = await create_mention_notifications(
            db_session,
            mentioned_user_ids=list(mapping.values()),
            author_id=STUB_USER_ID,
            comment_id=comment_id,
            entity_type="comment",
            entity_id=entity_id,
            comment_preview=text,
        )
        assert len(notifs) == 1
        assert notifs[0].user_id == other.id


# =====================================================================
# FM-143: Unified Activity Feed
# =====================================================================


class TestUnifiedActivity:
    @pytest.mark.asyncio
    async def test_empty_feed(self, db_session: AsyncSession):
        from app.services.unified_activity_service import get_unified_activity

        project = await _seed_project(db_session)
        items, total, _cursor = await get_unified_activity(
            db_session, project_id=project.id
        )
        assert total == 0
        assert items == []

    @pytest.mark.asyncio
    async def test_feed_with_entries(self, db_session: AsyncSession):
        from app.models.activity import ActivityFeedEntry, ActivityType
        from app.services.unified_activity_service import get_unified_activity

        project = await _seed_project(db_session)
        entry = ActivityFeedEntry(
            project_id=project.id,
            actor_id=STUB_USER_ID,
            activity_type=ActivityType.RUN_STARTED,
            summary="Run started",
        )
        db_session.add(entry)
        await db_session.flush()

        items, total, _cursor = await get_unified_activity(
            db_session, project_id=project.id
        )
        assert total == 1
        assert items[0]["event_type"] == "run_started"


# =====================================================================
# FM-144: Saved Views
# =====================================================================


class TestSavedViews:
    @pytest.mark.asyncio
    async def test_create_and_list(self, db_session: AsyncSession):
        project = await _seed_project(db_session)

        from app.schemas.saved_view import SavedViewCreate
        from app.services.saved_view_service import create_saved_view, list_saved_views

        data = SavedViewCreate(
            name="My Filter",
            entity_type="run",
            filter_json={"status": "running"},
        )
        view = await create_saved_view(db_session, project.id, data, STUB_USER_ID)
        assert view.name == "My Filter"

        views, total = await list_saved_views(db_session, project.id, STUB_USER_ID)
        assert any(v.id == view.id for v in views)

    @pytest.mark.asyncio
    async def test_update_creator_only(self, db_session: AsyncSession):
        project = await _seed_project(db_session)

        from app.schemas.saved_view import SavedViewCreate, SavedViewUpdate
        from app.services.saved_view_service import create_saved_view, update_saved_view
        from fastapi import HTTPException

        data = SavedViewCreate(name="V1", entity_type="run", filter_json={})
        view = await create_saved_view(db_session, project.id, data, STUB_USER_ID)
        updated = await update_saved_view(
            db_session, view.id, SavedViewUpdate(name="V2"), STUB_USER_ID
        )
        assert updated.name == "V2"

        with pytest.raises(HTTPException) as exc:
            await update_saved_view(
                db_session, view.id, SavedViewUpdate(name="Nope"), uuid.uuid4()
            )
        assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_saved_views_http(self, client: AsyncClient, sample_project):
        resp = await client.post(
            f"/projects/{sample_project.id}/views",
            json={
                "name": "HTTP View",
                "entity_type": "task",
                "filter_json": {"type": "architecture"},
            },
        )
        assert resp.status_code == 201
        view_id = resp.json()["id"]

        resp = await client.get(f"/projects/{sample_project.id}/views")
        assert resp.status_code == 200

        resp = await client.delete(f"/views/{view_id}")
        assert resp.status_code == 204


# =====================================================================
# FM-146: Run Annotations
# =====================================================================


class TestRunAnnotations:
    @pytest.mark.asyncio
    async def test_create_annotation(self, db_session: AsyncSession):
        project = await _seed_project(db_session)
        run = await _seed_run(db_session, project.id)

        from app.schemas.run_annotation import AnnotationCreate
        from app.services.run_annotation_service import create_annotation

        data = AnnotationCreate(annotation_type="note", body="Important observation")
        ann = await create_annotation(db_session, run.id, data, STUB_USER_ID)
        assert ann.body == "Important observation"
        assert ann.annotation_type.value == "note"

    @pytest.mark.asyncio
    async def test_list_with_type_filter(self, db_session: AsyncSession):
        project = await _seed_project(db_session)
        run = await _seed_run(db_session, project.id)

        from app.models.run_annotation import AnnotationType
        from app.schemas.run_annotation import AnnotationCreate
        from app.services.run_annotation_service import (
            create_annotation,
            list_annotations,
        )

        d1 = AnnotationCreate(annotation_type="note", body="N1")
        d2 = AnnotationCreate(annotation_type="warning", body="W1")
        await create_annotation(db_session, run.id, d1, STUB_USER_ID)
        await create_annotation(db_session, run.id, d2, STUB_USER_ID)

        notes, total = await list_annotations(db_session, run.id, AnnotationType.NOTE)
        assert all(a.annotation_type.value == "note" for a in notes)

    @pytest.mark.asyncio
    async def test_annotation_http(self, client: AsyncClient, sample_run):
        resp = await client.post(
            f"/runs/{sample_run.id}/annotations",
            json={"annotation_type": "decision", "body": "Decided to proceed"},
        )
        assert resp.status_code == 201
        ann_id = resp.json()["id"]

        resp = await client.get(f"/runs/{sample_run.id}/annotations")
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

        resp = await client.delete(f"/annotations/{ann_id}")
        assert resp.status_code == 204


# =====================================================================
# FM-147: Task Assignment
# =====================================================================


class TestTaskAssignment:
    @pytest.mark.asyncio
    async def test_assign_task(self, db_session: AsyncSession):
        project = await _seed_project(db_session)
        run = await _seed_run(db_session, project.id)
        task = await _seed_task(db_session, run.id)

        from app.services.task_assignment_service import assign_task

        result = await assign_task(db_session, task.id, STUB_USER_ID)
        assert result.assignee_id == STUB_USER_ID
        assert result.assigned_at is not None

    @pytest.mark.asyncio
    async def test_unassign_task(self, db_session: AsyncSession):
        project = await _seed_project(db_session)
        run = await _seed_run(db_session, project.id)
        task = await _seed_task(db_session, run.id)

        from app.services.task_assignment_service import assign_task, unassign_task

        await assign_task(db_session, task.id, STUB_USER_ID)
        result = await unassign_task(db_session, task.id)
        assert result.assignee_id is None
        assert result.assigned_at is None

    @pytest.mark.asyncio
    async def test_list_user_tasks(self, db_session: AsyncSession):
        project = await _seed_project(db_session)
        run = await _seed_run(db_session, project.id)
        task = await _seed_task(db_session, run.id)

        from app.services.task_assignment_service import (
            assign_task,
            list_user_assigned_tasks,
        )

        await assign_task(db_session, task.id, STUB_USER_ID)
        tasks = await list_user_assigned_tasks(db_session, STUB_USER_ID)
        assert any(t.id == task.id for t in tasks)

    @pytest.mark.asyncio
    async def test_project_workload(self, db_session: AsyncSession):
        project = await _seed_project(db_session)
        run = await _seed_run(db_session, project.id)
        task = await _seed_task(db_session, run.id)

        from app.services.task_assignment_service import (
            assign_task,
            get_project_workload,
        )

        await assign_task(db_session, task.id, STUB_USER_ID)
        workload = await get_project_workload(db_session, project.id)
        assert len(workload) >= 1
        assert workload[0]["user_id"] == str(STUB_USER_ID)


# =====================================================================
# FM-148: Approval Enhancements
# =====================================================================


class TestApprovalEnhancements:
    @pytest.mark.asyncio
    async def test_create_delegation(self, db_session: AsyncSession):
        from app.services.approval_enhanced_service import create_delegation
        from app.models.user import User

        delegate_id = uuid.uuid4()
        db_session.add(
            User(id=delegate_id, email="delegate@test.dev", display_name="Delegate")
        )
        await db_session.flush()

        delegation = await create_delegation(db_session, STUB_USER_ID, delegate_id)
        assert delegation.delegator_id == STUB_USER_ID
        assert delegation.delegate_id == delegate_id
        assert delegation.is_active is True

    @pytest.mark.asyncio
    async def test_batch_approve(self, db_session: AsyncSession):
        project = await _seed_project(db_session)
        run = await _seed_run(db_session, project.id)

        from app.models.approval_request import ApprovalRequest, ApprovalStatus
        from app.services.approval_enhanced_service import batch_decide

        approvals = []
        for i in range(3):
            a = ApprovalRequest(
                project_id=project.id,
                run_id=run.id,
                title=f"Approval {i}",
                description="Test",
                status=ApprovalStatus.PENDING,
            )
            db_session.add(a)
            await db_session.flush()
            await db_session.refresh(a)
            approvals.append(a)

        result = await batch_decide(
            db_session,
            [a.id for a in approvals],
            ApprovalStatus.APPROVED,
            decided_by="Test User",
            comment="LGTM",
        )
        assert len(result) == 3
        assert all(r.status == ApprovalStatus.APPROVED for r in result)

    @pytest.mark.asyncio
    async def test_check_expired(self, db_session: AsyncSession):
        project = await _seed_project(db_session)
        run = await _seed_run(db_session, project.id)

        from app.models.approval_request import ApprovalRequest, ApprovalStatus
        from app.services.approval_enhanced_service import check_expired_approvals

        past = datetime(2020, 1, 1, tzinfo=timezone.utc)
        a = ApprovalRequest(
            project_id=project.id,
            run_id=run.id,
            title="Expired",
            description="Test",
            status=ApprovalStatus.PENDING,
            expires_at=past,
        )
        db_session.add(a)
        await db_session.flush()

        expired = await check_expired_approvals(db_session)
        assert any(e.id == a.id for e in expired)


# =====================================================================
# FM-149: Notification Center
# =====================================================================


class TestNotificationCenter:
    @pytest.mark.asyncio
    async def test_mark_all_read(self, db_session: AsyncSession):
        from app.models.notification import (
            Notification,
            NotificationType,
            NotificationPriority,
        )
        from app.services.notification_digest_service import mark_all_read

        for i in range(3):
            db_session.add(
                Notification(
                    user_id=STUB_USER_ID,
                    notification_type=NotificationType.SYSTEM,
                    priority=NotificationPriority.NORMAL,
                    title=f"Notif {i}",
                    body="Test",
                    is_read=False,
                )
            )
        await db_session.flush()

        count = await mark_all_read(db_session, STUB_USER_ID)
        assert count == 3

    @pytest.mark.asyncio
    async def test_dismiss_notification(self, db_session: AsyncSession):
        from app.models.notification import (
            Notification,
            NotificationType,
            NotificationPriority,
        )
        from app.services.notification_digest_service import dismiss_notification

        n = Notification(
            user_id=STUB_USER_ID,
            notification_type=NotificationType.SYSTEM,
            priority=NotificationPriority.NORMAL,
            title="Dismiss me",
            body="Test",
            is_read=False,
        )
        db_session.add(n)
        await db_session.flush()
        await db_session.refresh(n)

        result = await dismiss_notification(db_session, n.id, STUB_USER_ID)
        assert result is not None
        assert result.dismissed_at is not None

    @pytest.mark.asyncio
    async def test_list_notifications_with_filter(self, db_session: AsyncSession):
        from app.models.notification import (
            Notification,
            NotificationType,
            NotificationPriority,
        )
        from app.services.notification_digest_service import list_notifications

        for i, cat in enumerate(["mention", "mention", "approval"]):
            db_session.add(
                Notification(
                    user_id=STUB_USER_ID,
                    notification_type=NotificationType.SYSTEM,
                    priority=NotificationPriority.NORMAL,
                    title=f"N{i}",
                    body="Test",
                    is_read=False,
                    category=cat,
                )
            )
        await db_session.flush()

        items, total = await list_notifications(
            db_session, STUB_USER_ID, category="mention"
        )
        assert total == 2

    @pytest.mark.asyncio
    async def test_digest_preview(self, db_session: AsyncSession):
        from app.models.notification import (
            Notification,
            NotificationType,
            NotificationPriority,
        )
        from app.services.notification_digest_service import get_digest_preview

        for i in range(5):
            db_session.add(
                Notification(
                    user_id=STUB_USER_ID,
                    notification_type=NotificationType.SYSTEM,
                    priority=NotificationPriority.NORMAL,
                    title=f"D{i}",
                    body="Digest",
                    is_read=False,
                )
            )
        await db_session.flush()

        digest = await get_digest_preview(db_session, STUB_USER_ID)
        assert len(digest) == 5


# =====================================================================
# FM-150: Project Overview
# =====================================================================


class TestProjectOverview:
    @pytest.mark.asyncio
    async def test_overview_empty(self, db_session: AsyncSession):
        project = await _seed_project(db_session)

        from app.services.project_overview_service import get_project_overview

        overview = await get_project_overview(db_session, project.id)
        assert overview["total_runs"] == 0
        assert overview["health_grade"] == "A"  # 100% success rate when 0 runs
        assert overview["team_size"] >= 1

    @pytest.mark.asyncio
    async def test_overview_with_data(self, db_session: AsyncSession):
        project = await _seed_project(db_session)
        from app.models.run import Run

        for i in range(3):
            db_session.add(
                Run(
                    project_id=project.id,
                    run_number=i + 1,
                    trigger="test",
                    status="completed",
                )
            )
        await db_session.flush()

        from app.services.project_overview_service import get_project_overview

        overview = await get_project_overview(db_session, project.id)
        assert overview["total_runs"] == 3
        assert overview["successful_runs"] == 3
        assert overview["success_rate"] == 100.0


# =====================================================================
# FM-145: User Presence — Heartbeat, Staleness, Project Scope
# =====================================================================


class TestPresenceHeartbeat:
    @pytest.mark.asyncio
    async def test_heartbeat_creates_online_presence(self, db_session: AsyncSession):
        from app.services.activity_service import heartbeat, get_presence

        project = await _seed_project(db_session)
        p = await heartbeat(
            db_session,
            user_id=STUB_USER_ID,
            project_id=project.id,
            current_resource_type="run",
        )
        assert p.status == "online"
        assert p.project_id == project.id
        assert p.current_resource_type == "run"

        fetched = await get_presence(db_session, STUB_USER_ID)
        assert fetched is not None
        assert fetched.status == "online"

    @pytest.mark.asyncio
    async def test_heartbeat_updates_existing(self, db_session: AsyncSession):
        from app.services.activity_service import heartbeat

        project = await _seed_project(db_session)
        p1 = await heartbeat(db_session, user_id=STUB_USER_ID, project_id=project.id)
        p2 = await heartbeat(
            db_session,
            user_id=STUB_USER_ID,
            project_id=project.id,
            current_resource_type="task",
        )
        assert p1.id == p2.id
        assert p2.current_resource_type == "task"
        assert p2.status == "online"


class TestPresenceStaleness:
    @pytest.mark.asyncio
    async def test_staleness_marks_away_and_offline(self, db_session: AsyncSession):
        from app.models.activity import UserPresence
        from app.services.activity_service import apply_staleness

        now = datetime.now(timezone.utc)

        # User 1: fresh (should stay online)
        u1 = UserPresence(
            user_id=uuid.uuid4(),
            status="online",
            last_seen_at=now,
        )
        # User 2: 10 minutes ago (should become away)
        u2 = UserPresence(
            user_id=uuid.uuid4(),
            status="online",
            last_seen_at=now - timedelta(minutes=10),
        )
        # User 3: 20 minutes ago (should become offline)
        u3 = UserPresence(
            user_id=uuid.uuid4(),
            status="online",
            last_seen_at=now - timedelta(minutes=20),
        )
        db_session.add_all([u1, u2, u3])
        await db_session.flush()

        updated_count = await apply_staleness(db_session)
        assert updated_count >= 2

        await db_session.refresh(u1)
        await db_session.refresh(u2)
        await db_session.refresh(u3)
        assert u1.status == "online"
        assert u2.status == "away"
        assert u3.status == "offline"


class TestProjectScopedPresence:
    @pytest.mark.asyncio
    async def test_list_project_presence(self, db_session: AsyncSession):
        from app.models.activity import UserPresence
        from app.services.activity_service import list_project_presence

        project = await _seed_project(db_session)
        now = datetime.now(timezone.utc)

        # Online user in project
        u1 = UserPresence(
            user_id=uuid.uuid4(),
            status="online",
            project_id=project.id,
            last_seen_at=now,
        )
        # Offline user in project — should be excluded
        u2 = UserPresence(
            user_id=uuid.uuid4(),
            status="offline",
            project_id=project.id,
            last_seen_at=now - timedelta(minutes=30),
        )
        # Online user in DIFFERENT project — should be excluded
        u3 = UserPresence(
            user_id=uuid.uuid4(),
            status="online",
            project_id=uuid.uuid4(),
            last_seen_at=now,
        )
        db_session.add_all([u1, u2, u3])
        await db_session.flush()

        result = await list_project_presence(db_session, project.id)
        assert len(result) == 1
        assert result[0].user_id == u1.user_id

    @pytest.mark.asyncio
    async def test_heartbeat_route(self, client: AsyncClient):
        resp = await client.post(
            "/presence/heartbeat",
            json={"current_resource_type": "task"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "online"

    @pytest.mark.asyncio
    async def test_project_presence_route(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        project = await _seed_project(db_session)
        # Seed presence for current user
        from app.services.activity_service import heartbeat

        await heartbeat(db_session, user_id=STUB_USER_ID, project_id=project.id)
        await db_session.commit()

        resp = await client.get(f"/projects/{project.id}/presence")
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list)
