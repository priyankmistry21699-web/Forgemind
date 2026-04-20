"""FM-141→180 V4 Implementation Pass Tests — Wave 10/11/12/13 improvements.

Tests newly wired routes and features:
  - FM-147: Task assignment HTTP routes
  - FM-148: Approval delegation HTTP routes
  - FM-150: Project overview HTTP route
  - FM-153: Webhook signature verification (runtime enforcement)
  - FM-154/157: Outbound GitHub client (unit tests)
  - FM-161/165: Search faceting + date-range filtering
  - FM-176: Retention enforcement execution
"""

import hashlib
import hmac
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import STUB_USER_ID


# ── Helpers ──────────────────────────────────────────────────────


async def _seed_project(db: AsyncSession):
    from app.models.project import Project
    from app.models.membership import ProjectMember, ProjectRole

    project = Project(
        name="V4 Pass Test Project",
        description="For implementation pass tests",
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
        title="Assignable Task",
        task_type="architecture",
        status=TaskStatus.READY,
        order_index=0,
        run_id=run_id,
    )
    db.add(task)
    await db.flush()
    await db.refresh(task)
    return task


async def _seed_approval(db: AsyncSession, project_id: uuid.UUID):
    from app.models.approval_request import ApprovalRequest, ApprovalStatus

    approval = ApprovalRequest(
        title="Test Approval",
        description="Needs review",
        project_id=project_id,
        status=ApprovalStatus.PENDING,
    )
    db.add(approval)
    await db.flush()
    await db.refresh(approval)
    return approval


async def _seed_github_stack(db: AsyncSession, project_id: uuid.UUID):
    """Seed installation -> repo link -> PR link for outbound tests."""
    from app.models.github_integration import (
        GitHubInstallation,
        RepositoryLink,
        PullRequestLink,
        PRStatus,
    )

    inst = GitHubInstallation(
        installation_id=12345,
        account_login="testorg",
        account_type="Organization",
        connected_by=STUB_USER_ID,
    )
    db.add(inst)
    await db.flush()
    await db.refresh(inst)

    repo = RepositoryLink(
        installation_id=inst.id,
        project_id=project_id,
        github_repo_id=99999,
        full_name="testorg/testrepo",
        default_branch="main",
    )
    db.add(repo)
    await db.flush()
    await db.refresh(repo)

    pr = PullRequestLink(
        repository_link_id=repo.id,
        pr_number=42,
        pr_title="Test PR",
        pr_url="https://github.com/testorg/testrepo/pull/42",
        head_branch="feature",
        base_branch="main",
        status=PRStatus.OPEN,
    )
    db.add(pr)
    await db.flush()
    await db.refresh(pr)

    return inst, repo, pr


# =====================================================================
# FM-147: Task Assignment HTTP Routes
# =====================================================================


class TestTaskAssignmentRoutes:
    """Test FM-147 task assignment routes (newly wired)."""

    @pytest.mark.asyncio
    async def test_assign_task(self, client: AsyncClient, db_session: AsyncSession):
        project = await _seed_project(db_session)
        run = await _seed_run(db_session, project.id)
        task = await _seed_task(db_session, run.id)

        resp = await client.post(
            f"/tasks/{task.id}/assign",
            json={"assignee_id": str(STUB_USER_ID)},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["assignee_id"] == str(STUB_USER_ID)
        assert data["assigned_at"] is not None

    @pytest.mark.asyncio
    async def test_unassign_task(self, client: AsyncClient, db_session: AsyncSession):
        project = await _seed_project(db_session)
        run = await _seed_run(db_session, project.id)
        task = await _seed_task(db_session, run.id)

        # Assign first
        await client.post(
            f"/tasks/{task.id}/assign",
            json={"assignee_id": str(STUB_USER_ID)},
        )

        # Unassign
        resp = await client.delete(f"/tasks/{task.id}/assign")
        assert resp.status_code == 200
        data = resp.json()
        assert data["assignee_id"] is None
        assert data["assigned_at"] is None

    @pytest.mark.asyncio
    async def test_assign_nonexistent_task(self, client: AsyncClient):
        fake_id = uuid.uuid4()
        resp = await client.post(
            f"/tasks/{fake_id}/assign",
            json={"assignee_id": str(STUB_USER_ID)},
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_my_assigned_tasks(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        project = await _seed_project(db_session)
        run = await _seed_run(db_session, project.id)
        task = await _seed_task(db_session, run.id)

        # Assign task to current user
        await client.post(
            f"/tasks/{task.id}/assign",
            json={"assignee_id": str(STUB_USER_ID)},
        )

        resp = await client.get("/users/me/assigned-tasks")
        assert resp.status_code == 200
        items = resp.json()
        assert len(items) >= 1
        assert any(t["id"] == str(task.id) for t in items)

    @pytest.mark.asyncio
    async def test_project_workload(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        project = await _seed_project(db_session)
        run = await _seed_run(db_session, project.id)
        task = await _seed_task(db_session, run.id)

        # Assign task
        await client.post(
            f"/tasks/{task.id}/assign",
            json={"assignee_id": str(STUB_USER_ID)},
        )

        resp = await client.get(f"/projects/{project.id}/workload")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["user_id"] == str(STUB_USER_ID)


# =====================================================================
# FM-148: Approval Delegation HTTP Routes
# =====================================================================


class TestApprovalDelegationRoutes:
    """Test FM-148 approval delegation routes (newly wired)."""

    @pytest.mark.asyncio
    async def test_create_delegation(self, client: AsyncClient):
        delegate_id = uuid.uuid4()
        resp = await client.post(
            "/approval-delegations",
            json={"delegate_id": str(delegate_id)},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["delegator_id"] == str(STUB_USER_ID)
        assert data["delegate_id"] == str(delegate_id)
        assert data["is_active"] is True

    @pytest.mark.asyncio
    async def test_create_delegation_with_project_scope(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        project = await _seed_project(db_session)
        delegate_id = uuid.uuid4()

        resp = await client.post(
            "/approval-delegations",
            json={
                "delegate_id": str(delegate_id),
                "project_id": str(project.id),
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["project_id"] == str(project.id)

    @pytest.mark.asyncio
    async def test_list_delegations(self, client: AsyncClient):
        delegate_id = uuid.uuid4()
        await client.post(
            "/approval-delegations",
            json={"delegate_id": str(delegate_id)},
        )

        resp = await client.get("/approval-delegations")
        assert resp.status_code == 200
        items = resp.json()
        assert isinstance(items, list)
        assert len(items) >= 1

    @pytest.mark.asyncio
    async def test_pending_approvals(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        project = await _seed_project(db_session)
        await _seed_approval(db_session, project.id)

        resp = await client.get("/approval-delegations/pending")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["status"] == "pending"

    @pytest.mark.asyncio
    async def test_pending_approvals_scoped_to_user(self, db_session: AsyncSession):
        """Pending approvals must only return approvals for projects the user leads."""
        from app.services.approval_enhanced_service import (
            get_pending_approvals_for_user,
        )
        from app.models.project import Project
        from app.models.approval_request import ApprovalRequest, ApprovalStatus

        # Create a project the user has NO membership in
        other_project = Project(
            name="Other Team Project",
            description="User is not a member",
            owner_id=uuid.uuid4(),
        )
        db_session.add(other_project)
        await db_session.flush()
        await db_session.refresh(other_project)

        # Create a pending approval on that other project
        approval = ApprovalRequest(
            title="Should be invisible",
            project_id=other_project.id,
            status=ApprovalStatus.PENDING,
        )
        db_session.add(approval)
        await db_session.flush()

        # STUB_USER_ID should NOT see this approval
        results = await get_pending_approvals_for_user(db_session, STUB_USER_ID)
        invisible_ids = {str(a.id) for a in results}
        assert str(approval.id) not in invisible_ids

    @pytest.mark.asyncio
    async def test_batch_decide(self, client: AsyncClient, db_session: AsyncSession):
        project = await _seed_project(db_session)
        a1 = await _seed_approval(db_session, project.id)
        a2 = await _seed_approval(db_session, project.id)

        resp = await client.post(
            "/approval-delegations/batch-decide",
            json={
                "approval_ids": [str(a1.id), str(a2.id)],
                "status": "approved",
                "comment": "LGTM",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["decided"] == 2
        assert data["status"] == "approved"

    @pytest.mark.asyncio
    async def test_batch_decide_invalid_status(self, client: AsyncClient):
        resp = await client.post(
            "/approval-delegations/batch-decide",
            json={
                "approval_ids": [str(uuid.uuid4())],
                "status": "invalid",
            },
        )
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_expired_approvals(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        project = await _seed_project(db_session)
        from app.models.approval_request import ApprovalRequest, ApprovalStatus

        expired = ApprovalRequest(
            title="Expired Approval",
            project_id=project.id,
            status=ApprovalStatus.PENDING,
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
        )
        db_session.add(expired)
        await db_session.flush()

        resp = await client.get("/approval-delegations/expired")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] >= 1

    @pytest.mark.asyncio
    async def test_escalate_expired_no_expired(self, client: AsyncClient):
        """Escalate returns empty when no approvals are expired."""
        resp = await client.post("/approval-delegations/escalate")
        assert resp.status_code == 200
        data = resp.json()
        assert data["escalated_count"] == 0
        assert data["escalations"] == []

    @pytest.mark.asyncio
    async def test_escalate_expired_with_delegation(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Escalation finds delegates as escalation targets."""
        project = await _seed_project(db_session)
        from app.models.approval_request import ApprovalRequest, ApprovalStatus
        from app.models.approval_delegation import ApprovalDelegation

        delegate_id = uuid.UUID("00000000-0000-0000-0000-000000000099")
        from app.models.user import User

        delegate_user = User(
            id=delegate_id,
            email="delegate@test.dev",
            display_name="Delegate User",
        )
        db_session.add(delegate_user)

        # Create expired approval
        expired = ApprovalRequest(
            title="Expired With Delegate",
            project_id=project.id,
            status=ApprovalStatus.PENDING,
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
        )
        db_session.add(expired)

        # Create delegation for this project
        delegation = ApprovalDelegation(
            delegator_id=STUB_USER_ID,
            delegate_id=delegate_id,
            project_id=project.id,
        )
        db_session.add(delegation)
        await db_session.flush()

        resp = await client.post("/approval-delegations/escalate")
        assert resp.status_code == 200
        data = resp.json()
        assert data["escalated_count"] >= 1

        # Find our escalation
        matched = [
            e for e in data["escalations"] if e["title"] == "Expired With Delegate"
        ]
        assert len(matched) == 1
        esc = matched[0]
        assert esc["target_count"] >= 1
        target_user_ids = [t["user_id"] for t in esc["escalation_targets"]]
        assert str(delegate_id) in target_user_ids

    @pytest.mark.asyncio
    async def test_escalate_expired_service_direct(self, db_session: AsyncSession):
        """Direct service-level test of escalation logic."""
        project = await _seed_project(db_session)
        from app.models.approval_request import ApprovalRequest, ApprovalStatus
        from app.services import approval_enhanced_service

        expired = ApprovalRequest(
            title="Service-Level Escalation Test",
            project_id=project.id,
            status=ApprovalStatus.PENDING,
            expires_at=datetime.now(timezone.utc) - timedelta(hours=2),
        )
        db_session.add(expired)
        await db_session.flush()

        report = await approval_enhanced_service.escalate_expired_approvals(db_session)
        assert len(report) >= 1
        matched = [r for r in report if r["title"] == "Service-Level Escalation Test"]
        assert len(matched) == 1
        # Stub user is a project lead, should be an escalation target
        assert matched[0]["target_count"] >= 1


# =====================================================================
# FM-150: Project Overview HTTP Route
# =====================================================================


class TestProjectOverviewRoute:
    """Test FM-150 project overview route (newly wired)."""

    @pytest.mark.asyncio
    async def test_project_overview(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        project = await _seed_project(db_session)
        await _seed_run(db_session, project.id)

        resp = await client.get(f"/projects/{project.id}/overview")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_runs" in data
        assert "open_tasks" in data
        assert "health_grade" in data
        assert "team_members" in data
        assert "team_size" in data
        assert data["total_runs"] >= 1
        assert data["team_size"] >= 1

    @pytest.mark.asyncio
    async def test_overview_health_grade_a(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        project = await _seed_project(db_session)
        from app.models.run import Run

        # All runs completed — success rate 100% → grade A
        for i in range(3):
            r = Run(
                project_id=project.id,
                run_number=i + 1,
                trigger="test",
                status="completed",
            )
            db_session.add(r)
        await db_session.flush()

        resp = await client.get(f"/projects/{project.id}/overview")
        data = resp.json()
        assert data["health_grade"] == "A"
        assert data["success_rate"] == 100.0


# =====================================================================
# FM-153: Webhook Signature Verification (Runtime Enforcement)
# =====================================================================


class TestWebhookSignatureVerification:
    """Test that verify_github_signature is actually enforced in the webhook endpoint."""

    @pytest.mark.asyncio
    async def test_signature_verification_function(self):
        """Test the verify_github_signature function directly."""
        from app.services.webhook_service import verify_github_signature

        secret = "test-secret-123"
        payload = b'{"action": "opened"}'
        mac = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        sig = f"sha256={mac}"

        assert verify_github_signature(payload, sig, secret) is True
        assert verify_github_signature(payload, "sha256=invalid", secret) is False
        assert verify_github_signature(payload, "md5=nope", secret) is False
        assert verify_github_signature(payload, "", secret) is False

    @pytest.mark.asyncio
    async def test_webhook_rejects_bad_signature_when_secret_configured(
        self, client: AsyncClient
    ):
        """When GITHUB_WEBHOOK_SECRET is set, invalid signatures must be rejected."""
        with patch("app.core.config.settings") as mock_settings:
            mock_settings.github_webhook_secret = "my-secret"

            resp = await client.post(
                "/github/webhooks",
                content=b'{"action": "opened"}',
                headers={
                    "X-GitHub-Event": "ping",
                    "X-Hub-Signature-256": "sha256=wrong",
                    "Content-Type": "application/json",
                },
            )
            assert resp.status_code == 401
            assert "signature" in resp.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_webhook_accepts_valid_signature(self, client: AsyncClient):
        """When GITHUB_WEBHOOK_SECRET is set, valid signatures must pass."""
        secret = "my-secret"
        payload = b'{"action": "opened"}'
        mac = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        sig = f"sha256={mac}"

        with patch("app.core.config.settings") as mock_settings:
            mock_settings.github_webhook_secret = secret

            resp = await client.post(
                "/github/webhooks",
                content=payload,
                headers={
                    "X-GitHub-Event": "ping",
                    "X-Hub-Signature-256": sig,
                    "Content-Type": "application/json",
                },
            )
            assert resp.status_code == 201

    @pytest.mark.asyncio
    async def test_webhook_skips_verification_when_no_secret(self, client: AsyncClient):
        """When GITHUB_WEBHOOK_SECRET is empty, webhooks pass without signature."""
        with patch("app.core.config.settings") as mock_settings:
            mock_settings.github_webhook_secret = ""

            resp = await client.post(
                "/github/webhooks",
                content=b'{"action": "opened"}',
                headers={
                    "X-GitHub-Event": "ping",
                    "Content-Type": "application/json",
                },
            )
            assert resp.status_code == 201


# =====================================================================
# FM-154/157: Outbound GitHub Client (Unit Tests)
# =====================================================================


class TestGitHubClient:
    """Unit tests for the outbound GitHub API client."""

    @pytest.mark.asyncio
    async def test_post_pr_comment(self):
        """Test PR comment posting with mocked HTTP."""
        from app.services.github_client import post_pr_comment, GitHubComment
        import httpx

        mock_response = httpx.Response(
            status_code=201,
            json={
                "id": 123,
                "html_url": "https://github.com/o/r/pull/1#comment-123",
                "body": "Test comment",
            },
            request=httpx.Request("POST", "https://api.github.com/test"),
        )

        with patch("app.services.github_client.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            result = await post_pr_comment("owner", "repo", 1, "Test comment", "tok")
            assert isinstance(result, GitHubComment)
            assert result.id == 123
            assert result.body == "Test comment"

        with patch("app.services.github_client.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            result = await post_pr_comment("owner", "repo", 1, "Test comment", "tok")
            assert isinstance(result, GitHubComment)
            assert result.id == 123
            assert result.body == "Test comment"

    @pytest.mark.asyncio
    async def test_post_pr_comment_sync_json(self):
        """Test with sync json return (non-coroutine)."""
        from app.services.github_client import post_pr_comment
        import httpx

        mock_response = httpx.Response(
            status_code=201,
            json={"id": 123, "html_url": "https://example.com", "body": "ok"},
            request=httpx.Request("POST", "https://api.github.com/test"),
        )

        with patch("app.services.github_client.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            result = await post_pr_comment("owner", "repo", 1, "ok", "tok")
            assert result.id == 123

    @pytest.mark.asyncio
    async def test_post_issue_comment(self):
        """Test issue comment posting with mocked HTTP."""
        from app.services.github_client import post_issue_comment, GitHubComment
        import httpx

        mock_response = httpx.Response(
            status_code=201,
            json={
                "id": 456,
                "html_url": "https://github.com/o/r/issues/5#comment-456",
                "body": "Issue note",
            },
            request=httpx.Request("POST", "https://api.github.com/test"),
        )

        with patch("app.services.github_client.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            result = await post_issue_comment("owner", "repo", 5, "Issue note", "tok")
            assert isinstance(result, GitHubComment)
            assert result.id == 456

    @pytest.mark.asyncio
    async def test_create_commit_status(self):
        """Test commit status creation with mocked HTTP."""
        from app.services.github_client import create_commit_status, CommitStatus
        import httpx

        mock_response = httpx.Response(
            status_code=201,
            json={
                "id": 789,
                "state": "success",
                "target_url": None,
                "description": "All checks passed",
                "context": "forgemind/ci",
            },
            request=httpx.Request("POST", "https://api.github.com/test"),
        )

        with patch("app.services.github_client.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            result = await create_commit_status(
                "owner",
                "repo",
                "abc123",
                state="success",
                description="All checks passed",
                token="tok",
            )
            assert isinstance(result, CommitStatus)
            assert result.state == "success"

    @pytest.mark.asyncio
    async def test_github_client_error_handling(self):
        """Test that API errors raise GitHubClientError."""
        from app.services.github_client import _github_request, GitHubClientError
        import httpx

        mock_response = httpx.Response(
            status_code=403,
            text="Rate limited",
            request=httpx.Request("GET", "https://api.github.com/test"),
        )

        with patch("app.services.github_client.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            with pytest.raises(GitHubClientError) as exc_info:
                await _github_request("GET", "/repos/o/r", token="tok")
            assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_invalid_commit_status_state(self):
        """Test that invalid state raises ValueError."""
        from app.services.github_client import create_commit_status

        with pytest.raises(ValueError, match="Invalid commit status state"):
            await create_commit_status(
                "owner",
                "repo",
                "abc123",
                state="invalid",
                token="tok",
            )

    @pytest.mark.asyncio
    async def test_pr_comment_route_no_credentials(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Test that outbound routes return 503 when no credentials configured."""
        project = await _seed_project(db_session)
        _, _, pr = await _seed_github_stack(db_session, project.id)

        # The route now uses settings.github_api_token (not webhook_secret)
        from app.core.config import settings as _s

        old_val = getattr(_s, "github_api_token", "")
        object.__setattr__(_s, "github_api_token", "")
        try:
            resp = await client.post(
                f"/github/prs/{pr.id}/comments",
                json={"body": "Hello"},
            )
            assert resp.status_code == 503
            assert "credentials" in resp.json()["detail"].lower()
        finally:
            object.__setattr__(_s, "github_api_token", old_val)

    @pytest.mark.asyncio
    async def test_commit_status_route_not_found(self, client: AsyncClient):
        """Test commit status route with nonexistent repo."""
        fake_id = uuid.uuid4()
        resp = await client.post(
            f"/github/repos/{fake_id}/statuses/abc123",
            json={"state": "success"},
        )
        assert resp.status_code == 404


# =====================================================================
# FM-161/165: Search Faceting & Date-Range Filtering
# =====================================================================


class TestSearchFaceting:
    """Test search faceting and date-range filtering improvements."""

    @pytest.mark.asyncio
    async def test_search_returns_facets(self, db_session: AsyncSession):
        """Test that search returns facet aggregations when requested."""
        from app.services.search_service import search, _upsert_index
        from app.models.search_knowledge import SearchEntityType

        project = await _seed_project(db_session)

        # Index diverse entities
        await _upsert_index(
            db_session,
            entity_type=SearchEntityType.TASK,
            entity_id=uuid.uuid4(),
            project_id=project.id,
            title="Deploy API server",
            body="Deploy the API server to production",
            entity_status="ready",
        )
        await _upsert_index(
            db_session,
            entity_type=SearchEntityType.ARTIFACT,
            entity_id=uuid.uuid4(),
            project_id=project.id,
            title="API specification",
            body="OpenAPI specification for the API",
            entity_status="draft",
        )
        await _upsert_index(
            db_session,
            entity_type=SearchEntityType.TASK,
            entity_id=uuid.uuid4(),
            project_id=project.id,
            title="Test API endpoints",
            body="Write tests for all API endpoints",
            entity_status="ready",
        )

        items, total, facets = await search(
            db_session,
            query="API",
            project_id=project.id,
            include_facets=True,
        )
        assert total >= 3
        assert facets is not None
        assert "entity_type" in facets
        assert "entity_status" in facets
        # Should have task and artifact in facets
        assert "task" in facets["entity_type"]

    @pytest.mark.asyncio
    async def test_search_no_facets_by_default(self, db_session: AsyncSession):
        """Verify facets are None when not requested."""
        from app.services.search_service import search, _upsert_index
        from app.models.search_knowledge import SearchEntityType

        project = await _seed_project(db_session)
        await _upsert_index(
            db_session,
            entity_type=SearchEntityType.TASK,
            entity_id=uuid.uuid4(),
            project_id=project.id,
            title="Build widget",
            body="Build the widget component",
        )

        items, total, facets = await search(
            db_session, query="widget", project_id=project.id
        )
        assert facets is None

    @pytest.mark.asyncio
    async def test_search_date_range_filter(self, db_session: AsyncSession):
        """Test created_after / created_before date-range filtering."""
        from app.services.search_service import search, _upsert_index
        from app.models.search_knowledge import SearchEntityType

        project = await _seed_project(db_session)
        await _upsert_index(
            db_session,
            entity_type=SearchEntityType.TASK,
            entity_id=uuid.uuid4(),
            project_id=project.id,
            title="Recent task deploy",
            body="Deploy service recently",
        )

        now = datetime.now(timezone.utc)
        # Search with created_after set to yesterday — should find the item
        items, total, _ = await search(
            db_session,
            query="deploy",
            project_id=project.id,
            created_after=now - timedelta(days=1),
        )
        assert total >= 1

        # Search with created_after set to tomorrow — should find nothing
        items, total, _ = await search(
            db_session,
            query="deploy",
            project_id=project.id,
            created_after=now + timedelta(days=1),
        )
        assert total == 0

    @pytest.mark.asyncio
    async def test_search_facets_http_route(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Test the /search endpoint returns facets when facets=true."""
        from app.services.search_service import _upsert_index
        from app.models.search_knowledge import SearchEntityType

        project = await _seed_project(db_session)
        await _upsert_index(
            db_session,
            entity_type=SearchEntityType.TASK,
            entity_id=uuid.uuid4(),
            project_id=project.id,
            title="Search facet test item",
            body="Faceted search item body",
        )

        resp = await client.get(
            "/search",
            params={
                "q": "facet",
                "project_id": str(project.id),
                "facets": "true",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "facets" in data
        assert data["facets"] is not None

    @pytest.mark.asyncio
    async def test_search_date_range_http_route(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Test the /search endpoint accepts date-range query params."""
        from app.services.search_service import _upsert_index
        from app.models.search_knowledge import SearchEntityType

        project = await _seed_project(db_session)
        await _upsert_index(
            db_session,
            entity_type=SearchEntityType.TASK,
            entity_id=uuid.uuid4(),
            project_id=project.id,
            title="Date range test item",
            body="Testing date range filter",
        )

        resp = await client.get(
            "/search",
            params={
                "q": "date range",
                "project_id": str(project.id),
                "created_after": "2020-01-01",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1


# =====================================================================
# FM-176: Retention Enforcement Execution
# =====================================================================


class TestRetentionEnforcement:
    """Test retention policy enforcement (not just dry_run)."""

    @pytest.mark.asyncio
    async def test_retention_dry_run_no_deletes(self, db_session: AsyncSession):
        """Dry run should count but not delete anything."""
        from app.services.retention_policy_service import (
            create_retention_policy,
            evaluate_retention,
        )
        from app.models.enterprise_governance import RetentionAction
        from app.models.workspace import Workspace

        ws = Workspace(name="RetTest WS", slug="rettest-ws", owner_id=STUB_USER_ID)
        db_session.add(ws)
        await db_session.flush()
        await db_session.refresh(ws)

        await create_retention_policy(
            db_session,
            workspace_id=ws.id,
            entity_type="run",
            retention_days=0,  # All runs are "expired"
            action=RetentionAction.DELETE,
            created_by=STUB_USER_ID,
        )

        result = await evaluate_retention(db_session, ws.id, dry_run=True)
        assert result["dry_run"] is True
        assert result["total_deleted"] == 0

    @pytest.mark.asyncio
    async def test_retention_execute_deletes_audit_logs(self, db_session: AsyncSession):
        """Execute mode should actually delete expired audit logs."""
        from app.services.retention_policy_service import (
            create_retention_policy,
            evaluate_retention,
        )
        from app.models.enterprise_governance import RetentionAction, AuditLog
        from app.models.workspace import Workspace

        ws = Workspace(name="RetExec WS", slug="retexec-ws", owner_id=STUB_USER_ID)
        db_session.add(ws)
        await db_session.flush()
        await db_session.refresh(ws)

        # Create an old audit log with backdated created_at
        old_log = AuditLog(
            workspace_id=ws.id,
            actor_id=STUB_USER_ID,
            action="test.action",
            resource_type="test",
            resource_id=uuid.uuid4(),
            created_at=datetime(2020, 1, 1, tzinfo=timezone.utc),
        )
        db_session.add(old_log)
        await db_session.flush()

        await create_retention_policy(
            db_session,
            workspace_id=ws.id,
            entity_type="audit_log",
            retention_days=30,
            action=RetentionAction.DELETE,
            created_by=STUB_USER_ID,
        )

        # Dry run first
        dr = await evaluate_retention(db_session, ws.id, dry_run=True)
        assert dr["total_affected"] >= 1
        assert dr["total_deleted"] == 0

        # Execute
        result = await evaluate_retention(db_session, ws.id, dry_run=False)
        assert result["dry_run"] is False
        assert result["total_deleted"] >= 1

    @pytest.mark.asyncio
    async def test_retention_respects_legal_hold(self, db_session: AsyncSession):
        """Policies with legal_hold should never execute deletions."""
        from app.services.retention_policy_service import (
            create_retention_policy,
            evaluate_retention,
        )
        from app.models.enterprise_governance import RetentionAction
        from app.models.workspace import Workspace

        ws = Workspace(name="LegalHold WS", slug="legalhold-ws", owner_id=STUB_USER_ID)
        db_session.add(ws)
        await db_session.flush()
        await db_session.refresh(ws)

        await create_retention_policy(
            db_session,
            workspace_id=ws.id,
            entity_type="run",
            retention_days=0,
            action=RetentionAction.DELETE,
            legal_hold=True,
            created_by=STUB_USER_ID,
        )

        result = await evaluate_retention(db_session, ws.id, dry_run=False)
        # Legal hold policies are excluded from evaluation
        assert result["policies_evaluated"] == 0
        assert result["total_deleted"] == 0
