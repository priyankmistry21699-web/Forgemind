"""Project overview service — composite dashboard data.

FM-150: Team Dashboard & Project Overview Redesign.
"""

import uuid

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.run import Run
from app.models.task import Task, TaskStatus
from app.models.approval_request import ApprovalRequest, ApprovalStatus
from app.models.activity import UserPresence
from app.models.membership import ProjectMember


async def get_project_overview(
    db: AsyncSession,
    project_id: uuid.UUID,
) -> dict:
    """Return composite health, team, and activity data."""
    # Run stats
    total_runs_r = await db.execute(
        select(func.count()).where(Run.project_id == project_id)
    )
    total_runs = total_runs_r.scalar_one()

    successful_r = await db.execute(
        select(func.count()).where(
            Run.project_id == project_id, Run.status == "completed"
        )
    )
    successful = successful_r.scalar_one()

    # Task stats
    open_tasks_r = await db.execute(
        select(func.count())
        .select_from(Task)
        .join(Run, Run.id == Task.run_id)
        .where(
            Run.project_id == project_id,
            Task.status.notin_([TaskStatus.COMPLETED, TaskStatus.SKIPPED]),
        )
    )
    open_tasks = open_tasks_r.scalar_one()

    # Pending approvals
    pending_r = await db.execute(
        select(func.count()).where(
            ApprovalRequest.project_id == project_id,
            ApprovalRequest.status == ApprovalStatus.PENDING,
        )
    )
    pending_approvals = pending_r.scalar_one()

    # Team members
    members_r = await db.execute(
        select(ProjectMember.user_id, ProjectMember.role).where(
            ProjectMember.project_id == project_id
        )
    )
    members = [
        {"user_id": str(m.user_id), "role": m.role.value if hasattr(m.role, "value") else str(m.role)}
        for m in members_r.all()
    ]

    # Health score (simple: run success rate as percentage)
    success_rate = (successful / total_runs * 100) if total_runs > 0 else 100

    if success_rate >= 90:
        grade = "A"
    elif success_rate >= 75:
        grade = "B"
    elif success_rate >= 60:
        grade = "C"
    elif success_rate >= 45:
        grade = "D"
    else:
        grade = "F"

    return {
        "total_runs": total_runs,
        "successful_runs": successful,
        "success_rate": round(success_rate, 1),
        "open_tasks": open_tasks,
        "pending_approvals": pending_approvals,
        "health_grade": grade,
        "team_members": members,
        "team_size": len(members),
    }
