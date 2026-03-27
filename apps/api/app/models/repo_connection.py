"""RepoConnection model — external repository/workspace integration.

FM-049: Stores repository connections (GitHub, GitLab, etc.) for
project-level code execution, PR creation, and workspace access.
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
