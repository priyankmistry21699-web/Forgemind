import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth_stub import get_current_user_id
from app.db.session import get_db
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectRead, ProjectList
from app.services import project_service

router = APIRouter()


@router.post("/projects", response_model=ProjectRead, status_code=201)
async def create_project(
    data: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    owner_id: uuid.UUID = Depends(get_current_user_id),
) -> ProjectRead:
    project = await project_service.create_project(db, data, owner_id=owner_id)
    return ProjectRead.model_validate(project)


@router.get("/projects", response_model=ProjectList)
async def list_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    owner_id: uuid.UUID = Depends(get_current_user_id),
) -> ProjectList:
    projects, total = await project_service.list_projects(
        db, owner_id=owner_id, skip=skip, limit=limit
    )
    return ProjectList(
        items=[ProjectRead.model_validate(p) for p in projects],
        total=total,
    )


@router.get("/projects/{project_id}", response_model=ProjectRead)
async def get_project(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> ProjectRead:
    project = await project_service.get_project(db, project_id)
    return ProjectRead.model_validate(project)


@router.patch("/projects/{project_id}", response_model=ProjectRead)
async def update_project(
    project_id: uuid.UUID,
    data: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
) -> ProjectRead:
    project = await project_service.update_project(db, project_id, data)
    return ProjectRead.model_validate(project)
