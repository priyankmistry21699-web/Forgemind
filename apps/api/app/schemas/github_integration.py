"""Pydantic schemas for GitHub integration models.

FM-151–160.
"""

import uuid
from datetime import datetime
from pydantic import BaseModel


# ---------------------------------------------------------------------------
# FM-151: GitHub Installation
# ---------------------------------------------------------------------------


class GitHubInstallationCreate(BaseModel):
    installation_id: int
    account_login: str
    account_type: str = "Organization"
    permissions: dict | None = None


class GitHubInstallationRead(BaseModel):
    id: uuid.UUID
    installation_id: int
    account_login: str
    account_type: str
    is_active: bool
    permissions: dict | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# FM-151: Repository Link
# ---------------------------------------------------------------------------


class RepositoryLinkCreate(BaseModel):
    installation_id: uuid.UUID
    project_id: uuid.UUID
    github_repo_id: int
    full_name: str
    default_branch: str = "main"


class RepositoryLinkRead(BaseModel):
    id: uuid.UUID
    installation_id: uuid.UUID
    project_id: uuid.UUID
    github_repo_id: int
    full_name: str
    default_branch: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# FM-153: Pull Request Link
# ---------------------------------------------------------------------------


class PullRequestLinkCreate(BaseModel):
    repository_link_id: uuid.UUID
    run_id: uuid.UUID | None = None
    task_id: uuid.UUID | None = None
    pr_number: int
    pr_title: str
    pr_url: str
    head_branch: str
    base_branch: str


class PullRequestLinkRead(BaseModel):
    id: uuid.UUID
    repository_link_id: uuid.UUID
    run_id: uuid.UUID | None = None
    task_id: uuid.UUID | None = None
    pr_number: int
    pr_title: str
    pr_url: str
    head_branch: str
    base_branch: str
    status: str
    created_at: datetime
    merged_at: datetime | None = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# FM-154: CI Pipeline
# ---------------------------------------------------------------------------


class CIPipelineRunRead(BaseModel):
    id: uuid.UUID
    repository_link_id: uuid.UUID
    run_id: uuid.UUID | None = None
    external_run_id: int
    workflow_name: str
    head_sha: str
    branch: str
    status: str
    conclusion: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# FM-155: Issue Link
# ---------------------------------------------------------------------------


class IssueLinkCreate(BaseModel):
    repository_link_id: uuid.UUID
    project_id: uuid.UUID
    run_id: uuid.UUID | None = None
    issue_number: int
    title: str
    issue_url: str
    labels: list | None = None


class IssueLinkRead(BaseModel):
    id: uuid.UUID
    repository_link_id: uuid.UUID
    project_id: uuid.UUID
    run_id: uuid.UUID | None = None
    issue_number: int
    title: str
    issue_url: str
    status: str
    labels: list | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# FM-157: Code Ownership
# ---------------------------------------------------------------------------


class CodeOwnershipCreate(BaseModel):
    repository_link_id: uuid.UUID
    file_pattern: str
    owner_user_id: uuid.UUID | None = None
    owner_team_name: str | None = None


class CodeOwnershipRead(BaseModel):
    id: uuid.UUID
    repository_link_id: uuid.UUID
    file_pattern: str
    owner_user_id: uuid.UUID | None = None
    owner_team_name: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
