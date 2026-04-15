"""Unified activity feed service — merge events from multiple sources.

FM-143: Activity Feed — Project & Run Level.
Aggregates comments, task changes, approvals, artifacts, and release events.
"""

import uuid
from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity import ActivityFeedEntry


async def get_unified_activity(
    db: AsyncSession,
    *,
    project_id: uuid.UUID | None = None,
    run_id: uuid.UUID | None = None,
    event_types: list[str] | None = None,
    limit: int = 50,
    offset: int = 0,
    cursor: datetime | None = None,
) -> tuple[list[dict], int, str | None]:
    """Return a merged, chronological activity stream.

    Merges data from activity_feed_entries plus inline comment/task/approval events.
    When run_id is provided, returns only events related to that run.

    If *cursor* is provided, returns entries older than the cursor timestamp
    (for forward pagination). Returns (items, total, next_cursor).
    """
    base = select(
        ActivityFeedEntry.id,
        ActivityFeedEntry.activity_type,
        ActivityFeedEntry.summary,
        ActivityFeedEntry.actor_id,
        ActivityFeedEntry.resource_type,
        ActivityFeedEntry.resource_id,
        ActivityFeedEntry.created_at,
    )

    if project_id:
        base = base.where(ActivityFeedEntry.project_id == project_id)
    if run_id:
        base = base.where(
            (ActivityFeedEntry.resource_type == "run")
            & (ActivityFeedEntry.resource_id == run_id)
        )
    if event_types:
        base = base.where(ActivityFeedEntry.activity_type.in_(event_types))

    # Cursor-based pagination: fetch entries older than cursor (FM-143)
    if cursor is not None:
        base = base.where(ActivityFeedEntry.created_at < cursor)

    count_q = select(func.count()).select_from(base.subquery())
    total_result = await db.execute(count_q)
    total = total_result.scalar_one()

    ordered = (
        base.order_by(ActivityFeedEntry.created_at.desc())
    )
    if cursor is None:
        ordered = ordered.offset(offset)
    ordered = ordered.limit(limit)

    result = await db.execute(ordered)
    rows = result.all()

    items = [
        {
            "id": str(r.id),
            "event_type": r.activity_type.value
            if hasattr(r.activity_type, "value")
            else str(r.activity_type),
            "summary": r.summary,
            "actor_id": str(r.actor_id),
            "resource_type": r.resource_type,
            "resource_id": str(r.resource_id) if r.resource_id else None,
            "timestamp": r.created_at.isoformat(),
        }
        for r in rows
    ]

    # Compute next_cursor from the oldest item in this page
    next_cursor: str | None = None
    if items and len(items) == limit:
        next_cursor = items[-1]["timestamp"]

    return items, total, next_cursor
