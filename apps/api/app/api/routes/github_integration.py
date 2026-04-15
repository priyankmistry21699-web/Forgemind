"""GitHub integration routes — installations, repos, webhooks, PRs, CI, issues.

FM-151–160.
"""

import uuid

from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import BaseModel as _BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.auth import get_current_user_id
from app.schemas.github_integration import (
    GitHubInstallationCreate,
    GitHubInstallationRead,
    RepositoryLinkCreate,
    RepositoryLinkRead,
    PullRequestLinkRead,
    CIPipelineRunRead,
    IssueLinkRead,
    CodeOwnershipCreate,
    CodeOwnershipRead,
)
from app.services import (
    github_installation_service,
    webhook_service,
    pr_service,
    ci_pipeline_service,
    issue_sync_service,
    code_review_service,
    merge_readiness_service,
)

router = APIRouter(prefix="/github")


# ---------------------------------------------------------------------------
# FM-151: Installations & repo links
# ---------------------------------------------------------------------------


@router.post("/installations", response_model=GitHubInstallationRead)
async def register_installation(
    body: GitHubInstallationCreate,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    return await github_installation_service.create_installation(
        db,
        installation_id=body.installation_id,
        account_login=body.account_login,
        account_type=body.account_type,
        connected_by=user_id,
        permissions=body.permissions,
    )


@router.get("/installations", response_model=list[GitHubInstallationRead])
async def list_installations(
    db: AsyncSession = Depends(get_db),
    _user_id: uuid.UUID = Depends(get_current_user_id),
):
    return await github_installation_service.list_installations(db)


@router.post("/repos", response_model=RepositoryLinkRead)
async def link_repo(
    body: RepositoryLinkCreate,
    db: AsyncSession = Depends(get_db),
    _user_id: uuid.UUID = Depends(get_current_user_id),
):
    return await github_installation_service.link_repository(
        db,
        installation_id=body.installation_id,
        project_id=body.project_id,
        github_repo_id=body.github_repo_id,
        full_name=body.full_name,
        default_branch=body.default_branch,
    )


@router.get("/repos/{project_id}", response_model=list[RepositoryLinkRead])
async def list_project_repos(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user_id: uuid.UUID = Depends(get_current_user_id),
):
    return await github_installation_service.list_repos_for_project(db, project_id)


@router.delete("/repos/{link_id}", status_code=204)
async def unlink_repo(
    link_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user_id: uuid.UUID = Depends(get_current_user_id),
):
    await github_installation_service.unlink_repository(db, link_id)


# ---------------------------------------------------------------------------
# FM-152: Webhooks
# ---------------------------------------------------------------------------


@router.post("/webhooks", status_code=201)
async def receive_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Receive GitHub webhook events.

    Verifies HMAC-SHA256 signature when GITHUB_WEBHOOK_SECRET is configured.
    """
    from app.core.config import settings

    payload_bytes = await request.body()

    # Enforce signature verification when a webhook secret is configured
    if settings.github_webhook_secret:
        signature = request.headers.get("X-Hub-Signature-256", "")
        if not webhook_service.verify_github_signature(
            payload_bytes, signature, settings.github_webhook_secret
        ):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

    event_type = request.headers.get("X-GitHub-Event", "ping")
    delivery_id = request.headers.get("X-GitHub-Delivery")
    import json as _json

    payload = _json.loads(payload_bytes)

    event = await webhook_service.ingest_event(db, event_type, delivery_id, payload)

    # Process known event types
    if event_type == "pull_request" and event.repository_link_id:
        await webhook_service.process_pr_event(db, event)
    elif event_type == "workflow_run" and event.repository_link_id:
        await webhook_service.process_workflow_run_event(db, event)
    elif event_type == "issues" and event.repository_link_id:
        await webhook_service.process_issues_event(db, event)
    elif event_type == "push" and event.repository_link_id:
        await webhook_service.process_push_event(db, event)
    elif event_type == "release" and event.repository_link_id:
        await webhook_service.process_release_event(db, event)
    elif event_type == "check_run" and event.repository_link_id:
        await webhook_service.process_check_run_event(db, event)

    return {"status": "accepted", "event_id": str(event.id)}


# ---------------------------------------------------------------------------
# FM-153: Pull Requests
# ---------------------------------------------------------------------------


@router.get("/prs/run/{run_id}", response_model=list[PullRequestLinkRead])
async def list_run_prs(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user_id: uuid.UUID = Depends(get_current_user_id),
):
    return await pr_service.list_prs_for_run(db, run_id)


@router.get("/prs/repo/{repo_link_id}", response_model=list[PullRequestLinkRead])
async def list_repo_prs(
    repo_link_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user_id: uuid.UUID = Depends(get_current_user_id),
):
    return await pr_service.list_prs_for_repo(db, repo_link_id)


# ---------------------------------------------------------------------------
# FM-154: CI Pipelines
# ---------------------------------------------------------------------------


@router.get("/ci/repo/{repo_link_id}", response_model=list[CIPipelineRunRead])
async def list_ci_runs(
    repo_link_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user_id: uuid.UUID = Depends(get_current_user_id),
):
    return await ci_pipeline_service.list_pipelines_for_repo(db, repo_link_id)


@router.get("/ci/repo/{repo_link_id}/latest", response_model=CIPipelineRunRead | None)
async def latest_ci_run(
    repo_link_id: uuid.UUID,
    branch: str | None = None,
    db: AsyncSession = Depends(get_db),
    _user_id: uuid.UUID = Depends(get_current_user_id),
):
    return await ci_pipeline_service.get_latest_pipeline(
        db, repo_link_id, branch=branch
    )


# ---------------------------------------------------------------------------
# FM-155: Issues
# ---------------------------------------------------------------------------


@router.get("/issues/{project_id}", response_model=list[IssueLinkRead])
async def list_project_issues(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user_id: uuid.UUID = Depends(get_current_user_id),
):
    return await issue_sync_service.list_issues_for_project(db, project_id)


class _ExportIssueBody(_BaseModel):
    title: str
    body: str | None = None
    labels: list[str] | None = None


@router.post("/issues/{project_id}/export", response_model=IssueLinkRead, status_code=201)
async def export_issue(
    project_id: uuid.UUID,
    body: _ExportIssueBody,
    db: AsyncSession = Depends(get_db),
    _user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Export (create) an issue from ForgeMind to GitHub (FM-155)."""
    issue = await issue_sync_service.export_issue_to_github(
        db,
        project_id=project_id,
        title=body.title,
        body=body.body,
        labels=body.labels,
    )
    await db.commit()
    return issue


class _SyncStatusBody(_BaseModel):
    status: str  # "open" or "closed"


@router.post("/issues/{issue_link_id}/sync-status")
async def sync_issue_status_to_github(
    issue_link_id: uuid.UUID,
    body: _SyncStatusBody,
    db: AsyncSession = Depends(get_db),
    _user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Push a ForgeMind issue status change to GitHub (FM-155).

    Bidirectional sync: ForgeMind → GitHub direction.
    Without a configured github_client, updates local state only.
    """
    from app.models.github_integration import IssueLinkStatus
    try:
        new_status = IssueLinkStatus(body.status)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid status: {body.status}")

    issue = await issue_sync_service.sync_status_to_github(
        db, issue_link_id, new_status, github_client=None,
    )
    if issue is None:
        raise HTTPException(status_code=404, detail="Issue link not found")
    await db.commit()
    return {
        "issue_link_id": str(issue.id),
        "issue_number": issue.issue_number,
        "status": issue.status.value,
        "sync_direction": issue.sync_direction,
        "last_synced_at": issue.last_synced_at.isoformat() if issue.last_synced_at else None,
    }


@router.post("/issues/{project_id}/sync-pending")
async def sync_pending_exports(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Batch-export all pending issues to GitHub (FM-155).

    Returns the list of pending issues. Without a live GitHub client,
    no mutations occur — just returns what would be exported.
    """
    pending = await issue_sync_service.process_pending_exports(
        db, project_id, github_client=None,
    )
    return {
        "pending_count": len(pending),
        "issues": [
            {"id": str(i.id), "title": i.title, "issue_number": i.issue_number}
            for i in pending
        ],
    }


# ---------------------------------------------------------------------------
# FM-157: Code Ownership
# ---------------------------------------------------------------------------


@router.post("/code-owners", response_model=CodeOwnershipRead)
async def upsert_code_owner(
    body: CodeOwnershipCreate,
    db: AsyncSession = Depends(get_db),
    _user_id: uuid.UUID = Depends(get_current_user_id),
):
    return await code_review_service.upsert_ownership_rule(
        db,
        repository_link_id=body.repository_link_id,
        file_pattern=body.file_pattern,
        owner_user_id=body.owner_user_id,
        owner_team_name=body.owner_team_name,
    )


@router.post("/code-owners/match")
async def match_code_owners(
    repo_link_id: uuid.UUID,
    file_paths: list[str],
    db: AsyncSession = Depends(get_db),
    _user_id: uuid.UUID = Depends(get_current_user_id),
):
    return await code_review_service.get_owners_for_files(db, repo_link_id, file_paths)


class _SuggestReviewersBody(_BaseModel):
    file_paths: list[str]
    max_reviewers: int = 5
    exclude_user_ids: list[uuid.UUID] | None = None


@router.post("/code-owners/suggest-reviewers")
async def suggest_reviewers(
    repo_link_id: uuid.UUID,
    body: _SuggestReviewersBody,
    db: AsyncSession = Depends(get_db),
    _user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Suggest ranked reviewers for changed files based on code ownership.

    Uses CODEOWNERS patterns to score reviewers by coverage breadth and
    pattern specificity. Returns a ranked list of suggested reviewers.
    """
    return await code_review_service.suggest_reviewers(
        db,
        repo_link_id,
        body.file_paths,
        max_reviewers=body.max_reviewers,
        exclude_user_ids=body.exclude_user_ids,
    )


# ---------------------------------------------------------------------------
# FM-156: Merge Readiness
# ---------------------------------------------------------------------------


@router.get("/prs/{pr_link_id}/merge-readiness")
async def get_merge_readiness(
    pr_link_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Evaluate whether a PR is ready to merge."""
    result = await merge_readiness_service.evaluate_merge_readiness(db, pr_link_id)
    return {
        "ready": result.ready,
        "blockers": [
            {"category": b.category, "message": b.message} for b in result.blockers
        ],
        "checks_passed": result.checks_passed,
    }


# ---------------------------------------------------------------------------
# FM-160: Webhook Replay
# ---------------------------------------------------------------------------


@router.post("/webhooks/replay/{event_id}", status_code=200)
async def replay_webhook(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Re-process a stored webhook event (admin/debug tool)."""
    from app.models.github_integration import ExternalEvent

    event = await db.get(ExternalEvent, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")

    # Re-process based on event type
    result = None
    if event.event_type == "pull_request" and event.repository_link_id:
        result = await webhook_service.process_pr_event(db, event)
    elif event.event_type == "workflow_run" and event.repository_link_id:
        result = await webhook_service.process_workflow_run_event(db, event)
    elif event.event_type == "issues" and event.repository_link_id:
        result = await webhook_service.process_issues_event(db, event)

    return {
        "status": "replayed",
        "event_id": str(event.id),
        "event_type": event.event_type,
        "result": str(result) if result else None,
    }


# ---------------------------------------------------------------------------
# FM-154/157: Outbound GitHub Actions — PR comments & commit status
# ---------------------------------------------------------------------------


class _PRCommentBody(_BaseModel):
    body: str


class _CommitStatusBody(_BaseModel):
    state: str  # pending, success, failure, error
    description: str = ""
    target_url: str | None = None
    context: str = "forgemind/ci"


@router.post("/prs/{pr_link_id}/comments")
async def post_pr_comment(
    pr_link_id: uuid.UUID,
    body: _PRCommentBody,
    db: AsyncSession = Depends(get_db),
    _user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Post a comment on a GitHub PR via the outbound API.

    Requires GITHUB_API_TOKEN (personal access token or installation token).
    Resolves the PR's repo owner/name from the linked repository.
    """
    from app.models.github_integration import PullRequestLink, RepositoryLink
    from app.services.github_client import post_pr_comment as gh_post_comment
    from app.services.github_client import GitHubClientError
    from app.core.config import settings

    pr = await db.get(PullRequestLink, pr_link_id)
    if pr is None:
        raise HTTPException(status_code=404, detail="PR link not found")

    repo = await db.get(RepositoryLink, pr.repository_link_id)
    if repo is None:
        raise HTTPException(status_code=404, detail="Repository link not found")

    # Parse owner/repo from full_name (e.g. "owner/repo")
    parts = repo.full_name.split("/", 1)
    if len(parts) != 2:
        raise HTTPException(status_code=400, detail="Invalid repo full_name format")
    owner, repo_name = parts

    # Resolve outbound API token: prefer github_api_token, never use webhook_secret
    # (webhook_secret is an HMAC key for signature verification, not an API token)
    token = settings.github_api_token or ""
    if not token:
        raise HTTPException(
            status_code=503,
            detail="GitHub credentials not configured — set GITHUB_API_TOKEN",
        )

    try:
        comment = await gh_post_comment(owner, repo_name, pr.pr_number, body.body, token)
        return {
            "posted": True,
            "github_comment_id": comment.id,
            "html_url": comment.html_url,
        }
    except GitHubClientError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/repos/{repo_link_id}/statuses/{sha}")
async def create_commit_status(
    repo_link_id: uuid.UUID,
    sha: str,
    body: _CommitStatusBody,
    db: AsyncSession = Depends(get_db),
    _user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Create a commit status on GitHub (pending/success/failure/error)."""
    from app.models.github_integration import RepositoryLink
    from app.services.github_client import create_commit_status as gh_create_status
    from app.services.github_client import GitHubClientError
    from app.core.config import settings

    repo = await db.get(RepositoryLink, repo_link_id)
    if repo is None:
        raise HTTPException(status_code=404, detail="Repository link not found")

    parts = repo.full_name.split("/", 1)
    if len(parts) != 2:
        raise HTTPException(status_code=400, detail="Invalid repo full_name format")
    owner, repo_name = parts

    token = settings.github_api_token or ""
    if not token:
        raise HTTPException(
            status_code=503,
            detail="GitHub credentials not configured — set GITHUB_API_TOKEN",
        )

    try:
        status = await gh_create_status(
            owner, repo_name, sha,
            state=body.state,
            description=body.description,
            target_url=body.target_url,
            context=body.context,
            token=token,
        )
        return {
            "posted": True,
            "state": status.state,
            "context": status.context,
            "description": status.description,
        }
    except GitHubClientError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


# ---------------------------------------------------------------------------
# FM-153: Outbound PR Creation
# ---------------------------------------------------------------------------


class _CreatePRBody(_BaseModel):
    title: str
    head: str
    base: str = "main"
    body: str = ""
    draft: bool = False


@router.post("/repos/{repo_link_id}/pulls")
async def create_pull_request(
    repo_link_id: uuid.UUID,
    body: _CreatePRBody,
    db: AsyncSession = Depends(get_db),
    _user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Create a pull request on GitHub and record the link locally.

    Requires GITHUB_API_TOKEN. Resolves owner/repo from the linked repository.
    """
    from app.models.github_integration import RepositoryLink
    from app.services.github_client import create_pull_request as gh_create_pr
    from app.services.github_client import GitHubClientError
    from app.core.config import settings

    repo = await db.get(RepositoryLink, repo_link_id)
    if repo is None:
        raise HTTPException(status_code=404, detail="Repository link not found")

    parts = repo.full_name.split("/", 1)
    if len(parts) != 2:
        raise HTTPException(status_code=400, detail="Invalid repo full_name format")
    owner, repo_name = parts

    token = settings.github_api_token or ""
    if not token:
        raise HTTPException(
            status_code=503,
            detail="GitHub credentials not configured — set GITHUB_API_TOKEN",
        )

    try:
        gh_pr = await gh_create_pr(
            owner, repo_name,
            title=body.title,
            head=body.head,
            base=body.base,
            body=body.body,
            draft=body.draft,
            token=token,
        )
    except GitHubClientError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

    # Record the PR link in the local DB
    pr_link = await pr_service.create_pr_link(
        db,
        repository_link_id=repo_link_id,
        pr_number=gh_pr.number,
        pr_title=gh_pr.title,
        pr_url=gh_pr.html_url,
        head_branch=gh_pr.head_ref,
        base_branch=gh_pr.base_ref,
    )

    return {
        "created": True,
        "pr_number": gh_pr.number,
        "html_url": gh_pr.html_url,
        "pr_link_id": str(pr_link.id),
    }


# ---------------------------------------------------------------------------
# FM-157: Reviewer Request
# ---------------------------------------------------------------------------


class _ReviewerRequestBody(_BaseModel):
    reviewers: list[str] | None = None
    team_reviewers: list[str] | None = None


@router.post("/prs/{pr_link_id}/reviewers")
async def request_pr_reviewers(
    pr_link_id: uuid.UUID,
    body: _ReviewerRequestBody,
    db: AsyncSession = Depends(get_db),
    _user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Request reviewers on a GitHub pull request.

    Accepts individual GitHub usernames and/or team slugs.
    Requires GITHUB_API_TOKEN.
    """
    from app.models.github_integration import PullRequestLink, RepositoryLink
    from app.services.github_client import request_reviewers as gh_request_reviewers
    from app.services.github_client import GitHubClientError
    from app.core.config import settings

    if not body.reviewers and not body.team_reviewers:
        raise HTTPException(
            status_code=400,
            detail="At least one reviewer or team_reviewer must be specified",
        )

    pr = await db.get(PullRequestLink, pr_link_id)
    if pr is None:
        raise HTTPException(status_code=404, detail="PR link not found")

    repo = await db.get(RepositoryLink, pr.repository_link_id)
    if repo is None:
        raise HTTPException(status_code=404, detail="Repository link not found")

    parts = repo.full_name.split("/", 1)
    if len(parts) != 2:
        raise HTTPException(status_code=400, detail="Invalid repo full_name format")
    owner, repo_name = parts

    token = settings.github_api_token or ""
    if not token:
        raise HTTPException(
            status_code=503,
            detail="GitHub credentials not configured — set GITHUB_API_TOKEN",
        )

    try:
        result = await gh_request_reviewers(
            owner, repo_name, pr.pr_number,
            reviewers=body.reviewers,
            team_reviewers=body.team_reviewers,
            token=token,
        )
        return {
            "requested": True,
            "pr_number": pr.pr_number,
            **result,
        }
    except GitHubClientError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


# ---------------------------------------------------------------------------
# FM-154: CI Pass Rate
# ---------------------------------------------------------------------------


@router.get("/repos/{repo_link_id}/ci/pass-rate")
async def get_ci_pass_rate(
    repo_link_id: uuid.UUID,
    branch: str = "main",
    db: AsyncSession = Depends(get_db),
    _user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Get CI pass rate for a repo branch from recent GitHub Actions runs."""
    from app.models.github_integration import RepositoryLink
    from app.services.github_client import get_ci_pass_rate as gh_pass_rate
    from app.services.github_client import GitHubClientError
    from app.core.config import settings

    repo = await db.get(RepositoryLink, repo_link_id)
    if repo is None:
        raise HTTPException(status_code=404, detail="Repository link not found")

    parts = repo.full_name.split("/", 1)
    if len(parts) != 2:
        raise HTTPException(status_code=400, detail="Invalid repo full_name format")
    owner, repo_name = parts

    token = settings.github_api_token or ""
    if not token:
        raise HTTPException(
            status_code=503,
            detail="GitHub credentials not configured — set GITHUB_API_TOKEN",
        )

    try:
        return await gh_pass_rate(
            owner, repo_name, branch=branch, token=token,
        )
    except GitHubClientError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("/repos/{repo_link_id}/ci/readiness")
async def get_ci_readiness(
    repo_link_id: uuid.UUID,
    threshold: float = 70.0,
    window: int = 20,
    db: AsyncSession = Depends(get_db),
    _user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Evaluate CI readiness gate for a repository.

    Checks whether the historical CI pass rate meets the required threshold.
    This is a gating signal — "pass" means the branch is stable enough.
    Also used as a merge blocker in merge readiness evaluation.
    """
    from app.models.github_integration import RepositoryLink

    repo = await db.get(RepositoryLink, repo_link_id)
    if repo is None:
        raise HTTPException(status_code=404, detail="Repository link not found")

    return await merge_readiness_service.evaluate_ci_readiness(
        db, repo_link_id, threshold=threshold, window=window,
    )


# ---------------------------------------------------------------------------
# FM-158: Diff Intelligence — risk rules & analysis routes
# ---------------------------------------------------------------------------


class _DiffAnalysisBody(_BaseModel):
    diff_text: str


@router.post("/diffs/analyze")
async def analyze_diff(
    body: _DiffAnalysisBody,
    _user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Analyze a unified diff — file stats, impact score, and churn metrics."""
    from app.services import diff_intelligence_service

    return diff_intelligence_service.analyze_diff_stats(body.diff_text)


@router.post("/diffs/risk")
async def evaluate_diff_risk(
    body: _DiffAnalysisBody,
    _user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Evaluate risk rules against a diff (FM-158).

    Returns triggered rules, risk score, and risk level.
    """
    from app.services import diff_intelligence_service

    return diff_intelligence_service.evaluate_risk_rules(body.diff_text)


@router.get("/diffs/rules")
async def list_risk_rules(
    _user_id: uuid.UUID = Depends(get_current_user_id),
):
    """List available diff risk rules."""
    from app.services import diff_intelligence_service

    return diff_intelligence_service.get_risk_rules()


# ---------------------------------------------------------------------------
# FM-156: Auto-create branch from task
# ---------------------------------------------------------------------------


class _AutoBranchBody(_BaseModel):
    task_id: str
    task_title: str
    repo_link_id: str
    base_branch: str = "main"


@router.post("/branches/auto-create")
async def auto_create_branch(
    body: _AutoBranchBody,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Auto-create a GitHub branch named after a task (FM-156).

    Generates a slug from the task title, creates the branch on GitHub,
    and returns the branch info.
    """
    from app.services.github_client import create_branch, slugify_branch_name
    from app.models.github_integration import RepositoryLink
    from app.core.config import settings
    import uuid as _uuid

    repo_link = await db.get(RepositoryLink, _uuid.UUID(body.repo_link_id))
    if repo_link is None:
        raise HTTPException(status_code=404, detail="Repository link not found")

    token = settings.github_api_token or ""
    if not token:
        raise HTTPException(
            status_code=503,
            detail="GitHub credentials not configured — set GITHUB_API_TOKEN",
        )

    branch_name = slugify_branch_name(body.task_title, body.task_id)
    owner, repo_name = repo_link.full_name.split("/", 1)
    result = await create_branch(
        owner, repo_name,
        branch_name=branch_name,
        base_branch=body.base_branch,
        token=token,
    )
    return result


# ---------------------------------------------------------------------------
# FM-151: Installation health & token lifecycle
# ---------------------------------------------------------------------------


@router.get("/installations/{installation_id}/token-status")
async def installation_token_status(
    installation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Check health/token status of a GitHub installation (FM-151)."""
    return await github_installation_service.validate_installation(db, installation_id)


@router.post("/installations/{installation_id}/refresh-token")
async def refresh_installation_token(
    installation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Trigger token refresh for a GitHub installation (FM-151).

    Without a configured GitHub App client, returns current token status.
    """
    token = await github_installation_service.get_or_refresh_token(
        db, installation_id, github_client=None,
    )
    status = await github_installation_service.validate_installation(db, installation_id)
    status["token_refreshed"] = token is not None
    return status


@router.post("/installations/{installation_id}/deactivate")
async def deactivate_installation(
    installation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Deactivate a GitHub installation (FM-151)."""
    inst = await github_installation_service.deactivate_installation(db, installation_id)
    return {"installation_id": inst.installation_id, "active": inst.is_active}


# ---------------------------------------------------------------------------
# FM-151: OAuth / App Installation callback
# ---------------------------------------------------------------------------


class _OAuthCallbackBody(_BaseModel):
    installation_id: int
    access_token: str
    expires_at: str | None = None


@router.post("/auth/callback")
async def github_auth_callback(
    body: _OAuthCallbackBody,
    db: AsyncSession = Depends(get_db),
    _user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Handle GitHub App installation token callback (FM-151).

    Stores the access token encrypted and records expiry.
    """
    from datetime import datetime

    expires = None
    if body.expires_at:
        expires = datetime.fromisoformat(body.expires_at.replace("Z", "+00:00"))

    inst = await github_installation_service.handle_oauth_callback(
        db,
        installation_id_gh=body.installation_id,
        access_token=body.access_token,
        expires_at=expires,
    )
    return {
        "installation_id": inst.installation_id,
        "account_login": inst.account_login,
        "token_stored": True,
        "expires_at": inst.token_expires_at.isoformat() if inst.token_expires_at else None,
    }
