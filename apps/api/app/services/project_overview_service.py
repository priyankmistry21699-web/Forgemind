"""Project overview service — composite dashboard data.

FM-150: Team Dashboard & Project Overview Redesign.
"""

import uuid

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.run import Run
from app.models.task import Task, TaskStatus
from app.models.approval_request import ApprovalRequest, ApprovalStatus
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
        {
            "user_id": str(m.user_id),
            "role": m.role.value if hasattr(m.role, "value") else str(m.role),
        }
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


async def get_cross_project_dashboard(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> dict:
    """Aggregate dashboard across all projects the user belongs to (FM-148).

    Returns per-project summaries with health grades, pending approval details,
    and cross-project totals.
    """
    # Get all project IDs this user is a member of
    member_result = await db.execute(
        select(ProjectMember.project_id).where(
            ProjectMember.user_id == user_id,
        )
    )
    project_ids = [r for (r,) in member_result.all()]

    if not project_ids:
        return {
            "projects": [],
            "totals": {
                "total_runs": 0,
                "successful_runs": 0,
                "open_tasks": 0,
                "pending_approvals": 0,
                "project_count": 0,
                "overall_success_rate": 100.0,
            },
        }

    from app.models.project import Project
    from app.models.approval_request import ApprovalRequest, ApprovalStatus

    summaries = []
    agg_runs = agg_success = agg_tasks = agg_approvals = 0

    for pid in project_ids:
        overview = await get_project_overview(db, pid)

        p_result = await db.execute(select(Project.name).where(Project.id == pid))
        name = p_result.scalar_one_or_none() or "Unknown"

        # Health grade based on success rate
        total_r = overview["total_runs"]
        success_r = overview["successful_runs"]
        rate = (success_r / total_r * 100) if total_r > 0 else 100
        if rate >= 90:
            health_grade = "A"
        elif rate >= 75:
            health_grade = "B"
        elif rate >= 60:
            health_grade = "C"
        elif rate >= 40:
            health_grade = "D"
        else:
            health_grade = "F"

        # Per-project pending approval details
        pending_q = await db.execute(
            select(ApprovalRequest)
            .where(
                ApprovalRequest.project_id == pid,
                ApprovalRequest.status == ApprovalStatus.PENDING,
            )
            .limit(10)
        )
        pending_items = [
            {
                "approval_id": str(a.id),
                "task_id": str(a.task_id) if a.task_id else None,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in pending_q.scalars().all()
        ]

        entry = {
            "project_id": str(pid),
            "name": name,
            "health_grade": health_grade,
            "success_rate": round(rate, 1),
            "pending_approval_details": pending_items,
            **overview,
        }
        summaries.append(entry)
        agg_runs += total_r
        agg_success += success_r
        agg_tasks += overview["open_tasks"]
        agg_approvals += overview["pending_approvals"]

    overall_rate = (agg_success / agg_runs * 100) if agg_runs > 0 else 100

    return {
        "projects": summaries,
        "totals": {
            "total_runs": agg_runs,
            "successful_runs": agg_success,
            "overall_success_rate": round(overall_rate, 1),
            "open_tasks": agg_tasks,
            "pending_approvals": agg_approvals,
            "project_count": len(project_ids),
        },
    }
