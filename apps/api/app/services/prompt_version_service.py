"""FM-234: Prompt version registry service."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.platform_intelligence import PromptVersion


async def create_version(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    role: str,
    content: str,
    change_summary: str | None = None,
    created_by: str | None = None,
) -> PromptVersion:
    # Deactivate previous active version for this role
    result = await db.execute(
        select(PromptVersion).where(
            PromptVersion.project_id == project_id,
            PromptVersion.role == role,
            PromptVersion.is_active == True,
        )
    )
    for prev in result.scalars().all():
        prev.is_active = False

    # Compute next version number
    count_result = await db.execute(
        select(PromptVersion).where(
            PromptVersion.project_id == project_id,
            PromptVersion.role == role,
        )
    )
    version_num = len(count_result.scalars().all()) + 1

    pv = PromptVersion(
        project_id=project_id,
        role=role,
        version=version_num,
        content=content,
        is_active=True,
        change_summary=change_summary,
        created_by=created_by,
    )
    db.add(pv)
    await db.flush()
    return pv


async def get_active_version(
    db: AsyncSession,
    project_id: uuid.UUID,
    role: str,
) -> PromptVersion | None:
    result = await db.execute(
        select(PromptVersion).where(
            PromptVersion.project_id == project_id,
            PromptVersion.role == role,
            PromptVersion.is_active == True,
        )
    )
    return result.scalar_one_or_none()


async def list_versions(
    db: AsyncSession,
    project_id: uuid.UUID,
    role: str | None = None,
) -> list[PromptVersion]:
    q = (
        select(PromptVersion)
        .where(PromptVersion.project_id == project_id)
        .order_by(PromptVersion.version.desc())
    )
    if role:
        q = q.where(PromptVersion.role == role)
    result = await db.execute(q)
    return list(result.scalars().all())


async def rollback_to_version(
    db: AsyncSession,
    version_id: uuid.UUID,
) -> PromptVersion | None:
    target = await db.get(PromptVersion, version_id)
    if target is None:
        return None

    # Deactivate current active
    result = await db.execute(
        select(PromptVersion).where(
            PromptVersion.project_id == target.project_id,
            PromptVersion.role == target.role,
            PromptVersion.is_active == True,
        )
    )
    for prev in result.scalars().all():
        prev.is_active = False

    target.is_active = True
    await db.flush()
    return target
