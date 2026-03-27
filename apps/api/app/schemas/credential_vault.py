"""Credential vault schemas — Pydantic models for secret metadata API."""

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.credential_vault import SecretStatus


class CredentialVaultCreate(BaseModel):
    """Create a new credential vault entry."""
    name: str
    description: str | None = None
    env_key: str
    connector_slug: str | None = None
    project_id: uuid.UUID | None = None
    secret_type: str = "api_key"
    scopes: list[str] | None = None
    expires_at: datetime | None = None
    metadata: dict | None = None


class CredentialVaultRead(BaseModel):
    """Read a credential vault entry — never exposes raw secret values."""
    id: uuid.UUID
    name: str
    description: str | None
    env_key: str
    connector_id: uuid.UUID | None
    connector_slug: str | None
    project_id: uuid.UUID | None
    status: SecretStatus
    secret_type: str
    scopes: list[str] | None
    expires_at: datetime | None
    last_rotated_at: datetime | None
    is_set: bool  # Whether the env var is currently set
    masked_preview: str  # e.g. "sk-****abc1"
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CredentialVaultUpdate(BaseModel):
    """Update credential vault metadata (not the secret itself)."""
    name: str | None = None
    description: str | None = None
    scopes: list[str] | None = None
    expires_at: datetime | None = None
    status: SecretStatus | None = None
    metadata: dict | None = None


class CredentialVaultList(BaseModel):
    items: list[CredentialVaultRead]
    total: int


class CredentialCheckResult(BaseModel):
    """Result of checking if a credential is available."""
    env_key: str
    is_set: bool
    status: SecretStatus
    connector_slug: str | None
