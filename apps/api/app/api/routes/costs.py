"""Cost tracking routes — query token usage and costs.

FM-047: Endpoints for cost dashboards and budget monitoring.
"""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.cost import CostRecordRead, CostRecordList
from app.services import cost_tracking_service

router = APIRouter(prefix="/costs")


@router.get("/runs/{run_id}/summary")
async def get_run_cost_summary(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get aggregated cost summary for a run."""
    return await cost_tracking_service.get_run_cost_summary(db, run_id)


@router.get("/projects/{project_id}/summary")
async def get_project_cost_summary(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get aggregated cost summary for a project."""
    return await cost_tracking_service.get_project_cost_summary(db, project_id)


@router.get("/breakdown")
async def get_cost_breakdown(
    project_id: uuid.UUID | None = Query(None),
    run_id: uuid.UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Get cost breakdown by model."""
    return await cost_tracking_service.get_cost_breakdown_by_model(
        db, project_id=project_id, run_id=run_id
    )


@router.get("", response_model=CostRecordList)
async def list_cost_records(
    project_id: uuid.UUID | None = Query(None),
    run_id: uuid.UUID | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> CostRecordList:
    """List individual cost records."""
    records, total = await cost_tracking_service.list_cost_records(
        db, project_id=project_id, run_id=run_id, limit=limit, offset=offset
    )
    return CostRecordList(
        items=[CostRecordRead.model_validate(r) for r in records],
        total=total,
    )
