"""Issue sync service.

FM-155: Issue Synchronization — import from GitHub and export to GitHub.
Supports live API export, webhook-driven import, and conflict resolution.
"""

import uuid
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.github_integration import IssueLink, IssueLinkStatus, RepositoryLink

logger = logging.getLogger(__name__)


async def list_issues_for_project(
    db: AsyncSession,
    project_id: uuid.UUID,
    status: IssueLinkStatus | None = None,
) -> list[IssueLink]:
    q = select(IssueLink).where(IssueLink.project_id == project_id)
    if status:
        q = q.where(IssueLink.status == status)
    result = await db.execute(q.order_by(IssueLink.created_at.desc()))
    return list(result.scalars().all())


async def link_issue_to_run(
    db: AsyncSession,
    issue_link_id: uuid.UUID,
    run_id: uuid.UUID,
) -> IssueLink:
    issue = await db.get(IssueLink, issue_link_id)
    if issue is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Issue link not found")
    issue.run_id = run_id
    await db.flush()
    await db.refresh(issue)
    return issue


async def export_issue_to_github(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    title: str,
    body: str | None = None,
    labels: list[str] | None = None,
    github_client: object | None = None,
) -> IssueLink:
    """Export a ForgeMind-originated issue to GitHub (FM-155).

    If github_client is provided, calls the live GitHub API to create
    the issue and stores the returned issue number. Otherwise creates
    a local record with issue_number=0 (pending outbound sync).
    """
    from fastapi import HTTPException

    # Find a repo link for this project
    result = await db.execute(
        select(RepositoryLink).where(
            RepositoryLink.project_id == project_id,
            RepositoryLink.is_active.is_(True),
        )
    )
    repo_link = result.scalar_one_or_none()
    if repo_link is None:
        raise HTTPException(
            status_code=400,
            detail="No active repository linked to this project",
        )

    issue_number = 0
    issue_url = f"https://github.com/{repo_link.full_name}/issues/new"

    # Live API export if client available
    if github_client is not None:
        try:
            parts = repo_link.full_name.split("/", 1)
            if len(parts) == 2:
                resp = await github_client.create_issue(
                    parts[0], parts[1],
                    title=title, body=body, labels=labels,
                )
                issue_number = resp.get("number", 0)
                issue_url = resp.get("html_url", issue_url)
        except Exception as exc:
            logger.warning("GitHub API export failed, storing as pending: %s", exc)

    issue = IssueLink(
        repository_link_id=repo_link.id,
        project_id=project_id,
        issue_number=issue_number,
        title=title,
        issue_url=issue_url,
        status=IssueLinkStatus.OPEN,
        labels=labels or [],
    )
    db.add(issue)
    await db.flush()
    await db.refresh(issue)
    return issue


async def list_exportable_issues(
    db: AsyncSession,
    project_id: uuid.UUID,
) -> list[IssueLink]:
    """List issues pending outbound export (issue_number == 0)."""
    result = await db.execute(
        select(IssueLink).where(
            IssueLink.project_id == project_id,
            IssueLink.issue_number == 0,
        ).order_by(IssueLink.created_at.desc())
    )
    return list(result.scalars().all())


# ---------------------------------------------------------------------------
# FM-155: Webhook-driven import
# ---------------------------------------------------------------------------


async def handle_issue_webhook(
    db: AsyncSession,
    payload: dict,
    repo_link: RepositoryLink,
) -> IssueLink | None:
    """Handle a GitHub `issues` webhook event (FM-155).

    Creates or updates an IssueLink based on the webhook payload.
    Supports opened, closed, reopened, and edited actions.
    """
    action = payload.get("action", "")
    issue_data = payload.get("issue", {})
    issue_number = issue_data.get("number")
    if not issue_number:
        return None

    # Look for existing link
    result = await db.execute(
        select(IssueLink).where(
            IssueLink.repository_link_id == repo_link.id,
            IssueLink.issue_number == issue_number,
        )
    )
    existing = result.scalar_one_or_none()

    if action == "opened" and existing is None:
        issue = IssueLink(
            repository_link_id=repo_link.id,
            project_id=repo_link.project_id,
            issue_number=issue_number,
            title=issue_data.get("title", ""),
            issue_url=issue_data.get("html_url", ""),
            status=IssueLinkStatus.OPEN,
            labels=[lbl.get("name", "") for lbl in issue_data.get("labels", [])],
        )
        db.add(issue)
        await db.flush()
        await db.refresh(issue)
        return issue

    if existing is None:
        return None

    if action == "closed":
        existing.status = IssueLinkStatus.CLOSED
    elif action == "reopened":
        existing.status = IssueLinkStatus.OPEN
    elif action == "edited":
        # Conflict resolution: GitHub is authoritative for webhook-sourced issues
        new_title = issue_data.get("title", existing.title)
        existing.title = new_title
        existing.labels = [lbl.get("name", "") for lbl in issue_data.get("labels", [])]

    await db.flush()
    await db.refresh(existing)
    return existing


async def resolve_conflict(
    db: AsyncSession,
    issue_link_id: uuid.UUID,
    *,
    strategy: str = "remote_wins",
    remote_title: str | None = None,
    remote_status: str | None = None,
    remote_labels: list[str] | None = None,
) -> IssueLink | None:
    """Resolve a conflict between local and remote issue state (FM-155).

    Strategies:
    - remote_wins: apply remote state unconditionally
    - local_wins: keep local state (no-op)
    """
    issue = await db.get(IssueLink, issue_link_id)
    if issue is None:
        return None

    if strategy == "remote_wins":
        if remote_title is not None:
            issue.title = remote_title
        if remote_status is not None:
            try:
                issue.status = IssueLinkStatus(remote_status)
            except ValueError:
                pass
        if remote_labels is not None:
            issue.labels = remote_labels
        await db.flush()
        await db.refresh(issue)
    # local_wins: keep local state — nothing to do

    return issue
