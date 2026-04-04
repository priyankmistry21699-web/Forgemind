"""Run lifecycle routes — health checks, auto-completion, lifecycle management.

FM-046: Exposes run health monitoring and lifecycle transition endpoints.
FM-101: Adds gated lifecycle transitions (SPEC-before-PLAN, PLAN-before-RUN).
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user_id
from app.db.session import get_db
from app.models.run import RunStatus
from app.services import run_lifecycle_service
from app.services.authz_service import check_project_permission, Action
from app.core.authz_deps import resolve_project_for_run

router = APIRouter(prefix="/lifecycle")


@router.get("/runs/{run_id}/health")
async def get_run_health(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Get comprehensive health status for a run."""
    pid = await resolve_project_for_run(db, run_id)
    await check_project_permission(db, pid, user_id, Action.PROJECT_VIEW)
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
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Attempt to auto-complete a run if all tasks are in terminal states."""
    pid = await resolve_project_for_run(db, run_id)
    await check_project_permission(db, pid, user_id, Action.PROJECT_RUN)
    result = await run_lifecycle_service.try_auto_complete_run(db, run_id)
    await db.commit()
    return result


@router.post("/runs/{run_id}/auto-fail")
async def try_auto_fail(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Attempt to auto-fail a run if unrecoverable blocking failures exist."""
    pid = await resolve_project_for_run(db, run_id)
    await check_project_permission(db, pid, user_id, Action.PROJECT_RUN)
    result = await run_lifecycle_service.try_auto_fail_run(db, run_id)
    await db.commit()
    return result


@router.get("/runs/health/scan")
async def scan_all_runs(
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Scan all active runs and return health summaries."""
    return await run_lifecycle_service.scan_all_runs_health(db)


# ---------------------------------------------------------------------------
# FM-101: Gated lifecycle transitions
# ---------------------------------------------------------------------------


class TransitionRequest(BaseModel):
    target_status: RunStatus


@router.post("/runs/{run_id}/transition")
async def transition_run(
    run_id: uuid.UUID,
    body: TransitionRequest,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Transition a run to a new lifecycle status with gating enforcement."""
    pid = await resolve_project_for_run(db, run_id)
    await check_project_permission(db, pid, user_id, Action.PROJECT_RUN)
    result = await run_lifecycle_service.transition_run(db, run_id, body.target_status)
    if not result.get("transitioned") and not result.get("allowed", True):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=result.get("reason", "Transition not allowed"),
        )
    return result


@router.get("/runs/{run_id}/transition/validate")
async def validate_transition(
    run_id: uuid.UUID,
    target_status: RunStatus,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Check whether a lifecycle transition is currently allowed."""
    pid = await resolve_project_for_run(db, run_id)
    await check_project_permission(db, pid, user_id, Action.PROJECT_VIEW)
    return await run_lifecycle_service.validate_transition(db, run_id, target_status)


# ---------------------------------------------------------------------------
# FM-108: Spec-to-plan validation endpoint
# ---------------------------------------------------------------------------


@router.get("/runs/{run_id}/spec-plan/validate")
async def validate_spec_plan(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Validate that a run's PLAN adequately covers its SPEC.

    Returns validation result with issues and coverage map.
    """
    from app.services import spec_plan_validation_service

    pid = await resolve_project_for_run(db, run_id)
    await check_project_permission(db, pid, user_id, Action.PROJECT_VIEW)
    result = await spec_plan_validation_service.validate_spec_plan(db, run_id)
    return result.to_dict()


# ---------------------------------------------------------------------------
# FM-109: SPEC/PLAN approval endpoints
# ---------------------------------------------------------------------------


@router.post("/runs/{run_id}/spec/approve")
async def request_spec_approval(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Create an approval request for the run's SPEC artifact."""
    from app.services import spec_plan_approval_service

    pid = await resolve_project_for_run(db, run_id)
    await check_project_permission(db, pid, user_id, Action.PROJECT_RUN)
    approval = await spec_plan_approval_service.request_spec_approval(
        db, run_id=run_id, project_id=pid
    )
    await db.commit()
    if approval is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No SPEC artifact found or approval already pending",
        )
    return {"approval_id": str(approval.id), "status": approval.status.value}


@router.post("/runs/{run_id}/plan/approve")
async def request_plan_approval(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Create an approval request for the run's PLAN artifact."""
    from app.services import spec_plan_approval_service

    pid = await resolve_project_for_run(db, run_id)
    await check_project_permission(db, pid, user_id, Action.PROJECT_RUN)
    approval = await spec_plan_approval_service.request_plan_approval(
        db, run_id=run_id, project_id=pid
    )
    await db.commit()
    if approval is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No PLAN artifact found or approval already pending",
        )
    return {"approval_id": str(approval.id), "status": approval.status.value}


@router.get("/runs/{run_id}/artifact-approvals")
async def get_artifact_approval_status(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Get approval status for SPEC and PLAN artifacts of a run."""
    from app.services import spec_plan_approval_service

    pid = await resolve_project_for_run(db, run_id)
    await check_project_permission(db, pid, user_id, Action.PROJECT_VIEW)
    return await spec_plan_approval_service.get_artifact_approval_status(db, run_id)
