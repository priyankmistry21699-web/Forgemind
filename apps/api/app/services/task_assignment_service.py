"""Task assignment service — assign/reassign tasks to users, workload queries.

FM-147: Task Assignment & Workload Visibility.
"""

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task, TaskStatus


async def assign_task(
    db: AsyncSession,
    task_id: uuid.UUID,
    assignee_id: uuid.UUID,
) -> Task:
    task = await db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    previous_assignee = task.assignee_id
    task.assignee_id = assignee_id
    task.assigned_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(task)

    # FM-147: Emit assignment execution event
    from app.services.event_service import emit_event
    from app.models.execution_event import EventType

    evt = EventType.TASK_REASSIGNED if previous_assignee else EventType.TASK_ASSIGNED
    run_id = task.run_id
    project_id = None
    if run_id:
        from app.models.run import Run

        run = await db.get(Run, run_id)
        if run:
            project_id = run.project_id

    await emit_event(
        db,
        event_type=evt,
        summary=f"Task '{task.title}' assigned to {assignee_id}",
        project_id=project_id,
        run_id=run_id,
        task_id=task_id,
        metadata={
            "assignee_id": str(assignee_id),
            "previous_assignee_id": str(previous_assignee)
            if previous_assignee
            else None,
        },
    )
    return task


async def unassign_task(
    db: AsyncSession,
    task_id: uuid.UUID,
) -> Task:
    task = await db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    previous_assignee = task.assignee_id
    task.assignee_id = None
    task.assigned_at = None
    await db.flush()
    await db.refresh(task)

    # FM-147: Emit unassignment execution event
    from app.services.event_service import emit_event
    from app.models.execution_event import EventType

    run_id = task.run_id
    project_id = None
    if run_id:
        from app.models.run import Run

        run = await db.get(Run, run_id)
        if run:
            project_id = run.project_id

    await emit_event(
        db,
        event_type=EventType.TASK_UNASSIGNED,
        summary=f"Task '{task.title}' unassigned",
        project_id=project_id,
        run_id=run_id,
        task_id=task_id,
        metadata={
            "previous_assignee_id": str(previous_assignee)
            if previous_assignee
            else None,
        },
    )
    return task


async def list_user_assigned_tasks(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> list[Task]:
    """Get all tasks assigned to a user across all projects."""
    result = await db.execute(
        select(Task)
        .where(
            Task.assignee_id == user_id,
            Task.status.notin_([TaskStatus.COMPLETED, TaskStatus.SKIPPED]),
        )
        .order_by(Task.created_at.desc())
    )
    return list(result.scalars().all())


async def get_project_workload(
    db: AsyncSession,
    project_id: uuid.UUID,
) -> list[dict]:
    """Return task counts per assignee for a project's active runs."""
    from app.models.run import Run

    result = await db.execute(
        select(
            Task.assignee_id,
            Task.status,
            func.count(Task.id).label("count"),
        )
        .join(Run, Run.id == Task.run_id)
        .where(Run.project_id == project_id, Task.assignee_id.isnot(None))
        .group_by(Task.assignee_id, Task.status)
    )
    rows = result.all()
    workload: dict[str, dict[str, int]] = {}
    for row in rows:
        uid = str(row.assignee_id)
        if uid not in workload:
            workload[uid] = {}
        workload[uid][
            row.status.value if hasattr(row.status, "value") else str(row.status)
        ] = row.count

    return [{"user_id": uid, "tasks": counts} for uid, counts in workload.items()]
