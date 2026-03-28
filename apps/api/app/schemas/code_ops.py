import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.code_ops import (
    PatchStatus, ReviewDecision, PRDraftStatus,
    RepoActionType, SandboxStatus,
)


# ── Code Mappings (FM-061) ───────────────────────────────────────

class CodeMappingCreate(BaseModel):
    artifact_id: uuid.UUID
    file_path: str = Field(..., min_length=1, max_length=1000)
    language: str | None = None
    metadata_: dict | None = None


class CodeMappingRead(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    artifact_id: uuid.UUID
    file_path: str
    language: str | None
    metadata_: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}


class CodeMappingList(BaseModel):
    items: list[CodeMappingRead]
    total: int


# ── Patch Proposals (FM-062) ─────────────────────────────────────

class PatchProposalCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: str | None = None
    diff_content: str
    target_branch: str = "main"
    rationale: str | None = None


class PatchProposalUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    description: str | None = None
    diff_content: str | None = None
    target_branch: str | None = None
    status: PatchStatus | None = None
    rationale: str | None = None


class PatchProposalRead(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    title: str
    description: str | None
    diff_content: str
    target_branch: str
    status: PatchStatus
    rationale: str | None
    created_by: uuid.UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PatchProposalList(BaseModel):
    items: list[PatchProposalRead]
    total: int


# ── Change Reviews (FM-063/066) ──────────────────────────────────

class ChangeReviewCreate(BaseModel):
    decision: ReviewDecision
    comment: str | None = None


class ChangeReviewRead(BaseModel):
    id: uuid.UUID
    patch_id: uuid.UUID
    reviewer_id: uuid.UUID
    decision: ReviewDecision
    comment: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ChangeReviewList(BaseModel):
    items: list[ChangeReviewRead]
    total: int


# ── Branch Strategies (FM-064) ───────────────────────────────────

class BranchStrategyCreate(BaseModel):
    base_branch: str = "main"
    branch_pattern: str = "forgemind/{task_id}"
    auto_create_branch: bool = True
    pr_target_branch: str = "main"
    config: dict | None = None


class BranchStrategyUpdate(BaseModel):
    base_branch: str | None = None
    branch_pattern: str | None = None
    auto_create_branch: bool | None = None
    pr_target_branch: str | None = None
    config: dict | None = None


class BranchStrategyRead(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    base_branch: str
    branch_pattern: str
    auto_create_branch: bool
    pr_target_branch: str
    config: dict | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BranchStrategyList(BaseModel):
    items: list[BranchStrategyRead]
    total: int


# ── PR Drafts (FM-065) ──────────────────────────────────────────

class PRDraftCreate(BaseModel):
    patch_id: uuid.UUID | None = None
    title: str = Field(..., min_length=1, max_length=500)
    body: str | None = None
    source_branch: str
    target_branch: str = "main"
    reviewers: list | None = None
    checklist: list | None = None
    linked_artifacts: list | None = None


class PRDraftUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    body: str | None = None
    source_branch: str | None = None
    target_branch: str | None = None
    status: PRDraftStatus | None = None
    reviewers: list | None = None
    checklist: list | None = None
    linked_artifacts: list | None = None


class PRDraftRead(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    patch_id: uuid.UUID | None
    title: str
    body: str | None
    source_branch: str
    target_branch: str
    status: PRDraftStatus
    reviewers: list | None
    checklist: list | None
    linked_artifacts: list | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PRDraftList(BaseModel):
    items: list[PRDraftRead]
    total: int


# ── Repo Action Approvals (FM-067) ──────────────────────────────

class RepoActionApprovalCreate(BaseModel):
    action_type: RepoActionType
    reason: str | None = None
    context: dict | None = None


class RepoActionDecision(BaseModel):
    status: str = Field(..., pattern="^(approved|rejected)$")
    decision_comment: str | None = None


class RepoActionApprovalRead(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    action_type: RepoActionType
    status: str
    reason: str | None
    context: dict | None
    decided_by: uuid.UUID | None
    decision_comment: str | None
    decided_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RepoActionApprovalList(BaseModel):
    items: list[RepoActionApprovalRead]
    total: int


# ── Sandbox Executions (FM-068/069) ─────────────────────────────

class SandboxExecutionCreate(BaseModel):
    command: str = Field(..., min_length=1)
    task_id: uuid.UUID | None = None
    patch_id: uuid.UUID | None = None
    working_directory: str | None = None
    environment: dict | None = None
    timeout_seconds: int = 60


class SandboxExecutionRead(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    task_id: uuid.UUID | None
    patch_id: uuid.UUID | None
    command: str
    working_directory: str | None
    environment: dict | None
    timeout_seconds: int
    status: SandboxStatus
    stdout: str | None
    stderr: str | None
    exit_code: int | None
    duration_ms: int | None
    created_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class SandboxExecutionList(BaseModel):
    items: list[SandboxExecutionRead]
    total: int
