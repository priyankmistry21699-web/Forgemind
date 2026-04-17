"""Task service — DAG-aware task state management and ready-task selection."""

import logging
import uuid

from fastapi import HTTPException, status
from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task, TaskStatus
from app.models.run import Run

logger = logging.getLogger(__name__)


async def get_task(db: AsyncSession, task_id: uuid.UUID) -> Task:
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )
    return task


async def list_tasks_by_run(
    db: AsyncSession, run_id: uuid.UUID
) -> tuple[list[Task], int]:
    query = select(Task).where(Task.run_id == run_id)
    count_result = await db.execute(
        select(sa_func.count()).select_from(query.subquery())
    )
    total = count_result.scalar_one()

    result = await db.execute(query.order_by(Task.order_index))
    tasks = list(result.scalars().all())
    return tasks, total


async def update_task_status(
    db: AsyncSession, task_id: uuid.UUID, new_status: TaskStatus
) -> Task:
    """Transition a task to a new status and re-evaluate downstream readiness."""
    task = await get_task(db, task_id)

    # Basic state-machine validation
    valid_transitions: dict[TaskStatus, set[TaskStatus]] = {
        TaskStatus.PENDING: {TaskStatus.READY, TaskStatus.BLOCKED, TaskStatus.SKIPPED},
        TaskStatus.BLOCKED: {TaskStatus.READY, TaskStatus.SKIPPED},
        TaskStatus.READY: {TaskStatus.RUNNING, TaskStatus.SKIPPED},
        TaskStatus.RUNNING: {TaskStatus.COMPLETED, TaskStatus.FAILED},
        TaskStatus.COMPLETED: set(),  # terminal
        TaskStatus.FAILED: {TaskStatus.READY},  # allow retry
        TaskStatus.SKIPPED: set(),  # terminal
    }

    allowed = valid_transitions.get(task.status, set())
    if new_status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot transition from {task.status.value} to {new_status.value}",
        )

    old_status = task.status
    task.status = new_status
    await db.flush()

    # FM-191: Auto-capture execution metric from status transition
    await _emit_execution_metric(
        db, task=task, old_status=old_status, new_status=new_status,
    )

    # If task just completed, promote any blocked dependents that are now ready
    if new_status == TaskStatus.COMPLETED:
        await _promote_ready_tasks(db, task.run_id)

    await db.refresh(task)
    return task


async def get_ready_tasks(
    db: AsyncSession, run_id: uuid.UUID
) -> tuple[list[Task], int]:
    """Return tasks in a run whose dependencies are all satisfied (READY status)."""
    query = select(Task).where(Task.run_id == run_id, Task.status == TaskStatus.READY)
    count_result = await db.execute(
        select(sa_func.count()).select_from(query.subquery())
    )
    total = count_result.scalar_one()

    result = await db.execute(query.order_by(Task.order_index))
    tasks = list(result.scalars().all())
    return tasks, total


async def _promote_ready_tasks(db: AsyncSession, run_id: uuid.UUID) -> None:
    """Check blocked tasks in a run and promote any whose deps are all completed."""
    # Get all completed task IDs in this run
    completed_result = await db.execute(
        select(Task.id).where(
            Task.run_id == run_id, Task.status == TaskStatus.COMPLETED
        )
    )
    completed_ids = {row[0] for row in completed_result.all()}

    # Get all blocked tasks in this run
    blocked_result = await db.execute(
        select(Task).where(Task.run_id == run_id, Task.status == TaskStatus.BLOCKED)
    )
    blocked_tasks = list(blocked_result.scalars().all())

    for task in blocked_tasks:
        deps = task.depends_on or []
        if all(dep_id in completed_ids for dep_id in deps):
            task.status = TaskStatus.READY

    await db.flush()


# ── FM-191: Auto-capture execution metrics from task transitions ─

# Map TaskStatus values to the string keys used by _STATUS_METRIC_MAP
_TASK_STATUS_TO_LIFECYCLE: dict[TaskStatus, str] = {
    TaskStatus.PENDING: "queued",
    TaskStatus.BLOCKED: "queued",
    TaskStatus.READY: "queued",
    TaskStatus.RUNNING: "in_progress",
    TaskStatus.COMPLETED: "completed",
    TaskStatus.FAILED: "completed",
    TaskStatus.SKIPPED: "completed",
}


async def _emit_execution_metric(
    db: AsyncSession,
    *,
    task: Task,
    old_status: TaskStatus,
    new_status: TaskStatus,
) -> None:
    """Best-effort hook: record an execution metric when a task transitions.

    Uses the same _STATUS_METRIC_MAP in execution_health_service so the
    mapping is consistent. Fails silently to avoid breaking the task
    lifecycle.
    """
    try:
        from app.services import execution_health_service

        # Resolve project_id from the run
        run_result = await db.execute(
            select(Run.project_id).where(Run.id == task.run_id)
        )
        project_id = run_result.scalar_one_or_none()
        if project_id is None:
            return

        old_lc = _TASK_STATUS_TO_LIFECYCLE.get(old_status, old_status.value)
        new_lc = _TASK_STATUS_TO_LIFECYCLE.get(new_status, new_status.value)

        # Duration is not available from the task model alone, so we pass 0
        # and let the caller (route) provide a real duration if available.
        # The metric is still useful for counting transitions.
        await execution_health_service.auto_record_from_status_transition(
            db,
            project_id=project_id,
            run_id=task.run_id,
            task_id=task.id,
            old_status=old_lc,
            new_status=new_lc,
            duration_ms=0,
        )
    except Exception:
        logger.debug(
            "FM-191: failed to emit execution metric for task %s (%s→%s)",
            task.id, old_status.value, new_status.value,
            exc_info=True,
        )
