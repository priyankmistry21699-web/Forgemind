"""SSO configuration service — CRUD + validation + OIDC URL builder + enforcement.

FM-175: Manages SAML/OIDC provider configuration per workspace.
Includes config validation, OIDC authorization URL construction,
SSO enforcement checks, and JIT provisioning readiness.
Live protocol flows (SAML assertion validation, OIDC token exchange)
require external libraries (python3-saml / authlib).
"""

import uuid
import secrets
from urllib.parse import urlencode

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sso_configuration import SSOConfiguration, SSOProviderType


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


# ---------------------------------------------------------------------------
# FM-175: Config validation
# ---------------------------------------------------------------------------


def validate_sso_config(config: SSOConfiguration) -> list[str]:
    """Validate that an SSO configuration has all required fields.

    Returns a list of error messages. Empty list = valid.
    """
    errors: list[str] = []

    if not config.display_name or not config.display_name.strip():
        errors.append("display_name is required")

    ptype = config.provider_type
    if isinstance(ptype, str):
        ptype = ptype.lower()

    if ptype in ("saml", SSOProviderType.SAML):
        # SAML requires either metadata_url (for auto-config) or manual fields
        if not config.metadata_url and not config.sso_url:
            errors.append("SAML requires metadata_url or sso_url")
        if not config.metadata_url and not config.entity_id:
            errors.append("SAML requires metadata_url or entity_id")
    elif ptype in ("oidc", SSOProviderType.OIDC):
        if not config.client_id:
            errors.append("OIDC requires client_id")
        if not config.issuer_url:
            errors.append("OIDC requires issuer_url")
    else:
        errors.append(f"Unknown provider_type: {ptype}")

    return errors


# ---------------------------------------------------------------------------
# FM-175: OIDC authorization URL builder
# ---------------------------------------------------------------------------


def build_oidc_authorize_url(
    config: SSOConfiguration,
    redirect_uri: str,
    *,
    state: str | None = None,
    nonce: str | None = None,
) -> str | None:
    """Build the OIDC authorization redirect URL from config (FM-175).

    This constructs a standard OAuth 2.0 / OpenID Connect authorization
    request URL. No external library needed — it's standard URL construction.
    Returns None if config is not OIDC or is missing required fields.
    """
    ptype = config.provider_type
    if isinstance(ptype, str):
        ptype = ptype.lower()
    if ptype not in ("oidc", SSOProviderType.OIDC):
        return None

    if not config.issuer_url or not config.client_id:
        return None

    # Standard OIDC authorize endpoint: {issuer}/authorize
    # (In production, fetched from .well-known/openid-configuration)
    issuer = config.issuer_url.rstrip("/")
    authorize_endpoint = f"{issuer}/authorize"

    scopes = config.scopes if isinstance(config.scopes, list) else ["openid", "profile", "email"]
    scope_str = " ".join(scopes) if scopes else "openid profile email"

    params = {
        "response_type": "code",
        "client_id": config.client_id,
        "redirect_uri": redirect_uri,
        "scope": scope_str,
        "state": state or secrets.token_urlsafe(32),
        "nonce": nonce or secrets.token_urlsafe(32),
    }

    return f"{authorize_endpoint}?{urlencode(params)}"


# ---------------------------------------------------------------------------
# FM-175: SSO enforcement check
# ---------------------------------------------------------------------------


async def get_active_sso_for_workspace(
    db: AsyncSession,
    workspace_id: uuid.UUID,
) -> SSOConfiguration | None:
    """Get the active SSO configuration for a workspace, if any."""
    result = await db.execute(
        select(SSOConfiguration).where(
            SSOConfiguration.workspace_id == workspace_id,
            SSOConfiguration.is_active.is_(True),
        ).limit(1)
    )
    return result.scalar_one_or_none()


async def check_sso_enforcement(
    db: AsyncSession,
    workspace_id: uuid.UUID,
) -> dict:
    """Check if SSO is enforced for a workspace and return enforcement status.

    Returns a dict with: enforced, has_active_config, provider_type,
    and login_url (for OIDC configs).
    """
    from app.models.workspace import Workspace

    ws = await db.get(Workspace, workspace_id)
    if ws is None:
        return {"enforced": False, "reason": "workspace_not_found"}

    gov = ws.governance_settings or {}
    sso_enforced = gov.get("sso_enforced", False)

    active_config = await get_active_sso_for_workspace(db, workspace_id)

    return {
        "enforced": sso_enforced and active_config is not None,
        "sso_enforced_flag": sso_enforced,
        "has_active_config": active_config is not None,
        "provider_type": (
            active_config.provider_type
            if active_config and hasattr(active_config.provider_type, "value")
            else str(active_config.provider_type) if active_config else None
        ),
        "display_name": active_config.display_name if active_config else None,
        "auto_provision": active_config.auto_provision if active_config else False,
    }


def check_jit_provisioning_ready(config: SSOConfiguration) -> dict:
    """Check if JIT (Just-In-Time) user provisioning is configured.

    Returns readiness status. Actual user creation happens during
    the SSO callback (requires live SAML/OIDC assertion parsing).
    """
    ready = config.auto_provision and config.is_active
    return {
        "auto_provision_enabled": config.auto_provision,
        "config_active": config.is_active,
        "jit_ready": ready,
        "provider_type": (
            config.provider_type.value
            if hasattr(config.provider_type, "value")
            else str(config.provider_type)
        ),
        "note": (
            "JIT provisioning will create users on first SSO login"
            if ready
            else "Enable auto_provision and activate the config for JIT"
        ),
    }
