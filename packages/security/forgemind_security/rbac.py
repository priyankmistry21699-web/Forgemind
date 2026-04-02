"""RBAC permission engine — pure policy definitions.

Defines action enums and permission matrices for workspace and project
scopes. These are stateless and DB-independent so they can be used
across services or in tests.
"""

from enum import Enum


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


# Roles are kept as string enums so the package doesn't depend on
# SQLAlchemy models.  Import your actual Role enum and use .value
# to compare, or pass strings directly.

class WorkspaceRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    OPERATOR = "operator"
    REVIEWER = "reviewer"
    VIEWER = "viewer"


class ProjectRole(str, Enum):
    LEAD = "lead"
    OPERATOR = "operator"
    REVIEWER = "reviewer"
    VIEWER = "viewer"


# ── Permission matrices ──────────────────────────────────────────

WORKSPACE_PERMISSIONS: dict[Action, set[WorkspaceRole]] = {
    Action.WORKSPACE_UPDATE: {WorkspaceRole.OWNER, WorkspaceRole.ADMIN},
    Action.WORKSPACE_DELETE: {WorkspaceRole.OWNER},
    Action.WORKSPACE_MANAGE_MEMBERS: {WorkspaceRole.OWNER, WorkspaceRole.ADMIN},
    Action.WORKSPACE_MANAGE_GOVERNANCE: {WorkspaceRole.OWNER, WorkspaceRole.ADMIN},
    Action.WORKSPACE_MANAGE_CONNECTORS: {WorkspaceRole.OWNER, WorkspaceRole.ADMIN, WorkspaceRole.OPERATOR},
    Action.WORKSPACE_MANAGE_REPOS: {WorkspaceRole.OWNER, WorkspaceRole.ADMIN, WorkspaceRole.OPERATOR},
    Action.WORKSPACE_CREATE_PROJECT: {WorkspaceRole.OWNER, WorkspaceRole.ADMIN, WorkspaceRole.OPERATOR},
    Action.WORKSPACE_VIEW: {WorkspaceRole.OWNER, WorkspaceRole.ADMIN, WorkspaceRole.OPERATOR, WorkspaceRole.REVIEWER, WorkspaceRole.VIEWER},
    Action.WORKSPACE_MANAGE_SECRETS: {WorkspaceRole.OWNER, WorkspaceRole.ADMIN},
    Action.WORKSPACE_VIEW_AUDIT: {WorkspaceRole.OWNER, WorkspaceRole.ADMIN, WorkspaceRole.REVIEWER},
}

PROJECT_PERMISSIONS: dict[Action, set[ProjectRole]] = {
    Action.PROJECT_UPDATE: {ProjectRole.LEAD, ProjectRole.OPERATOR},
    Action.PROJECT_DELETE: {ProjectRole.LEAD},
    Action.PROJECT_MANAGE_MEMBERS: {ProjectRole.LEAD},
    Action.PROJECT_VIEW: {ProjectRole.LEAD, ProjectRole.OPERATOR, ProjectRole.REVIEWER, ProjectRole.VIEWER},
    Action.PROJECT_RUN: {ProjectRole.LEAD, ProjectRole.OPERATOR},
    Action.PROJECT_APPROVE: {ProjectRole.LEAD, ProjectRole.REVIEWER},
    Action.PROJECT_REVIEW: {ProjectRole.LEAD, ProjectRole.REVIEWER},
    Action.PROJECT_EXECUTE_CODE: {ProjectRole.LEAD, ProjectRole.OPERATOR},
    Action.PROJECT_MANAGE_KNOWLEDGE: {ProjectRole.LEAD, ProjectRole.OPERATOR},
    Action.PROJECT_MANAGE_ESCALATION: {ProjectRole.LEAD},
}


# ── Pure checks ──────────────────────────────────────────────────

def is_workspace_action_allowed(role: WorkspaceRole, action: Action) -> bool:
    """Pure check — use when you already have the role."""
    return role in WORKSPACE_PERMISSIONS.get(action, set())


def is_project_action_allowed(role: ProjectRole, action: Action) -> bool:
    """Pure check — use when you already have the role."""
    return role in PROJECT_PERMISSIONS.get(action, set())
