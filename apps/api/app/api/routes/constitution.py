"""FM-102/103: Constitution routes — CRUD for project constitutions."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user_id
from app.db.session import get_db
from app.schemas.constitution import ConstitutionRead, ConstitutionCreate, ConstitutionUpdate
from app.services import constitution_service
from app.services.authz_service import check_project_permission, Action

router = APIRouter()


@router.get(
    "/projects/{project_id}/constitution",
    response_model=ConstitutionRead,
)
async def get_constitution(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Get the constitution for a project."""
    await check_project_permission(db, project_id, user_id, Action.PROJECT_VIEW)
    constitution = await constitution_service.get_constitution(db, project_id)
    if constitution is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No constitution found for this project",
        )
    return constitution


@router.put(
    "/projects/{project_id}/constitution",
    response_model=ConstitutionRead,
)
async def upsert_constitution(
    project_id: uuid.UUID,
    data: ConstitutionCreate,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Create or update the constitution for a project."""
    await check_project_permission(db, project_id, user_id, Action.PROJECT_UPDATE)
    return await constitution_service.create_or_update_constitution(
        db, project_id, data
    )


@router.patch(
    "/projects/{project_id}/constitution",
    response_model=ConstitutionRead,
)
async def update_constitution(
    project_id: uuid.UUID,
    data: ConstitutionUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Partially update the constitution for a project."""
    await check_project_permission(db, project_id, user_id, Action.PROJECT_UPDATE)
    return await constitution_service.create_or_update_constitution(
        db, project_id, data
    )


@router.delete(
    "/projects/{project_id}/constitution",
    status_code=204,
)
async def delete_constitution(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Delete the constitution for a project."""
    await check_project_permission(db, project_id, user_id, Action.PROJECT_UPDATE)
    deleted = await constitution_service.delete_constitution(db, project_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No constitution found for this project",
        )
