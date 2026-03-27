"""Run lifecycle routes — health checks, auto-completion, lifecycle management.

FM-046: Exposes run health monitoring and lifecycle transition endpoints.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services import run_lifecycle_service

router = APIRouter(prefix="/lifecycle")


@router.get("/runs/{run_id}/health")
async def get_run_health(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get comprehensive health status for a run."""
    result = await run_lifecycle_service.get_run_health(db, run_id)
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["error"],
        )
    return result


@router.post("/runs/{run_id}/auto-complete")
async def try_auto_complete(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Attempt to auto-complete a run if all tasks are in terminal states."""
    result = await run_lifecycle_service.try_auto_complete_run(db, run_id)
    await db.commit()
    return result


@router.post("/runs/{run_id}/auto-fail")
async def try_auto_fail(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Attempt to auto-fail a run if unrecoverable blocking failures exist."""
    result = await run_lifecycle_service.try_auto_fail_run(db, run_id)
    await db.commit()
    return result


@router.get("/runs/health/scan")
async def scan_all_runs(
    db: AsyncSession = Depends(get_db),
):
    """Scan all active runs and return health summaries."""
    return await run_lifecycle_service.scan_all_runs_health(db)
