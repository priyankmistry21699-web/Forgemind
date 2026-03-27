"""Run lifecycle service — health checks, auto-completion, stuck run detection.

FM-046: Monitors run health and manages lifecycle transitions:
- Detect stuck runs (no progress for configurable duration)
- Auto-complete runs when all tasks are done
- Auto-fail runs when unrecoverable failures exist
- Health check summaries for operator dashboards
"""

import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import Any

from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.run import Run, RunStatus
from app.models.task import Task, TaskStatus
from app.models.execution_event import EventType
from app.services import event_service

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configurable thresholds
# ---------------------------------------------------------------------------

STUCK_RUN_THRESHOLD_MINUTES = 60  # No progress for 60 min = stuck
AUTO_FAIL_EXHAUSTED_RETRIES = True  # Fail run if blocking tasks exhausted retries


class RunHealth:
    HEALTHY = "healthy"
    DEGRADED = "degraded"       # Some failures but progress possible
    STUCK = "stuck"             # No progress for extended time
    CRITICAL = "critical"       # Blocking failures, cannot proceed
    COMPLETED = "completed"
    FAILED = "failed"


async def get_run_health(
    db: AsyncSession,
    run_id: uuid.UUID,
) -> dict[str, Any]:
    """Compute comprehensive health status for a run.

    Returns:
        run_id, status, health, progress, task_breakdown,
        stuck_since, blocking_issues, suggested_actions
    """
    run_result = await db.execute(select(Run).where(Run.id == run_id))
    run = run_result.scalar_one_or_none()
    if run is None:
        return {"error": "Run not found"}

    # Terminal states
    if run.status in (RunStatus.COMPLETED, RunStatus.FAILED):
        return {
            "run_id": str(run.id),
            "run_number": run.run_number,
            "status": run.status.value,
            "health": RunHealth.COMPLETED if run.status == RunStatus.COMPLETED else RunHealth.FAILED,
            "progress": 1.0 if run.status == RunStatus.COMPLETED else None,
            "task_breakdown": {},
            "stuck_since": None,
            "blocking_issues": [],
            "suggested_actions": [],
        }

    # Get task breakdown
    task_result = await db.execute(
        select(Task).where(Task.run_id == run_id)
    )
    tasks = list(task_result.scalars().all())

    status_counts: dict[str, int] = {}
    for t in tasks:
        status_counts[t.status.value] = status_counts.get(t.status.value, 0) + 1

    total = len(tasks)
    completed = status_counts.get("completed", 0)
    failed = status_counts.get("failed", 0)
    running = status_counts.get("running", 0)
    blocked = status_counts.get("blocked", 0)
    ready = status_counts.get("ready", 0)
    progress = completed / total if total > 0 else 0.0

    # Detect blocking issues
    blocking_issues: list[str] = []

    # Failed tasks that block downstream
    failed_tasks = [t for t in tasks if t.status == TaskStatus.FAILED]
    for ft in failed_tasks:
        ft_id_str = str(ft.id)
        downstream = [
            t for t in tasks
            if t.depends_on and (ft.id in t.depends_on or ft_id_str in t.depends_on)
            and t.status in (TaskStatus.BLOCKED, TaskStatus.PENDING)
        ]
        if downstream:
            blocking_issues.append(
                f"Failed task '{ft.title}' blocks {len(downstream)} downstream task(s)"
            )

    # Exhausted retries
    exhausted = [
        t for t in failed_tasks
        if t.retry_count >= t.max_retries and t.retry_policy != "no_retry"
    ]
    if exhausted:
        blocking_issues.append(
            f"{len(exhausted)} task(s) exhausted all retries"
        )

    # Stuck detection — check last event timestamp
    stuck_since = None
    from app.models.execution_event import ExecutionEvent
    last_event_result = await db.execute(
        select(ExecutionEvent.created_at)
        .where(ExecutionEvent.run_id == run_id)
        .order_by(ExecutionEvent.created_at.desc())
        .limit(1)
    )
    last_event_time = last_event_result.scalar_one_or_none()

    now = datetime.now(timezone.utc)
    if last_event_time:
        # Ensure timezone aware
        if last_event_time.tzinfo is None:
            last_event_time = last_event_time.replace(tzinfo=timezone.utc)
        elapsed = now - last_event_time
        if elapsed > timedelta(minutes=STUCK_RUN_THRESHOLD_MINUTES):
            stuck_since = last_event_time.isoformat()

    # Determine health
    health = RunHealth.HEALTHY
    if run.status == RunStatus.COMPLETED:
        health = RunHealth.COMPLETED
    elif run.status == RunStatus.FAILED:
        health = RunHealth.FAILED
    elif blocking_issues and ready == 0 and running == 0:
        health = RunHealth.CRITICAL
    elif stuck_since:
        health = RunHealth.STUCK
    elif failed > 0:
        health = RunHealth.DEGRADED

    # Suggested actions
    suggested_actions: list[str] = []
    if health == RunHealth.STUCK:
        suggested_actions.append("Run appears stuck — check for pending approvals or unresolvable blockers")
    if health == RunHealth.CRITICAL:
        suggested_actions.append("Run is in critical state — retry or create revision tasks for blocking failures")
    if failed > 0:
        retryable = [t for t in failed_tasks if t.retry_count < t.max_retries]
        if retryable:
            suggested_actions.append(f"Retry {len(retryable)} failed task(s)")
    if status_counts.get("pending", 0) > 0 and blocked > 0:
        suggested_actions.append("Resolve blocked tasks to enable pending work")
    if progress == 1.0 and run.status != RunStatus.COMPLETED:
        suggested_actions.append("All tasks complete — run can be finalized")

    return {
        "run_id": str(run.id),
        "run_number": run.run_number,
        "status": run.status.value,
        "health": health,
        "progress": round(progress, 3),
        "task_breakdown": status_counts,
        "stuck_since": stuck_since,
        "blocking_issues": blocking_issues,
        "suggested_actions": suggested_actions,
    }


async def try_auto_complete_run(
    db: AsyncSession,
    run_id: uuid.UUID,
) -> dict[str, Any]:
    """Check if a run can be auto-completed and transition if so.

    A run is auto-completable when all tasks are in terminal states
    (COMPLETED, SKIPPED) with no FAILED, RUNNING, BLOCKED, or PENDING tasks.
    """
    run_result = await db.execute(select(Run).where(Run.id == run_id))
    run = run_result.scalar_one_or_none()
    if run is None:
        return {"completed": False, "reason": "Run not found"}

    if run.status in (RunStatus.COMPLETED, RunStatus.FAILED):
        return {"completed": False, "reason": f"Run already {run.status.value}"}

    task_result = await db.execute(
        select(Task).where(Task.run_id == run_id)
    )
    tasks = list(task_result.scalars().all())

    if not tasks:
        return {"completed": False, "reason": "Run has no tasks"}

    terminal_states = {TaskStatus.COMPLETED, TaskStatus.SKIPPED}
    non_terminal = [t for t in tasks if t.status not in terminal_states]

    if non_terminal:
        remaining = {}
        for t in non_terminal:
            remaining[t.status.value] = remaining.get(t.status.value, 0) + 1
        return {
            "completed": False,
            "reason": f"Non-terminal tasks remain: {remaining}",
        }

    # All terminal — complete the run
    run.status = RunStatus.COMPLETED
    await db.flush()

    await event_service.emit_event(
        db,
        event_type=EventType.RUN_COMPLETED,
        summary=f"Run #{run.run_number} auto-completed — all tasks in terminal state",
        project_id=run.project_id,
        run_id=run.id,
        metadata={"action": "auto_complete", "total_tasks": len(tasks)},
    )

    return {"completed": True, "reason": "All tasks in terminal state"}


async def try_auto_fail_run(
    db: AsyncSession,
    run_id: uuid.UUID,
) -> dict[str, Any]:
    """Check if a run should be auto-failed due to unrecoverable state.

    A run is auto-failed when:
    - There are failed tasks with exhausted retries that block downstream work
    - No tasks are RUNNING or READY
    """
    run_result = await db.execute(select(Run).where(Run.id == run_id))
    run = run_result.scalar_one_or_none()
    if run is None:
        return {"failed": False, "reason": "Run not found"}

    if run.status in (RunStatus.COMPLETED, RunStatus.FAILED):
        return {"failed": False, "reason": f"Run already {run.status.value}"}

    task_result = await db.execute(
        select(Task).where(Task.run_id == run_id)
    )
    tasks = list(task_result.scalars().all())

    running = [t for t in tasks if t.status == TaskStatus.RUNNING]
    ready = [t for t in tasks if t.status == TaskStatus.READY]

    if running or ready:
        return {"failed": False, "reason": "Active tasks still in progress"}

    failed_blocking = []
    failed_tasks = [t for t in tasks if t.status == TaskStatus.FAILED]
    for ft in failed_tasks:
        if ft.retry_count >= ft.max_retries:
            ft_id_str = str(ft.id)
            downstream = [
                t for t in tasks
                if t.depends_on and (ft.id in t.depends_on or ft_id_str in t.depends_on)
                and t.status in (TaskStatus.BLOCKED, TaskStatus.PENDING)
            ]
            if downstream:
                failed_blocking.append(ft)

    if not failed_blocking:
        return {"failed": False, "reason": "No unrecoverable blocking failures"}

    # Auto-fail the run
    run.status = RunStatus.FAILED
    await db.flush()

    await event_service.emit_event(
        db,
        event_type=EventType.RUN_FAILED,
        summary=(
            f"Run #{run.run_number} auto-failed — "
            f"{len(failed_blocking)} blocking task(s) exhausted retries"
        ),
        project_id=run.project_id,
        run_id=run.id,
        metadata={
            "action": "auto_fail",
            "blocking_tasks": [str(t.id) for t in failed_blocking],
        },
    )

    return {
        "failed": True,
        "reason": f"{len(failed_blocking)} blocking task(s) exhausted all retries",
    }


async def scan_all_runs_health(
    db: AsyncSession,
) -> list[dict[str, Any]]:
    """Scan all active runs and return health summaries.

    Active runs = status in (RUNNING, PLANNING, PAUSED).
    """
    result = await db.execute(
        select(Run).where(
            Run.status.in_([RunStatus.RUNNING, RunStatus.PLANNING, RunStatus.PAUSED])
        )
    )
    active_runs = list(result.scalars().all())

    summaries = []
    for run in active_runs:
        health = await get_run_health(db, run.id)
        summaries.append(health)

    return summaries
