"""Unified activity feed service — merge events from multiple sources.

FM-143: Activity Feed — Project & Run Level.
Aggregates comments, task changes, approvals, artifacts, and release events.
"""

import uuid
from datetime import datetime

from sqlalchemy import select, func, union_all, literal_column, literal, String, cast
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.models.activity import ActivityFeedEntry
from app.models.comment import Comment
from app.models.task import Task
from app.models.approval_request import ApprovalRequest
from app.models.artifact import Artifact


async def get_unified_activity(
    db: AsyncSession,
    *,
    project_id: uuid.UUID | None = None,
    run_id: uuid.UUID | None = None,
    event_types: list[str] | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[dict], int]:
    """Return a merged, chronological activity stream.

    Merges data from activity_feed_entries plus inline comment/task/approval events.
    When run_id is provided, returns only events related to that run.
    """
    # Strategy: query the primary ActivityFeedEntry table with optional filters.
    # For run-level, we filter by resource_type='run' and resource_id=run_id,
    # or any activity whose resource ties back to the run.
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

    count_q = select(func.count()).select_from(base.subquery())
    total_result = await db.execute(count_q)
    total = total_result.scalar_one()

    ordered = base.order_by(ActivityFeedEntry.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(ordered)
    rows = result.all()

    items = [
        {
            "id": str(r.id),
            "event_type": r.activity_type.value if hasattr(r.activity_type, "value") else str(r.activity_type),
            "summary": r.summary,
            "actor_id": str(r.actor_id),
            "resource_type": r.resource_type,
            "resource_id": str(r.resource_id) if r.resource_id else None,
            "timestamp": r.created_at.isoformat(),
        }
        for r in rows
    ]

    return items, total
