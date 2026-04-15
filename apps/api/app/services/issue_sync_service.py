"""Issue sync service.

FM-155: Issue Synchronization — import from GitHub and export to GitHub.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.github_integration import IssueLink, IssueLinkStatus, RepositoryLink


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
) -> IssueLink:
    """Export a ForgeMind-originated issue to GitHub (FM-155).

    Creates a local IssueLink record representing an outbound issue.
    In a production system this would call the GitHub API to create
    the issue and store the returned issue number. Here we record
    the intent with issue_number=-1 (pending) and mark it for
    outbound sync.
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

    issue = IssueLink(
        repository_link_id=repo_link.id,
        project_id=project_id,
        issue_number=0,  # 0 = pending outbound sync
        title=title,
        issue_url=f"https://github.com/{repo_link.full_name}/issues/new",
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
