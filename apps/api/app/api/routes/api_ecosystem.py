"""API & Ecosystem routes — FM-201 through FM-208.

API key management, rate limiting, webhooks, connector registry.
FM-201: /api/v1/ versioned prefix.
FM-202: Per-key rate limiting.
FM-203: Webhook event firing.
FM-208: Connector health check.
"""

import uuid

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user_id
from app.db.session import get_db
from app.services import api_key_service
from app.services import webhook_connector_service

router = APIRouter(prefix="/api/v1/ecosystem")


# ── Inline Schemas ───────────────────────────────────────────────


class APIKeyCreateRequest(BaseModel):
    name: str
    scopes: list[str] | None = None
    org_id: uuid.UUID | None = None


class WebhookCreateRequest(BaseModel):
    url: str
    events: list[str]
    secret: str | None = None
    description: str | None = None
    org_id: uuid.UUID | None = None


class WebhookFireRequest(BaseModel):
    event_type: str
    payload: dict


class ConnectorCreateRequest(BaseModel):
    name: str
    connector_type: str = "source"
    description: str | None = None
    config_json: dict | None = None
    org_id: uuid.UUID | None = None


# ── FM-201: API Keys ─────────────────────────────────────────────


@router.post("/api-keys")
async def create_api_key(
    data: APIKeyCreateRequest,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
    _rl: None = Depends(api_key_service.require_rate_limit()),
):
    """Create a new API key. The raw key is returned ONLY at creation time.

    FM-202: Applies per-user rate limiting via require_rate_limit().
    """
    key, raw_key = await api_key_service.create_api_key(
        db, creator_id=user_id, name=data.name,
        scopes=data.scopes, org_id=data.org_id,
    )
    return {
        "id": str(key.id),
        "name": key.name,
        "key_prefix": key.key_prefix,
        "key": raw_key,  # Only returned at creation
        "scopes": key.scopes,
    }


@router.get("/api-keys")
async def list_api_keys(
    include_revoked: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """List API keys (without raw key values)."""
    keys = await api_key_service.list_api_keys(
        db, user_id, include_revoked=include_revoked,
    )
    return {
        "items": [
            {"id": str(k.id), "name": k.name, "key_prefix": k.key_prefix,
             "scopes": k.scopes, "revoked": k.revoked,
             "last_used_at": k.last_used_at.isoformat() if k.last_used_at else None}
            for k in keys
        ]
    }


@router.delete("/api-keys/{key_id}")
async def revoke_api_key(
    key_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Revoke an API key."""
    await api_key_service.revoke_api_key(db, key_id, user_id)
    return {"revoked": True}


# ── FM-202: Rate Limiting ────────────────────────────────────────


@router.get("/rate-limit/status")
async def get_rate_limit_status(
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Check current rate limit status for the authenticated user."""
    info = api_key_service.check_rate_limit(str(user_id))
    return info


# ── FM-203: Webhooks ─────────────────────────────────────────────


@router.post("/webhooks")
async def create_webhook(
    data: WebhookCreateRequest,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Create a webhook subscription."""
    wh = await webhook_connector_service.create_webhook(
        db, creator_id=user_id, url=data.url, events=data.events,
        secret=data.secret, description=data.description, org_id=data.org_id,
    )
    return {"id": str(wh.id), "url": wh.url, "events": wh.events}


@router.get("/webhooks")
async def list_webhooks(
    active_only: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """List webhook subscriptions."""
    webhooks = await webhook_connector_service.list_webhooks(
        db, user_id, active_only=active_only,
    )
    return {
        "items": [
            {"id": str(w.id), "url": w.url, "events": w.events, "active": w.active}
            for w in webhooks
        ]
    }


@router.get("/webhooks/{webhook_id}")
async def get_webhook(
    webhook_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Get webhook details."""
    wh = await webhook_connector_service.get_webhook(db, webhook_id)
    return {
        "id": str(wh.id), "url": wh.url, "events": wh.events,
        "active": wh.active, "description": wh.description,
    }


@router.delete("/webhooks/{webhook_id}")
async def delete_webhook(
    webhook_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Delete a webhook subscription."""
    await webhook_connector_service.delete_webhook(db, webhook_id)
    return {"deleted": True}


@router.get("/webhooks/{webhook_id}/deliveries")
async def get_deliveries(
    webhook_id: uuid.UUID,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Get delivery history for a webhook."""
    deliveries, total = await webhook_connector_service.get_delivery_history(
        db, webhook_id, limit=limit, offset=offset,
    )
    return {
        "total": total,
        "items": [
            {"id": str(d.id), "event_type": d.event_type,
             "status": d.status.value if d.status else None,
             "attempt": d.attempt, "status_code": d.status_code}
            for d in deliveries
        ],
    }


# ── FM-208: Connector Registry ───────────────────────────────────


@router.post("/connectors")
async def register_connector(
    data: ConnectorCreateRequest,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Register an integration connector."""
    from app.models.api_ecosystem import ConnectorType
    conn = await webhook_connector_service.register_connector(
        db, name=data.name, connector_type=ConnectorType(data.connector_type),
        description=data.description, config_json=data.config_json,
        org_id=data.org_id,
    )
    return {"id": str(conn.id), "name": conn.name}


@router.get("/connectors")
async def list_connectors(
    org_id: uuid.UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """List installed connectors."""
    connectors = await webhook_connector_service.list_connectors(db, org_id=org_id)
    return {
        "items": [
            {"id": str(c.id), "name": c.name,
             "connector_type": c.connector_type.value if c.connector_type else None,
             "status": c.status.value if c.status else None}
            for c in connectors
        ]
    }


@router.get("/connectors/{connector_id}")
async def get_connector(
    connector_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Get connector details."""
    conn = await webhook_connector_service.get_connector(db, connector_id)
    return {
        "id": str(conn.id), "name": conn.name, "description": conn.description,
        "connector_type": conn.connector_type.value if conn.connector_type else None,
        "status": conn.status.value if conn.status else None,
        "config_json": conn.config_json,
    }


@router.delete("/connectors/{connector_id}")
async def delete_connector(
    connector_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Uninstall a connector."""
    await webhook_connector_service.delete_connector(db, connector_id)
    return {"deleted": True}


@router.post("/connectors/{connector_id}/health")
async def health_check_connector(
    connector_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """FM-208: Perform a real health probe on a connector."""
    return await webhook_connector_service.health_check_connector(db, connector_id)


# ── FM-203: Webhook Event Firing ─────────────────────────────────


@router.post("/webhooks/fire")
async def fire_webhook_event(
    data: WebhookFireRequest,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """FM-203: Fire an event to all matching webhook subscriptions."""
    deliveries = await webhook_connector_service.fire_event(
        db, event_type=data.event_type, payload=data.payload,
    )
    return {
        "event_type": data.event_type,
        "deliveries": len(deliveries),
        "items": [
            {"id": str(d.id), "status": d.status.value if d.status else None,
             "status_code": d.status_code}
            for d in deliveries
        ],
    }
