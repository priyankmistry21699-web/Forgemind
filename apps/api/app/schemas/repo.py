"""Repo connection schemas — request/response models.

FM-049: Pydantic models for external repo/workspace integration.
FM-061: Extended with sync metadata, branch targets, linked paths.
FM-066: Added branch strategy fields.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.repo_connection import (
    RepoProvider, RepoConnectionStatus, SyncStatus, BranchMode,
)


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
    # FM-061: sync metadata
    base_branch: str | None
    target_branch: str | None
    linked_paths: list | None
    last_sync_status: SyncStatus | None
    last_sync_error: str | None
    last_synced_commit: str | None
    provider_metadata: dict | None
    # FM-066: branch strategy
    branch_mode: BranchMode | None
    target_branch_template: str | None
    last_generated_branch: str | None

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
    # FM-061
    base_branch: str | None = None
    target_branch: str | None = None
    linked_paths: list | None = None
    provider_metadata: dict | None = None
    # FM-066
    branch_mode: BranchMode | None = None
    target_branch_template: str | None = None


class RepoConnectionUpdate(BaseModel):
    default_branch: str | None = None
    credential_env_key: str | None = None
    config: dict | None = None
    workspace_path: str | None = None
    status: RepoConnectionStatus | None = None
    # FM-061
    base_branch: str | None = None
    target_branch: str | None = None
    linked_paths: list | None = None
    provider_metadata: dict | None = None
    # FM-066
    branch_mode: BranchMode | None = None
    target_branch_template: str | None = None


class RepoBranchInfo(BaseModel):
    name: str
    is_default: bool
    last_commit: str | None


class RepoSyncResult(BaseModel):
    repo_id: uuid.UUID
    status: str
    message: str
    synced_at: datetime | None


# FM-062: File tree / content schemas
class FileTreeEntry(BaseModel):
    name: str
    path: str
    is_directory: bool
    size: int | None = None


class FileTreeResult(BaseModel):
    connection_id: uuid.UUID
    base_path: str
    entries: list[FileTreeEntry]


class FileContentResult(BaseModel):
    connection_id: uuid.UUID
    path: str
    content: str
    size: int
    language: str | None = None


class RepoSyncMetadata(BaseModel):
    """FM-061: Sync status summary."""
    connection_id: uuid.UUID
    last_sync_status: SyncStatus | None
    last_sync_error: str | None
    last_synced_commit: str | None
    last_synced_at: datetime | None
