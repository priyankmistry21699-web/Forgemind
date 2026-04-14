"""SSO configuration service — CRUD for SSO provider configs.

FM-175: Manages SAML/OIDC provider configuration per workspace.
Does NOT implement live SSO flows (that requires python3-saml / authlib).
"""

import uuid

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sso_configuration import SSOConfiguration


async def create_sso_config(
    db: AsyncSession,
    *,
    workspace_id: uuid.UUID,
    provider_type: str,
    display_name: str,
    metadata_url: str | None = None,
    client_id: str | None = None,
    issuer_url: str | None = None,
    is_active: bool = True,
    auto_provision: bool = True,
    created_by: uuid.UUID | None = None,
) -> SSOConfiguration:
    """Create a new SSO provider configuration."""
    config = SSOConfiguration(
        workspace_id=workspace_id,
        provider_type=provider_type,
        display_name=display_name,
        metadata_url=metadata_url,
        client_id=client_id,
        issuer_url=issuer_url,
        is_active=is_active,
        auto_provision=auto_provision,
        created_by=created_by,
    )
    db.add(config)
    await db.flush()
    return config


async def list_sso_configs(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    *,
    offset: int = 0,
    limit: int = 50,
) -> tuple[list[SSOConfiguration], int]:
    """List SSO configurations for a workspace."""
    base = select(SSOConfiguration).filter(
        SSOConfiguration.workspace_id == workspace_id
    )

    count_q = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    items_q = (
        base.order_by(SSOConfiguration.created_at.desc()).offset(offset).limit(limit)
    )
    items = (await db.execute(items_q)).scalars().all()

    return list(items), total


async def get_sso_config(
    db: AsyncSession,
    config_id: uuid.UUID,
) -> SSOConfiguration | None:
    """Get a single SSO configuration by ID."""
    return await db.get(SSOConfiguration, config_id)


async def delete_sso_config(
    db: AsyncSession,
    config_id: uuid.UUID,
) -> bool:
    """Delete an SSO configuration."""
    config = await db.get(SSOConfiguration, config_id)
    if config is None:
        return False
    await db.delete(config)
    return True


async def toggle_sso_config(
    db: AsyncSession,
    config_id: uuid.UUID,
    is_active: bool,
) -> SSOConfiguration | None:
    """Activate or deactivate an SSO configuration."""
    config = await db.get(SSOConfiguration, config_id)
    if config is None:
        return None
    config.is_active = is_active
    db.add(config)
    return config
