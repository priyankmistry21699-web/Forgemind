import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.auth import get_current_user_id
from app.models.run import Run
from app.schemas.run import RunRead, RunList
from app.services.authz_service import check_project_permission, Action
from app.core.authz_deps import resolve_project_for_run

router = APIRouter()


@router.get("/projects/{project_id}/runs", response_model=RunList)
async def list_runs(
    project_id: uuid.UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> RunList:
    """List all runs for a project, newest first."""
    await check_project_permission(db, project_id, user_id, Action.PROJECT_VIEW)
    query = select(Run).where(Run.project_id == project_id)

    count_result = await db.execute(
        select(sa_func.count()).select_from(query.subquery())
    )
    total = count_result.scalar_one()

    result = await db.execute(
        query.order_by(Run.created_at.desc()).offset(skip).limit(limit)
    )
    runs = list(result.scalars().all())
    return RunList(
        items=[RunRead.model_validate(r) for r in runs],
        total=total,
    )


@router.get("/projects/{project_id}/runs/latest", response_model=RunRead)
async def get_latest_run(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> RunRead:
    """Get the most recent run for a project."""
    await check_project_permission(db, project_id, user_id, Action.PROJECT_VIEW)
    result = await db.execute(
        select(Run)
        .where(Run.project_id == project_id)
        .order_by(Run.created_at.desc())
        .limit(1)
    )
    run = result.scalar_one_or_none()
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No runs found for this project",
        )
    return RunRead.model_validate(run)


@router.get("/runs/{run_id}", response_model=RunRead)
async def get_run(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> RunRead:
    """Get a single run by ID."""
    pid = await resolve_project_for_run(db, run_id)
    await check_project_permission(db, pid, user_id, Action.PROJECT_VIEW)
    result = await db.execute(select(Run).where(Run.id == run_id))
    run = result.scalar_one_or_none()
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found",
        )
    return RunRead.model_validate(run)
