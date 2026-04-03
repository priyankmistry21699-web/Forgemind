"""Reusable authorization dependency helpers for route-level RBAC.

FM-075: Central helpers that resolve ownership chains and enforce permissions.
"""

import uuid
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.run import Run
from app.models.task import Task


async def resolve_workspace_for_project(
    db: AsyncSession, project_id: uuid.UUID,
) -> uuid.UUID:
    """Resolve workspace_id from a project. Raises 404 if project not found."""
    result = await db.execute(
        select(Project.workspace_id).where(Project.id == project_id)
    )
    ws_id = result.scalar_one_or_none()
    if ws_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or not linked to a workspace",
        )
    return ws_id


async def resolve_project_for_run(
    db: AsyncSession, run_id: uuid.UUID,
) -> uuid.UUID:
    """Resolve project_id from a run. Raises 404 if run not found."""
    result = await db.execute(
        select(Run.project_id).where(Run.id == run_id)
    )
    proj_id = result.scalar_one_or_none()
    if proj_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found",
        )
    return proj_id


async def resolve_project_for_task(
    db: AsyncSession, task_id: uuid.UUID,
) -> uuid.UUID:
    """Resolve project_id from a task (task → run → project). Raises 404."""
    result = await db.execute(
        select(Run.project_id).join(Task, Task.run_id == Run.id).where(Task.id == task_id)
    )
    proj_id = result.scalar_one_or_none()
    if proj_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    return proj_id


async def resolve_project_for_entity(
    db: AsyncSession, model_class: Any, entity_id: uuid.UUID,
) -> uuid.UUID | None:
    """Generic resolver: fetch entity's project_id by primary key.

    Returns the project_id or None if the entity doesn't exist or
    the entity has no project_id set (nullable column).
    """
    result = await db.execute(
        select(model_class.project_id).where(model_class.id == entity_id)
    )
    return result.scalar_one_or_none()
