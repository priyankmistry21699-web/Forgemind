"""Authorization service — central permission helpers for RBAC.

FM-052: Role-based access control for workspace and project actions.
"""

import uuid
from enum import Enum

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.membership import (
    WorkspaceMember,
    WorkspaceRole,
    ProjectMember,
    ProjectRole,
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
    WORKSPACE_MANAGE_SECRETS = "workspace:manage_secrets"
    WORKSPACE_VIEW_AUDIT = "workspace:view_audit"

    # Project-level
    PROJECT_UPDATE = "project:update"
    PROJECT_DELETE = "project:delete"
    PROJECT_MANAGE_MEMBERS = "project:manage_members"
    PROJECT_VIEW = "project:view"
    PROJECT_RUN = "project:run"
    PROJECT_APPROVE = "project:approve"
    PROJECT_REVIEW = "project:review"
    PROJECT_EXECUTE_CODE = "project:execute_code"
    PROJECT_MANAGE_KNOWLEDGE = "project:manage_knowledge"
    PROJECT_MANAGE_ESCALATION = "project:manage_escalation"
    PROJECT_MANAGE_ARCHITECTURE = "project:manage_architecture"


# ── Permission matrix ────────────────────────────────────────────

WORKSPACE_PERMISSIONS: dict[Action, set[WorkspaceRole]] = {
    Action.WORKSPACE_UPDATE: {WorkspaceRole.OWNER, WorkspaceRole.ADMIN},
    Action.WORKSPACE_DELETE: {WorkspaceRole.OWNER},
    Action.WORKSPACE_MANAGE_MEMBERS: {WorkspaceRole.OWNER, WorkspaceRole.ADMIN},
    Action.WORKSPACE_MANAGE_GOVERNANCE: {WorkspaceRole.OWNER, WorkspaceRole.ADMIN},
    Action.WORKSPACE_MANAGE_CONNECTORS: {
        WorkspaceRole.OWNER,
        WorkspaceRole.ADMIN,
        WorkspaceRole.OPERATOR,
    },
    Action.WORKSPACE_MANAGE_REPOS: {
        WorkspaceRole.OWNER,
        WorkspaceRole.ADMIN,
        WorkspaceRole.OPERATOR,
    },
    Action.WORKSPACE_CREATE_PROJECT: {
        WorkspaceRole.OWNER,
        WorkspaceRole.ADMIN,
        WorkspaceRole.OPERATOR,
    },
    Action.WORKSPACE_VIEW: {
        WorkspaceRole.OWNER,
        WorkspaceRole.ADMIN,
        WorkspaceRole.OPERATOR,
        WorkspaceRole.REVIEWER,
        WorkspaceRole.VIEWER,
    },
    Action.WORKSPACE_MANAGE_SECRETS: {WorkspaceRole.OWNER, WorkspaceRole.ADMIN},
    Action.WORKSPACE_VIEW_AUDIT: {
        WorkspaceRole.OWNER,
        WorkspaceRole.ADMIN,
        WorkspaceRole.REVIEWER,
    },
}

PROJECT_PERMISSIONS: dict[Action, set[ProjectRole]] = {
    Action.PROJECT_UPDATE: {ProjectRole.LEAD, ProjectRole.OPERATOR},
    Action.PROJECT_DELETE: {ProjectRole.LEAD},
    Action.PROJECT_MANAGE_MEMBERS: {ProjectRole.LEAD},
    Action.PROJECT_VIEW: {
        ProjectRole.LEAD,
        ProjectRole.OPERATOR,
        ProjectRole.REVIEWER,
        ProjectRole.VIEWER,
    },
    Action.PROJECT_RUN: {ProjectRole.LEAD, ProjectRole.OPERATOR},
    Action.PROJECT_APPROVE: {ProjectRole.LEAD, ProjectRole.REVIEWER},
    Action.PROJECT_REVIEW: {ProjectRole.LEAD, ProjectRole.REVIEWER},
    Action.PROJECT_EXECUTE_CODE: {ProjectRole.LEAD, ProjectRole.OPERATOR},
    Action.PROJECT_MANAGE_KNOWLEDGE: {ProjectRole.LEAD, ProjectRole.OPERATOR},
    Action.PROJECT_MANAGE_ESCALATION: {ProjectRole.LEAD},
    Action.PROJECT_MANAGE_ARCHITECTURE: {ProjectRole.LEAD, ProjectRole.OPERATOR},
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


# ── Role introspection (FM-172) ──────────────────────────────────


def get_workspace_role_permissions(role: WorkspaceRole) -> list[str]:
    """Return all actions permitted for a workspace role."""
    return sorted(
        action.value
        for action, allowed_roles in WORKSPACE_PERMISSIONS.items()
        if role in allowed_roles
    )


def get_project_role_permissions(role: ProjectRole) -> list[str]:
    """Return all actions permitted for a project role."""
    return sorted(
        action.value
        for action, allowed_roles in PROJECT_PERMISSIONS.items()
        if role in allowed_roles
    )


async def get_user_permissions(
    db: AsyncSession,
    *,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    project_id: uuid.UUID | None = None,
) -> dict:
    """Return the user's roles and computed permissions for a workspace/project."""
    ws_role = await get_workspace_role(db, workspace_id, user_id)
    ws_actions = get_workspace_role_permissions(ws_role) if ws_role else []

    proj_role = None
    proj_actions: list[str] = []
    if project_id:
        proj_role = await get_project_role(db, project_id, user_id)
        proj_actions = get_project_role_permissions(proj_role) if proj_role else []

    return {
        "workspace_role": ws_role.value if ws_role else None,
        "workspace_actions": ws_actions,
        "project_role": proj_role.value if proj_role else None,
        "project_actions": proj_actions,
    }


# ── FM-172: Custom Role Management ──────────────────────────────


async def create_custom_role(
    db: AsyncSession,
    *,
    workspace_id: uuid.UUID,
    name: str,
    scope: str = "project",
    description: str | None = None,
    permissions: list[str],
    created_by: uuid.UUID,
):
    """Create a custom role for a workspace (FM-172)."""
    from app.models.enterprise_governance import CustomRole

    # Validate permission strings
    valid_actions = {a.value for a in Action}
    invalid = set(permissions) - valid_actions
    if invalid:
        raise ValueError(f"Invalid permissions: {', '.join(sorted(invalid))}")

    role = CustomRole(
        workspace_id=workspace_id,
        name=name,
        scope=scope,
        description=description,
        permissions=permissions,
        created_by=created_by,
    )
    db.add(role)
    await db.flush()
    await db.refresh(role)
    return role


async def list_custom_roles(
    db: AsyncSession,
    workspace_id: uuid.UUID,
):
    """List all custom roles for a workspace."""
    from app.models.enterprise_governance import CustomRole

    result = await db.execute(
        select(CustomRole)
        .where(CustomRole.workspace_id == workspace_id, CustomRole.is_active == True)  # noqa: E712
        .order_by(CustomRole.name)
    )
    return list(result.scalars().all())


async def get_custom_role(
    db: AsyncSession,
    role_id: uuid.UUID,
):
    """Get a single custom role by ID."""
    from app.models.enterprise_governance import CustomRole

    result = await db.execute(select(CustomRole).where(CustomRole.id == role_id))
    return result.scalar_one_or_none()


async def update_custom_role(
    db: AsyncSession,
    role_id: uuid.UUID,
    *,
    name: str | None = None,
    description: str | None = None,
    permissions: list[str] | None = None,
    is_active: bool | None = None,
):
    """Update a custom role."""
    from app.models.enterprise_governance import CustomRole

    result = await db.execute(select(CustomRole).where(CustomRole.id == role_id))
    role = result.scalar_one_or_none()
    if role is None:
        raise ValueError(f"Custom role {role_id} not found")

    if name is not None:
        role.name = name
    if description is not None:
        role.description = description
    if permissions is not None:
        valid_actions = {a.value for a in Action}
        invalid = set(permissions) - valid_actions
        if invalid:
            raise ValueError(f"Invalid permissions: {', '.join(sorted(invalid))}")
        role.permissions = permissions
    if is_active is not None:
        role.is_active = is_active

    await db.flush()
    await db.refresh(role)
    return role
