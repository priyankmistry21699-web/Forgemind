"""V4 Pass 2 — Depth tests for FM-148, FM-154, FM-157, FM-176 improvements.

Tests:
  FM-157: Reviewer suggestion/scoring via code ownership
  FM-154: CI readiness gating (pass-rate threshold in merge readiness)
  FM-148: Escalation → notification delivery wiring
  FM-176: Notification entity retention (workspace-scoped via membership)
"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import STUB_USER_ID


# Alias the conftest fixture name for brevity in this file
@pytest.fixture
def db(db_session):
    return db_session


# ── Helpers ──────────────────────────────────────────────────────


async def _seed_project(db: AsyncSession):
    from app.models.project import Project
    from app.models.membership import ProjectMember, ProjectRole

    project = Project(
        name="V4 Pass 2 Project",
        description="For depth tests",
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

    ws = Workspace(
        name="Test WS", slug=f"test-ws-{uuid.uuid4().hex[:8]}", owner_id=STUB_USER_ID
    )
    db.add(ws)
    await db.flush()
    await db.refresh(ws)
    mem = WorkspaceMember(
        workspace_id=ws.id, user_id=STUB_USER_ID, role=WorkspaceRole.ADMIN
    )
    db.add(mem)
    await db.flush()
    return ws


async def _seed_github_stack(db: AsyncSession, project_id: uuid.UUID):
    from app.models.github_integration import (
        GitHubInstallation,
        RepositoryLink,
    )

    inst = GitHubInstallation(
        installation_id=54321,
        account_login="test-org",
        account_type="Organization",
        connected_by=STUB_USER_ID,
    )
    db.add(inst)
    await db.flush()
    await db.refresh(inst)
    repo = RepositoryLink(
        installation_id=inst.id,
        project_id=project_id,
        github_repo_id=88888,
        full_name="test-org/depth-repo",
        default_branch="main",
    )
    db.add(repo)
    await db.flush()
    await db.refresh(repo)
    return inst, repo


async def _seed_code_ownership(db: AsyncSession, repo_link_id: uuid.UUID):
    from app.models.github_integration import CodeOwnership

    user_a = uuid.uuid4()
    user_b = uuid.uuid4()
    user_c = uuid.uuid4()

    rules = [
        CodeOwnership(
            repository_link_id=repo_link_id,
            file_pattern="src/api/*.py",
            owner_user_id=user_a,
            owner_team_name=None,
        ),
        CodeOwnership(
            repository_link_id=repo_link_id,
            file_pattern="src/api/auth/*.py",
            owner_user_id=user_a,
            owner_team_name=None,
        ),
        CodeOwnership(
            repository_link_id=repo_link_id,
            file_pattern="src/api/*.py",
            owner_user_id=user_b,
            owner_team_name="backend-team",
        ),
        CodeOwnership(
            repository_link_id=repo_link_id,
            file_pattern="docs/*.md",
            owner_user_id=user_c,
            owner_team_name="docs-team",
        ),
    ]
    for r in rules:
        db.add(r)
    await db.flush()
    return user_a, user_b, user_c


# =====================================================================
# FM-157: Reviewer Suggestion / Scoring
# =====================================================================


class TestReviewerSuggestion:
    @pytest.mark.asyncio
    async def test_suggest_reviewers_ranks_by_coverage(self, db: AsyncSession):
        from app.services.code_review_service import suggest_reviewers

        project = await _seed_project(db)
        _, repo = await _seed_github_stack(db, project.id)
        user_a, user_b, user_c = await _seed_code_ownership(db, repo.id)

        # user_a owns "src/api/*.py" AND "src/api/auth/*.py" → matches 2 files
        # user_b owns "src/api/*.py" → matches 1 file
        # user_c owns "docs/*.md" → matches 1 file
        file_paths = [
            "src/api/main.py",
            "src/api/auth/handler.py",
            "docs/README.md",
        ]

        results = await suggest_reviewers(db, repo.id, file_paths)

        assert len(results) == 3
        # user_a → 2 files matched (api/main.py, api/auth/handler.py)
        assert results[0]["owner_user_id"] == str(user_a)
        assert results[0]["coverage_count"] >= 2
        # user_c → 1 file but docs pattern
        # user_b → 1 file
        assert results[0]["score"] > results[1]["score"]

    @pytest.mark.asyncio
    async def test_suggest_reviewers_empty_files(self, db: AsyncSession):
        from app.services.code_review_service import suggest_reviewers

        project = await _seed_project(db)
        _, repo = await _seed_github_stack(db, project.id)

        results = await suggest_reviewers(db, repo.id, [])
        assert results == []

    @pytest.mark.asyncio
    async def test_suggest_reviewers_no_rules(self, db: AsyncSession):
        from app.services.code_review_service import suggest_reviewers

        project = await _seed_project(db)
        _, repo = await _seed_github_stack(db, project.id)

        results = await suggest_reviewers(db, repo.id, ["foo/bar.py"])
        assert results == []

    @pytest.mark.asyncio
    async def test_suggest_reviewers_exclude_author(self, db: AsyncSession):
        from app.services.code_review_service import suggest_reviewers

        project = await _seed_project(db)
        _, repo = await _seed_github_stack(db, project.id)
        user_a, user_b, user_c = await _seed_code_ownership(db, repo.id)

        results = await suggest_reviewers(
            db,
            repo.id,
            ["src/api/main.py"],
            exclude_user_ids=[user_a],
        )
        # user_a excluded → only user_b visible
        assert all(r["owner_user_id"] != str(user_a) for r in results)

    @pytest.mark.asyncio
    async def test_suggest_reviewers_max_reviewers(self, db: AsyncSession):
        from app.services.code_review_service import suggest_reviewers

        project = await _seed_project(db)
        _, repo = await _seed_github_stack(db, project.id)
        await _seed_code_ownership(db, repo.id)

        results = await suggest_reviewers(
            db,
            repo.id,
            ["src/api/main.py", "docs/README.md"],
            max_reviewers=1,
        )
        assert len(results) <= 1

    @pytest.mark.asyncio
    async def test_suggest_reviewers_route(self, client: AsyncClient, db: AsyncSession):
        project = await _seed_project(db)
        _, repo = await _seed_github_stack(db, project.id)
        await _seed_code_ownership(db, repo.id)
        await db.commit()

        resp = await client.post(
            f"/github/code-owners/suggest-reviewers?repo_link_id={repo.id}",
            json={"file_paths": ["src/api/main.py", "docs/README.md"]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert "score" in data[0]
        assert "coverage_count" in data[0]


# =====================================================================
# FM-154: CI Readiness Gating
# =====================================================================


class TestCIReadinessGating:
    async def _seed_ci_runs(
        self,
        db: AsyncSession,
        repo_link_id: uuid.UUID,
        *,
        success: int = 0,
        failure: int = 0,
    ):
        from app.models.github_integration import CIPipelineRun, CIPipelineStatus

        base_time = datetime.now(timezone.utc) - timedelta(hours=success + failure)
        for i in range(success):
            run = CIPipelineRun(
                repository_link_id=repo_link_id,
                external_run_id=10000 + i,
                workflow_name="CI",
                status=CIPipelineStatus.SUCCESS,
                head_sha=f"abc{i:04d}",
                branch="main",
                created_at=base_time + timedelta(hours=i),
            )
            db.add(run)
        for i in range(failure):
            run = CIPipelineRun(
                repository_link_id=repo_link_id,
                external_run_id=20000 + i,
                workflow_name="CI",
                status=CIPipelineStatus.FAILURE,
                head_sha=f"fail{i:04d}",
                branch="main",
                created_at=base_time + timedelta(hours=success + i),
            )
            db.add(run)
        await db.flush()

    @pytest.mark.asyncio
    async def test_ci_readiness_pass(self, db: AsyncSession):
        from app.services.merge_readiness_service import evaluate_ci_readiness

        project = await _seed_project(db)
        _, repo = await _seed_github_stack(db, project.id)
        await self._seed_ci_runs(db, repo.id, success=8, failure=2)

        result = await evaluate_ci_readiness(db, repo.id, threshold=70.0)
        assert result["status"] == "pass"
        assert result["pass_rate"] >= 70.0
        assert result["total_runs"] == 10
        assert result["success_count"] == 8

    @pytest.mark.asyncio
    async def test_ci_readiness_fail(self, db: AsyncSession):
        from app.services.merge_readiness_service import evaluate_ci_readiness

        project = await _seed_project(db)
        _, repo = await _seed_github_stack(db, project.id)
        await self._seed_ci_runs(db, repo.id, success=2, failure=8)

        result = await evaluate_ci_readiness(db, repo.id, threshold=70.0)
        assert result["status"] == "fail"
        assert result["pass_rate"] < 70.0

    @pytest.mark.asyncio
    async def test_ci_readiness_no_data(self, db: AsyncSession):
        from app.services.merge_readiness_service import evaluate_ci_readiness

        project = await _seed_project(db)
        _, repo = await _seed_github_stack(db, project.id)

        result = await evaluate_ci_readiness(db, repo.id)
        assert result["status"] == "no_data"
        assert result["total_runs"] == 0

    @pytest.mark.asyncio
    async def test_ci_readiness_in_merge_readiness(self, db: AsyncSession):
        """Verify that CI pass-rate gate integrates into merge readiness."""
        from app.services.merge_readiness_service import evaluate_merge_readiness
        from app.models.github_integration import PullRequestLink, PRStatus

        project = await _seed_project(db)
        _, repo = await _seed_github_stack(db, project.id)
        # Seed mostly-failing CI
        await self._seed_ci_runs(db, repo.id, success=1, failure=9)

        pr = PullRequestLink(
            repository_link_id=repo.id,
            pr_number=1,
            pr_title="Test PR",
            pr_url="https://github.com/test-org/depth-repo/pull/1",
            head_branch="feature",
            base_branch="main",
            status=PRStatus.OPEN,
        )
        db.add(pr)
        await db.flush()
        await db.refresh(pr)

        result = await evaluate_merge_readiness(db, pr.id)
        # Should have ci_pass_rate blocker
        blocker_cats = [b.category for b in result.blockers]
        assert "ci_pass_rate" in blocker_cats
        assert not result.ready

    @pytest.mark.asyncio
    async def test_ci_readiness_route(self, client: AsyncClient, db: AsyncSession):
        project = await _seed_project(db)
        _, repo = await _seed_github_stack(db, project.id)
        await db.commit()

        resp = await client.get(f"/github/repos/{repo.id}/ci/readiness")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
        assert "pass_rate" in data
        assert "threshold" in data

    @pytest.mark.asyncio
    async def test_ci_readiness_route_not_found(self, client: AsyncClient):
        fake_id = str(uuid.uuid4())
        resp = await client.get(f"/github/repos/{fake_id}/ci/readiness")
        assert resp.status_code == 404


# =====================================================================
# FM-148: Escalation → Notification Delivery
# =====================================================================


class TestEscalationNotification:
    @pytest.mark.asyncio
    async def test_escalation_creates_notifications(self, db: AsyncSession):
        from app.services.approval_enhanced_service import escalate_expired_approvals
        from app.models.approval_request import ApprovalRequest, ApprovalStatus
        from app.models.notification import Notification

        project = await _seed_project(db)

        # Create an expired approval
        approval = ApprovalRequest(
            title="Expired Review",
            description="Needs urgent attention",
            project_id=project.id,
            status=ApprovalStatus.PENDING,
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
        )
        db.add(approval)
        await db.flush()
        await db.refresh(approval)

        report = await escalate_expired_approvals(db)
        assert len(report) >= 1

        entry = report[0]
        assert entry["approval_id"] == str(approval.id)
        assert entry["target_count"] >= 1
        assert len(entry["notifications_created"]) >= 1

        # Verify notifications were actually created in the DB
        from sqlalchemy import select as sa_select

        notifs = (
            (
                await db.execute(
                    sa_select(Notification).where(
                        Notification.resource_type == "approval_request",
                        Notification.resource_id == approval.id,
                    )
                )
            )
            .scalars()
            .all()
        )
        assert len(notifs) >= 1
        assert notifs[0].notification_type.value == "escalation"
        assert notifs[0].priority.value == "high"

    @pytest.mark.asyncio
    async def test_escalation_no_expired(self, db: AsyncSession):
        from app.services.approval_enhanced_service import escalate_expired_approvals

        report = await escalate_expired_approvals(db)
        assert report == []

    @pytest.mark.asyncio
    async def test_escalation_with_delegate_target(self, db: AsyncSession):
        from app.services.approval_enhanced_service import (
            escalate_expired_approvals,
            create_delegation,
        )
        from app.models.approval_request import ApprovalRequest, ApprovalStatus

        project = await _seed_project(db)
        delegate_id = uuid.uuid4()

        # Seed a user for the delegate
        from app.models.user import User

        delegate_user = User(
            id=delegate_id,
            email=f"delegate-{delegate_id.hex[:8]}@test.com",
            display_name="Delegate User",
        )
        db.add(delegate_user)
        await db.flush()

        # Create delegation
        await create_delegation(
            db,
            delegator_id=STUB_USER_ID,
            delegate_id=delegate_id,
            project_id=project.id,
        )

        # Create expired approval
        approval = ApprovalRequest(
            title="Delegated Expired",
            description="delegation test",
            project_id=project.id,
            status=ApprovalStatus.PENDING,
            expires_at=datetime.now(timezone.utc) - timedelta(hours=2),
        )
        db.add(approval)
        await db.flush()

        report = await escalate_expired_approvals(db)
        assert len(report) >= 1
        targets = report[0]["escalation_targets"]
        delegate_targets = [t for t in targets if t["role"] == "delegate"]
        assert len(delegate_targets) >= 1
        assert delegate_targets[0]["user_id"] == str(delegate_id)


# =====================================================================
# FM-176: Notification Retention
# =====================================================================


class TestNotificationRetention:
    @pytest.mark.asyncio
    async def test_notification_entity_type_supported(self):
        from app.services.retention_policy_service import SUPPORTED_ENTITY_TYPES

        assert "notification" in SUPPORTED_ENTITY_TYPES

    @pytest.mark.asyncio
    async def test_create_notification_retention_policy(self, db: AsyncSession):
        from app.services.retention_policy_service import create_retention_policy

        ws = await _seed_workspace(db)
        policy = await create_retention_policy(
            db,
            workspace_id=ws.id,
            entity_type="notification",
            retention_days=30,
            created_by=STUB_USER_ID,
        )
        assert policy.entity_type == "notification"
        assert policy.retention_days == 30

    @pytest.mark.asyncio
    async def test_notification_retention_dry_run(self, db: AsyncSession):
        from app.services.retention_policy_service import (
            create_retention_policy,
            evaluate_retention,
        )
        from app.models.notification import (
            Notification,
            NotificationType,
            NotificationPriority,
        )

        ws = await _seed_workspace(db)
        await create_retention_policy(
            db,
            workspace_id=ws.id,
            entity_type="notification",
            retention_days=7,
            created_by=STUB_USER_ID,
        )

        # Create old and new notifications for the workspace member (STUB_USER_ID)
        old_notif = Notification(
            user_id=STUB_USER_ID,
            notification_type=NotificationType.ESCALATION,
            priority=NotificationPriority.NORMAL,
            title="Old notification",
            body="Should be retained",
            created_at=datetime.now(timezone.utc) - timedelta(days=30),
        )
        new_notif = Notification(
            user_id=STUB_USER_ID,
            notification_type=NotificationType.ESCALATION,
            priority=NotificationPriority.NORMAL,
            title="Recent notification",
            body="Should NOT be retained",
        )
        db.add_all([old_notif, new_notif])
        await db.flush()

        result = await evaluate_retention(db, ws.id, dry_run=True)
        assert result["total_affected"] >= 1
        notif_result = [
            r for r in result["results"] if r["entity_type"] == "notification"
        ]
        assert len(notif_result) == 1
        assert notif_result[0]["affected_count"] >= 1
        assert notif_result[0]["deleted_count"] == 0  # dry run

    @pytest.mark.asyncio
    async def test_notification_retention_execute(self, db: AsyncSession):
        from app.services.retention_policy_service import (
            create_retention_policy,
            evaluate_retention,
        )
        from app.models.enterprise_governance import RetentionAction
        from app.models.notification import (
            Notification,
            NotificationType,
            NotificationPriority,
        )
        from sqlalchemy import select as sa_select, func as sa_func

        ws = await _seed_workspace(db)
        await create_retention_policy(
            db,
            workspace_id=ws.id,
            entity_type="notification",
            retention_days=7,
            action=RetentionAction.DELETE,
            created_by=STUB_USER_ID,
        )

        # Seed two old notifications
        for i in range(2):
            n = Notification(
                user_id=STUB_USER_ID,
                notification_type=NotificationType.ESCALATION,
                priority=NotificationPriority.LOW,
                title=f"Old notif {i}",
                body="delete me",
                created_at=datetime.now(timezone.utc) - timedelta(days=60),
            )
            db.add(n)
        await db.flush()

        result = await evaluate_retention(db, ws.id, dry_run=False)
        notif_result = [
            r for r in result["results"] if r["entity_type"] == "notification"
        ]
        assert len(notif_result) == 1
        assert notif_result[0]["deleted_count"] >= 2

        # Verify they're gone
        remaining = (
            await db.execute(
                sa_select(sa_func.count())
                .select_from(Notification)
                .where(Notification.user_id == STUB_USER_ID)
            )
        ).scalar()
        assert remaining == 0

    @pytest.mark.asyncio
    async def test_notification_retention_unsupported_entity_rejected(
        self, db: AsyncSession
    ):
        from app.services.retention_policy_service import create_retention_policy

        ws = await _seed_workspace(db)
        with pytest.raises(ValueError, match="Unsupported entity type"):
            await create_retention_policy(
                db,
                workspace_id=ws.id,
                entity_type="bogus",
                retention_days=30,
                created_by=STUB_USER_ID,
            )
