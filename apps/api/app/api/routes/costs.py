"""Cost tracking routes — query token usage and costs.

FM-047: Endpoints for cost dashboards and budget monitoring.
FM-193: Configurable model rates management.
"""

import uuid

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user_id
from app.db.session import get_db
from app.schemas.cost import CostRecordRead, CostRecordList
from app.services import cost_tracking_service
from app.services.authz_service import check_project_permission, Action
from app.core.authz_deps import resolve_project_for_run

router = APIRouter(prefix="/costs")


@router.get("/runs/{run_id}/summary")
async def get_run_cost_summary(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Get aggregated cost summary for a run."""
    pid = await resolve_project_for_run(db, run_id)
    await check_project_permission(db, pid, user_id, Action.PROJECT_VIEW)
    return await cost_tracking_service.get_run_cost_summary(db, run_id)


@router.get("/projects/{project_id}/summary")
async def get_project_cost_summary(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Get aggregated cost summary for a project."""
    await check_project_permission(db, project_id, user_id, Action.PROJECT_VIEW)
    return await cost_tracking_service.get_project_cost_summary(db, project_id)


@router.get("/breakdown")
async def get_cost_breakdown(
    project_id: uuid.UUID | None = Query(None),
    run_id: uuid.UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Get cost breakdown by model."""
    if project_id is not None:
        await check_project_permission(db, project_id, user_id, Action.PROJECT_VIEW)
    elif run_id is not None:
        pid = await resolve_project_for_run(db, run_id)
        await check_project_permission(db, pid, user_id, Action.PROJECT_VIEW)
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
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> CostRecordList:
    """List individual cost records."""
    if project_id is not None:
        await check_project_permission(db, project_id, user_id, Action.PROJECT_VIEW)
    elif run_id is not None:
        pid = await resolve_project_for_run(db, run_id)
        await check_project_permission(db, pid, user_id, Action.PROJECT_VIEW)
    records, total = await cost_tracking_service.list_cost_records(
        db, project_id=project_id, run_id=run_id, limit=limit, offset=offset
    )
    return CostRecordList(
        items=[CostRecordRead.model_validate(r) for r in records],
        total=total,
    )


# ── FM-193: Configurable Model Rates ────────────────────────────


class ModelRatesUpdateRequest(BaseModel):
    rates: dict[str, dict[str, float]]


@router.get("/model-rates")
async def get_model_rates(
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """FM-193: Get current model cost rates."""
    return {"rates": cost_tracking_service.get_model_rates()}


@router.put("/model-rates")
async def update_model_rates(
    data: ModelRatesUpdateRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """FM-193: Update configurable model cost rates at runtime."""
    updated = cost_tracking_service.update_model_rates(data.rates)
    return {"rates": updated}
