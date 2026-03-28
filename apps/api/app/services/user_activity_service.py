"""User activity service — lightweight presence and activity tracking.

FM-059: Tracks user presence, recent activity, and assignment awareness.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity import UserPresence


async def touch_user_activity(
    db: AsyncSession,
    user_id: uuid.UUID,
    *,
    resource_type: str | None = None,
    resource_id: uuid.UUID | None = None,
) -> UserPresence:
    """Update or create user presence with current timestamp.

    Called from routes or middleware to track user activity.
    """
    result = await db.execute(
        select(UserPresence).where(UserPresence.user_id == user_id)
    )
    presence = result.scalar_one_or_none()

    now = datetime.now(timezone.utc)

    if presence:
        presence.status = "online"
        presence.last_seen_at = now
        if resource_type is not None:
            presence.current_resource_type = resource_type
        if resource_id is not None:
            presence.current_resource_id = resource_id
        await db.flush()
        await db.refresh(presence)
    else:
        presence = UserPresence(
            user_id=user_id,
            status="online",
            current_resource_type=resource_type,
            current_resource_id=resource_id,
            last_seen_at=now,
        )
        db.add(presence)
        await db.flush()
        await db.refresh(presence)

    return presence


async def get_active_users_on_resource(
    db: AsyncSession,
    resource_type: str,
    resource_id: uuid.UUID,
) -> list[UserPresence]:
    """Get all users currently active on a specific resource."""
    result = await db.execute(
        select(UserPresence).where(
            UserPresence.current_resource_type == resource_type,
            UserPresence.current_resource_id == resource_id,
        )
    )
    return list(result.scalars().all())


async def get_user_assignment_context(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> dict:
    """Get assignment context for a user — presence + membership info.

    Returns a dict with presence and activity metadata.
    """
    from app.models.membership import ProjectMember, WorkspaceMember

    presence_result = await db.execute(
        select(UserPresence).where(UserPresence.user_id == user_id)
    )
    presence = presence_result.scalar_one_or_none()

    # Count memberships
    ws_count = (await db.execute(
        select(WorkspaceMember).where(WorkspaceMember.user_id == user_id)
    )).scalars().all()

    proj_count = (await db.execute(
        select(ProjectMember).where(ProjectMember.user_id == user_id)
    )).scalars().all()

    return {
        "user_id": str(user_id),
        "status": presence.status if presence else "offline",
        "last_seen_at": presence.last_seen_at.isoformat() if presence and presence.last_seen_at else None,
        "current_resource_type": presence.current_resource_type if presence else None,
        "current_resource_id": str(presence.current_resource_id) if presence and presence.current_resource_id else None,
        "workspace_memberships": len(ws_count),
        "project_memberships": len(proj_count),
    }
