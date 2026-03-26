"""Execution event routes — query the event timeline."""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.execution_event import ExecutionEventRead, ExecutionEventList
from app.services import event_service

router = APIRouter(prefix="/events")


@router.get("", response_model=ExecutionEventList)
async def list_events(
    project_id: uuid.UUID | None = Query(None),
    run_id: uuid.UUID | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> ExecutionEventList:
    """List execution events with optional filters."""
    events, total = await event_service.list_events(
        db,
        project_id=project_id,
        run_id=run_id,
        limit=limit,
        offset=offset,
    )
    return ExecutionEventList(
        items=[ExecutionEventRead.model_validate(e) for e in events],
        total=total,
    )
