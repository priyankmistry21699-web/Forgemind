"""FM-114/115: Project Template routes — list, get, and manage templates."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
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
from app.services import template_inheritance_service

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
    items, total = await project_template_service.list_templates(db, category=category)
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


# ---------------------------------------------------------------------------
# FM-164: Deep Clone & Template Versioning
# ---------------------------------------------------------------------------


class _CloneBody(BaseModel):
    new_slug: str
    new_name: str | None = None


class _VersionBody(BaseModel):
    updates: dict


@router.post("/templates/{template_id}/clone", status_code=status.HTTP_201_CREATED)
async def clone_template(
    template_id: uuid.UUID,
    body: _CloneBody,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Deep-clone a template with all nested configs (FM-164)."""
    try:
        clone = await template_inheritance_service.clone_template(
            db, template_id, new_slug=body.new_slug, new_name=body.new_name,
        )
        await db.commit()
        return ProjectTemplateRead.model_validate(clone)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/templates/{template_id}/version", status_code=status.HTTP_201_CREATED)
async def create_version(
    template_id: uuid.UUID,
    body: _VersionBody,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Create a new version of a template with field overrides (FM-164)."""
    try:
        versioned = await template_inheritance_service.create_template_version(
            db, template_id, updates=body.updates,
        )
        await db.commit()
        return ProjectTemplateRead.model_validate(versioned)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
