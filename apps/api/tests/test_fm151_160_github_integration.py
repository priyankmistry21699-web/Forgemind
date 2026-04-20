"""FM-151–160: Comprehensive tests for Wave 11 — GitHub & CI Integration.

Covers:
  FM-151: GitHub installations & repository linking
  FM-152: Webhook ingestion & event processing
  FM-153: Pull request auto-creation & tracking
  FM-154: CI pipeline status tracking
  FM-155: Issue sync
  FM-157: Code review routing / CODEOWNERS
  FM-158: Commit & diff intelligence
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import STUB_USER_ID


# ── Helpers ──────────────────────────────────────────────────────


async def _seed_project(db: AsyncSession):
    from app.models.project import Project
    from app.models.membership import ProjectMember, ProjectRole

    project = Project(
        name="GitHub Test Project",
        description="For FM-151–160 tests",
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


async def _seed_installation(db: AsyncSession):
    from app.models.github_integration import GitHubInstallation

    inst = GitHubInstallation(
        installation_id=12345,
        account_login="test-org",
        account_type="Organization",
        connected_by=STUB_USER_ID,
    )
    db.add(inst)
    await db.flush()
    await db.refresh(inst)
    return inst


async def _seed_repo_link(db: AsyncSession, installation_id, project_id):
    from app.models.github_integration import RepositoryLink

    link = RepositoryLink(
        installation_id=installation_id,
        project_id=project_id,
        github_repo_id=99999,
        full_name="test-org/test-repo",
        default_branch="main",
    )
    db.add(link)
    await db.flush()
    await db.refresh(link)
    return link


# =====================================================================
# FM-151: GitHub Installation & Repo Linking
# =====================================================================


class TestGitHubInstallation:
    @pytest.mark.asyncio
    async def test_create_installation(self, db_session: AsyncSession):
        from app.services.github_installation_service import create_installation

        inst = await create_installation(
            db_session,
            installation_id=11111,
            account_login="my-org",
            account_type="Organization",
            connected_by=STUB_USER_ID,
        )
        assert inst.installation_id == 11111
        assert inst.account_login == "my-org"
        assert inst.is_active is True

    @pytest.mark.asyncio
    async def test_link_repository(self, db_session: AsyncSession):
        project = await _seed_project(db_session)
        inst = await _seed_installation(db_session)

        from app.services.github_installation_service import link_repository

        link = await link_repository(
            db_session,
            installation_id=inst.id,
            project_id=project.id,
            github_repo_id=42,
            full_name="test-org/my-repo",
        )
        assert link.full_name == "test-org/my-repo"

    @pytest.mark.asyncio
    async def test_list_repos_for_project(self, db_session: AsyncSession):
        project = await _seed_project(db_session)
        inst = await _seed_installation(db_session)
        await _seed_repo_link(db_session, inst.id, project.id)

        from app.services.github_installation_service import list_repos_for_project

        repos = await list_repos_for_project(db_session, project.id)
        assert len(repos) == 1

    @pytest.mark.asyncio
    async def test_unlink_repository(self, db_session: AsyncSession):
        project = await _seed_project(db_session)
        inst = await _seed_installation(db_session)
        link = await _seed_repo_link(db_session, inst.id, project.id)

        from app.services.github_installation_service import (
            unlink_repository,
            list_repos_for_project,
        )

        await unlink_repository(db_session, link.id)
        repos = await list_repos_for_project(db_session, project.id)
        assert len(repos) == 0  # Deactivated

    @pytest.mark.asyncio
    async def test_installation_http(self, client: AsyncClient):
        resp = await client.post(
            "/github/installations",
            json={
                "installation_id": 77777,
                "account_login": "http-org",
                "account_type": "Organization",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["account_login"] == "http-org"

    @pytest.mark.asyncio
    async def test_list_installations_http(self, client: AsyncClient):
        resp = await client.get("/github/installations")
        assert resp.status_code == 200


# =====================================================================
# FM-152: Webhook Ingestion
# =====================================================================


class TestWebhookIngestion:
    @pytest.mark.asyncio
    async def test_ingest_event(self, db_session: AsyncSession):
        from app.services.webhook_service import ingest_event

        event = await ingest_event(
            db_session,
            event_type="push",
            delivery_id="abc-123",
            payload={"ref": "refs/heads/main", "repository": {"full_name": "x/y"}},
        )
        assert event.event_type == "push"
        assert event.processed is False

    @pytest.mark.asyncio
    async def test_process_pr_event(self, db_session: AsyncSession):
        project = await _seed_project(db_session)
        inst = await _seed_installation(db_session)
        await _seed_repo_link(db_session, inst.id, project.id)

        from app.services.webhook_service import ingest_event, process_pr_event

        event = await ingest_event(
            db_session,
            event_type="pull_request",
            delivery_id="pr-001",
            payload={
                "action": "opened",
                "repository": {"full_name": "test-org/test-repo"},
                "pull_request": {
                    "number": 42,
                    "title": "Add feature",
                    "html_url": "https://github.com/test-org/test-repo/pull/42",
                    "state": "open",
                    "merged": False,
                    "head": {"ref": "feature-branch"},
                    "base": {"ref": "main"},
                },
            },
        )
        pr = await process_pr_event(db_session, event)
        assert pr is not None
        assert pr.pr_number == 42
        assert pr.status.value == "open"

    @pytest.mark.asyncio
    async def test_process_issues_event(self, db_session: AsyncSession):
        project = await _seed_project(db_session)
        inst = await _seed_installation(db_session)
        await _seed_repo_link(db_session, inst.id, project.id)

        from app.services.webhook_service import ingest_event, process_issues_event

        event = await ingest_event(
            db_session,
            event_type="issues",
            delivery_id="iss-001",
            payload={
                "action": "opened",
                "repository": {"full_name": "test-org/test-repo"},
                "issue": {
                    "number": 10,
                    "title": "Bug report",
                    "html_url": "https://github.com/test-org/test-repo/issues/10",
                    "state": "open",
                    "labels": [{"name": "bug"}],
                },
            },
        )
        issue = await process_issues_event(db_session, event)
        assert issue is not None
        assert issue.issue_number == 10
        assert issue.labels == ["bug"]

    @pytest.mark.asyncio
    async def test_webhook_http(self, client: AsyncClient):
        resp = await client.post(
            "/github/webhooks",
            json={"ref": "refs/heads/main", "repository": {"full_name": "x/y"}},
            headers={
                "X-GitHub-Event": "push",
                "X-GitHub-Delivery": "http-del-001",
            },
        )
        assert resp.status_code == 201
        assert resp.json()["status"] == "accepted"


# =====================================================================
# FM-153: PR Service
# =====================================================================


class TestPRService:
    @pytest.mark.asyncio
    async def test_create_pr_link(self, db_session: AsyncSession):
        project = await _seed_project(db_session)
        inst = await _seed_installation(db_session)
        repo_link = await _seed_repo_link(db_session, inst.id, project.id)

        from app.services.pr_service import create_pr_link

        pr = await create_pr_link(
            db_session,
            repository_link_id=repo_link.id,
            pr_number=1,
            pr_title="My PR",
            pr_url="https://github.com/test/1",
            head_branch="feat",
            base_branch="main",
        )
        assert pr.pr_number == 1

    @pytest.mark.asyncio
    async def test_list_prs_for_repo(self, db_session: AsyncSession):
        project = await _seed_project(db_session)
        inst = await _seed_installation(db_session)
        repo_link = await _seed_repo_link(db_session, inst.id, project.id)

        from app.services.pr_service import create_pr_link, list_prs_for_repo

        await create_pr_link(
            db_session, repo_link.id, 1, "PR1", "url1", "feat1", "main"
        )
        await create_pr_link(
            db_session, repo_link.id, 2, "PR2", "url2", "feat2", "main"
        )
        prs = await list_prs_for_repo(db_session, repo_link.id)
        assert len(prs) == 2


# =====================================================================
# FM-154: CI Pipeline
# =====================================================================


class TestCIPipeline:
    @pytest.mark.asyncio
    async def test_list_and_latest(self, db_session: AsyncSession):
        project = await _seed_project(db_session)
        inst = await _seed_installation(db_session)
        repo_link = await _seed_repo_link(db_session, inst.id, project.id)

        from app.models.github_integration import CIPipelineRun, CIPipelineStatus
        from app.services.ci_pipeline_service import (
            list_pipelines_for_repo,
            get_latest_pipeline,
        )

        for i in range(3):
            db_session.add(
                CIPipelineRun(
                    repository_link_id=repo_link.id,
                    external_run_id=1000 + i,
                    workflow_name="CI",
                    head_sha=f"sha{i}",
                    branch="main",
                    status=CIPipelineStatus.SUCCESS,
                )
            )
        await db_session.flush()

        pipelines = await list_pipelines_for_repo(db_session, repo_link.id)
        assert len(pipelines) == 3

        latest = await get_latest_pipeline(db_session, repo_link.id, branch="main")
        assert latest is not None


# =====================================================================
# FM-155: Issue Sync
# =====================================================================


class TestIssueSync:
    @pytest.mark.asyncio
    async def test_list_issues_for_project(self, db_session: AsyncSession):
        project = await _seed_project(db_session)
        inst = await _seed_installation(db_session)
        repo_link = await _seed_repo_link(db_session, inst.id, project.id)

        from app.models.github_integration import IssueLink, IssueLinkStatus
        from app.services.issue_sync_service import list_issues_for_project

        db_session.add(
            IssueLink(
                repository_link_id=repo_link.id,
                project_id=project.id,
                issue_number=1,
                title="Bug",
                issue_url="https://github.com/x/1",
                status=IssueLinkStatus.OPEN,
            )
        )
        await db_session.flush()

        issues = await list_issues_for_project(db_session, project.id)
        assert len(issues) == 1


# =====================================================================
# FM-157: Code Review Routing
# =====================================================================


class TestCodeReviewRouting:
    @pytest.mark.asyncio
    async def test_ownership_matching(self, db_session: AsyncSession):
        project = await _seed_project(db_session)
        inst = await _seed_installation(db_session)
        repo_link = await _seed_repo_link(db_session, inst.id, project.id)

        from app.services.code_review_service import (
            upsert_ownership_rule,
            get_owners_for_files,
        )

        await upsert_ownership_rule(
            db_session,
            repo_link.id,
            "*.py",
            owner_team_name="backend-team",
        )
        await upsert_ownership_rule(
            db_session,
            repo_link.id,
            "frontend/*",
            owner_team_name="frontend-team",
        )

        matches = await get_owners_for_files(
            db_session, repo_link.id, ["main.py", "frontend/app.tsx", "README.md"]
        )
        patterns = {m["file"]: m["owner_team_name"] for m in matches}
        assert patterns.get("main.py") == "backend-team"
        assert patterns.get("frontend/app.tsx") == "frontend-team"

    @pytest.mark.asyncio
    async def test_upsert_updates_existing(self, db_session: AsyncSession):
        project = await _seed_project(db_session)
        inst = await _seed_installation(db_session)
        repo_link = await _seed_repo_link(db_session, inst.id, project.id)

        from app.services.code_review_service import upsert_ownership_rule

        rule1 = await upsert_ownership_rule(
            db_session, repo_link.id, "*.py", owner_team_name="team-a"
        )
        rule2 = await upsert_ownership_rule(
            db_session, repo_link.id, "*.py", owner_team_name="team-b"
        )
        assert rule1.id == rule2.id
        assert rule2.owner_team_name == "team-b"


# =====================================================================
# FM-158: Diff Intelligence
# =====================================================================


class TestDiffIntelligence:
    def test_analyze_diff_stats(self):
        from app.services.diff_intelligence_service import analyze_diff_stats

        diff = """diff --git a/main.py b/main.py
--- a/main.py
+++ b/main.py
@@ -1,3 +1,5 @@
 import os
+import sys
+import json
 def main():
-    pass
+    print("hello")
diff --git a/utils.py b/utils.py
--- a/utils.py
+++ b/utils.py
@@ -1 +1,2 @@
 # utils
+def helper(): pass
"""
        result = analyze_diff_stats(diff)
        assert result["files_changed"] == 2
        assert result["total_additions"] == 4
        assert result["total_deletions"] == 1
        assert result["impact_score"] > 0

    def test_extract_changed_files(self):
        from app.services.diff_intelligence_service import extract_changed_files

        diff = """diff --git a/foo.py b/foo.py
diff --git a/bar/baz.ts b/bar/baz.ts
"""
        files = extract_changed_files(diff)
        assert files == ["foo.py", "bar/baz.ts"]

    def test_empty_diff(self):
        from app.services.diff_intelligence_service import analyze_diff_stats

        result = analyze_diff_stats("")
        assert result["files_changed"] == 0
        assert result["impact_score"] == 0


# =====================================================================
# FM-156: Merge Readiness Service
# =====================================================================


class TestMergeReadiness:
    @pytest.mark.asyncio
    async def test_ready_when_all_checks_pass(self, db_session: AsyncSession):
        from app.models.github_integration import (
            PullRequestLink,
            PRStatus,
            CIPipelineRun,
            CIPipelineStatus,
        )
        from app.models.task import Task, TaskStatus
        from app.services.merge_readiness_service import evaluate_merge_readiness

        project = await _seed_project(db_session)
        inst = await _seed_installation(db_session)
        repo = await _seed_repo_link(db_session, inst.id, project.id)

        from app.models.run import Run

        run = Run(project_id=project.id, run_number=1, trigger="test")
        db_session.add(run)
        await db_session.flush()

        pr = PullRequestLink(
            repository_link_id=repo.id,
            run_id=run.id,
            pr_number=42,
            pr_title="feat: add feature",
            pr_url="https://github.com/test/repo/pull/42",
            head_branch="feature",
            base_branch="main",
            status=PRStatus.OPEN,
        )
        db_session.add(pr)
        await db_session.flush()

        # Passing CI
        ci = CIPipelineRun(
            repository_link_id=repo.id,
            external_run_id=1001,
            workflow_name="CI",
            head_sha="abc123",
            branch="feature",
            status=CIPipelineStatus.SUCCESS,
        )
        db_session.add(ci)

        # All tasks done
        task = Task(
            title="Done task",
            task_type="architecture",
            status=TaskStatus.COMPLETED,
            order_index=0,
            run_id=run.id,
        )
        db_session.add(task)
        await db_session.flush()

        result = await evaluate_merge_readiness(db_session, pr.id)
        assert result.ready is True
        assert len(result.blockers) == 0
        assert "ci_passing" in result.checks_passed
        assert "all_tasks_complete" in result.checks_passed

    @pytest.mark.asyncio
    async def test_blocked_by_failing_ci(self, db_session: AsyncSession):
        from app.models.github_integration import (
            PullRequestLink,
            PRStatus,
            CIPipelineRun,
            CIPipelineStatus,
        )
        from app.services.merge_readiness_service import evaluate_merge_readiness

        project = await _seed_project(db_session)
        inst = await _seed_installation(db_session)
        repo = await _seed_repo_link(db_session, inst.id, project.id)

        pr = PullRequestLink(
            repository_link_id=repo.id,
            pr_number=43,
            pr_title="feat: broken",
            pr_url="https://github.com/test/repo/pull/43",
            head_branch="broken",
            base_branch="main",
            status=PRStatus.OPEN,
        )
        db_session.add(pr)

        ci = CIPipelineRun(
            repository_link_id=repo.id,
            external_run_id=1002,
            workflow_name="CI",
            head_sha="def456",
            branch="broken",
            status=CIPipelineStatus.FAILURE,
        )
        db_session.add(ci)
        await db_session.flush()

        result = await evaluate_merge_readiness(db_session, pr.id)
        assert result.ready is False
        assert any(b.category == "ci" for b in result.blockers)

    @pytest.mark.asyncio
    async def test_blocked_by_incomplete_tasks(self, db_session: AsyncSession):
        from app.models.github_integration import (
            PullRequestLink,
            PRStatus,
            CIPipelineRun,
            CIPipelineStatus,
        )
        from app.models.task import Task, TaskStatus
        from app.services.merge_readiness_service import evaluate_merge_readiness

        project = await _seed_project(db_session)
        inst = await _seed_installation(db_session)
        repo = await _seed_repo_link(db_session, inst.id, project.id)

        from app.models.run import Run

        run = Run(project_id=project.id, run_number=2, trigger="test")
        db_session.add(run)
        await db_session.flush()

        pr = PullRequestLink(
            repository_link_id=repo.id,
            run_id=run.id,
            pr_number=44,
            pr_title="feat: wip",
            pr_url="https://github.com/test/repo/pull/44",
            head_branch="wip",
            base_branch="main",
            status=PRStatus.OPEN,
        )
        db_session.add(pr)

        ci = CIPipelineRun(
            repository_link_id=repo.id,
            external_run_id=1003,
            workflow_name="CI",
            head_sha="ghi789",
            branch="wip",
            status=CIPipelineStatus.SUCCESS,
        )
        db_session.add(ci)

        task = Task(
            title="Incomplete task",
            task_type="architecture",
            status=TaskStatus.READY,
            order_index=0,
            run_id=run.id,
        )
        db_session.add(task)
        await db_session.flush()

        result = await evaluate_merge_readiness(db_session, pr.id)
        assert result.ready is False
        assert any(b.category == "tasks" for b in result.blockers)

    @pytest.mark.asyncio
    async def test_not_found_pr(self, db_session: AsyncSession):
        from app.services.merge_readiness_service import evaluate_merge_readiness

        result = await evaluate_merge_readiness(db_session, uuid.uuid4())
        assert result.ready is False
        assert result.blockers[0].category == "pr_status"

    @pytest.mark.asyncio
    async def test_merge_readiness_route(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        from app.models.github_integration import PullRequestLink, PRStatus

        project = await _seed_project(db_session)
        inst = await _seed_installation(db_session)
        repo = await _seed_repo_link(db_session, inst.id, project.id)

        pr = PullRequestLink(
            repository_link_id=repo.id,
            pr_number=50,
            pr_title="test merge readiness",
            pr_url="https://github.com/test/repo/pull/50",
            head_branch="feat",
            base_branch="main",
            status=PRStatus.OPEN,
        )
        db_session.add(pr)
        await db_session.flush()
        await db_session.commit()

        resp = await client.get(f"/github/prs/{pr.id}/merge-readiness")
        assert resp.status_code == 200
        body = resp.json()
        assert "ready" in body
        assert "blockers" in body
        assert "checks_passed" in body


# =====================================================================
# FM-160: Hardening — Rate Limiter, Retry, Webhook Replay
# =====================================================================


class TestGitHubRateLimiter:
    def test_update_from_headers(self):
        from app.services.github_rate_limiter import GitHubRateLimiter

        limiter = GitHubRateLimiter()
        limiter.update_from_headers(
            {
                "X-RateLimit-Remaining": "50",
                "X-RateLimit-Limit": "5000",
                "X-RateLimit-Reset": "1700000000",
            }
        )
        assert limiter.remaining == 50
        assert limiter.limit == 5000
        assert limiter.reset_at == 1700000000.0

    def test_is_near_limit(self):
        from app.services.github_rate_limiter import GitHubRateLimiter

        limiter = GitHubRateLimiter(remaining_threshold=10)
        assert limiter.is_near_limit is False

        limiter.update_from_headers({"X-RateLimit-Remaining": "5"})
        assert limiter.is_near_limit is True

        limiter.update_from_headers({"X-RateLimit-Remaining": "100"})
        assert limiter.is_near_limit is False

    @pytest.mark.asyncio
    async def test_wait_if_needed_no_wait(self):
        from app.services.github_rate_limiter import GitHubRateLimiter

        limiter = GitHubRateLimiter()
        limiter.remaining = 100
        # Should not block
        await limiter.wait_if_needed()

    def test_empty_headers_no_crash(self):
        from app.services.github_rate_limiter import GitHubRateLimiter

        limiter = GitHubRateLimiter()
        limiter.update_from_headers({})
        assert limiter.remaining is None
        assert limiter.limit is None


class TestGitHubRetryDecorator:
    @pytest.mark.asyncio
    async def test_retry_on_transient_error(self):
        from app.services.github_rate_limiter import github_retry

        call_count = 0

        class TransientError(Exception):
            status_code = 502

        @github_retry(max_attempts=3, base_delay=0.01)
        async def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise TransientError("Bad Gateway")
            return "ok"

        result = await flaky()
        assert result == "ok"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_no_retry_on_non_retryable(self):
        from app.services.github_rate_limiter import github_retry

        class NotRetryable(Exception):
            status_code = 404

        @github_retry(max_attempts=3, base_delay=0.01)
        async def fail():
            raise NotRetryable("Not Found")

        with pytest.raises(NotRetryable):
            await fail()

    @pytest.mark.asyncio
    async def test_succeeds_first_try(self):
        from app.services.github_rate_limiter import github_retry

        @github_retry(max_attempts=3, base_delay=0.01)
        async def succeed():
            return 42

        result = await succeed()
        assert result == 42


class TestWebhookReplay:
    @pytest.mark.asyncio
    async def test_replay_not_found(self, client: AsyncClient):
        fake_id = str(uuid.uuid4())
        resp = await client.post(f"/github/webhooks/replay/{fake_id}")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_replay_stored_event(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        from app.models.github_integration import ExternalEvent, ExternalEventSource

        event = ExternalEvent(
            source=ExternalEventSource.GITHUB,
            event_type="push",
            delivery_id="test-replay-001",
            payload={"action": "completed"},
            processed=True,
        )
        db_session.add(event)
        await db_session.flush()
        await db_session.commit()

        resp = await client.post(f"/github/webhooks/replay/{event.id}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "replayed"
        assert body["event_type"] == "push"


# =====================================================================
# FM-153: Outbound PR Creation (client unit tests)
# =====================================================================


class TestGitHubClientCreatePR:
    """Unit tests for github_client.create_pull_request()."""

    @pytest.mark.asyncio
    async def test_create_pull_request_success(self):
        from unittest.mock import AsyncMock, patch, MagicMock

        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "number": 42,
            "html_url": "https://github.com/test-org/test-repo/pull/42",
            "title": "feat: add feature",
            "head": {"ref": "feature-branch"},
            "base": {"ref": "main"},
            "state": "open",
        }
        mock_response.is_success = True

        with patch("httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.request.return_value = mock_response
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            from app.services.github_client import create_pull_request

            pr = await create_pull_request(
                "test-org",
                "test-repo",
                title="feat: add feature",
                head="feature-branch",
                base="main",
                body="Description of changes",
                token="test-token-123",
            )

            assert pr.number == 42
            assert pr.html_url == "https://github.com/test-org/test-repo/pull/42"
            assert pr.head_ref == "feature-branch"
            assert pr.base_ref == "main"
            assert pr.state == "open"

    @pytest.mark.asyncio
    async def test_create_pull_request_failure(self):
        from unittest.mock import AsyncMock, patch, MagicMock
        from app.services.github_client import GitHubClientError

        mock_response = MagicMock()
        mock_response.status_code = 422
        mock_response.is_success = False
        mock_response.text = "Validation Failed"

        with patch("httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.request.return_value = mock_response
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            from app.services.github_client import create_pull_request

            with pytest.raises(GitHubClientError) as exc_info:
                await create_pull_request(
                    "test-org",
                    "test-repo",
                    title="feat: add feature",
                    head="feature-branch",
                    base="main",
                    token="test-token-123",
                )
            assert exc_info.value.status_code == 422


class TestGitHubClientRequestReviewers:
    """Unit tests for github_client.request_reviewers()."""

    @pytest.mark.asyncio
    async def test_request_reviewers_success(self):
        from unittest.mock import AsyncMock, patch, MagicMock

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "requested_reviewers": [
                {"login": "alice"},
                {"login": "bob"},
            ],
            "requested_teams": [
                {"slug": "backend-team"},
            ],
        }
        mock_response.is_success = True

        with patch("httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.request.return_value = mock_response
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            from app.services.github_client import request_reviewers

            result = await request_reviewers(
                "test-org",
                "test-repo",
                42,
                reviewers=["alice", "bob"],
                team_reviewers=["backend-team"],
                token="test-token-123",
            )

            assert result["requested_reviewers"] == ["alice", "bob"]
            assert result["requested_teams"] == ["backend-team"]

    @pytest.mark.asyncio
    async def test_request_reviewers_no_reviewers_raises(self):
        from app.services.github_client import request_reviewers

        with pytest.raises(ValueError, match="At least one"):
            await request_reviewers(
                "test-org",
                "test-repo",
                42,
                token="test-token-123",
            )


class TestGitHubClientCIPassRate:
    """Unit tests for github_client.get_ci_pass_rate()."""

    @pytest.mark.asyncio
    async def test_ci_pass_rate_success(self):
        from unittest.mock import AsyncMock, patch, MagicMock

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "workflow_runs": [
                {"conclusion": "success"},
                {"conclusion": "success"},
                {"conclusion": "failure"},
                {"conclusion": "success"},
            ]
        }
        mock_response.is_success = True

        with patch("httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.request.return_value = mock_response
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            from app.services.github_client import get_ci_pass_rate

            result = await get_ci_pass_rate(
                "test-org",
                "test-repo",
                branch="main",
                token="test-token-123",
            )

            assert result["total_runs"] == 4
            assert result["success_count"] == 3
            assert result["pass_rate"] == 75.0

    @pytest.mark.asyncio
    async def test_ci_pass_rate_empty(self):
        from unittest.mock import AsyncMock, patch, MagicMock

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"workflow_runs": []}
        mock_response.is_success = True

        with patch("httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.request.return_value = mock_response
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            from app.services.github_client import get_ci_pass_rate

            result = await get_ci_pass_rate(
                "test-org",
                "test-repo",
                branch="main",
                token="test-token-123",
            )
            assert result["total_runs"] == 0
            assert result["pass_rate"] == 0.0


# =====================================================================
# FM-153: Outbound PR Creation (route integration tests)
# =====================================================================


class TestCreatePRRoute:
    @pytest.mark.asyncio
    async def test_create_pr_repo_not_found(self, client: AsyncClient):
        fake_id = str(uuid.uuid4())
        resp = await client.post(
            f"/github/repos/{fake_id}/pulls",
            json={"title": "test pr", "head": "feature", "base": "main"},
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_create_pr_no_token(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Route returns 503 when GITHUB_API_TOKEN is empty."""
        from unittest.mock import patch

        project = await _seed_project(db_session)
        inst = await _seed_installation(db_session)
        repo = await _seed_repo_link(db_session, inst.id, project.id)
        await db_session.commit()

        with patch("app.core.config.settings.github_api_token", ""):
            resp = await client.post(
                f"/github/repos/{repo.id}/pulls",
                json={"title": "test pr", "head": "feature", "base": "main"},
            )
        assert resp.status_code == 503


# =====================================================================
# FM-157: Reviewer Request (route integration tests)
# =====================================================================


class TestReviewerRequestRoute:
    @pytest.mark.asyncio
    async def test_request_reviewers_pr_not_found(self, client: AsyncClient):
        fake_id = str(uuid.uuid4())
        resp = await client.post(
            f"/github/prs/{fake_id}/reviewers",
            json={"reviewers": ["alice"]},
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_request_reviewers_no_body(self, client: AsyncClient):
        fake_id = str(uuid.uuid4())
        resp = await client.post(
            f"/github/prs/{fake_id}/reviewers",
            json={},
        )
        assert resp.status_code == 400


# =====================================================================
# FM-154: CI Pass Rate (route integration tests)
# =====================================================================


class TestCIPassRateRoute:
    @pytest.mark.asyncio
    async def test_ci_pass_rate_repo_not_found(self, client: AsyncClient):
        fake_id = str(uuid.uuid4())
        resp = await client.get(f"/github/repos/{fake_id}/ci/pass-rate")
        assert resp.status_code == 404
