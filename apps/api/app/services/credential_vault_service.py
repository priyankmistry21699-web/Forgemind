"""Credential vault service — secret metadata management and resolution.

SECURITY: This service NEVER stores or returns raw secret values.
Secrets are resolved from environment variables at runtime.
Only metadata (name, env_key, status, scopes, expiry) is persisted.
"""

import os
import uuid
import logging
from typing import Any

from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.credential_vault import CredentialVault, SecretStatus
from app.models.connector import Connector

logger = logging.getLogger(__name__)


def _mask_secret(env_key: str) -> str:
    """Return a masked preview of a secret value from environment.

    Shows first 3 and last 4 characters only, e.g. 'sk-****abc1'.
    Returns '(not set)' if the env var is missing.
    """
    value = os.environ.get(env_key, "")
    if not value:
        return "(not set)"
    if len(value) <= 8:
        return value[:2] + "****"
    return value[:3] + "****" + value[-4:]


def _is_secret_set(env_key: str) -> bool:
    """Check if a secret environment variable is set and non-empty."""
    return bool(os.environ.get(env_key, "").strip())


async def create_credential(
    db: AsyncSession,
    *,
    name: str,
    env_key: str,
    connector_slug: str | None = None,
    project_id: uuid.UUID | None = None,
    description: str | None = None,
    secret_type: str = "api_key",
    scopes: list[str] | None = None,
    expires_at: Any = None,
    metadata: dict | None = None,
) -> CredentialVault:
    """Register a new credential in the vault."""
    connector_id = None
    if connector_slug:
        result = await db.execute(
            select(Connector).where(Connector.slug == connector_slug)
        )
        connector = result.scalar_one_or_none()
        if connector:
            connector_id = connector.id

    # Determine initial status
    status = SecretStatus.ACTIVE if _is_secret_set(env_key) else SecretStatus.MISSING

    credential = CredentialVault(
        name=name,
        description=description,
        env_key=env_key,
        connector_id=connector_id,
        project_id=project_id,
        status=status,
        secret_type=secret_type,
        scopes=scopes,
        expires_at=expires_at,
        metadata_=metadata,
    )
    db.add(credential)
    await db.flush()
    await db.refresh(credential)
    return credential


async def get_credential(
    db: AsyncSession,
    credential_id: uuid.UUID,
) -> CredentialVault | None:
    """Get a credential vault entry by ID."""
    result = await db.execute(
        select(CredentialVault).where(CredentialVault.id == credential_id)
    )
    return result.scalar_one_or_none()


async def list_credentials(
    db: AsyncSession,
    *,
    project_id: uuid.UUID | None = None,
    connector_id: uuid.UUID | None = None,
) -> tuple[list[CredentialVault], int]:
    """List credential vault entries with optional filters."""
    query = select(CredentialVault)

    if project_id is not None:
        query = query.where(
            (CredentialVault.project_id == project_id)
            | (CredentialVault.project_id.is_(None))
        )
    if connector_id is not None:
        query = query.where(CredentialVault.connector_id == connector_id)

    count_result = await db.execute(
        select(sa_func.count()).select_from(query.subquery())
    )
    total = count_result.scalar_one()

    result = await db.execute(query.order_by(CredentialVault.name))
    credentials = list(result.scalars().all())
    return credentials, total


async def update_credential(
    db: AsyncSession,
    credential_id: uuid.UUID,
    **kwargs: Any,
) -> CredentialVault | None:
    """Update credential metadata (not the secret value itself)."""
    credential = await get_credential(db, credential_id)
    if credential is None:
        return None

    for key, value in kwargs.items():
        if value is not None and hasattr(credential, key):
            if key == "metadata":
                credential.metadata_ = value
            else:
                setattr(credential, key, value)

    await db.flush()
    await db.refresh(credential)
    return credential


async def delete_credential(
    db: AsyncSession,
    credential_id: uuid.UUID,
) -> bool:
    """Delete a credential vault entry."""
    credential = await get_credential(db, credential_id)
    if credential is None:
        return False
    await db.delete(credential)
    await db.flush()
    return True


async def refresh_credential_statuses(db: AsyncSession) -> int:
    """Refresh the status of all credentials based on env var availability.

    Returns the number of credentials whose status changed.
    """
    result = await db.execute(select(CredentialVault))
    credentials = list(result.scalars().all())
    changed = 0

    for cred in credentials:
        if cred.status == SecretStatus.REVOKED:
            continue  # Don't auto-change revoked secrets

        is_set = _is_secret_set(cred.env_key)
        new_status = SecretStatus.ACTIVE if is_set else SecretStatus.MISSING

        # Check expiry
        if is_set and cred.expires_at:
            from datetime import datetime, timezone
            if cred.expires_at < datetime.now(timezone.utc):
                new_status = SecretStatus.EXPIRED

        if cred.status != new_status:
            cred.status = new_status
            changed += 1

    if changed:
        await db.flush()

    return changed


def build_credential_read(
    credential: CredentialVault,
    connector_slug: str | None = None,
) -> dict[str, Any]:
    """Build a credential read dict with masked preview and is_set flag."""
    return {
        "id": credential.id,
        "name": credential.name,
        "description": credential.description,
        "env_key": credential.env_key,
        "connector_id": credential.connector_id,
        "connector_slug": connector_slug,
        "project_id": credential.project_id,
        "status": credential.status,
        "secret_type": credential.secret_type,
        "scopes": credential.scopes,
        "expires_at": credential.expires_at,
        "last_rotated_at": credential.last_rotated_at,
        "is_set": _is_secret_set(credential.env_key),
        "masked_preview": _mask_secret(credential.env_key),
        "created_at": credential.created_at,
        "updated_at": credential.updated_at,
    }
