"""Credential vault routes — secret metadata CRUD and status checking."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.credential_vault import (
    CredentialVaultCreate,
    CredentialVaultRead,
    CredentialVaultUpdate,
    CredentialVaultList,
    CredentialCheckResult,
)
from app.services import credential_vault_service
from app.models.connector import Connector
from sqlalchemy import select

router = APIRouter()


async def _resolve_connector_slug(
    db: AsyncSession, connector_id: uuid.UUID | None
) -> str | None:
    """Helper to resolve connector slug from ID."""
    if connector_id is None:
        return None
    result = await db.execute(
        select(Connector).where(Connector.id == connector_id)
    )
    connector = result.scalar_one_or_none()
    return connector.slug if connector else None


@router.post(
    "/vault/credentials",
    response_model=CredentialVaultRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_credential(
    body: CredentialVaultCreate,
    db: AsyncSession = Depends(get_db),
) -> CredentialVaultRead:
    """Register a new credential in the vault."""
    credential = await credential_vault_service.create_credential(
        db,
        name=body.name,
        env_key=body.env_key,
        connector_slug=body.connector_slug,
        project_id=body.project_id,
        description=body.description,
        secret_type=body.secret_type,
        scopes=body.scopes,
        expires_at=body.expires_at,
        metadata=body.metadata,
    )
    slug = await _resolve_connector_slug(db, credential.connector_id)
    return CredentialVaultRead(
        **credential_vault_service.build_credential_read(credential, slug)
    )


@router.get("/vault/credentials", response_model=CredentialVaultList)
async def list_credentials(
    project_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
) -> CredentialVaultList:
    """List all credential vault entries."""
    credentials, total = await credential_vault_service.list_credentials(
        db, project_id=project_id
    )
    items = []
    for cred in credentials:
        slug = await _resolve_connector_slug(db, cred.connector_id)
        items.append(
            CredentialVaultRead(
                **credential_vault_service.build_credential_read(cred, slug)
            )
        )
    return CredentialVaultList(items=items, total=total)


@router.get(
    "/vault/credentials/{credential_id}",
    response_model=CredentialVaultRead,
)
async def get_credential(
    credential_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> CredentialVaultRead:
    """Get a single credential vault entry."""
    credential = await credential_vault_service.get_credential(db, credential_id)
    if credential is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credential not found",
        )
    slug = await _resolve_connector_slug(db, credential.connector_id)
    return CredentialVaultRead(
        **credential_vault_service.build_credential_read(credential, slug)
    )


@router.patch(
    "/vault/credentials/{credential_id}",
    response_model=CredentialVaultRead,
)
async def update_credential(
    credential_id: uuid.UUID,
    body: CredentialVaultUpdate,
    db: AsyncSession = Depends(get_db),
) -> CredentialVaultRead:
    """Update credential metadata."""
    update_data = body.model_dump(exclude_unset=True)
    credential = await credential_vault_service.update_credential(
        db, credential_id, **update_data
    )
    if credential is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credential not found",
        )
    slug = await _resolve_connector_slug(db, credential.connector_id)
    return CredentialVaultRead(
        **credential_vault_service.build_credential_read(credential, slug)
    )


@router.delete(
    "/vault/credentials/{credential_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_credential(
    credential_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a credential vault entry."""
    deleted = await credential_vault_service.delete_credential(db, credential_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credential not found",
        )


@router.post("/vault/credentials/refresh")
async def refresh_statuses(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Refresh all credential statuses based on current env vars."""
    changed = await credential_vault_service.refresh_credential_statuses(db)
    return {"changed": changed}
