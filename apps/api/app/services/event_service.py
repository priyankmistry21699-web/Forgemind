"""Event service — emit and query execution timeline events."""

import uuid

from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.execution_event import ExecutionEvent, EventType


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
    """Create and persist an execution event."""
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
