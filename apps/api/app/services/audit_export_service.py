"""Audit export service — export execution events for compliance.

FM-049: Supports JSON and CSV export with date range filters,
data retention awareness, and compliance metadata.
"""

import csv
import io
import uuid
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.execution_event import ExecutionEvent, EventType

logger = logging.getLogger(__name__)


async def _fetch_events(
    db: AsyncSession,
    *,
    project_id: uuid.UUID | None = None,
    run_id: uuid.UUID | None = None,
    event_type: EventType | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> list[ExecutionEvent]:
    """Fetch events with optional filters for export."""
    query = select(ExecutionEvent)

    if project_id:
        query = query.where(ExecutionEvent.project_id == project_id)
    if run_id:
        query = query.where(ExecutionEvent.run_id == run_id)
    if event_type:
        query = query.where(ExecutionEvent.event_type == event_type)
    if start_date:
        query = query.where(ExecutionEvent.created_at >= start_date)
    if end_date:
        query = query.where(ExecutionEvent.created_at <= end_date)

    query = query.order_by(ExecutionEvent.created_at.asc())
    result = await db.execute(query)
    return list(result.scalars().all())


def _event_to_dict(event: ExecutionEvent) -> dict[str, Any]:
    """Convert an event to a serializable dict."""
    return {
        "id": str(event.id),
        "event_type": event.event_type.value,
        "summary": event.summary,
        "metadata": event.metadata_,
        "project_id": str(event.project_id) if event.project_id else None,
        "run_id": str(event.run_id) if event.run_id else None,
        "task_id": str(event.task_id) if event.task_id else None,
        "artifact_id": str(event.artifact_id) if event.artifact_id else None,
        "agent_slug": event.agent_slug,
        "created_at": event.created_at.isoformat() if event.created_at else None,
    }


async def export_events_json(
    db: AsyncSession,
    *,
    project_id: uuid.UUID | None = None,
    run_id: uuid.UUID | None = None,
    event_type: EventType | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> dict[str, Any]:
    """Export events as a JSON-serializable dict with compliance metadata."""
    events = await _fetch_events(
        db,
        project_id=project_id,
        run_id=run_id,
        event_type=event_type,
        start_date=start_date,
        end_date=end_date,
    )

    return {
        "export_metadata": {
            "format": "json",
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "total_events": len(events),
            "filters": {
                "project_id": str(project_id) if project_id else None,
                "run_id": str(run_id) if run_id else None,
                "event_type": event_type.value if event_type else None,
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
            },
        },
        "events": [_event_to_dict(e) for e in events],
    }


async def export_events_csv(
    db: AsyncSession,
    *,
    project_id: uuid.UUID | None = None,
    run_id: uuid.UUID | None = None,
    event_type: EventType | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> str:
    """Export events as CSV string."""
    events = await _fetch_events(
        db,
        project_id=project_id,
        run_id=run_id,
        event_type=event_type,
        start_date=start_date,
        end_date=end_date,
    )

    output = io.StringIO()
    fieldnames = [
        "id", "event_type", "summary", "metadata",
        "project_id", "run_id", "task_id", "artifact_id",
        "agent_slug", "created_at",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for event in events:
        row = _event_to_dict(event)
        # Convert metadata dict to string for CSV
        if row["metadata"] is not None:
            import json
            row["metadata"] = json.dumps(row["metadata"])
        writer.writerow(row)

    return output.getvalue()


async def get_audit_summary(
    db: AsyncSession,
    *,
    project_id: uuid.UUID | None = None,
    run_id: uuid.UUID | None = None,
) -> dict[str, Any]:
    """Get audit trail summary with event type breakdown."""
    events = await _fetch_events(
        db, project_id=project_id, run_id=run_id
    )

    type_counts: dict[str, int] = {}
    for e in events:
        type_counts[e.event_type.value] = type_counts.get(e.event_type.value, 0) + 1

    first_event = events[0].created_at.isoformat() if events else None
    last_event = events[-1].created_at.isoformat() if events else None

    return {
        "total_events": len(events),
        "event_type_breakdown": type_counts,
        "first_event_at": first_event,
        "last_event_at": last_event,
        "project_id": str(project_id) if project_id else None,
        "run_id": str(run_id) if run_id else None,
    }
