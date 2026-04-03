"""Approval routes — list, get, and resolve approval requests."""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.auth import get_current_user_id
from app.models.approval_request import ApprovalStatus
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
    """List approval requests with optional filters."""
    if project_id is not None:
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
    proj_id = await resolve_project_for_entity(db, ApprovalRequest, approval_id)
    if proj_id is not None:
        await check_project_permission(db, proj_id, user_id, Action.PROJECT_VIEW)
    approval = await approval_service.get_approval(db, approval_id)
    return ApprovalRead.model_validate(approval)


@router.post("/{approval_id}/decide", response_model=ApprovalRead)
async def decide_approval(
    approval_id: uuid.UUID,
    data: ApprovalDecision,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> ApprovalRead:
    """Approve or reject a pending approval request."""
    proj_id = await resolve_project_for_entity(db, ApprovalRequest, approval_id)
    if proj_id is not None:
        await check_project_permission(db, proj_id, user_id, Action.PROJECT_APPROVE)
    approval = await approval_service.resolve_approval(db, approval_id, data)
    return ApprovalRead.model_validate(approval)
