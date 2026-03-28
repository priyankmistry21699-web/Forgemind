import uuid
from typing import Any

from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workspace import Workspace, WorkspaceStatus


async def create_workspace(
    db: AsyncSession,
    *,
    name: str,
    slug: str,
    owner_id: uuid.UUID,
    description: str | None = None,
    settings: dict | None = None,
) -> Workspace:
    ws = Workspace(
        name=name,
        slug=slug,
        description=description,
        owner_id=owner_id,
        settings=settings,
    )
    db.add(ws)
    await db.flush()
    await db.refresh(ws)
    return ws


async def get_workspace(
    db: AsyncSession, workspace_id: uuid.UUID
) -> Workspace | None:
    result = await db.execute(
        select(Workspace).where(Workspace.id == workspace_id)
    )
    return result.scalar_one_or_none()


async def get_workspace_by_slug(
    db: AsyncSession, slug: str
) -> Workspace | None:
    result = await db.execute(
        select(Workspace).where(Workspace.slug == slug)
    )
    return result.scalar_one_or_none()


async def list_workspaces(
    db: AsyncSession,
    owner_id: uuid.UUID,
    *,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[Workspace], int]:
    query = select(Workspace).where(Workspace.owner_id == owner_id)
    total = (await db.execute(
        select(sa_func.count()).select_from(query.subquery())
    )).scalar_one()
    result = await db.execute(
        query.order_by(Workspace.created_at.desc()).offset(offset).limit(limit)
    )
    return list(result.scalars().all()), total


async def update_workspace(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    **updates: Any,
) -> Workspace | None:
    ws = await get_workspace(db, workspace_id)
    if ws is None:
        return None
    allowed = {"name", "description", "status", "settings"}
    for k, v in updates.items():
        if k in allowed and v is not None:
            setattr(ws, k, v)
    await db.flush()
    await db.refresh(ws)
    return ws


async def delete_workspace(
    db: AsyncSession, workspace_id: uuid.UUID
) -> bool:
    ws = await get_workspace(db, workspace_id)
    if ws is None:
        return False
    await db.delete(ws)
    await db.flush()
    return True
