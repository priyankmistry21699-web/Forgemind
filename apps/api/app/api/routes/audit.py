"""Audit export routes — export execution events for compliance.

FM-049: Export endpoints for JSON/CSV, audit summaries.
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.execution_event import EventType
from app.services import audit_export_service

router = APIRouter(prefix="/audit")


@router.get("/export/json")
async def export_json(
    project_id: uuid.UUID | None = Query(None),
    run_id: uuid.UUID | None = Query(None),
    event_type: EventType | None = Query(None),
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Export execution events as JSON with compliance metadata."""
    return await audit_export_service.export_events_json(
        db,
        project_id=project_id,
        run_id=run_id,
        event_type=event_type,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/export/csv")
async def export_csv(
    project_id: uuid.UUID | None = Query(None),
    run_id: uuid.UUID | None = Query(None),
    event_type: EventType | None = Query(None),
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Export execution events as CSV."""
    csv_content = await audit_export_service.export_events_csv(
        db,
        project_id=project_id,
        run_id=run_id,
        event_type=event_type,
        start_date=start_date,
        end_date=end_date,
    )
    return PlainTextResponse(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=audit_export.csv"},
    )


@router.get("/summary")
async def audit_summary(
    project_id: uuid.UUID | None = Query(None),
    run_id: uuid.UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Get audit trail summary with event type breakdown."""
    return await audit_export_service.get_audit_summary(
        db, project_id=project_id, run_id=run_id
    )
