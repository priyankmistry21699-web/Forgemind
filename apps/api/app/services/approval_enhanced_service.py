"""Enhanced approval service — delegation, batch approval, dashboard.

FM-148: Approval Workflow Enhancements.
"""

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select, or_, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.approval_request import ApprovalRequest, ApprovalStatus
from app.models.approval_delegation import ApprovalDelegation
from app.models.membership import ProjectMember, ProjectRole


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
    """Pending approvals scoped to the current user.

    Returns approvals for projects where the user is:
      1. A project lead or flagged as approver (via ProjectMember), OR
      2. An active delegate for the project (via ApprovalDelegation).
    """
    now = datetime.now(timezone.utc)

    # Sub-query: project IDs where user is a lead or designated approver
    lead_projects = (
        select(ProjectMember.project_id)
        .where(
            ProjectMember.user_id == user_id,
            or_(
                ProjectMember.role == ProjectRole.LEAD,
                ProjectMember.is_approver.is_(True),
            ),
        )
    )

    # Sub-query: project IDs where user is an active, non-expired delegate
    delegated_projects = (
        select(ApprovalDelegation.project_id)
        .where(
            ApprovalDelegation.delegate_id == user_id,
            ApprovalDelegation.is_active.is_(True),
            ApprovalDelegation.project_id.isnot(None),
            or_(
                ApprovalDelegation.active_until.is_(None),
                ApprovalDelegation.active_until > now,
            ),
        )
    )

    result = await db.execute(
        select(ApprovalRequest)
        .where(
            ApprovalRequest.status == ApprovalStatus.PENDING,
            or_(
                ApprovalRequest.project_id.in_(lead_projects),
                ApprovalRequest.project_id.in_(delegated_projects),
            ),
        )
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
    """Return approvals that have expired and have NOT yet been escalated."""
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(ApprovalRequest).where(
            ApprovalRequest.status == ApprovalStatus.PENDING,
            ApprovalRequest.expires_at.isnot(None),
            ApprovalRequest.expires_at < now,
            ApprovalRequest.escalated_at.is_(None),
        )
    )
    return list(result.scalars().all())


async def escalate_expired_approvals(
    db: AsyncSession,
) -> list[dict]:
    """Delegation-aware escalation of expired approvals.

    For each expired pending approval:
    1. Find active delegates for the approval's project.
    2. Find project leads as fallback escalation targets.
    3. Create an ESCALATION notification for each target via notification_service.
    4. Return an escalation report with recommended targets and notifications.

    This enables callers (routes, cron jobs) to trigger real escalation.
    """
    from app.services import notification_service

    expired = await check_expired_approvals(db)
    if not expired:
        return []

    escalation_report: list[dict] = []

    for approval in expired:
        now = datetime.now(timezone.utc)

        # Find active, non-expired delegates for this project
        delegate_result = await db.execute(
            select(ApprovalDelegation).where(
                ApprovalDelegation.project_id == approval.project_id,
                ApprovalDelegation.is_active.is_(True),
                or_(
                    ApprovalDelegation.active_until.is_(None),
                    ApprovalDelegation.active_until > now,
                ),
            )
        )
        delegates = list(delegate_result.scalars().all())

        # Find project leads as fallback
        lead_result = await db.execute(
            select(ProjectMember).where(
                ProjectMember.project_id == approval.project_id,
                or_(
                    ProjectMember.role == ProjectRole.LEAD,
                    ProjectMember.is_approver.is_(True),
                ),
            )
        )
        leads = list(lead_result.scalars().all())

        # Build escalation targets: delegates first, then leads
        targets: list[dict] = []
        seen_user_ids: set[uuid.UUID] = set()
        notifications_created: list[str] = []

        for d in delegates:
            if d.delegate_id not in seen_user_ids:
                seen_user_ids.add(d.delegate_id)
                targets.append({
                    "user_id": str(d.delegate_id),
                    "role": "delegate",
                    "delegator_id": str(d.delegator_id),
                })

        for lead in leads:
            if lead.user_id not in seen_user_ids:
                seen_user_ids.add(lead.user_id)
                targets.append({
                    "user_id": str(lead.user_id),
                    "role": "lead" if lead.role == ProjectRole.LEAD else "approver",
                })

        # Create notifications for each escalation target
        for target in targets:
            notif = await notification_service.create_notification(
                db,
                user_id=uuid.UUID(target["user_id"]),
                notification_type="escalation",
                title=f"Escalation: {approval.title}",
                priority="high",
                body=(
                    f"Approval \"{approval.title}\" has expired and requires "
                    f"attention. You are being notified as a {target['role']}."
                ),
                resource_type="approval_request",
                resource_id=approval.id,
                metadata_={
                    "escalation_role": target["role"],
                    "project_id": str(approval.project_id),
                },
            )
            notifications_created.append(str(notif.id))

        # Mark this approval as escalated so it won't be re-processed
        approval.escalated_at = datetime.now(timezone.utc)

        escalation_report.append({
            "approval_id": str(approval.id),
            "title": approval.title,
            "project_id": str(approval.project_id),
            "expired_at": approval.expires_at.isoformat() if approval.expires_at else None,
            "escalation_targets": targets,
            "target_count": len(targets),
            "notifications_created": notifications_created,
        })

    return escalation_report


async def deactivate_expired_delegations(
    db: AsyncSession,
) -> int:
    """Deactivate delegations whose active_until has passed.

    Returns the number of delegations deactivated.
    """
    now = datetime.now(timezone.utc)
    result = await db.execute(
        update(ApprovalDelegation)
        .where(
            ApprovalDelegation.is_active.is_(True),
            ApprovalDelegation.active_until.isnot(None),
            ApprovalDelegation.active_until < now,
        )
        .values(is_active=False)
    )
    return result.rowcount


async def revoke_delegation(
    db: AsyncSession,
    delegation_id: uuid.UUID,
    user_id: uuid.UUID,
) -> ApprovalDelegation | None:
    """Revoke (deactivate) a delegation. Only the delegator can revoke."""
    delegation = await db.get(ApprovalDelegation, delegation_id)
    if delegation is None:
        return None
    if delegation.delegator_id != user_id:
        raise HTTPException(
            status_code=403,
            detail="Only the delegator can revoke a delegation",
        )
    delegation.is_active = False
    await db.flush()
    await db.refresh(delegation)
    return delegation
