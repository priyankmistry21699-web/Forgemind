"""Approval routes — list, get, and resolve approval requests."""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.approval_request import ApprovalStatus
from app.schemas.approval import ApprovalRead, ApprovalList, ApprovalDecision
from app.services import approval_service

router = APIRouter(prefix="/approvals")


@router.get("", response_model=ApprovalList)
async def list_approvals(
    project_id: uuid.UUID | None = Query(None),
    run_id: uuid.UUID | None = Query(None),
    status: ApprovalStatus | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> ApprovalList:
    """List approval requests with optional filters."""
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
) -> ApprovalRead:
    """Get a single approval request."""
    approval = await approval_service.get_approval(db, approval_id)
    return ApprovalRead.model_validate(approval)


@router.post("/{approval_id}/decide", response_model=ApprovalRead)
async def decide_approval(
    approval_id: uuid.UUID,
    data: ApprovalDecision,
    db: AsyncSession = Depends(get_db),
) -> ApprovalRead:
    """Approve or reject a pending approval request."""
    approval = await approval_service.resolve_approval(db, approval_id, data)
    return ApprovalRead.model_validate(approval)
