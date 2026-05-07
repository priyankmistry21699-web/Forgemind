"""Approval routes — list, get, and resolve approval requests."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status as http_status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.auth import get_current_user_id
from app.models.approval_request import ApprovalStatus
from app.models.run import Run
from app.schemas.approval import ApprovalRead, ApprovalList, ApprovalDecision
from app.services import approval_service
from app.services.authz_service import check_project_permission, Action
from app.core.authz_deps import resolve_project_for_entity
from app.models.approval_request import ApprovalRequest

router = APIRouter(prefix="/approvals")


@router.get("", response_model=ApprovalList)
async def list_approvals(
    project_id: uuid.UUID | None = Query(None),
    run_id: uuid.UUID | None = Query(None),
    status: ApprovalStatus | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> ApprovalList:
    """List approval requests. At least one of project_id or run_id is required."""
    # H-11: at least one scope qualifier required to prevent cross-project IDOR
    if project_id is None and run_id is None:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="At least one of project_id or run_id must be provided",
        )

    # Resolve project_id from the run when not supplied directly
    if project_id is None and run_id is not None:
        result = await db.execute(select(Run).where(Run.id == run_id))
        run = result.scalar_one_or_none()
        if run is None:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Run not found",
            )
        project_id = run.project_id

    await check_project_permission(db, project_id, user_id, Action.PROJECT_VIEW)
    approvals, total = await approval_service.list_approvals(
        db,
        project_id=project_id,
        run_id=run_id,
        status_filter=status,
        limit=limit,
        offset=offset,
    )
    return ApprovalList(
        items=[ApprovalRead.model_validate(a) for a in approvals],
        total=total,
    )


@router.get("/{approval_id}", response_model=ApprovalRead)
async def get_approval(
    approval_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> ApprovalRead:
    """Get a single approval request."""
    # Service raises 404 if not found; then C-3 check guards NULL project_id
    approval = await approval_service.get_approval(db, approval_id)
    if approval.project_id is None:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Cannot determine project for this approval",
        )
    await check_project_permission(
        db, approval.project_id, user_id, Action.PROJECT_VIEW
    )
    return ApprovalRead.model_validate(approval)


@router.post("/{approval_id}/decide", response_model=ApprovalRead)
async def decide_approval(
    approval_id: uuid.UUID,
    data: ApprovalDecision,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> ApprovalRead:
    """Approve or reject a pending approval request."""
    # C-3: null project_id must never bypass the auth check
    # resolve_project_for_entity returns None both for "not found" and "no project";
    # we deliberately return 403 for both to avoid leaking existence.
    proj_id = await resolve_project_for_entity(db, ApprovalRequest, approval_id)
    if proj_id is None:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Cannot determine project for this approval",
        )
    await check_project_permission(db, proj_id, user_id, Action.PROJECT_APPROVE)
    approval = await approval_service.resolve_approval(
        db, approval_id, data, user_id=user_id
    )
    return ApprovalRead.model_validate(approval)
