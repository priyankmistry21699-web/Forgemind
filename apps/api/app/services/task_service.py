"""Task service — DAG-aware task state management and ready-task selection."""

import uuid

from fastapi import HTTPException, status
from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task, TaskStatus


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

    task.status = new_status
    await db.flush()

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
        select(Task).where(
            Task.run_id == run_id, Task.status == TaskStatus.BLOCKED
        )
    )
    blocked_tasks = list(blocked_result.scalars().all())

    for task in blocked_tasks:
        deps = task.depends_on or []
        if all(dep_id in completed_ids for dep_id in deps):
            task.status = TaskStatus.READY

    await db.flush()
