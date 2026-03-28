import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.membership import WorkspaceRole, ProjectRole


# ── Workspace Members ────────────────────────────────────────────

class WorkspaceMemberCreate(BaseModel):
    user_id: uuid.UUID
    role: WorkspaceRole = WorkspaceRole.VIEWER


class WorkspaceMemberUpdate(BaseModel):
    role: WorkspaceRole


class WorkspaceMemberRead(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    user_id: uuid.UUID
    role: WorkspaceRole
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WorkspaceMemberList(BaseModel):
    items: list[WorkspaceMemberRead]
    total: int


# ── Project Members ──────────────────────────────────────────────

class ProjectMemberCreate(BaseModel):
    user_id: uuid.UUID
    role: ProjectRole = ProjectRole.VIEWER
    is_approver: bool = False
    is_reviewer: bool = False


class ProjectMemberUpdate(BaseModel):
    role: ProjectRole | None = None
    is_approver: bool | None = None
    is_reviewer: bool | None = None


class ProjectMemberRead(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    user_id: uuid.UUID
    role: ProjectRole
    is_approver: bool
    is_reviewer: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectMemberList(BaseModel):
    items: list[ProjectMemberRead]
    total: int
