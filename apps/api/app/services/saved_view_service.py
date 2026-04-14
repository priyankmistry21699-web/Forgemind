"""Saved view service — CRUD for FM-144."""

import uuid

from fastapi import HTTPException
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.saved_view import SavedView, ViewVisibility
from app.schemas.saved_view import SavedViewCreate, SavedViewUpdate


async def create_saved_view(
    db: AsyncSession,
    project_id: uuid.UUID,
    data: SavedViewCreate,
    creator_id: uuid.UUID,
) -> SavedView:
    view = SavedView(
        project_id=project_id,
        creator_id=creator_id,
        name=data.name,
        entity_type=data.entity_type,
        filter_json=data.filter_json,
        visibility=data.visibility,
    )
    db.add(view)
    await db.flush()
    await db.refresh(view)
    return view


async def list_saved_views(
    db: AsyncSession,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
) -> tuple[list[SavedView], int]:
    """Return views the user can see: their own + team-shared."""
    base = select(SavedView).where(
        SavedView.project_id == project_id,
        or_(
            SavedView.creator_id == user_id,
            SavedView.visibility == ViewVisibility.TEAM,
        ),
    )
    count_q = select(func.count()).select_from(base.subquery())
    total_result = await db.execute(count_q)
    total = total_result.scalar_one()

    result = await db.execute(base.order_by(SavedView.created_at.desc()))
    return list(result.scalars().all()), total


async def update_saved_view(
    db: AsyncSession,
    view_id: uuid.UUID,
    data: SavedViewUpdate,
    user_id: uuid.UUID,
) -> SavedView:
    view = await db.get(SavedView, view_id)
    if view is None:
        raise HTTPException(status_code=404, detail="Saved view not found")
    if view.creator_id != user_id:
        raise HTTPException(status_code=403, detail="Only the creator can update this view")
    if data.name is not None:
        view.name = data.name
    if data.filter_json is not None:
        view.filter_json = data.filter_json
    if data.visibility is not None:
        view.visibility = data.visibility
    await db.flush()
    await db.refresh(view)
    return view


async def delete_saved_view(
    db: AsyncSession,
    view_id: uuid.UUID,
    user_id: uuid.UUID,
) -> None:
    view = await db.get(SavedView, view_id)
    if view is None:
        raise HTTPException(status_code=404, detail="Saved view not found")
    if view.creator_id != user_id:
        raise HTTPException(status_code=403, detail="Only the creator can delete this view")
    await db.delete(view)
    await db.flush()
