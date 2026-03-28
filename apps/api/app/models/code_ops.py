"""Code operations models — repository and code execution workflows.

FM-061: Code mapping (artifact-to-file)
FM-062: Patch proposals
FM-063: Inline review
FM-064: Patch proposal engine enhancements (target_files, format, readiness)
FM-065: Change review workspace (file-level annotations)
FM-066: Change reviews / branch strategies
FM-067: Repo action approvals
FM-068: Sandbox execution
FM-069: Execution results with runner safety
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import String, Text, Integer, Boolean, DateTime, Enum, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base


# ── Enums ────────────────────────────────────────────────────────

class PatchStatus(str, enum.Enum):
    DRAFT = "draft"
    PROPOSED = "proposed"
    APPROVED = "approved"
    REJECTED = "rejected"
    APPLIED = "applied"
    SUPERSEDED = "superseded"


class PatchFormat(str, enum.Enum):
    """FM-064: Format of the diff content."""
    UNIFIED = "unified"
    SIDE_BY_SIDE = "side_by_side"
    RAW = "raw"


class ReadinessState(str, enum.Enum):
    """FM-064: How ready a patch is for application."""
    INCOMPLETE = "incomplete"
    NEEDS_REVIEW = "needs_review"
    READY = "ready"
    BLOCKED = "blocked"


class ReviewDecision(str, enum.Enum):
    APPROVE = "approve"
    REQUEST_CHANGES = "request_changes"
    COMMENT = "comment"


class PRDraftStatus(str, enum.Enum):
    DRAFT = "draft"
    READY = "ready"
    SUBMITTED = "submitted"
    MERGED = "merged"
    CLOSED = "closed"


class RepoActionType(str, enum.Enum):
    PATCH_APPLY = "patch_apply"
    BRANCH_CREATE = "branch_create"
    PR_CREATE = "pr_create"
    PUSH = "push"
    MERGE = "merge"


class SandboxStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


# ── Models ───────────────────────────────────────────────────────

class CodeMapping(Base):
    """FM-061: Maps artifacts to files in the repo."""
    __tablename__ = "code_mappings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    artifact_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("artifacts.id", ondelete="CASCADE"),
        nullable=False,
    )
    file_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    language: Mapped[str | None] = mapped_column(String(50), nullable=True)
    metadata_: Mapped[dict | None] = mapped_column(
        "metadata", JSON, nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class PatchProposal(Base):
    """FM-062/064: AI-generated code patches for review."""
    __tablename__ = "patch_proposals"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    diff_content: Mapped[str] = mapped_column(Text, nullable=False)
    target_branch: Mapped[str] = mapped_column(
        String(200), default="main", nullable=False
    )
    status: Mapped[PatchStatus] = mapped_column(
        Enum(PatchStatus, name="patch_status"),
        default=PatchStatus.DRAFT,
        nullable=False,
        index=True,
    )
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    # FM-064: Enhanced patch proposal fields
    target_files: Mapped[list | None] = mapped_column(JSON, nullable=True)
    patch_format: Mapped[PatchFormat | None] = mapped_column(
        Enum(PatchFormat, name="patch_format"), nullable=True
    )
    proposed_by_agent: Mapped[str | None] = mapped_column(String(200), nullable=True)
    readiness_state: Mapped[ReadinessState | None] = mapped_column(
        Enum(ReadinessState, name="readiness_state"), nullable=True
    )
    linked_artifact_ids: Mapped[list | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class ChangeReview(Base):
    """FM-063/065/066: Review comments on patches with file-level annotations."""
    __tablename__ = "change_reviews"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    patch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("patch_proposals.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    reviewer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    decision: Mapped[ReviewDecision] = mapped_column(
        Enum(ReviewDecision, name="review_decision"),
        nullable=False,
    )
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    # FM-065: File-level review annotations
    file_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    line_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    line_end: Mapped[int | None] = mapped_column(Integer, nullable=True)
    suggestion: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class BranchStrategy(Base):
    """FM-064: Per-project branch configuration."""
    __tablename__ = "branch_strategies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    base_branch: Mapped[str] = mapped_column(
        String(200), default="main", nullable=False
    )
    branch_pattern: Mapped[str] = mapped_column(
        String(200), default="forgemind/{task_id}", nullable=False
    )
    auto_create_branch: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    pr_target_branch: Mapped[str] = mapped_column(
        String(200), default="main", nullable=False
    )
    config: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class PRDraft(Base):
    """FM-065: Generated pull request drafts."""
    __tablename__ = "pr_drafts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    patch_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("patch_proposals.id", ondelete="SET NULL"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_branch: Mapped[str] = mapped_column(String(200), nullable=False)
    target_branch: Mapped[str] = mapped_column(
        String(200), default="main", nullable=False
    )
    status: Mapped[PRDraftStatus] = mapped_column(
        Enum(PRDraftStatus, name="pr_draft_status"),
        default=PRDraftStatus.DRAFT,
        nullable=False,
        index=True,
    )
    reviewers: Mapped[list | None] = mapped_column(JSON, nullable=True)
    checklist: Mapped[list | None] = mapped_column(JSON, nullable=True)
    linked_artifacts: Mapped[list | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class RepoActionApproval(Base):
    """FM-067: Approval gates for repo-level actions."""
    __tablename__ = "repo_action_approvals"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    action_type: Mapped[RepoActionType] = mapped_column(
        Enum(RepoActionType, name="repo_action_type"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20), default="pending", nullable=False, index=True
    )
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    context: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    decided_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    decision_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class SandboxExecution(Base):
    """FM-068/069: Sandboxed code execution with safety controls."""
    __tablename__ = "sandbox_executions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    task_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    patch_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    command: Mapped[str] = mapped_column(Text, nullable=False)
    working_directory: Mapped[str | None] = mapped_column(String(500), nullable=True)
    environment: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=60, nullable=False)

    status: Mapped[SandboxStatus] = mapped_column(
        Enum(SandboxStatus, name="sandbox_status"),
        default=SandboxStatus.QUEUED,
        nullable=False,
        index=True,
    )
    stdout: Mapped[str | None] = mapped_column(Text, nullable=True)
    stderr: Mapped[str | None] = mapped_column(Text, nullable=True)
    exit_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # FM-069: Safety / runner fields
    approval_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    allowed_commands: Mapped[list | None] = mapped_column(JSON, nullable=True)
    resource_limits: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    isolated: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self) -> str:
        return f"<SandboxExecution {self.id} status={self.status.value}>"
