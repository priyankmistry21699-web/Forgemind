import uuid
from typing import Any

from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.membership import (
    WorkspaceMember, WorkspaceRole,
    ProjectMember, ProjectRole,
)


# ── Workspace members ────────────────────────────────────────────

async def add_workspace_member(
    db: AsyncSession,
    *,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    role: WorkspaceRole = WorkspaceRole.VIEWER,
) -> WorkspaceMember:
    member = WorkspaceMember(
        workspace_id=workspace_id,
        user_id=user_id,
        role=role,
    )
    db.add(member)
    await db.flush()
    await db.refresh(member)
    return member


async def get_workspace_member(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
) -> WorkspaceMember | None:
    result = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def list_workspace_members(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    *,
    limit: int = 100,
    offset: int = 0,
) -> tuple[list[WorkspaceMember], int]:
    query = select(WorkspaceMember).where(
        WorkspaceMember.workspace_id == workspace_id
    )
    total = (await db.execute(
        select(sa_func.count()).select_from(query.subquery())
    )).scalar_one()
    result = await db.execute(
        query.order_by(WorkspaceMember.created_at).offset(offset).limit(limit)
    )
    return list(result.scalars().all()), total


async def update_workspace_member_role(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    role: WorkspaceRole,
) -> WorkspaceMember | None:
    member = await get_workspace_member(db, workspace_id, user_id)
    if member is None:
        return None
    member.role = role
    await db.flush()
    await db.refresh(member)
    return member


async def remove_workspace_member(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
) -> bool:
    member = await get_workspace_member(db, workspace_id, user_id)
    if member is None:
        return False
    await db.delete(member)
    await db.flush()
    return True


# ── Project members ──────────────────────────────────────────────

async def add_project_member(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    role: ProjectRole = ProjectRole.VIEWER,
    is_approver: bool = False,
    is_reviewer: bool = False,
) -> ProjectMember:
    member = ProjectMember(
        project_id=project_id,
        user_id=user_id,
        role=role,
        is_approver=is_approver,
        is_reviewer=is_reviewer,
    )
    db.add(member)
    await db.flush()
    await db.refresh(member)
    return member


async def get_project_member(
    db: AsyncSession,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
) -> ProjectMember | None:
    result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def list_project_members(
    db: AsyncSession,
    project_id: uuid.UUID,
    *,
    limit: int = 100,
    offset: int = 0,
) -> tuple[list[ProjectMember], int]:
    query = select(ProjectMember).where(ProjectMember.project_id == project_id)
    total = (await db.execute(
        select(sa_func.count()).select_from(query.subquery())
    )).scalar_one()
    result = await db.execute(
        query.order_by(ProjectMember.created_at).offset(offset).limit(limit)
    )
    return list(result.scalars().all()), total


async def update_project_member(
    db: AsyncSession,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    **updates: Any,
) -> ProjectMember | None:
    member = await get_project_member(db, project_id, user_id)
    if member is None:
        return None
    for k, v in updates.items():
        if k in {"role", "is_approver", "is_reviewer"} and v is not None:
            setattr(member, k, v)
    await db.flush()
    await db.refresh(member)
    return member


async def remove_project_member(
    db: AsyncSession,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
) -> bool:
    member = await get_project_member(db, project_id, user_id)
    if member is None:
        return False
    await db.delete(member)
    await db.flush()
    return True
