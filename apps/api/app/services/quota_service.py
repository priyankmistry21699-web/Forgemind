"""FM-241: Resource quota service."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import func as sa_func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.platform_ops import ResourceQuota
from app.models.run import Run, RunStatus
from app.models.project import Project


async def get_quota(
    db: AsyncSession,
    workspace_id: uuid.UUID,
) -> ResourceQuota | None:
    result = await db.execute(
        select(ResourceQuota).where(ResourceQuota.workspace_id == workspace_id)
    )
    return result.scalar_one_or_none()


async def upsert_quota(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    *,
    max_concurrent_runs: int | None = None,
    max_projects: int | None = None,
    max_monthly_cost_usd: float | None = None,
    max_api_calls_per_minute: int | None = None,
    max_storage_gb: float | None = None,
    enforce: bool = True,
) -> ResourceQuota:
    quota = await get_quota(db, workspace_id)
    if quota is None:
        quota = ResourceQuota(workspace_id=workspace_id)
        db.add(quota)

    if max_concurrent_runs is not None:
        quota.max_concurrent_runs = max_concurrent_runs
    if max_projects is not None:
        quota.max_projects = max_projects
    if max_monthly_cost_usd is not None:
        quota.max_monthly_cost_usd = max_monthly_cost_usd
    if max_api_calls_per_minute is not None:
        quota.max_api_calls_per_minute = max_api_calls_per_minute
    if max_storage_gb is not None:
        quota.max_storage_gb = max_storage_gb
    quota.enforce = enforce
    await db.flush()
    return quota


async def check_quota_violations(
    db: AsyncSession,
    workspace_id: uuid.UUID,
) -> dict[str, Any]:
    """Return current usage vs quota limits for a workspace."""
    quota = await get_quota(db, workspace_id)
    if quota is None:
        return {"workspace_id": str(workspace_id), "quota_defined": False, "violations": []}

    violations = []
    usage: dict[str, Any] = {}

    # Concurrent runs
    active_runs_q = select(sa_func.count(Run.id)).where(
        Run.project_id.in_(
            select(Project.id).where(Project.workspace_id == workspace_id)
        ),
        Run.status.in_([RunStatus.RUNNING, RunStatus.PLANNING]),
    )
    active_runs = int((await db.execute(active_runs_q)).scalar_one() or 0)
    usage["active_runs"] = active_runs
    if quota.max_concurrent_runs and active_runs >= quota.max_concurrent_runs:
        violations.append(
            {"limit": "max_concurrent_runs", "limit_value": quota.max_concurrent_runs, "current": active_runs}
        )

    # Project count
    project_count_q = select(sa_func.count(Project.id)).where(
        Project.workspace_id == workspace_id
    )
    project_count = int((await db.execute(project_count_q)).scalar_one() or 0)
    usage["project_count"] = project_count
    if quota.max_projects and project_count >= quota.max_projects:
        violations.append(
            {"limit": "max_projects", "limit_value": quota.max_projects, "current": project_count}
        )

    return {
        "workspace_id": str(workspace_id),
        "quota_defined": True,
        "enforce": quota.enforce,
        "usage": usage,
        "violations": violations,
        "within_limits": len(violations) == 0,
    }
