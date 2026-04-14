"""Mention service — parse @mentions from comment bodies, resolve users, route notifications.

FM-142: @Mentions, User Tagging & Notification Routing.
"""

import re
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.notification import Notification, NotificationType, NotificationPriority


# Pattern: @username (alphanumeric, dots, hyphens, underscores, 2-50 chars)
_MENTION_RE = re.compile(r"@([A-Za-z0-9._-]{2,50})\b")


def extract_mentions(text: str) -> list[str]:
    """Extract unique @usernames from text."""
    return list(dict.fromkeys(_MENTION_RE.findall(text)))


async def resolve_mentions(
    db: AsyncSession, usernames: list[str]
) -> dict[str, uuid.UUID]:
    """Resolve display_name/email prefixes to user IDs."""
    if not usernames:
        return {}

    result = await db.execute(
        select(User.id, User.display_name).where(User.display_name.in_(usernames))
    )
    return {row.display_name: row.id for row in result.all()}


async def create_mention_notifications(
    db: AsyncSession,
    *,
    mentioned_user_ids: list[uuid.UUID],
    author_id: uuid.UUID,
    comment_id: uuid.UUID,
    entity_type: str,
    entity_id: uuid.UUID,
    comment_preview: str,
) -> list[Notification]:
    """Generate a notification for each mentioned user (skip self-mentions)."""
    notifications = []
    preview = comment_preview[:200]

    for uid in mentioned_user_ids:
        if uid == author_id:
            continue
        notif = Notification(
            user_id=uid,
            notification_type=NotificationType.SYSTEM,
            priority=NotificationPriority.NORMAL,
            title=f"You were mentioned in a comment",
            body=preview,
            resource_type=entity_type,
            resource_id=entity_id,
            metadata_={"comment_id": str(comment_id)},
        )
        db.add(notif)
        notifications.append(notif)

    if notifications:
        await db.flush()

    return notifications
