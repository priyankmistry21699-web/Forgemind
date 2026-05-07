"""FM-248: Platform admin stats service."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func as sa_func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.workspace import Workspace
from app.models.project import Project
from app.models.run import Run, RunStatus
from app.models.agent_intelligence import LLMCallLog
from app.models.agent_intelligence import SecurityFinding


async def get_platform_stats(db: AsyncSession) -> dict[str, Any]:
    """Return aggregate platform statistics for super-admin view."""
    now = datetime.now(timezone.utc)
    last_30 = now - timedelta(days=30)
    last_7 = now - timedelta(days=7)

    # Counts
    user_count = int(
        (await db.execute(select(sa_func.count(User.id)))).scalar_one() or 0
    )
    workspace_count = int(
        (await db.execute(select(sa_func.count(Workspace.id)))).scalar_one() or 0
    )
    project_count = int(
        (await db.execute(select(sa_func.count(Project.id)))).scalar_one() or 0
    )

    # Run stats
    total_runs = int(
        (await db.execute(select(sa_func.count(Run.id)))).scalar_one() or 0
    )
    active_runs = int(
        (
            await db.execute(
                select(sa_func.count(Run.id)).where(
                    Run.status.in_([RunStatus.RUNNING, RunStatus.PLANNING])
                )
            )
        ).scalar_one()
        or 0
    )
    runs_last_7d = int(
        (
            await db.execute(
                select(sa_func.count(Run.id)).where(Run.created_at >= last_7)
            )
        ).scalar_one()
        or 0
    )

    # Cost
    total_cost_30d = float(
        (
            await db.execute(
                select(sa_func.sum(LLMCallLog.cost_usd)).where(
                    LLMCallLog.created_at >= last_30
                )
            )
        ).scalar_one()
        or 0.0
    )
    total_cost_7d = float(
        (
            await db.execute(
                select(sa_func.sum(LLMCallLog.cost_usd)).where(
                    LLMCallLog.created_at >= last_7
                )
            )
        ).scalar_one()
        or 0.0
    )

    # LLM call counts
    llm_calls_30d = int(
        (
            await db.execute(
                select(sa_func.count(LLMCallLog.id)).where(
                    LLMCallLog.created_at >= last_30
                )
            )
        ).scalar_one()
        or 0
    )

    # Security
    open_findings = int(
        (
            await db.execute(
                select(sa_func.count(SecurityFinding.id)).where(
                    SecurityFinding.resolved.is_(False)
                )
            )
        ).scalar_one()
        or 0
    )
    critical_findings = int(
        (
            await db.execute(
                select(sa_func.count(SecurityFinding.id)).where(
                    SecurityFinding.resolved.is_(False),
                    SecurityFinding.severity == "critical",
                )
            )
        ).scalar_one()
        or 0
    )

    # Top projects by cost
    top_projects_q = (
        select(Project.id, Project.name, sa_func.sum(LLMCallLog.cost_usd).label("cost"))
        .join(Run, Run.project_id == Project.id)
        .join(LLMCallLog, LLMCallLog.run_id == Run.id)
        .where(LLMCallLog.created_at >= last_30)
        .group_by(Project.id, Project.name)
        .order_by(sa_func.sum(LLMCallLog.cost_usd).desc())
        .limit(5)
    )
    top_projects_result = await db.execute(top_projects_q)
    top_projects = [
        {"id": str(r.id), "name": r.name, "cost_usd_30d": round(float(r.cost or 0), 4)}
        for r in top_projects_result.all()
    ]

    return {
        "generated_at": now.isoformat(),
        "users": {"total": user_count},
        "workspaces": {"total": workspace_count},
        "projects": {"total": project_count},
        "runs": {
            "total": total_runs,
            "active": active_runs,
            "last_7_days": runs_last_7d,
        },
        "llm_costs": {
            "total_usd_30d": round(total_cost_30d, 4),
            "total_usd_7d": round(total_cost_7d, 4),
            "calls_30d": llm_calls_30d,
        },
        "security": {
            "open_findings": open_findings,
            "critical_findings": critical_findings,
        },
        "top_projects_by_cost_30d": top_projects,
    }
