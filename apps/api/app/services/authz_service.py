"""Authorization service — central permission helpers for RBAC.

FM-052: Role-based access control for workspace and project actions.
"""

import uuid
from enum import Enum

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.membership import (
    WorkspaceMember, WorkspaceRole,
    ProjectMember, ProjectRole,
)


class Action(str, Enum):
    """Actions that can be authorized."""
    # Workspace-level
    WORKSPACE_UPDATE = "workspace:update"
    WORKSPACE_DELETE = "workspace:delete"
    WORKSPACE_MANAGE_MEMBERS = "workspace:manage_members"
    WORKSPACE_MANAGE_GOVERNANCE = "workspace:manage_governance"
    WORKSPACE_MANAGE_CONNECTORS = "workspace:manage_connectors"
    WORKSPACE_MANAGE_REPOS = "workspace:manage_repos"
    WORKSPACE_CREATE_PROJECT = "workspace:create_project"
    WORKSPACE_VIEW = "workspace:view"

    # Project-level
    PROJECT_UPDATE = "project:update"
    PROJECT_DELETE = "project:delete"
    PROJECT_MANAGE_MEMBERS = "project:manage_members"
    PROJECT_VIEW = "project:view"
    PROJECT_RUN = "project:run"
    PROJECT_APPROVE = "project:approve"
    PROJECT_REVIEW = "project:review"


# ── Permission matrix ────────────────────────────────────────────

WORKSPACE_PERMISSIONS: dict[Action, set[WorkspaceRole]] = {
    Action.WORKSPACE_UPDATE: {WorkspaceRole.OWNER, WorkspaceRole.ADMIN},
    Action.WORKSPACE_DELETE: {WorkspaceRole.OWNER},
    Action.WORKSPACE_MANAGE_MEMBERS: {WorkspaceRole.OWNER, WorkspaceRole.ADMIN},
    Action.WORKSPACE_MANAGE_GOVERNANCE: {WorkspaceRole.OWNER, WorkspaceRole.ADMIN},
    Action.WORKSPACE_MANAGE_CONNECTORS: {WorkspaceRole.OWNER, WorkspaceRole.ADMIN, WorkspaceRole.OPERATOR},
    Action.WORKSPACE_MANAGE_REPOS: {WorkspaceRole.OWNER, WorkspaceRole.ADMIN, WorkspaceRole.OPERATOR},
    Action.WORKSPACE_CREATE_PROJECT: {WorkspaceRole.OWNER, WorkspaceRole.ADMIN, WorkspaceRole.OPERATOR},
    Action.WORKSPACE_VIEW: {WorkspaceRole.OWNER, WorkspaceRole.ADMIN, WorkspaceRole.OPERATOR, WorkspaceRole.REVIEWER, WorkspaceRole.VIEWER},
}

PROJECT_PERMISSIONS: dict[Action, set[ProjectRole]] = {
    Action.PROJECT_UPDATE: {ProjectRole.LEAD, ProjectRole.OPERATOR},
    Action.PROJECT_DELETE: {ProjectRole.LEAD},
    Action.PROJECT_MANAGE_MEMBERS: {ProjectRole.LEAD},
    Action.PROJECT_VIEW: {ProjectRole.LEAD, ProjectRole.OPERATOR, ProjectRole.REVIEWER, ProjectRole.VIEWER},
    Action.PROJECT_RUN: {ProjectRole.LEAD, ProjectRole.OPERATOR},
    Action.PROJECT_APPROVE: {ProjectRole.LEAD, ProjectRole.REVIEWER},
    Action.PROJECT_REVIEW: {ProjectRole.LEAD, ProjectRole.REVIEWER},
}


# ── Authorization checks ────────────────────────────────────────

async def get_workspace_role(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
) -> WorkspaceRole | None:
    """Get the user's role in a workspace, or None if not a member."""
    result = await db.execute(
        select(WorkspaceMember.role).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def get_project_role(
    db: AsyncSession,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
) -> ProjectRole | None:
    """Get the user's role in a project, or None if not a member."""
    result = await db.execute(
        select(ProjectMember.role).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def check_workspace_permission(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    action: Action,
) -> WorkspaceRole:
    """Check if user has permission for a workspace action.

    Returns the user's role if authorized.
    Raises 403 if not authorized, 404 if not a member.
    """
    role = await get_workspace_role(db, workspace_id, user_id)
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not a member of this workspace",
        )
    allowed_roles = WORKSPACE_PERMISSIONS.get(action, set())
    if role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions for {action.value}",
        )
    return role


async def check_project_permission(
    db: AsyncSession,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    action: Action,
) -> ProjectRole:
    """Check if user has permission for a project action.

    Returns the user's role if authorized.
    Raises 403 if not authorized, 404 if not a member.
    """
    role = await get_project_role(db, project_id, user_id)
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not a member of this project",
        )
    allowed_roles = PROJECT_PERMISSIONS.get(action, set())
    if role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions for {action.value}",
        )
    return role


def is_workspace_action_allowed(role: WorkspaceRole, action: Action) -> bool:
    """Pure check without DB — use when you already have the role."""
    return role in WORKSPACE_PERMISSIONS.get(action, set())


def is_project_action_allowed(role: ProjectRole, action: Action) -> bool:
    """Pure check without DB — use when you already have the role."""
    return role in PROJECT_PERMISSIONS.get(action, set())
