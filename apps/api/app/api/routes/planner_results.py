import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user_id
from app.db.session import get_db
from app.models.planner_result import PlannerResult
from app.schemas.planner_result import PlannerResultRead

router = APIRouter()


@router.get(
    "/runs/{run_id}/plan",
    response_model=PlannerResultRead,
)
async def get_planner_result(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> PlannerResultRead:
    """Retrieve the planner result for a specific run."""
    # VULN-1 fix: authenticate + verify project membership before returning plan data
    from app.models.run import Run
    from app.services.authz_service import check_project_permission, Action

    run = await db.get(Run, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    await check_project_permission(db, run.project_id, user_id, Action.PROJECT_VIEW)

    result = await db.execute(
        select(PlannerResult).where(PlannerResult.run_id == run_id)
    )
    planner_result = result.scalar_one_or_none()
    if planner_result is None:
        raise HTTPException(
            status_code=404, detail="No planner result found for this run"
        )
    return planner_result
