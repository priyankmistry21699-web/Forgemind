"""Notification digest service — grouping, read-all, digest preview.

FM-149: Notification Center & Digest System.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification


async def mark_all_read(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> int:
    """Mark all unread notifications as read for a user. Returns count updated."""
    result = await db.execute(
        update(Notification)
        .where(Notification.user_id == user_id, Notification.is_read.is_(False))
        .values(is_read=True)
    )
    await db.flush()
    return result.rowcount  # type: ignore[return-value]


async def dismiss_notification(
    db: AsyncSession,
    notification_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Notification | None:
    notif = await db.get(Notification, notification_id)
    if notif is None or notif.user_id != user_id:
        return None
    notif.dismissed_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(notif)
    return notif


async def list_notifications(
    db: AsyncSession,
    user_id: uuid.UUID,
    *,
    category: str | None = None,
    unread_only: bool = False,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[Notification], int]:
    base = select(Notification).where(
        Notification.user_id == user_id,
        Notification.dismissed_at.is_(None),
    )
    if category:
        base = base.where(Notification.category == category)
    if unread_only:
        base = base.where(Notification.is_read.is_(False))

    count_q = select(func.count()).select_from(base.subquery())
    total_r = await db.execute(count_q)
    total = total_r.scalar_one()

    result = await db.execute(
        base.order_by(Notification.created_at.desc()).offset(offset).limit(limit)
    )
    return list(result.scalars().all()), total


async def get_digest_preview(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> list[Notification]:
    """Return unread, undismissed notifications for digest email preview."""
    result = await db.execute(
        select(Notification).where(
            Notification.user_id == user_id,
            Notification.is_read.is_(False),
            Notification.dismissed_at.is_(None),
        ).order_by(Notification.created_at.desc())
        .limit(100)
    )
    return list(result.scalars().all())
