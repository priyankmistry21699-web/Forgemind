"""GitHub integration models — installation, repo link, events.

FM-151–160: GitHub & CI Integration Wave.
"""

import uuid
from datetime import datetime
import enum

from sqlalchemy import (
    DateTime,
    ForeignKey,
    LargeBinary,
    String,
    Boolean,
    Integer,
    Enum,
    func,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


# ---------------------------------------------------------------------------
# FM-151: GitHub App Installation
# ---------------------------------------------------------------------------


class GitHubInstallation(Base):
    """Stores a GitHub App installation record for an org/user account."""

    __tablename__ = "github_installations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    installation_id: Mapped[int] = mapped_column(
        Integer, unique=True, nullable=False, index=True
    )
    account_login: Mapped[str] = mapped_column(String(200), nullable=False)
    account_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="Organization"
    )
    connected_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    permissions: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # FM-151: Token management — encrypted access token + expiry
    access_token_encrypted: Mapped[bytes | None] = mapped_column(
        LargeBinary, nullable=True, default=None
    )
    token_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    repos: Mapped[list["RepositoryLink"]] = relationship(
        back_populates="installation", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<GitHubInstallation {self.account_login} #{self.installation_id}>"


# ---------------------------------------------------------------------------
# FM-151: Repository Link
# ---------------------------------------------------------------------------


class RepositoryLink(Base):
    """Maps a GitHub repo to a Forgemind project."""

    __tablename__ = "repository_links"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    installation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("github_installations.id", ondelete="CASCADE"),
        nullable=False,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    github_repo_id: Mapped[int] = mapped_column(Integer, nullable=False)
    full_name: Mapped[str] = mapped_column(String(300), nullable=False)
    default_branch: Mapped[str] = mapped_column(
        String(100), nullable=False, default="main"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    installation: Mapped["GitHubInstallation"] = relationship(back_populates="repos")

    def __repr__(self) -> str:
        return f"<RepositoryLink {self.full_name}>"


# ---------------------------------------------------------------------------
# FM-152: External Events (webhooks)
# ---------------------------------------------------------------------------


class ExternalEventSource(str, enum.Enum):
    GITHUB = "github"
    GITLAB = "gitlab"
    BITBUCKET = "bitbucket"


class ExternalEvent(Base):
    """Ingested webhook events (GitHub push, PR, issue, etc.)."""

    __tablename__ = "external_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    source: Mapped[ExternalEventSource] = mapped_column(
        Enum(ExternalEventSource), nullable=False, default=ExternalEventSource.GITHUB
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    delivery_id: Mapped[str | None] = mapped_column(
        String(100), unique=True, nullable=True
    )
    repository_link_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("repository_links.id", ondelete="SET NULL"),
        nullable=True,
    )
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    processed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<ExternalEvent {self.source.value}:{self.event_type}>"


# ---------------------------------------------------------------------------
# FM-153: Pull Request Links
# ---------------------------------------------------------------------------


class PRStatus(str, enum.Enum):
    OPEN = "open"
    CLOSED = "closed"
    MERGED = "merged"


class PullRequestLink(Base):
    """Links a GitHub PR to a Forgemind run/task."""

    __tablename__ = "pull_request_links"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    repository_link_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("repository_links.id", ondelete="CASCADE"),
        nullable=False,
    )
    run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("runs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    task_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="SET NULL"),
        nullable=True,
    )
    pr_number: Mapped[int] = mapped_column(Integer, nullable=False)
    pr_title: Mapped[str] = mapped_column(String(500), nullable=False)
    pr_url: Mapped[str] = mapped_column(String(500), nullable=False)
    head_branch: Mapped[str] = mapped_column(String(200), nullable=False)
    base_branch: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[PRStatus] = mapped_column(
        Enum(PRStatus), nullable=False, default=PRStatus.OPEN
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    merged_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self) -> str:
        return f"<PR #{self.pr_number} [{self.status.value}]>"


# ---------------------------------------------------------------------------
# FM-154: CI Pipeline Status
# ---------------------------------------------------------------------------


class CIPipelineStatus(str, enum.Enum):
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILURE = "failure"
    CANCELLED = "cancelled"


class CIPipelineRun(Base):
    """Tracks CI pipeline runs (GitHub Actions workflows)."""

    __tablename__ = "ci_pipeline_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    repository_link_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("repository_links.id", ondelete="CASCADE"),
        nullable=False,
    )
    run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("runs.id", ondelete="SET NULL"),
        nullable=True,
    )
    external_run_id: Mapped[int] = mapped_column(Integer, nullable=False)
    workflow_name: Mapped[str] = mapped_column(String(200), nullable=False)
    head_sha: Mapped[str] = mapped_column(String(60), nullable=False)
    branch: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[CIPipelineStatus] = mapped_column(
        Enum(CIPipelineStatus), nullable=False, default=CIPipelineStatus.QUEUED
    )
    conclusion: Mapped[str | None] = mapped_column(String(50), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<CIPipelineRun {self.workflow_name} [{self.status.value}]>"


# ---------------------------------------------------------------------------
# FM-155: Issue Links
# ---------------------------------------------------------------------------


class IssueLinkStatus(str, enum.Enum):
    OPEN = "open"
    CLOSED = "closed"


class IssueSyncDirection(str, enum.Enum):
    INBOUND = "inbound"    # GitHub → ForgeMind
    OUTBOUND = "outbound"  # ForgeMind → GitHub
    BOTH = "both"          # Bidirectional


class IssueLink(Base):
    """Links a GitHub issue to a Forgemind project/run."""

    __tablename__ = "issue_links"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    repository_link_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("repository_links.id", ondelete="CASCADE"),
        nullable=False,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("runs.id", ondelete="SET NULL"),
        nullable=True,
    )
    issue_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    issue_url: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[IssueLinkStatus] = mapped_column(
        Enum(IssueLinkStatus), nullable=False, default=IssueLinkStatus.OPEN
    )
    labels: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    # FM-155 Pass 7: Sync tracking
    sync_direction: Mapped[str | None] = mapped_column(
        String(20), nullable=True, default="inbound"
    )
    last_synced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<IssueLink #{self.issue_number}>"


# ---------------------------------------------------------------------------
# FM-157: Code Ownership
# ---------------------------------------------------------------------------


class CodeOwnership(Base):
    """Maps file patterns to owner user/team for code review routing."""

    __tablename__ = "code_ownerships"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    repository_link_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("repository_links.id", ondelete="CASCADE"),
        nullable=False,
    )
    file_pattern: Mapped[str] = mapped_column(String(500), nullable=False)
    owner_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    owner_team_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<CodeOwnership {self.file_pattern}>"
