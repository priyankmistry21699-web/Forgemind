"""Enhanced approval service — delegation, batch approval, dashboard.

FM-148: Approval Workflow Enhancements.
"""

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.approval_request import ApprovalRequest, ApprovalStatus
from app.models.approval_delegation import ApprovalDelegation


async def batch_decide(
    db: AsyncSession,
    approval_ids: list[uuid.UUID],
    status: ApprovalStatus,
    decided_by: str,
    comment: str | None = None,
) -> list[ApprovalRequest]:
    """Approve or reject multiple approvals atomically."""
    if status not in (ApprovalStatus.APPROVED, ApprovalStatus.REJECTED):
        raise HTTPException(status_code=400, detail="Status must be approved or rejected")

    results = []
    for aid in approval_ids:
        approval = await db.get(ApprovalRequest, aid)
        if approval is None:
            raise HTTPException(status_code=404, detail=f"Approval {aid} not found")
        if approval.status != ApprovalStatus.PENDING:
            raise HTTPException(
                status_code=409,
                detail=f"Approval {aid} is already {approval.status.value}",
            )
        approval.status = status
        approval.decided_by = decided_by
        approval.decision_comment = comment
        approval.decided_at = datetime.now(timezone.utc)
        results.append(approval)

    await db.flush()
    for r in results:
        await db.refresh(r)
    return results


async def get_pending_approvals_for_user(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> list[ApprovalRequest]:
    """All pending approvals where user is a project lead (simplified: all pending)."""
    result = await db.execute(
        select(ApprovalRequest)
        .where(ApprovalRequest.status == ApprovalStatus.PENDING)
        .order_by(ApprovalRequest.created_at.asc())
    )
    return list(result.scalars().all())


async def create_delegation(
    db: AsyncSession,
    delegator_id: uuid.UUID,
    delegate_id: uuid.UUID,
    project_id: uuid.UUID | None = None,
    active_until: datetime | None = None,
) -> ApprovalDelegation:
    delegation = ApprovalDelegation(
        delegator_id=delegator_id,
        delegate_id=delegate_id,
        project_id=project_id,
        active_until=active_until,
    )
    db.add(delegation)
    await db.flush()
    await db.refresh(delegation)
    return delegation


async def list_delegations(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> list[ApprovalDelegation]:
    result = await db.execute(
        select(ApprovalDelegation).where(
            ApprovalDelegation.delegator_id == user_id,
            ApprovalDelegation.is_active.is_(True),
        )
    )
    return list(result.scalars().all())


async def check_expired_approvals(
    db: AsyncSession,
) -> list[ApprovalRequest]:
    """Return approvals that have expired (for escalation processing)."""
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(ApprovalRequest).where(
            ApprovalRequest.status == ApprovalStatus.PENDING,
            ApprovalRequest.expires_at.isnot(None),
            ApprovalRequest.expires_at < now,
        )
    )
    return list(result.scalars().all())
