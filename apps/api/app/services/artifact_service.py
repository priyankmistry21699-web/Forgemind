"""Artifact service — CRUD operations for execution artifacts."""

import uuid

from fastapi import HTTPException, status
from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.artifact import Artifact
from app.schemas.artifact import ArtifactCreate, ArtifactUpdate


async def create_artifact(
    db: AsyncSession,
    project_id: uuid.UUID,
    data: ArtifactCreate,
) -> Artifact:
    artifact = Artifact(
        title=data.title,
        artifact_type=data.artifact_type,
        content=data.content,
        meta=data.meta,
        version=1,
        project_id=project_id,
        run_id=data.run_id,
        task_id=data.task_id,
        created_by=data.created_by,
        # FM-063: code artifact mapping
        repo_connection_id=data.repo_connection_id,
        target_path=data.target_path,
        target_module=data.target_module,
        change_type=data.change_type,
        target_metadata=data.target_metadata,
    )
    db.add(artifact)
    await db.flush()
    await db.refresh(artifact)
    return artifact


async def get_artifact(db: AsyncSession, artifact_id: uuid.UUID) -> Artifact:
    result = await db.execute(select(Artifact).where(Artifact.id == artifact_id))
    artifact = result.scalar_one_or_none()
    if artifact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Artifact not found"
        )
    return artifact


async def list_artifacts_by_project(
    db: AsyncSession,
    project_id: uuid.UUID,
    *,
    run_id: uuid.UUID | None = None,
    task_id: uuid.UUID | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[Artifact], int]:
    query = select(Artifact).where(Artifact.project_id == project_id)
    if run_id is not None:
        query = query.where(Artifact.run_id == run_id)
    if task_id is not None:
        query = query.where(Artifact.task_id == task_id)

    count_result = await db.execute(
        select(sa_func.count()).select_from(query.subquery())
    )
    total = count_result.scalar_one()

    result = await db.execute(
        query.order_by(Artifact.created_at.desc()).limit(limit).offset(offset)
    )
    artifacts = list(result.scalars().all())
    return artifacts, total


async def update_artifact(
    db: AsyncSession,
    artifact_id: uuid.UUID,
    data: ArtifactUpdate,
) -> Artifact:
    artifact = await get_artifact(db, artifact_id)
    update_data = data.model_dump(exclude_unset=True)

    if update_data:
        # Bump version on content changes
        if "content" in update_data:
            artifact.version += 1
        for field, value in update_data.items():
            setattr(artifact, field, value)

    await db.flush()
    await db.refresh(artifact)
    return artifact


async def delete_artifact(db: AsyncSession, artifact_id: uuid.UUID) -> None:
    artifact = await get_artifact(db, artifact_id)
    await db.delete(artifact)
    await db.flush()
