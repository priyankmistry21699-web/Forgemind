import uuid

from fastapi import HTTPException, status
from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.membership import ProjectMember, ProjectRole
from app.schemas.project import ProjectCreate, ProjectUpdate


async def create_project(
    db: AsyncSession, data: ProjectCreate, owner_id: uuid.UUID
) -> Project:
    project = Project(
        name=data.name,
        description=data.description,
        owner_id=owner_id,
        workspace_id=data.workspace_id,
        template_id=data.template_id,
    )
    db.add(project)
    await db.flush()
    await db.refresh(project)
    # Auto-enroll the creator as project lead
    lead = ProjectMember(
        project_id=project.id,
        user_id=owner_id,
        role=ProjectRole.LEAD,
    )
    db.add(lead)
    await db.flush()

    # FM-115: Apply template defaults if a template was specified
    if data.template_id:
        from app.services import project_template_service, template_inheritance_service

        template = await project_template_service.get_template(db, data.template_id)
        if template and template.is_active:
            await template_inheritance_service.apply_template_to_project(
                db, project, template
            )

    # FM-144: Seed default views on project creation
    from app.services.saved_view_service import seed_default_views

    await seed_default_views(db, project.id, owner_id)

    return project


async def get_project(db: AsyncSession, project_id: uuid.UUID) -> Project:
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    return project


async def list_projects(
    db: AsyncSession,
    owner_id: uuid.UUID,
    skip: int = 0,
    limit: int = 20,
) -> tuple[list[Project], int]:
    query = select(Project).where(Project.owner_id == owner_id)

    # Total count
    count_result = await db.execute(
        select(sa_func.count()).select_from(query.subquery())
    )
    total = count_result.scalar_one()

    # Paginated results
    result = await db.execute(
        query.order_by(Project.created_at.desc()).offset(skip).limit(limit)
    )
    projects = list(result.scalars().all())
    return projects, total


async def update_project(
    db: AsyncSession, project_id: uuid.UUID, data: ProjectUpdate
) -> Project:
    project = await get_project(db, project_id)
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)
    await db.flush()
    await db.refresh(project)
    return project
