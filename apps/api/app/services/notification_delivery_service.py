"""Notification delivery service — external delivery via webhook, Slack, email.

FM-056: Sends notifications to external channels based on user delivery configs.
Failures are logged, never fatal to the request flow.
"""

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import (
    Notification,
    NotificationDeliveryConfig,
    DeliveryChannel,
    DeliveryStatus,
)

logger = logging.getLogger(__name__)


async def deliver_notification(
    db: AsyncSession,
    notification: Notification,
) -> list[dict]:
    """Attempt to deliver a notification to all active channels for the user.

    Returns a list of delivery attempt results.
    Never raises — all failures are caught and logged.
    """
    results = []

    configs_result = await db.execute(
        select(NotificationDeliveryConfig).where(
            NotificationDeliveryConfig.user_id == notification.user_id,
            NotificationDeliveryConfig.status == DeliveryStatus.ACTIVE,
        )
    )
    configs = list(configs_result.scalars().all())

    for config in configs:
        result = await _deliver_to_channel(notification, config)
        results.append(result)

    return results


async def _deliver_to_channel(
    notification: Notification,
    config: NotificationDeliveryConfig,
) -> dict:
    """Deliver a single notification to a single channel.

    Returns delivery result dict with status and details.
    """
    try:
        if config.channel == DeliveryChannel.WEBHOOK:
            return await _deliver_webhook(notification, config)
        elif config.channel == DeliveryChannel.SLACK:
            return await _deliver_slack(notification, config)
        elif config.channel == DeliveryChannel.EMAIL:
            return await _deliver_email(notification, config)
        else:
            return {
                "channel": config.channel.value,
                "status": "skipped",
                "detail": f"Unknown channel: {config.channel.value}",
            }
    except Exception as exc:
        logger.error(
            "Notification delivery failed: channel=%s, notification=%s, error=%s",
            config.channel.value,
            notification.id,
            str(exc),
        )
        return {
            "channel": config.channel.value,
            "status": "failed",
            "detail": str(exc),
        }


async def _deliver_webhook(
    notification: Notification,
    config: NotificationDeliveryConfig,
) -> dict:
    """Send notification via webhook POST.

    Expects config.config to have {"url": "https://..."}.
    Uses httpx for async HTTP delivery.
    """
    webhook_url = (config.config or {}).get("url")
    if not webhook_url:
        return {
            "channel": "webhook",
            "status": "failed",
            "detail": "No webhook URL configured",
        }

    import httpx

    payload = {
        "notification_id": str(notification.id),
        "type": notification.notification_type.value if hasattr(notification.notification_type, 'value') else str(notification.notification_type),
        "priority": notification.priority.value if hasattr(notification.priority, 'value') else str(notification.priority),
        "title": notification.title,
        "body": notification.body,
        "resource_type": notification.resource_type,
        "resource_id": str(notification.resource_id) if notification.resource_id else None,
        "created_at": notification.created_at.isoformat() if notification.created_at else None,
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(webhook_url, json=payload)
        resp.raise_for_status()

    logger.info("Webhook delivered: notification=%s, url=%s", notification.id, webhook_url)
    return {
        "channel": "webhook",
        "status": "delivered",
        "detail": f"HTTP {resp.status_code}",
    }


async def _deliver_slack(
    notification: Notification,
    config: NotificationDeliveryConfig,
) -> dict:
    """Send notification to Slack via incoming webhook.

    Expects config.config to have {"webhook_url": "https://hooks.slack.com/..."}.
    """
    webhook_url = (config.config or {}).get("webhook_url")
    if not webhook_url:
        return {
            "channel": "slack",
            "status": "failed",
            "detail": "No Slack webhook URL configured",
        }

    import httpx

    priority_emoji = {
        "low": "ℹ️",
        "normal": "📋",
        "high": "⚠️",
        "urgent": "🚨",
    }
    priority_str = notification.priority.value if hasattr(notification.priority, 'value') else str(notification.priority)
    emoji = priority_emoji.get(priority_str, "📋")

    payload = {
        "text": f"{emoji} *{notification.title}*\n{notification.body or ''}",
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(webhook_url, json=payload)
        resp.raise_for_status()

    logger.info("Slack delivered: notification=%s", notification.id)
    return {
        "channel": "slack",
        "status": "delivered",
        "detail": f"HTTP {resp.status_code}",
    }


async def _deliver_email(
    notification: Notification,
    config: NotificationDeliveryConfig,
) -> dict:
    """Email delivery stub.

    Expects config.config to have {"email": "user@example.com"}.
    In v1, logs the email instead of actually sending.
    """
    email_addr = (config.config or {}).get("email")
    if not email_addr:
        return {
            "channel": "email",
            "status": "failed",
            "detail": "No email address configured",
        }

    # v1: log-only stub — real SMTP integration in a future FM
    logger.info(
        "Email delivery (stub): to=%s, subject=%s",
        email_addr,
        notification.title,
    )
    return {
        "channel": "email",
        "status": "delivered",
        "detail": f"Logged to {email_addr} (stub)",
    }
