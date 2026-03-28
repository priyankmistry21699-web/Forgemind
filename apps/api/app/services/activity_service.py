import uuid
from datetime import datetime, timezone

from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity import ActivityFeedEntry, UserPresence


# ── Activity Feed (FM-058) ───────────────────────────────────────

async def create_activity(
    db: AsyncSession,
    *,
    actor_id: uuid.UUID,
    activity_type: str,
    summary: str,
    project_id: uuid.UUID | None = None,
    workspace_id: uuid.UUID | None = None,
    resource_type: str | None = None,
    resource_id: uuid.UUID | None = None,
    metadata_: dict | None = None,
) -> ActivityFeedEntry:
    entry = ActivityFeedEntry(
        actor_id=actor_id,
        activity_type=activity_type,
        summary=summary,
        project_id=project_id,
        workspace_id=workspace_id,
        resource_type=resource_type,
        resource_id=resource_id,
        metadata_=metadata_,
    )
    db.add(entry)
    await db.flush()
    await db.refresh(entry)
    return entry


async def list_activities(
    db: AsyncSession,
    *,
    project_id: uuid.UUID | None = None,
    workspace_id: uuid.UUID | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[ActivityFeedEntry], int]:
    query = select(ActivityFeedEntry)
    if project_id:
        query = query.where(ActivityFeedEntry.project_id == project_id)
    if workspace_id:
        query = query.where(ActivityFeedEntry.workspace_id == workspace_id)
    total = (await db.execute(
        select(sa_func.count()).select_from(query.subquery())
    )).scalar_one()
    result = await db.execute(
        query.order_by(ActivityFeedEntry.created_at.desc()).offset(offset).limit(limit)
    )
    return list(result.scalars().all()), total


# ── Presence (FM-059) ───────────────────────────────────────────

async def upsert_presence(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    status: str = "online",
    current_resource_type: str | None = None,
    current_resource_id: uuid.UUID | None = None,
) -> UserPresence:
    result = await db.execute(
        select(UserPresence).where(UserPresence.user_id == user_id)
    )
    p = result.scalar_one_or_none()
    if p is None:
        p = UserPresence(
            user_id=user_id,
            status=status,
            current_resource_type=current_resource_type,
            current_resource_id=current_resource_id,
        )
        db.add(p)
    else:
        p.status = status
        p.current_resource_type = current_resource_type
        p.current_resource_id = current_resource_id
        p.last_seen_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(p)
    return p


async def get_presence(
    db: AsyncSession, user_id: uuid.UUID
) -> UserPresence | None:
    result = await db.execute(
        select(UserPresence).where(UserPresence.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def list_presence(
    db: AsyncSession,
    *,
    limit: int = 100,
    offset: int = 0,
) -> tuple[list[UserPresence], int]:
    query = select(UserPresence)
    total = (await db.execute(
        select(sa_func.count()).select_from(query.subquery())
    )).scalar_one()
    result = await db.execute(
        query.order_by(UserPresence.last_seen_at.desc()).offset(offset).limit(limit)
    )
    return list(result.scalars().all()), total
