"""Issue sync service.

FM-155: Issue Synchronization.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.github_integration import IssueLink, IssueLinkStatus


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
