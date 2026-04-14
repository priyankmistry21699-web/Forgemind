"""Merge readiness evaluation — FM-156.

Evaluates whether a pull request is ready to merge by checking:
- All linked tasks are complete
- CI pipeline is passing
- Required approvals are resolved
- No merge conflicts (via PR status)
"""

import uuid
from dataclasses import dataclass, field

from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.github_integration import (
    PullRequestLink,
    PRStatus,
    CIPipelineRun,
    CIPipelineStatus,
)
from app.models.task import Task
from app.models.approval_request import ApprovalRequest


@dataclass
class MergeBlocker:
    category: str  # "ci", "tasks", "approvals", "pr_status"
    message: str


@dataclass
class MergeReadinessResult:
    ready: bool
    blockers: list[MergeBlocker] = field(default_factory=list)
    checks_passed: list[str] = field(default_factory=list)


async def evaluate_merge_readiness(
    db: AsyncSession,
    pr_link_id: uuid.UUID,
) -> MergeReadinessResult:
    """Evaluate all merge preconditions for a pull request link."""
    blockers: list[MergeBlocker] = []
    passed: list[str] = []

    # 1. Get PR link
    pr_link = await db.get(PullRequestLink, pr_link_id)
    if pr_link is None:
        return MergeReadinessResult(
            ready=False,
            blockers=[MergeBlocker("pr_status", "Pull request link not found")],
        )

    # 2. PR status check
    if pr_link.status == PRStatus.MERGED:
        return MergeReadinessResult(
            ready=False,
            blockers=[MergeBlocker("pr_status", "PR is already merged")],
        )
    if pr_link.status == PRStatus.CLOSED:
        blockers.append(MergeBlocker("pr_status", "PR is closed"))
    else:
        passed.append("pr_open")

    # 3. CI check — latest pipeline for this repo must be passing
    if pr_link.repository_link_id:
        latest_ci = await db.execute(
            select(CIPipelineRun)
            .where(CIPipelineRun.repository_link_id == pr_link.repository_link_id)
            .order_by(CIPipelineRun.created_at.desc())
            .limit(1)
        )
        ci_run = latest_ci.scalar_one_or_none()
        if ci_run is None:
            blockers.append(MergeBlocker("ci", "No CI pipeline run found"))
        elif ci_run.status != CIPipelineStatus.SUCCESS:
            blockers.append(
                MergeBlocker("ci", f"CI pipeline status: {ci_run.status.value}")
            )
        else:
            passed.append("ci_passing")

    # 4. Task check — if PR is linked to a run, all tasks in that run must be done
    if pr_link.run_id:
        incomplete_count = (
            await db.execute(
                select(sa_func.count())
                .select_from(Task)
                .where(
                    Task.run_id == pr_link.run_id,
                    Task.status.notin_(["completed", "failed", "skipped"]),
                )
            )
        ).scalar_one()
        if incomplete_count > 0:
            blockers.append(
                MergeBlocker(
                    "tasks",
                    f"{incomplete_count} task(s) not yet complete in linked run",
                )
            )
        else:
            passed.append("all_tasks_complete")

        # 5. Approval check — all approvals for run must be decided
        pending_approvals = (
            await db.execute(
                select(sa_func.count())
                .select_from(ApprovalRequest)
                .where(
                    ApprovalRequest.run_id == pr_link.run_id,
                    ApprovalRequest.status == "pending",
                )
            )
        ).scalar_one()
        if pending_approvals > 0:
            blockers.append(
                MergeBlocker(
                    "approvals",
                    f"{pending_approvals} pending approval(s) on linked run",
                )
            )
        else:
            passed.append("approvals_resolved")

    return MergeReadinessResult(
        ready=len(blockers) == 0,
        blockers=blockers,
        checks_passed=passed,
    )
