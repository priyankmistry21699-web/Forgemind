"""Repo connection schemas — request/response models.

FM-049: Pydantic models for external repo/workspace integration.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.repo_connection import RepoProvider, RepoConnectionStatus


class RepoConnectionRead(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    provider: RepoProvider
    repo_url: str
    repo_name: str
    default_branch: str
    status: RepoConnectionStatus
    credential_env_key: str | None
    config: dict | None
    workspace_path: str | None
    last_synced_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RepoConnectionList(BaseModel):
    items: list[RepoConnectionRead]
    total: int


class RepoConnectionCreate(BaseModel):
    provider: RepoProvider
    repo_url: str = Field(..., min_length=1, max_length=500)
    repo_name: str = Field(..., min_length=1, max_length=200)
    default_branch: str = "main"
    credential_env_key: str | None = None
    config: dict | None = None
    workspace_path: str | None = None


class RepoConnectionUpdate(BaseModel):
    default_branch: str | None = None
    credential_env_key: str | None = None
    config: dict | None = None
    workspace_path: str | None = None
    status: RepoConnectionStatus | None = None


class RepoBranchInfo(BaseModel):
    name: str
    is_default: bool
    last_commit: str | None


class RepoSyncResult(BaseModel):
    repo_id: uuid.UUID
    status: str
    message: str
    synced_at: datetime | None
