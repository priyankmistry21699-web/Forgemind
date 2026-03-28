"""RepoConnection model — external repository/workspace integration.

FM-049: Stores repository connections (GitHub, GitLab, etc.) for
project-level code execution, PR creation, and workspace access.
FM-061: Extended with richer sync metadata, branch targets, and linked paths.
FM-066: Added branch_mode and target_branch_template for branch strategy.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import String, Text, DateTime, Enum, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base


class RepoProvider(str, enum.Enum):
    GITHUB = "github"
    GITLAB = "gitlab"
    BITBUCKET = "bitbucket"
    LOCAL = "local"


class RepoConnectionStatus(str, enum.Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    PENDING = "pending"


class SyncStatus(str, enum.Enum):
    IDLE = "idle"
    SYNCING = "syncing"
    SUCCESS = "success"
    FAILED = "failed"


class BranchMode(str, enum.Enum):
    DIRECT = "direct"
    FEATURE_BRANCH = "feature_branch"
    REVIEW_BRANCH = "review_branch"


class RepoConnection(Base):
    __tablename__ = "repo_connections"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Repository info
    provider: Mapped[RepoProvider] = mapped_column(
        Enum(RepoProvider, name="repo_provider"),
        nullable=False,
    )
    repo_url: Mapped[str] = mapped_column(String(500), nullable=False)
    repo_name: Mapped[str] = mapped_column(String(200), nullable=False)
    default_branch: Mapped[str] = mapped_column(
        String(100), default="main", nullable=False
    )

    # FM-061: Extended branch / sync metadata
    base_branch: Mapped[str | None] = mapped_column(String(200), nullable=True)
    target_branch: Mapped[str | None] = mapped_column(String(200), nullable=True)
    linked_paths: Mapped[list | None] = mapped_column(JSON, nullable=True)
    last_sync_status: Mapped[SyncStatus | None] = mapped_column(
        Enum(SyncStatus, name="sync_status"), nullable=True
    )
    last_sync_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_synced_commit: Mapped[str | None] = mapped_column(String(100), nullable=True)
    provider_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # FM-066: Branch strategy
    branch_mode: Mapped[BranchMode | None] = mapped_column(
        Enum(BranchMode, name="branch_mode"), nullable=True
    )
    target_branch_template: Mapped[str | None] = mapped_column(
        String(200), nullable=True
    )
    last_generated_branch: Mapped[str | None] = mapped_column(
        String(200), nullable=True
    )

    # Connection status
    status: Mapped[RepoConnectionStatus] = mapped_column(
        Enum(RepoConnectionStatus, name="repo_connection_status"),
        default=RepoConnectionStatus.PENDING,
        nullable=False,
        index=True,
    )

    # Credential reference (env var key for the token)
    credential_env_key: Mapped[str | None] = mapped_column(
        String(200), nullable=True
    )

    # Configuration
    config: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Workspace path (for local repos)
    workspace_path: Mapped[str | None] = mapped_column(String(500), nullable=True)

    last_synced_at: Mapped[datetime | None] = mapped_column(
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

    def __repr__(self) -> str:
        return f"<RepoConnection {self.repo_name} ({self.provider.value})>"
