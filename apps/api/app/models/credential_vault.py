"""CredentialVault model — encrypted secret metadata for connector credentials.

Stores metadata about secrets (name, scope, expiry, connector link) without
ever persisting raw secret values in the database. Actual secret values are
resolved from environment variables at runtime.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import String, Text, DateTime, Enum, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class SecretStatus(str, enum.Enum):
    ACTIVE = "active"           # Secret is set and usable
    EXPIRED = "expired"         # Secret has expired, needs rotation
    MISSING = "missing"         # Secret env var not found
    REVOKED = "revoked"         # Secret manually revoked


class CredentialVault(Base):
    __tablename__ = "credential_vault"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Environment variable key that holds the actual secret value
    env_key: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)

    # Connector linkage — which connector this credential is for
    connector_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("connectors.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Project scoping — None means global (available to all projects)
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    status: Mapped[SecretStatus] = mapped_column(
        Enum(SecretStatus, name="secret_status"),
        default=SecretStatus.MISSING,
        nullable=False,
    )

    # Metadata — non-sensitive info about the secret
    secret_type: Mapped[str] = mapped_column(
        String(50), default="api_key", nullable=False
    )  # api_key, oauth_token, password, certificate, etc.
    scopes: Mapped[list | None] = mapped_column(JSON, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_rotated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    metadata_: Mapped[dict | None] = mapped_column(
        "metadata", JSON, nullable=True
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

    # Relationships
    connector: Mapped["Connector | None"] = relationship()  # noqa: F821

    def __repr__(self) -> str:
        return f"<CredentialVault {self.name} ({self.status.value})>"
