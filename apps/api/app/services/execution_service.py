"""Execution service — task claiming, completion, and failure lifecycle."""

import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.artifact import ArtifactType
from app.models.task import Task, TaskStatus
from app.schemas.artifact import ArtifactCreate
from app.schemas.approval import ApprovalCreate
from app.services import task_service, artifact_service, agent_service, approval_service
from app.services import event_service
from app.models.execution_event import EventType

# Task types that require human approval after completion
APPROVAL_REQUIRED_TASK_TYPES = {"architecture", "review"}


async def claim_task(
    db: AsyncSession,
    task_id: uuid.UUID,
    agent_slug: str,
) -> Task:
    """Claim a READY task for an agent, setting it to RUNNING."""
    task = await task_service.get_task(db, task_id)

    if task.status != TaskStatus.READY:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Task is {task.status.value}, only READY tasks can be claimed",
        )

    # Verify the agent exists and is active
    agent = await agent_service.get_agent_by_slug(db, agent_slug)
    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_slug}' not found",
        )

    task.status = TaskStatus.RUNNING
    task.assigned_agent_slug = agent_slug
    await db.flush()

    # Emit event
    from app.models.run import Run
    from sqlalchemy import select as sel_run

    run_r = await db.execute(sel_run(Run).where(Run.id == task.run_id))
    run_obj = run_r.scalar_one()
    await event_service.emit_event(
        db,
        event_type=EventType.TASK_CLAIMED,
        summary=f"Task '{task.title}' claimed by agent '{agent_slug}'",
        project_id=run_obj.project_id,
        run_id=task.run_id,
        task_id=task.id,
        agent_slug=agent_slug,
    )

    await db.refresh(task)
    return task


async def complete_task(
    db: AsyncSession,
    task_id: uuid.UUID,
    *,
    artifact_title: str | None = None,
    artifact_content: str | None = None,
    artifact_type: str | None = None,
) -> Task:
    """Complete a RUNNING task, optionally creating an output artifact."""
    task = await task_service.get_task(db, task_id)

    if task.status != TaskStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Task is {task.status.value}, only RUNNING tasks can be completed",
        )

    # Resolve project_id from run (used by artifact, approval, and event)
    from app.models.run import Run
    from sqlalchemy import select

    run_result = await db.execute(select(Run).where(Run.id == task.run_id))
    run = run_result.scalar_one()
    project_id = run.project_id

    # Create artifact if content is provided
    if artifact_title and artifact_content:
        # Resolve artifact type
        try:
            a_type = ArtifactType(artifact_type) if artifact_type else ArtifactType.OTHER
        except ValueError:
            a_type = ArtifactType.OTHER

        artifact_data = ArtifactCreate(
            title=artifact_title,
            artifact_type=a_type,
            content=artifact_content,
            run_id=task.run_id,
            task_id=task.id,
            created_by=task.assigned_agent_slug or "unknown",
        )
        artifact = await artifact_service.create_artifact(db, project_id, artifact_data)

        await event_service.emit_event(
            db,
            event_type=EventType.ARTIFACT_CREATED,
            summary=f"Artifact '{artifact_title}' created for task '{task.title}'",
            project_id=project_id,
            run_id=task.run_id,
            task_id=task.id,
            artifact_id=artifact.id,
            agent_slug=task.assigned_agent_slug,
        )

    task.status = TaskStatus.COMPLETED
    task.error_message = None
    await db.flush()

    # Emit completion event
    await event_service.emit_event(
        db,
        event_type=EventType.TASK_COMPLETED,
        summary=f"Task '{task.title}' completed by agent '{task.assigned_agent_slug}'",
        project_id=project_id,
        run_id=task.run_id,
        task_id=task.id,
        agent_slug=task.assigned_agent_slug,
    )

    # Create approval request for high-impact task types
    if task.task_type in APPROVAL_REQUIRED_TASK_TYPES:
        approval = await approval_service.create_approval(
            db,
            ApprovalCreate(
                title=f"Review: {task.title}",
                description=f"Task '{task.title}' (type: {task.task_type}) completed by agent '{task.assigned_agent_slug}'. Please review before execution continues.",
                project_id=project_id,
                run_id=task.run_id,
                task_id=task.id,
            ),
        )
        await event_service.emit_event(
            db,
            event_type=EventType.APPROVAL_REQUESTED,
            summary=f"Approval requested for task '{task.title}'",
            project_id=project_id,
            run_id=task.run_id,
            task_id=task.id,
            metadata={"approval_id": str(approval.id)},
        )

    # Promote downstream tasks
    await task_service._promote_ready_tasks(db, task.run_id)

    await db.refresh(task)
    return task


async def fail_task(
    db: AsyncSession,
    task_id: uuid.UUID,
    error_message: str,
) -> Task:
    """Fail a RUNNING task with an error message."""
    task = await task_service.get_task(db, task_id)

    if task.status != TaskStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Task is {task.status.value}, only RUNNING tasks can be failed",
        )

    task.status = TaskStatus.FAILED
    task.error_message = error_message
    await db.flush()

    # Emit failure event
    from app.models.run import Run
    from sqlalchemy import select as sel_fail

    run_r = await db.execute(sel_fail(Run).where(Run.id == task.run_id))
    run_obj = run_r.scalar_one()
    await event_service.emit_event(
        db,
        event_type=EventType.TASK_FAILED,
        summary=f"Task '{task.title}' failed: {error_message[:200]}",
        project_id=run_obj.project_id,
        run_id=task.run_id,
        task_id=task.id,
        agent_slug=task.assigned_agent_slug,
        metadata={"error_message": error_message},
    )

    await db.refresh(task)
    return task


async def retry_task(
    db: AsyncSession,
    task_id: uuid.UUID,
) -> Task:
    """Retry a FAILED task by resetting it to READY."""
    task = await task_service.get_task(db, task_id)

    if task.status != TaskStatus.FAILED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Task is {task.status.value}, only FAILED tasks can be retried",
        )

    task.status = TaskStatus.READY
    task.error_message = None
    task.assigned_agent_slug = None
    await db.flush()

    # Emit retry event
    from app.models.run import Run
    from sqlalchemy import select as sel_retry

    run_r = await db.execute(sel_retry(Run).where(Run.id == task.run_id))
    run_obj = run_r.scalar_one()
    await event_service.emit_event(
        db,
        event_type=EventType.TASK_CLAIMED,
        summary=f"Task '{task.title}' retried — reset to READY",
        project_id=run_obj.project_id,
        run_id=task.run_id,
        task_id=task.id,
        metadata={"action": "retry"},
    )

    await db.refresh(task)
    return task


async def cancel_task(
    db: AsyncSession,
    task_id: uuid.UUID,
) -> Task:
    """Cancel a READY or RUNNING task by setting it to SKIPPED."""
    task = await task_service.get_task(db, task_id)

    if task.status not in (TaskStatus.READY, TaskStatus.RUNNING):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Task is {task.status.value}, only READY or RUNNING tasks can be cancelled",
        )

    task.status = TaskStatus.SKIPPED
    task.error_message = "Cancelled by operator"
    await db.flush()

    # Emit cancel event
    from app.models.run import Run
    from sqlalchemy import select as sel_cancel

    run_r = await db.execute(sel_cancel(Run).where(Run.id == task.run_id))
    run_obj = run_r.scalar_one()
    await event_service.emit_event(
        db,
        event_type=EventType.TASK_FAILED,
        summary=f"Task '{task.title}' cancelled by operator",
        project_id=run_obj.project_id,
        run_id=task.run_id,
        task_id=task.id,
        metadata={"action": "cancel"},
    )

    await db.refresh(task)
    return task
