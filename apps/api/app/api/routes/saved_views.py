"""Saved view routes — FM-144: Shared Views & Saved Filters."""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.auth import get_current_user_id
from app.schemas.saved_view import (
    SavedViewCreate,
    SavedViewUpdate,
    SavedViewRead,
    SavedViewList,
)
from app.services import saved_view_service
from app.services.authz_service import check_project_permission, Action

router = APIRouter()


@router.post(
    "/projects/{project_id}/views",
    response_model=SavedViewRead,
    status_code=201,
)
async def create_view(
    project_id: uuid.UUID,
    data: SavedViewCreate,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> SavedViewRead:
    await check_project_permission(db, project_id, user_id, Action.PROJECT_VIEW)
    view = await saved_view_service.create_saved_view(db, project_id, data, user_id)
    return SavedViewRead.model_validate(view)


@router.get("/projects/{project_id}/views", response_model=SavedViewList)
async def list_views(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> SavedViewList:
    await check_project_permission(db, project_id, user_id, Action.PROJECT_VIEW)
    items, total = await saved_view_service.list_saved_views(db, project_id, user_id)
    return SavedViewList(
        items=[SavedViewRead.model_validate(v) for v in items],
        total=total,
    )


@router.patch("/views/{view_id}", response_model=SavedViewRead)
async def update_view(
    view_id: uuid.UUID,
    data: SavedViewUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> SavedViewRead:
    view = await saved_view_service.update_saved_view(db, view_id, data, user_id)
    return SavedViewRead.model_validate(view)


@router.delete("/views/{view_id}", status_code=204)
async def delete_view(
    view_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> None:
    await saved_view_service.delete_saved_view(db, view_id, user_id)
