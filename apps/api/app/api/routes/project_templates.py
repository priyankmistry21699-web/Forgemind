"""FM-114/115: Project Template routes — list, get, and manage templates."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user_id
from app.db.session import get_db
from app.schemas.project_template import (
    ProjectTemplateCreate,
    ProjectTemplateList,
    ProjectTemplateRead,
    ProjectTemplateUpdate,
)
from app.services import project_template_service

router = APIRouter()


@router.get(
    "/templates",
    response_model=ProjectTemplateList,
)
async def list_templates(
    category: str | None = None,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """List available project templates."""
    items, total = await project_template_service.list_templates(
        db, category=category
    )
    return ProjectTemplateList(items=items, total=total)


@router.get(
    "/templates/{template_id}",
    response_model=ProjectTemplateRead,
)
async def get_template(
    template_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Get a single template by ID."""
    template = await project_template_service.get_template(db, template_id)
    if template is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found",
        )
    return template


@router.post(
    "/templates",
    response_model=ProjectTemplateRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_template(
    data: ProjectTemplateCreate,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Create a new custom template."""
    try:
        return await project_template_service.create_template(db, data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )


@router.patch(
    "/templates/{template_id}",
    response_model=ProjectTemplateRead,
)
async def update_template(
    template_id: uuid.UUID,
    data: ProjectTemplateUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Update a template."""
    try:
        return await project_template_service.update_template(db, template_id, data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
