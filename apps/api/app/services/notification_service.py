import uuid

from sqlalchemy import select, func as sa_func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import (
    Notification, NotificationDeliveryConfig,
)


# ── Notifications (FM-055) ───────────────────────────────────────

async def create_notification(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    notification_type: str,
    title: str,
    priority: str = "normal",
    body: str | None = None,
    resource_type: str | None = None,
    resource_id: uuid.UUID | None = None,
    metadata_: dict | None = None,
) -> Notification:
    n = Notification(
        user_id=user_id,
        notification_type=notification_type,
        title=title,
        priority=priority,
        body=body,
        resource_type=resource_type,
        resource_id=resource_id,
        metadata_=metadata_,
    )
    db.add(n)
    await db.flush()
    await db.refresh(n)
    return n


async def list_notifications(
    db: AsyncSession,
    user_id: uuid.UUID,
    *,
    unread_only: bool = False,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[Notification], int, int]:
    """Returns (items, total, unread_count)."""
    query = select(Notification).where(Notification.user_id == user_id)
    if unread_only:
        query = query.where(Notification.is_read == False)  # noqa: E712

    total = (await db.execute(
        select(sa_func.count()).select_from(query.subquery())
    )).scalar_one()

    unread_count = (await db.execute(
        select(sa_func.count()).select_from(
            select(Notification).where(
                Notification.user_id == user_id,
                Notification.is_read == False,  # noqa: E712
            ).subquery()
        )
    )).scalar_one()

    result = await db.execute(
        query.order_by(Notification.created_at.desc()).offset(offset).limit(limit)
    )
    return list(result.scalars().all()), total, unread_count


async def mark_notification_read(
    db: AsyncSession, notification_id: uuid.UUID
) -> Notification | None:
    result = await db.execute(
        select(Notification).where(Notification.id == notification_id)
    )
    n = result.scalar_one_or_none()
    if n is None:
        return None
    n.is_read = True
    await db.flush()
    await db.refresh(n)
    return n


async def mark_all_read(db: AsyncSession, user_id: uuid.UUID) -> int:
    result = await db.execute(
        update(Notification)
        .where(Notification.user_id == user_id, Notification.is_read == False)  # noqa: E712
        .values(is_read=True)
    )
    await db.flush()
    return result.rowcount  # type: ignore[return-value]


# ── Delivery Config (FM-056) ────────────────────────────────────

async def create_delivery_config(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    channel: str,
    status: str = "active",
    config: dict | None = None,
) -> NotificationDeliveryConfig:
    c = NotificationDeliveryConfig(
        user_id=user_id,
        channel=channel,
        status=status,
        config=config,
    )
    db.add(c)
    await db.flush()
    await db.refresh(c)
    return c


async def list_delivery_configs(
    db: AsyncSession, user_id: uuid.UUID
) -> tuple[list[NotificationDeliveryConfig], int]:
    query = select(NotificationDeliveryConfig).where(
        NotificationDeliveryConfig.user_id == user_id
    )
    total = (await db.execute(
        select(sa_func.count()).select_from(query.subquery())
    )).scalar_one()
    result = await db.execute(query.order_by(NotificationDeliveryConfig.created_at))
    return list(result.scalars().all()), total
