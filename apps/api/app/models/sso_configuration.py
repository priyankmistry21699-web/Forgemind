"""SSO configuration model — external authentication provider setup.

FM-175: Stores SAML/OIDC IdP configuration per workspace.
Actual protocol flows (SAML assertion validation, OIDC token exchange)
require external libraries and are not implemented in this pass.
This model provides the configuration infrastructure for future integration.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base


class SSOProviderType(str, enum.Enum):
    SAML = "saml"
    OIDC = "oidc"


class SSOConfiguration(Base):
    """SSO provider configuration per workspace.

    Stores IdP metadata and connection details. Does NOT perform
    live SAML/OIDC flows — that requires python3-saml / authlib.
    """

    __tablename__ = "sso_configurations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider_type: Mapped[SSOProviderType] = mapped_column(String(20), nullable=False)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)

    # SAML fields
    metadata_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    entity_id: Mapped[str | None] = mapped_column(String(500), nullable=True)
    sso_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    certificate: Mapped[str | None] = mapped_column(Text, nullable=True)

    # OIDC fields
    client_id: Mapped[str | None] = mapped_column(String(300), nullable=True)
    # client_secret stored via CredentialVault env_key reference, NOT plaintext
    client_secret_vault_ref: Mapped[str | None] = mapped_column(
        String(200), nullable=True
    )
    issuer_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    scopes: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Enforcement
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    auto_provision: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )  # JIT user provisioning on first SSO login

    # Metadata
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
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
        return f"<SSOConfiguration {self.display_name} ({self.provider_type})>"
