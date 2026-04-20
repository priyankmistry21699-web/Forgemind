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
        select(Notification)
        .where(
            Notification.user_id == user_id,
            Notification.is_read.is_(False),
            Notification.dismissed_at.is_(None),
        )
        .order_by(Notification.created_at.desc())
        .limit(100)
    )
    return list(result.scalars().all())


async def get_grouped_notifications(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> list[dict]:
    """Return unread notifications collapsed by group_key (FM-149).

    Notifications sharing the same non-null group_key are collapsed into a
    single entry with a count.  Ungrouped notifications appear individually.
    """
    base = select(Notification).where(
        Notification.user_id == user_id,
        Notification.dismissed_at.is_(None),
        Notification.is_read.is_(False),
    )
    result = await db.execute(base.order_by(Notification.created_at.desc()).limit(200))
    all_notifs = list(result.scalars().all())

    groups: dict[str, list[Notification]] = {}
    ungrouped: list[Notification] = []
    for n in all_notifs:
        if n.group_key:
            groups.setdefault(n.group_key, []).append(n)
        else:
            ungrouped.append(n)

    items: list[dict] = []
    for key, notifs in groups.items():
        latest = notifs[0]
        items.append(
            {
                "group_key": key,
                "count": len(notifs),
                "latest_id": str(latest.id),
                "latest_title": latest.title,
                "notification_type": latest.notification_type.value
                if hasattr(latest.notification_type, "value")
                else str(latest.notification_type),
                "latest_created_at": latest.created_at.isoformat(),
            }
        )
    for n in ungrouped:
        items.append(
            {
                "group_key": None,
                "count": 1,
                "latest_id": str(n.id),
                "latest_title": n.title,
                "notification_type": n.notification_type.value
                if hasattr(n.notification_type, "value")
                else str(n.notification_type),
                "latest_created_at": n.created_at.isoformat(),
            }
        )
    return items
