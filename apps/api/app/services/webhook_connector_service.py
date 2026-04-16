"""Webhook & Connector services — FM-203/208.

FM-203: Webhook subscription CRUD, HMAC signing, delivery tracking with retry.
        HTTP dispatch with httpx.
FM-208: Integration connector marketplace registry with abstract Connector interface.
"""

import abc
import hashlib
import hmac
import json
import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any

import httpx
from fastapi import HTTPException, status
from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.api_ecosystem import (
    WebhookSubscription,
    WebhookDelivery,
    DeliveryStatus,
    ConnectorRegistry,
    ConnectorType,
    ConnectorStatus,
)

logger = logging.getLogger(__name__)


# ── FM-208: Abstract Connector Interface ─────────────────────────


class ConnectorABC(abc.ABC):
    """Abstract base class for integration connectors.

    All concrete connectors (Slack, Jira, PagerDuty, Email, custom)
    must implement this interface to participate in the connector registry.
    """

    @abc.abstractmethod
    async def validate_config(self, config: dict) -> bool:
        """Validate connector configuration. Returns True if valid."""
        ...

    @abc.abstractmethod
    async def health_check(self, config: dict) -> dict:
        """Perform a health check. Returns status dict."""
        ...

    @abc.abstractmethod
    async def send(self, config: dict, event_type: str, payload: dict) -> dict:
        """Send a payload to the external system. Returns delivery result."""
        ...


# ── FM-203: Webhook Subscriptions ────────────────────────────────


async def create_webhook(
    db: AsyncSession,
    *,
    creator_id: uuid.UUID,
    url: str,
    events: list[str],
    secret: str | None = None,
    description: str | None = None,
    org_id: uuid.UUID | None = None,
) -> WebhookSubscription:
    """Create a webhook subscription."""
    secret_hash = (
        hashlib.sha256(secret.encode()).hexdigest() if secret else None
    )
    wh = WebhookSubscription(
        creator_id=creator_id,
        url=url,
        events=events,
        secret_hash=secret_hash,
        description=description,
        org_id=org_id,
    )
    db.add(wh)
    await db.flush()
    return wh


async def list_webhooks(
    db: AsyncSession,
    creator_id: uuid.UUID,
    *,
    active_only: bool = True,
) -> list[WebhookSubscription]:
    """List webhooks for a user."""
    query = select(WebhookSubscription).where(
        WebhookSubscription.creator_id == creator_id
    )
    if active_only:
        query = query.where(WebhookSubscription.active.is_(True))
    result = await db.execute(query.order_by(WebhookSubscription.created_at.desc()))
    return list(result.scalars().all())


async def get_webhook(
    db: AsyncSession,
    webhook_id: uuid.UUID,
) -> WebhookSubscription:
    """Get a webhook by ID."""
    result = await db.execute(
        select(WebhookSubscription).where(WebhookSubscription.id == webhook_id)
    )
    wh = result.scalar_one_or_none()
    if wh is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found",
        )
    return wh


async def delete_webhook(
    db: AsyncSession,
    webhook_id: uuid.UUID,
) -> None:
    """Delete a webhook subscription."""
    wh = await get_webhook(db, webhook_id)
    await db.delete(wh)
    await db.flush()


def sign_payload(payload: dict, secret: str) -> str:
    """Generate HMAC-SHA256 signature for webhook payload."""
    body = json.dumps(payload, sort_keys=True, default=str).encode()
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


async def record_delivery(
    db: AsyncSession,
    *,
    subscription_id: uuid.UUID,
    event_type: str,
    payload: dict,
    status_val: DeliveryStatus = DeliveryStatus.PENDING,
    status_code: int | None = None,
) -> WebhookDelivery:
    """Record a webhook delivery attempt."""
    payload_bytes = json.dumps(payload, sort_keys=True, default=str).encode()
    payload_hash = hashlib.sha256(payload_bytes).hexdigest()

    delivery = WebhookDelivery(
        subscription_id=subscription_id,
        event_type=event_type,
        payload_hash=payload_hash,
        status=status_val,
        status_code=status_code,
    )
    db.add(delivery)
    await db.flush()
    return delivery


async def mark_delivery_success(
    db: AsyncSession,
    delivery_id: uuid.UUID,
    status_code: int,
) -> WebhookDelivery:
    """Mark a delivery as successfully completed."""
    result = await db.execute(
        select(WebhookDelivery).where(WebhookDelivery.id == delivery_id)
    )
    delivery = result.scalar_one_or_none()
    if delivery is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery not found",
        )
    delivery.status = DeliveryStatus.DELIVERED
    delivery.status_code = status_code
    delivery.delivered_at = datetime.now(timezone.utc)
    await db.flush()
    return delivery


async def mark_delivery_failed(
    db: AsyncSession,
    delivery_id: uuid.UUID,
    status_code: int | None = None,
) -> WebhookDelivery:
    """Mark a delivery as failed and schedule retry if under max attempts."""
    result = await db.execute(
        select(WebhookDelivery).where(WebhookDelivery.id == delivery_id)
    )
    delivery = result.scalar_one_or_none()
    if delivery is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery not found",
        )

    delivery.status_code = status_code
    if delivery.attempt < delivery.max_attempts:
        delivery.status = DeliveryStatus.RETRYING
        delivery.attempt += 1
        # Exponential backoff: 2^attempt minutes
        backoff = timedelta(minutes=2 ** delivery.attempt)
        delivery.next_retry_at = datetime.now(timezone.utc) + backoff
    else:
        delivery.status = DeliveryStatus.FAILED

    await db.flush()
    return delivery


async def get_delivery_history(
    db: AsyncSession,
    subscription_id: uuid.UUID,
    *,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[WebhookDelivery], int]:
    """Get delivery history for a webhook subscription."""
    query = select(WebhookDelivery).where(
        WebhookDelivery.subscription_id == subscription_id
    )
    total = (
        await db.execute(select(sa_func.count()).select_from(query.subquery()))
    ).scalar_one()
    result = await db.execute(
        query.order_by(WebhookDelivery.created_at.desc()).offset(offset).limit(limit)
    )
    return list(result.scalars().all()), total


async def dispatch_webhook(
    db: AsyncSession,
    *,
    subscription: WebhookSubscription,
    event_type: str,
    payload: dict,
    secret: str | None = None,
    timeout: float = 10.0,
) -> WebhookDelivery:
    """Dispatch an HTTP POST to the webhook URL with HMAC signing.

    Records a delivery attempt, POSTs the payload, and marks
    the delivery as success or failed based on the HTTP response.
    """
    delivery = await record_delivery(
        db,
        subscription_id=subscription.id,
        event_type=event_type,
        payload=payload,
        status_val=DeliveryStatus.PENDING,
    )
    await db.flush()

    headers: dict[str, str] = {
        "Content-Type": "application/json",
        "X-ForgeMind-Event": event_type,
        "X-ForgeMind-Delivery": str(delivery.id),
    }
    body = json.dumps(payload, sort_keys=True, default=str)

    if secret:
        sig = sign_payload(payload, secret)
        headers["X-ForgeMind-Signature"] = f"sha256={sig}"

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(
                subscription.url,
                content=body,
                headers=headers,
            )
        if 200 <= resp.status_code < 300:
            await mark_delivery_success(db, delivery.id, resp.status_code)
        else:
            await mark_delivery_failed(db, delivery.id, resp.status_code)
    except httpx.RequestError as exc:
        logger.warning("Webhook dispatch failed for %s: %s", subscription.url, exc)
        await mark_delivery_failed(db, delivery.id, status_code=None)

    await db.flush()
    # Re-fetch to get updated state
    result = await db.execute(
        select(WebhookDelivery).where(WebhookDelivery.id == delivery.id)
    )
    return result.scalar_one()


async def fire_event(
    db: AsyncSession,
    *,
    event_type: str,
    payload: dict,
    org_id: uuid.UUID | None = None,
) -> list[WebhookDelivery]:
    """Fire an event to all matching active webhook subscriptions.

    Finds subscriptions that listen for event_type, dispatches to each.
    """
    query = select(WebhookSubscription).where(
        WebhookSubscription.active.is_(True),
    )
    if org_id:
        query = query.where(WebhookSubscription.org_id == org_id)

    result = await db.execute(query)
    subscriptions = list(result.scalars().all())

    deliveries: list[WebhookDelivery] = []
    for sub in subscriptions:
        # Check if subscription is interested in this event
        if event_type not in sub.events and "*" not in sub.events:
            continue
        # FM-203 fix: pass the stored secret_hash so dispatch can sign payloads.
        # The raw secret is not stored, but secret_hash is used for HMAC signing.
        delivery = await dispatch_webhook(
            db,
            subscription=sub,
            event_type=event_type,
            payload=payload,
            secret=sub.secret_hash,
        )
        deliveries.append(delivery)
    return deliveries


# ── FM-208: Integration Connector Registry ───────────────────────


async def register_connector(
    db: AsyncSession,
    *,
    name: str,
    connector_type: ConnectorType,
    description: str | None = None,
    config_json: dict | None = None,
    org_id: uuid.UUID | None = None,
) -> ConnectorRegistry:
    """Register a new integration connector."""
    conn = ConnectorRegistry(
        name=name,
        connector_type=connector_type,
        description=description,
        config_json=config_json or {},
        org_id=org_id,
    )
    db.add(conn)
    await db.flush()
    return conn


async def list_connectors(
    db: AsyncSession,
    *,
    org_id: uuid.UUID | None = None,
    status_filter: ConnectorStatus | None = None,
) -> list[ConnectorRegistry]:
    """List installed connectors."""
    query = select(ConnectorRegistry)
    if org_id:
        query = query.where(ConnectorRegistry.org_id == org_id)
    if status_filter:
        query = query.where(ConnectorRegistry.status == status_filter)
    result = await db.execute(query.order_by(ConnectorRegistry.installed_at.desc()))
    return list(result.scalars().all())


async def get_connector(
    db: AsyncSession,
    connector_id: uuid.UUID,
) -> ConnectorRegistry:
    """Get a connector by ID."""
    result = await db.execute(
        select(ConnectorRegistry).where(ConnectorRegistry.id == connector_id)
    )
    conn = result.scalar_one_or_none()
    if conn is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connector not found",
        )
    return conn


async def update_connector_status(
    db: AsyncSession,
    connector_id: uuid.UUID,
    new_status: ConnectorStatus,
) -> ConnectorRegistry:
    """Update connector health status."""
    conn = await get_connector(db, connector_id)
    conn.status = new_status
    conn.last_health_check = datetime.now(timezone.utc)
    await db.flush()
    return conn


async def health_check_connector(
    db: AsyncSession,
    connector_id: uuid.UUID,
    *,
    timeout: float = 5.0,
) -> dict[str, Any]:
    """FM-208: Perform a real health probe against a connector.

    For connectors with a URL in config_json["health_url"], makes an HTTP
    GET to check availability. Otherwise falls back to timestamp-only check.
    """
    conn = await get_connector(db, connector_id)
    health_url = (conn.config_json or {}).get("health_url")

    probe_result: dict[str, Any] = {
        "connector_id": str(conn.id),
        "name": conn.name,
        "previous_status": conn.status.value if conn.status else None,
    }

    if health_url:
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.get(health_url)
            if 200 <= resp.status_code < 300:
                new_status = ConnectorStatus.ACTIVE
                probe_result["probe"] = "http_ok"
                probe_result["status_code"] = resp.status_code
            else:
                new_status = ConnectorStatus.ERROR
                probe_result["probe"] = "http_error"
                probe_result["status_code"] = resp.status_code
        except httpx.RequestError as exc:
            new_status = ConnectorStatus.ERROR
            probe_result["probe"] = "http_unreachable"
            probe_result["error"] = str(exc)
    else:
        # No URL configured — consider active if config exists
        new_status = ConnectorStatus.ACTIVE if conn.config_json else ConnectorStatus.INACTIVE
        probe_result["probe"] = "config_only"

    conn.status = new_status
    conn.last_health_check = datetime.now(timezone.utc)
    await db.flush()

    probe_result["new_status"] = new_status.value
    probe_result["checked_at"] = conn.last_health_check.isoformat()
    return probe_result


async def delete_connector(
    db: AsyncSession,
    connector_id: uuid.UUID,
) -> None:
    """Uninstall a connector."""
    conn = await get_connector(db, connector_id)
    await db.delete(conn)
    await db.flush()
