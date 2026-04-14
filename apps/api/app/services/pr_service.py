"""PR auto-creation & management service.

FM-153: Pull Request Auto-Creation.
"""

import uuid

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.github_integration import PullRequestLink, PRStatus


async def create_pr_link(
    db: AsyncSession,
    repository_link_id: uuid.UUID,
    pr_number: int,
    pr_title: str,
    pr_url: str,
    head_branch: str,
    base_branch: str,
    run_id: uuid.UUID | None = None,
    task_id: uuid.UUID | None = None,
) -> PullRequestLink:
    pr = PullRequestLink(
        repository_link_id=repository_link_id,
        run_id=run_id,
        task_id=task_id,
        pr_number=pr_number,
        pr_title=pr_title,
        pr_url=pr_url,
        head_branch=head_branch,
        base_branch=base_branch,
        status=PRStatus.OPEN,
    )
    db.add(pr)
    await db.flush()
    await db.refresh(pr)
    return pr


async def list_prs_for_run(
    db: AsyncSession,
    run_id: uuid.UUID,
) -> list[PullRequestLink]:
    result = await db.execute(
        select(PullRequestLink).where(PullRequestLink.run_id == run_id)
    )
    return list(result.scalars().all())


async def list_prs_for_repo(
    db: AsyncSession,
    repository_link_id: uuid.UUID,
    status: PRStatus | None = None,
) -> list[PullRequestLink]:
    q = select(PullRequestLink).where(
        PullRequestLink.repository_link_id == repository_link_id
    )
    if status:
        q = q.where(PullRequestLink.status == status)
    result = await db.execute(q.order_by(PullRequestLink.created_at.desc()))
    return list(result.scalars().all())


async def update_pr_status(
    db: AsyncSession,
    pr_link_id: uuid.UUID,
    status: PRStatus,
) -> PullRequestLink:
    pr = await db.get(PullRequestLink, pr_link_id)
    if pr is None:
        raise HTTPException(status_code=404, detail="PR link not found")
    pr.status = status
    await db.flush()
    await db.refresh(pr)
    return pr
