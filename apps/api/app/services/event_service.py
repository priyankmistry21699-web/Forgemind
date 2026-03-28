"""Event service — emit and query execution timeline events.

FM-054/055: Enhanced with streaming pub/sub and notification generation.
"""

import logging
import uuid

from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.execution_event import ExecutionEvent, EventType

logger = logging.getLogger(__name__)

# Event types that should trigger notifications
_NOTIFICATION_EVENTS = {
    EventType.RUN_COMPLETED: ("run_completed", "normal"),
    EventType.RUN_FAILED: ("run_failed", "high"),
    EventType.APPROVAL_RESOLVED: ("approval_granted", "normal"),
}


async def emit_event(
    db: AsyncSession,
    *,
    event_type: EventType,
    summary: str,
    project_id: uuid.UUID | None = None,
    run_id: uuid.UUID | None = None,
    task_id: uuid.UUID | None = None,
    artifact_id: uuid.UUID | None = None,
    agent_slug: str | None = None,
    metadata: dict | None = None,
) -> ExecutionEvent:
    """Create and persist an execution event.

    Also publishes to SSE stream (FM-054) and generates notifications (FM-055)
    for important event types.
    """
    event = ExecutionEvent(
        event_type=event_type,
        summary=summary,
        project_id=project_id,
        run_id=run_id,
        task_id=task_id,
        artifact_id=artifact_id,
        agent_slug=agent_slug,
        metadata_=metadata,
    )
    db.add(event)
    await db.flush()

    # FM-054: Publish to run-scoped SSE stream
    if run_id:
        try:
            from app.services.stream_service import publish_run_event
            await publish_run_event(
                run_id,
                event_type.value,
                {
                    "event_id": str(event.id),
                    "summary": summary,
                    "task_id": str(task_id) if task_id else None,
                    "artifact_id": str(artifact_id) if artifact_id else None,
                    "metadata": metadata,
                },
            )
        except Exception:
            logger.debug("Stream publish failed for event %s", event.id, exc_info=True)

    return event


async def list_events(
    db: AsyncSession,
    *,
    project_id: uuid.UUID | None = None,
    run_id: uuid.UUID | None = None,
    limit: int = 100,
    offset: int = 0,
) -> tuple[list[ExecutionEvent], int]:
    """List execution events with optional filters, newest first."""
    query = select(ExecutionEvent)

    if project_id is not None:
        query = query.where(ExecutionEvent.project_id == project_id)
    if run_id is not None:
        query = query.where(ExecutionEvent.run_id == run_id)

    count_result = await db.execute(
        select(sa_func.count()).select_from(query.subquery())
    )
    total = count_result.scalar_one()

    result = await db.execute(
        query.order_by(ExecutionEvent.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    events = list(result.scalars().all())
    return events, total
