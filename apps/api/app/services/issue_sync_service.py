"""Issue sync service.

FM-155: Issue Synchronization — import from GitHub and export to GitHub.
Supports live API export, webhook-driven import, conflict resolution,
bidirectional status sync, and pending export batch processing.
"""

import uuid
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.github_integration import IssueLink, IssueLinkStatus, RepositoryLink

logger = logging.getLogger(__name__)

# Sync loop prevention: ignore events within this window
_SYNC_DEBOUNCE_SECONDS = 5


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
                    parts[0],
                    parts[1],
                    title=title,
                    body=body,
                    labels=labels,
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
        sync_direction="outbound",
        last_synced_at=datetime.now(timezone.utc) if issue_number > 0 else None,
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
        select(IssueLink)
        .where(
            IssueLink.project_id == project_id,
            IssueLink.issue_number == 0,
        )
        .order_by(IssueLink.created_at.desc())
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
            sync_direction="inbound",
            last_synced_at=datetime.now(timezone.utc),
        )
        db.add(issue)
        await db.flush()
        await db.refresh(issue)
        return issue

    if existing is None:
        return None

    # Loop prevention: if we just synced outbound, skip this inbound event
    if existing.last_synced_at:
        ls = existing.last_synced_at
        if ls.tzinfo is None:
            ls = ls.replace(tzinfo=timezone.utc)
        if (datetime.now(timezone.utc) - ls).total_seconds() < _SYNC_DEBOUNCE_SECONDS:
            if existing.sync_direction == "outbound":
                logger.info(
                    "Debounce: skipping inbound event for issue #%s", issue_number
                )
                return existing

    if action == "closed":
        existing.status = IssueLinkStatus.CLOSED
    elif action == "reopened":
        existing.status = IssueLinkStatus.OPEN
    elif action == "edited":
        # Conflict resolution: GitHub is authoritative for webhook-sourced issues
        new_title = issue_data.get("title", existing.title)
        existing.title = new_title
        existing.labels = [lbl.get("name", "") for lbl in issue_data.get("labels", [])]

    existing.sync_direction = "inbound"
    existing.last_synced_at = datetime.now(timezone.utc)

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


# ---------------------------------------------------------------------------
# FM-155: Bidirectional sync — ForgeMind → GitHub direction
# ---------------------------------------------------------------------------


async def sync_status_to_github(
    db: AsyncSession,
    issue_link_id: uuid.UUID,
    new_status: IssueLinkStatus,
    *,
    github_client: object | None = None,
) -> IssueLink | None:
    """Push a ForgeMind status change to GitHub (FM-155).

    Updates the local IssueLink status and, if a github_client is provided,
    calls the GitHub API to close/reopen the issue. Marks sync_direction
    as 'outbound' and updates last_synced_at for loop prevention.
    """
    issue = await db.get(IssueLink, issue_link_id)
    if issue is None:
        return None

    old_status = issue.status
    issue.status = new_status

    # Attempt live GitHub API update
    if github_client is not None and issue.issue_number > 0:
        repo_link = await db.get(RepositoryLink, issue.repository_link_id)
        if repo_link and repo_link.full_name:
            parts = repo_link.full_name.split("/", 1)
            if len(parts) == 2:
                gh_state = "closed" if new_status == IssueLinkStatus.CLOSED else "open"
                try:
                    await github_client.update_issue(
                        parts[0],
                        parts[1],
                        issue.issue_number,
                        state=gh_state,
                    )
                except Exception as exc:
                    logger.warning(
                        "GitHub API sync failed for issue #%s: %s",
                        issue.issue_number,
                        exc,
                    )

    issue.sync_direction = "outbound"
    issue.last_synced_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(issue)
    logger.info(
        "Synced issue #%s status: %s → %s",
        issue.issue_number,
        old_status.value,
        new_status.value,
    )
    return issue


async def process_pending_exports(
    db: AsyncSession,
    project_id: uuid.UUID,
    *,
    github_client: object | None = None,
) -> list[IssueLink]:
    """Batch-export all pending issues (issue_number == 0) to GitHub.

    If github_client is provided, calls the live API for each issue.
    Returns the list of issues that were processed.
    """
    pending = await list_exportable_issues(db, project_id)
    if not pending or github_client is None:
        return pending  # Return list for visibility; no mutations without client

    # Need a repo link for API calls
    result = await db.execute(
        select(RepositoryLink).where(
            RepositoryLink.project_id == project_id,
            RepositoryLink.is_active.is_(True),
        )
    )
    repo_link = result.scalar_one_or_none()
    if repo_link is None:
        return pending

    parts = repo_link.full_name.split("/", 1)
    if len(parts) != 2:
        return pending

    exported = []
    for issue in pending:
        try:
            resp = await github_client.create_issue(
                parts[0],
                parts[1],
                title=issue.title,
                body=None,
                labels=issue.labels or [],
            )
            issue.issue_number = resp.get("number", 0)
            issue.issue_url = resp.get("html_url", issue.issue_url)
            issue.sync_direction = "outbound"
            issue.last_synced_at = datetime.now(timezone.utc)
            exported.append(issue)
        except Exception as exc:
            logger.warning("Failed to export issue '%s': %s", issue.title, exc)

    if exported:
        await db.flush()
        for iss in exported:
            await db.refresh(iss)

    return exported


async def bulk_import_issues(
    db: AsyncSession,
    repo_link: RepositoryLink,
    issues_payload: list[dict],
) -> list[IssueLink]:
    """Bulk import issues from a GitHub response payload (FM-155).

    Each item in issues_payload should have: number, title, html_url, state,
    labels (list of dicts with 'name' key).
    Skips issues that are already linked.
    """
    imported = []
    for item in issues_payload:
        issue_number = item.get("number")
        if not issue_number:
            continue

        # Check for existing link
        existing_q = await db.execute(
            select(IssueLink).where(
                IssueLink.repository_link_id == repo_link.id,
                IssueLink.issue_number == issue_number,
            )
        )
        if existing_q.scalar_one_or_none() is not None:
            continue

        status = (
            IssueLinkStatus.CLOSED
            if item.get("state") == "closed"
            else IssueLinkStatus.OPEN
        )
        labels = [lbl.get("name", "") for lbl in item.get("labels", [])]

        issue = IssueLink(
            repository_link_id=repo_link.id,
            project_id=repo_link.project_id,
            issue_number=issue_number,
            title=item.get("title", ""),
            issue_url=item.get("html_url", ""),
            status=status,
            labels=labels,
            sync_direction="inbound",
            last_synced_at=datetime.now(timezone.utc),
        )
        db.add(issue)
        imported.append(issue)

    if imported:
        await db.flush()
        for iss in imported:
            await db.refresh(iss)

    return imported
