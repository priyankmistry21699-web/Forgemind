"""CI pipeline status service.

FM-154: CI Pipeline Status Tracking.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.github_integration import CIPipelineRun, CIPipelineStatus


async def list_pipelines_for_run(
    db: AsyncSession,
    run_id: uuid.UUID,
) -> list[CIPipelineRun]:
    result = await db.execute(
        select(CIPipelineRun)
        .where(CIPipelineRun.run_id == run_id)
        .order_by(CIPipelineRun.created_at.desc())
    )
    return list(result.scalars().all())


async def list_pipelines_for_repo(
    db: AsyncSession,
    repository_link_id: uuid.UUID,
    status: CIPipelineStatus | None = None,
    limit: int = 20,
) -> list[CIPipelineRun]:
    q = select(CIPipelineRun).where(
        CIPipelineRun.repository_link_id == repository_link_id
    )
    if status:
        q = q.where(CIPipelineRun.status == status)
    result = await db.execute(q.order_by(CIPipelineRun.created_at.desc()).limit(limit))
    return list(result.scalars().all())


async def get_latest_pipeline(
    db: AsyncSession,
    repository_link_id: uuid.UUID,
    branch: str | None = None,
) -> CIPipelineRun | None:
    q = select(CIPipelineRun).where(
        CIPipelineRun.repository_link_id == repository_link_id
    )
    if branch:
        q = q.where(CIPipelineRun.branch == branch)
    result = await db.execute(q.order_by(CIPipelineRun.created_at.desc()).limit(1))
    return result.scalar_one_or_none()
