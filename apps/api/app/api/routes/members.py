import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth_stub import get_current_user_id
from app.db.session import get_db
from app.schemas.membership import (
    WorkspaceMemberCreate, WorkspaceMemberUpdate, WorkspaceMemberRead, WorkspaceMemberList,
    ProjectMemberCreate, ProjectMemberUpdate, ProjectMemberRead, ProjectMemberList,
)
from app.services import membership_service

router = APIRouter()


# ── Workspace Members ────────────────────────────────────────────

@router.post(
    "/workspaces/{workspace_id}/members",
    response_model=WorkspaceMemberRead,
    status_code=201,
)
async def add_workspace_member(
    workspace_id: uuid.UUID,
    data: WorkspaceMemberCreate,
    db: AsyncSession = Depends(get_db),
) -> WorkspaceMemberRead:
    existing = await membership_service.get_workspace_member(
        db, workspace_id, data.user_id,
    )
    if existing:
        raise HTTPException(status_code=409, detail="Member already exists")
    member = await membership_service.add_workspace_member(
        db, workspace_id=workspace_id, user_id=data.user_id, role=data.role,
    )
    return WorkspaceMemberRead.model_validate(member)


@router.get(
    "/workspaces/{workspace_id}/members",
    response_model=WorkspaceMemberList,
)
async def list_workspace_members(
    workspace_id: uuid.UUID,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> WorkspaceMemberList:
    items, total = await membership_service.list_workspace_members(
        db, workspace_id, limit=limit, offset=offset,
    )
    return WorkspaceMemberList(
        items=[WorkspaceMemberRead.model_validate(m) for m in items],
        total=total,
    )


@router.patch(
    "/workspaces/{workspace_id}/members/{user_id}",
    response_model=WorkspaceMemberRead,
)
async def update_workspace_member(
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    data: WorkspaceMemberUpdate,
    db: AsyncSession = Depends(get_db),
) -> WorkspaceMemberRead:
    member = await membership_service.update_workspace_member_role(
        db, workspace_id, user_id, data.role,
    )
    if member is None:
        raise HTTPException(status_code=404, detail="Member not found")
    return WorkspaceMemberRead.model_validate(member)


@router.delete(
    "/workspaces/{workspace_id}/members/{user_id}",
    status_code=204,
)
async def remove_workspace_member(
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    removed = await membership_service.remove_workspace_member(
        db, workspace_id, user_id,
    )
    if not removed:
        raise HTTPException(status_code=404, detail="Member not found")


# ── Project Members ──────────────────────────────────────────────

@router.post(
    "/projects/{project_id}/members",
    response_model=ProjectMemberRead,
    status_code=201,
)
async def add_project_member(
    project_id: uuid.UUID,
    data: ProjectMemberCreate,
    db: AsyncSession = Depends(get_db),
) -> ProjectMemberRead:
    existing = await membership_service.get_project_member(
        db, project_id, data.user_id,
    )
    if existing:
        raise HTTPException(status_code=409, detail="Member already exists")
    member = await membership_service.add_project_member(
        db, project_id=project_id, user_id=data.user_id, role=data.role,
        is_approver=data.is_approver, is_reviewer=data.is_reviewer,
    )
    return ProjectMemberRead.model_validate(member)


@router.get(
    "/projects/{project_id}/members",
    response_model=ProjectMemberList,
)
async def list_project_members(
    project_id: uuid.UUID,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> ProjectMemberList:
    items, total = await membership_service.list_project_members(
        db, project_id, limit=limit, offset=offset,
    )
    return ProjectMemberList(
        items=[ProjectMemberRead.model_validate(m) for m in items],
        total=total,
    )


@router.patch(
    "/projects/{project_id}/members/{user_id}",
    response_model=ProjectMemberRead,
)
async def update_project_member(
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    data: ProjectMemberUpdate,
    db: AsyncSession = Depends(get_db),
) -> ProjectMemberRead:
    member = await membership_service.update_project_member(
        db, project_id, user_id, **data.model_dump(exclude_unset=True),
    )
    if member is None:
        raise HTTPException(status_code=404, detail="Member not found")
    return ProjectMemberRead.model_validate(member)


@router.delete(
    "/projects/{project_id}/members/{user_id}",
    status_code=204,
)
async def remove_project_member(
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    removed = await membership_service.remove_project_member(
        db, project_id, user_id,
    )
    if not removed:
        raise HTTPException(status_code=404, detail="Member not found")
