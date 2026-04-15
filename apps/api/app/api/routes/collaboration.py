"""Collaboration routes — task assignment, approval delegation, project overview.

FM-147: Task Assignment & Workload Visibility.
FM-148: Approval Delegation & Batch Decisions.
FM-150: Team Dashboard & Project Overview.
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.auth import get_current_user_id
from app.services import (
    task_assignment_service,
    approval_enhanced_service,
    project_overview_service,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class TaskAssignRequest(BaseModel):
    assignee_id: uuid.UUID


class TaskAssignRead(BaseModel):
    id: uuid.UUID
    title: str | None = None
    assignee_id: uuid.UUID | None = None
    assigned_at: datetime | None = None
    status: str

    model_config = {"from_attributes": True}


class WorkloadEntry(BaseModel):
    user_id: str
    tasks: dict[str, int]


class DelegationCreateRequest(BaseModel):
    delegate_id: uuid.UUID
    project_id: uuid.UUID | None = None
    active_until: datetime | None = None


class DelegationRead(BaseModel):
    id: uuid.UUID
    delegator_id: uuid.UUID
    delegate_id: uuid.UUID
    project_id: uuid.UUID | None = None
    active_until: datetime | None = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class BatchDecisionRequest(BaseModel):
    approval_ids: list[uuid.UUID]
    status: str  # "approved" or "rejected"
    comment: str | None = None


# ---------------------------------------------------------------------------
# FM-147: Task Assignment
# ---------------------------------------------------------------------------


@router.post("/tasks/{task_id}/assign", response_model=TaskAssignRead)
async def assign_task(
    task_id: uuid.UUID,
    body: TaskAssignRequest,
    db: AsyncSession = Depends(get_db),
    _user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Assign a task to a user."""
    task = await task_assignment_service.assign_task(db, task_id, body.assignee_id)
    return TaskAssignRead(
        id=task.id,
        title=task.title,
        assignee_id=task.assignee_id,
        assigned_at=task.assigned_at,
        status=task.status.value if hasattr(task.status, "value") else str(task.status),
    )


@router.delete("/tasks/{task_id}/assign", response_model=TaskAssignRead)
async def unassign_task(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Remove assignment from a task."""
    task = await task_assignment_service.unassign_task(db, task_id)
    return TaskAssignRead(
        id=task.id,
        title=task.title,
        assignee_id=task.assignee_id,
        assigned_at=task.assigned_at,
        status=task.status.value if hasattr(task.status, "value") else str(task.status),
    )


@router.get("/users/me/assigned-tasks", response_model=list[TaskAssignRead])
async def my_assigned_tasks(
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """List all active tasks assigned to the current user."""
    tasks = await task_assignment_service.list_user_assigned_tasks(db, user_id)
    return [
        TaskAssignRead(
            id=t.id,
            title=t.title,
            assignee_id=t.assignee_id,
            assigned_at=t.assigned_at,
            status=t.status.value if hasattr(t.status, "value") else str(t.status),
        )
        for t in tasks
    ]


@router.get(
    "/projects/{project_id}/workload", response_model=list[WorkloadEntry]
)
async def project_workload(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Get task workload distribution for a project."""
    return await task_assignment_service.get_project_workload(db, project_id)


# ---------------------------------------------------------------------------
# FM-148: Approval Delegation
# ---------------------------------------------------------------------------


@router.post("/approval-delegations", response_model=DelegationRead)
async def create_delegation(
    body: DelegationCreateRequest,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Create an approval delegation from the current user to a delegate."""
    delegation = await approval_enhanced_service.create_delegation(
        db,
        delegator_id=user_id,
        delegate_id=body.delegate_id,
        project_id=body.project_id,
        active_until=body.active_until,
    )
    return delegation


@router.get("/approval-delegations", response_model=list[DelegationRead])
async def list_my_delegations(
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """List active approval delegations created by the current user."""
    return await approval_enhanced_service.list_delegations(db, user_id)


@router.get("/approval-delegations/pending", response_model=list)
async def pending_approvals(
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """List all pending approvals visible to the current user."""
    approvals = await approval_enhanced_service.get_pending_approvals_for_user(
        db, user_id
    )
    return [
        {
            "id": str(a.id),
            "title": a.title,
            "status": a.status.value if hasattr(a.status, "value") else str(a.status),
            "project_id": str(a.project_id) if a.project_id else None,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in approvals
    ]


@router.post("/approval-delegations/batch-decide")
async def batch_decide(
    body: BatchDecisionRequest,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Approve or reject multiple approval requests atomically."""
    from app.models.approval_request import ApprovalStatus

    status_map = {
        "approved": ApprovalStatus.APPROVED,
        "rejected": ApprovalStatus.REJECTED,
    }
    mapped_status = status_map.get(body.status)
    if mapped_status is None:
        raise HTTPException(
            status_code=400, detail="status must be 'approved' or 'rejected'"
        )

    results = await approval_enhanced_service.batch_decide(
        db,
        approval_ids=body.approval_ids,
        status=mapped_status,
        decided_by=str(user_id),
        comment=body.comment,
    )
    return {
        "decided": len(results),
        "status": body.status,
        "approval_ids": [str(r.id) for r in results],
    }


@router.get("/approval-delegations/expired")
async def expired_approvals(
    db: AsyncSession = Depends(get_db),
    _user_id: uuid.UUID = Depends(get_current_user_id),
):
    """List expired pending approvals (for escalation)."""
    expired = await approval_enhanced_service.check_expired_approvals(db)
    return {
        "count": len(expired),
        "items": [
            {
                "id": str(a.id),
                "title": a.title,
                "expires_at": a.expires_at.isoformat() if a.expires_at else None,
            }
            for a in expired
        ],
    }


@router.post("/approval-delegations/escalate")
async def escalate_expired(
    db: AsyncSession = Depends(get_db),
    _user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Run delegation-aware escalation on expired approvals.

    Returns an escalation report identifying the right people to notify
    for each expired approval, considering active delegations and project leads.
    """
    report = await approval_enhanced_service.escalate_expired_approvals(db)
    return {
        "escalated_count": len(report),
        "escalations": report,
    }


# ---------------------------------------------------------------------------
# FM-150: Project Overview / Dashboard
# ---------------------------------------------------------------------------


@router.get("/projects/{project_id}/overview")
async def project_overview(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Get composite project dashboard: health, runs, tasks, team, approvals."""
    return await project_overview_service.get_project_overview(db, project_id)
