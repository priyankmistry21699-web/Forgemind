"""Approval service — create and resolve human-in-the-loop approval requests."""

import uuid
import logging
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.approval_request import ApprovalRequest, ApprovalStatus
from app.schemas.approval import ApprovalCreate, ApprovalDecision
from app.services import event_service
from app.models.execution_event import EventType

logger = logging.getLogger(__name__)


async def create_approval(
    db: AsyncSession,
    data: ApprovalCreate,
) -> ApprovalRequest:
    """Create a new pending approval request."""
    approval = ApprovalRequest(
        title=data.title,
        description=data.description,
        project_id=data.project_id,
        run_id=data.run_id,
        task_id=data.task_id,
        artifact_id=data.artifact_id,
        status=ApprovalStatus.PENDING,
    )
    db.add(approval)
    await db.flush()
    await db.refresh(approval)

    # FM-055: Create notification for approval request
    try:
        from app.services import notification_service
        await notification_service.create_notification(
            db,
            user_id=approval.project_id,  # placeholder - should route to project reviewers
            notification_type="approval_required",
            title=f"Approval required: {approval.title}",
            priority="high",
            body=approval.description,
            resource_type="approval",
            resource_id=approval.id,
        )
    except Exception:
        logger.warning("Failed to create notification for approval %s", approval.id, exc_info=True)

    # FM-054: Publish stream event
    try:
        from app.services.stream_service import publish_run_event
        if approval.run_id:
            await publish_run_event(
                approval.run_id,
                "approval_created",
                {"approval_id": str(approval.id), "title": approval.title},
            )
    except Exception:
        logger.debug("Stream publish failed for approval %s", approval.id, exc_info=True)

    return approval


async def get_approval(
    db: AsyncSession,
    approval_id: uuid.UUID,
) -> ApprovalRequest:
    """Get a single approval request by ID."""
    result = await db.execute(
        select(ApprovalRequest).where(ApprovalRequest.id == approval_id)
    )
    approval = result.scalar_one_or_none()
    if approval is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Approval request not found",
        )
    return approval


async def list_approvals(
    db: AsyncSession,
    *,
    project_id: uuid.UUID | None = None,
    run_id: uuid.UUID | None = None,
    status_filter: ApprovalStatus | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[ApprovalRequest], int]:
    """List approval requests with optional filters."""
    query = select(ApprovalRequest)

    if project_id is not None:
        query = query.where(ApprovalRequest.project_id == project_id)
    if run_id is not None:
        query = query.where(ApprovalRequest.run_id == run_id)
    if status_filter is not None:
        query = query.where(ApprovalRequest.status == status_filter)

    count_result = await db.execute(
        select(sa_func.count()).select_from(query.subquery())
    )
    total = count_result.scalar_one()

    result = await db.execute(
        query.order_by(ApprovalRequest.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    approvals = list(result.scalars().all())
    return approvals, total


async def resolve_approval(
    db: AsyncSession,
    approval_id: uuid.UUID,
    decision: ApprovalDecision,
) -> ApprovalRequest:
    """Approve or reject a pending approval request."""
    approval = await get_approval(db, approval_id)

    if approval.status != ApprovalStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Approval is already {approval.status.value}",
        )

    if decision.status not in (ApprovalStatus.APPROVED, ApprovalStatus.REJECTED):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Decision must be 'approved' or 'rejected'",
        )

    approval.status = decision.status
    approval.decided_by = decision.decided_by
    approval.decision_comment = decision.decision_comment
    approval.decided_at = datetime.now(timezone.utc)

    await db.flush()

    # Emit event
    await event_service.emit_event(
        db,
        event_type=EventType.APPROVAL_RESOLVED,
        summary=f"Approval '{approval.title}' {decision.status.value} by {decision.decided_by or 'unknown'}",
        project_id=approval.project_id,
        run_id=approval.run_id,
        task_id=approval.task_id,
        metadata={
            "approval_id": str(approval.id),
            "decision": decision.status.value,
            "comment": decision.decision_comment,
        },
    )

    # FM-055: Notify about resolution
    try:
        from app.services import notification_service
        ntype = "approval_granted" if decision.status == ApprovalStatus.APPROVED else "approval_denied"
        await notification_service.create_notification(
            db,
            user_id=approval.project_id,  # placeholder
            notification_type=ntype,
            title=f"Approval {decision.status.value}: {approval.title}",
            priority="normal",
            body=decision.decision_comment,
            resource_type="approval",
            resource_id=approval.id,
        )
    except Exception:
        logger.warning("Failed to create notification for resolved approval %s", approval.id, exc_info=True)

    # FM-054: Publish stream event
    try:
        from app.services.stream_service import publish_run_event
        if approval.run_id:
            await publish_run_event(
                approval.run_id,
                "approval_resolved",
                {
                    "approval_id": str(approval.id),
                    "decision": decision.status.value,
                },
            )
    except Exception:
        logger.debug("Stream publish failed for resolved approval %s", approval.id, exc_info=True)

    await db.refresh(approval)
    return approval
