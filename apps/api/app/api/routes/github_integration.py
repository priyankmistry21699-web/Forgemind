"""GitHub integration routes — installations, repos, webhooks, PRs, CI, issues.

FM-151–160.
"""

import uuid

from fastapi import APIRouter, Depends, Request, HTTPException
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
    """Receive GitHub webhook events."""
    event_type = request.headers.get("X-GitHub-Event", "ping")
    delivery_id = request.headers.get("X-GitHub-Delivery")
    payload = await request.json()

    event = await webhook_service.ingest_event(db, event_type, delivery_id, payload)

    # Process known event types
    if event_type == "pull_request" and event.repository_link_id:
        await webhook_service.process_pr_event(db, event)
    elif event_type == "workflow_run" and event.repository_link_id:
        await webhook_service.process_workflow_run_event(db, event)
    elif event_type == "issues" and event.repository_link_id:
        await webhook_service.process_issues_event(db, event)

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
