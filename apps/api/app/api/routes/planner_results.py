import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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
) -> PlannerResultRead:
    """Retrieve the planner result for a specific run."""
    result = await db.execute(
        select(PlannerResult).where(PlannerResult.run_id == run_id)
    )
    planner_result = result.scalar_one_or_none()
    if planner_result is None:
        raise HTTPException(status_code=404, detail="No planner result found for this run")
    return planner_result
