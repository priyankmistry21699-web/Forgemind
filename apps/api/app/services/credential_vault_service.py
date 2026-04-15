"""Credential vault service — secret metadata management and resolution.

SECURITY: This service NEVER returns raw secret values in API responses.
Secrets can be stored AES-256-GCM encrypted in DB (FM-179) or resolved
from environment variables at runtime.
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


def _mask_value(value: str) -> str:
    """Mask a secret value for display — shows first 3 and last 4 chars."""
    if not value:
        return "(not set)"
    if len(value) <= 8:
        return value[:2] + "****"
    return value[:3] + "****" + value[-4:]


def _mask_secret(env_key: str, credential: "CredentialVault | None" = None) -> str:
    """Return a masked preview of a secret value.

    Checks encrypted_value first (FM-179), then falls back to env var.
    """
    if credential and credential.encrypted_value:
        try:
            from app.services.encryption_service import decrypt
            plaintext = decrypt(credential.encrypted_value)
            return _mask_value(plaintext)
        except Exception:
            return "(decrypt error)"
    return _mask_value(os.environ.get(env_key, ""))


def _is_secret_set(env_key: str, credential: "CredentialVault | None" = None) -> bool:
    """Check if a secret is available (encrypted or env var)."""
    if credential and credential.encrypted_value:
        return True
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
    secret_value: str | None = None,
) -> CredentialVault:
    """Register a new credential in the vault.

    If secret_value is provided, it is encrypted with AES-256-GCM (FM-179)
    and stored in encrypted_value. Otherwise falls back to env var resolution.
    """
    connector_id = None
    if connector_slug:
        result = await db.execute(
            select(Connector).where(Connector.slug == connector_slug)
        )
        connector = result.scalar_one_or_none()
        if connector:
            connector_id = connector.id

    # Encrypt the secret value if provided (FM-179)
    encrypted_value = None
    if secret_value:
        from app.services.encryption_service import encrypt
        encrypted_value = encrypt(secret_value)

    # Determine initial status
    has_secret = encrypted_value is not None or bool(os.environ.get(env_key, "").strip())
    status = SecretStatus.ACTIVE if has_secret else SecretStatus.MISSING

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
        encrypted_value=encrypted_value,
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


# ── FM-179: Secret resolution & rotation lifecycle ───────────────


async def resolve_secret(
    db: AsyncSession,
    credential_id: uuid.UUID,
    *,
    allowed_scopes: list[str] | None = None,
) -> str | None:
    """Resolve the actual secret value for a credential.

    Priority: encrypted_value (AES-256-GCM) → env var fallback.
    Optionally enforces scope restrictions.
    """
    result = await db.execute(
        select(CredentialVault).where(CredentialVault.id == credential_id)
    )
    cred = result.scalar_one_or_none()
    if cred is None:
        return None

    # Scope enforcement
    if allowed_scopes is not None and cred.scopes:
        cred_scopes = set(cred.scopes) if isinstance(cred.scopes, list) else set()
        if not cred_scopes.intersection(allowed_scopes):
            return None  # Scope mismatch — deny access

    # Check status
    if cred.status in ("EXPIRED", "REVOKED"):
        return None

    # FM-179: Prefer encrypted value if present
    if cred.encrypted_value:
        try:
            from app.services.encryption_service import decrypt
            return decrypt(cred.encrypted_value)
        except Exception:
            logger.warning("Failed to decrypt secret %s", credential_id)
            return None

    return os.environ.get(cred.env_key)


async def rotate_credential(
    db: AsyncSession,
    credential_id: uuid.UUID,
) -> CredentialVault | None:
    """Mark a credential as rotated — updates last_rotated_at timestamp.

    Actual secret rotation (generating new API keys, etc.) happens
    externally. This tracks the rotation event for audit purposes.
    """
    result = await db.execute(
        select(CredentialVault).filter(CredentialVault.id == credential_id)
    )
    cred = result.scalar_one_or_none()
    if cred is None:
        return None

    cred.last_rotated_at = sa_func.now()
    cred.status = "ACTIVE"  # Reset status after rotation
    db.add(cred)
    return cred


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


async def store_encrypted_secret(
    db: AsyncSession,
    credential_id: uuid.UUID,
    secret_value: str,
) -> CredentialVault | None:
    """Encrypt and store a secret value for an existing credential (FM-179)."""
    credential = await get_credential(db, credential_id)
    if credential is None:
        return None
    from app.services.encryption_service import encrypt
    credential.encrypted_value = encrypt(secret_value)
    credential.status = SecretStatus.ACTIVE
    await db.flush()
    await db.refresh(credential)
    return credential


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

        is_set = _is_secret_set(cred.env_key, cred)
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
        "is_set": _is_secret_set(credential.env_key, credential),
        "masked_preview": _mask_secret(credential.env_key, credential),
        "created_at": credential.created_at,
        "updated_at": credential.updated_at,
    }
