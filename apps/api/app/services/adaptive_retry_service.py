"""Adaptive retry service — contextual retry policies and revision task generation.

Provides intelligent retry logic that considers:
- Task type and historical failure patterns
- Retry count and policy limits
- Failure context for revision task creation
- Escalation rules for persistent failures
"""

import uuid
import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task, TaskStatus
from app.models.run import Run
from app.models.execution_event import EventType
from app.services import event_service

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Retry policy definitions
# ---------------------------------------------------------------------------

RETRY_POLICIES: dict[str, dict[str, Any]] = {
    "standard": {
        "max_retries": 3,
        "description": "Standard retry — up to 3 attempts",
    },
    "aggressive": {
        "max_retries": 5,
        "description": "Aggressive retry — up to 5 attempts for critical tasks",
    },
    "conservative": {
        "max_retries": 1,
        "description": "Conservative retry — single retry only",
    },
    "no_retry": {
        "max_retries": 0,
        "description": "No retry — failure is terminal",
    },
}

# Task types that default to specific policies
TASK_TYPE_POLICIES: dict[str, str] = {
    "architecture": "conservative",
    "review": "conservative",
    "implementation": "standard",
    "testing": "aggressive",
    "deployment": "conservative",
    "generic": "standard",
}


def get_policy_for_task(task_type: str) -> str:
    """Determine the retry policy for a task type."""
    return TASK_TYPE_POLICIES.get(task_type, "standard")


def get_max_retries(policy: str) -> int:
    """Get the max retry count for a policy."""
    return RETRY_POLICIES.get(policy, RETRY_POLICIES["standard"])["max_retries"]


async def can_retry(db: AsyncSession, task: Task) -> dict[str, Any]:
    """Check whether a task can be retried and provide context.

    Returns:
        can_retry: bool
        reason: str - why it can/cannot be retried
        retry_count: int - current attempt count
        max_retries: int - max allowed attempts
        suggested_action: str - recommended next step
    """
    if task.status != TaskStatus.FAILED:
        return {
            "can_retry": False,
            "reason": f"Task is {task.status.value}, only FAILED tasks can be retried",
            "retry_count": task.retry_count,
            "max_retries": task.max_retries,
            "suggested_action": "none",
        }

    if task.retry_policy == "no_retry":
        return {
            "can_retry": False,
            "reason": "Task has no_retry policy — failure is terminal",
            "retry_count": task.retry_count,
            "max_retries": 0,
            "suggested_action": "create_revision_task",
        }

    if task.retry_count >= task.max_retries:
        return {
            "can_retry": False,
            "reason": f"Max retries ({task.max_retries}) exhausted",
            "retry_count": task.retry_count,
            "max_retries": task.max_retries,
            "suggested_action": "escalate",
        }

    return {
        "can_retry": True,
        "reason": f"Retry {task.retry_count + 1}/{task.max_retries} available",
        "retry_count": task.retry_count,
        "max_retries": task.max_retries,
        "suggested_action": "retry",
    }


async def adaptive_retry(
    db: AsyncSession,
    task_id: uuid.UUID,
) -> dict[str, Any]:
    """Perform an adaptive retry of a failed task.

    Increments the retry counter, resets the task to READY, and emits events.

    Returns:
        success: bool
        task_id: UUID
        retry_count: int
        message: str
    """
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if task is None:
        return {"success": False, "task_id": str(task_id), "retry_count": 0,
                "message": "Task not found"}

    check = await can_retry(db, task)
    if not check["can_retry"]:
        return {"success": False, "task_id": str(task_id),
                "retry_count": task.retry_count, "message": check["reason"]}

    # Increment retry count and reset to READY
    task.retry_count += 1
    task.status = TaskStatus.READY
    task.error_message = None
    task.assigned_agent_slug = None
    await db.flush()

    # Emit retry event
    run_result = await db.execute(select(Run).where(Run.id == task.run_id))
    run = run_result.scalar_one_or_none()
    project_id = run.project_id if run else None

    await event_service.emit_event(
        db,
        event_type=EventType.TASK_CLAIMED,
        summary=f"Task '{task.title}' adaptive retry {task.retry_count}/{task.max_retries}",
        project_id=project_id,
        run_id=task.run_id,
        task_id=task.id,
        metadata={
            "action": "adaptive_retry",
            "retry_count": task.retry_count,
            "max_retries": task.max_retries,
            "policy": task.retry_policy,
        },
    )

    return {
        "success": True,
        "task_id": str(task_id),
        "retry_count": task.retry_count,
        "message": f"Retry {task.retry_count}/{task.max_retries} initiated",
    }


async def create_revision_task(
    db: AsyncSession,
    failed_task_id: uuid.UUID,
    revision_description: str | None = None,
) -> dict[str, Any]:
    """Create a revision task when a failed task has exhausted retries.

    The revision task depends on a human review and generates a new
    approach to the failed work.
    """
    result = await db.execute(select(Task).where(Task.id == failed_task_id))
    failed_task = result.scalar_one_or_none()
    if failed_task is None:
        return {"success": False, "message": "Failed task not found"}

    if failed_task.status != TaskStatus.FAILED:
        return {"success": False, "message": "Task is not in FAILED state"}

    # Build revision description
    desc = revision_description or (
        f"Revision of failed task '{failed_task.title}'. "
        f"Original error: {failed_task.error_message or 'unknown'}. "
        f"Retries exhausted ({failed_task.retry_count}/{failed_task.max_retries}). "
        f"Requires a new approach."
    )

    # Find the next available order_index in this run
    max_order_result = await db.execute(
        select(Task.order_index)
        .where(Task.run_id == failed_task.run_id)
        .order_by(Task.order_index.desc())
        .limit(1)
    )
    max_order = max_order_result.scalar_one_or_none() or 0

    revision_task = Task(
        title=f"[Revision] {failed_task.title}",
        description=desc,
        task_type=failed_task.task_type,
        status=TaskStatus.READY,
        order_index=max_order + 1,
        run_id=failed_task.run_id,
        parent_id=failed_task.id,
        retry_policy="conservative",
        max_retries=1,
    )
    db.add(revision_task)
    await db.flush()
    await db.refresh(revision_task)

    # Emit revision event
    run_result = await db.execute(select(Run).where(Run.id == failed_task.run_id))
    run = run_result.scalar_one_or_none()
    project_id = run.project_id if run else None

    await event_service.emit_event(
        db,
        event_type=EventType.TASK_CLAIMED,
        summary=f"Revision task created for '{failed_task.title}'",
        project_id=project_id,
        run_id=failed_task.run_id,
        task_id=revision_task.id,
        metadata={
            "action": "revision_created",
            "original_task_id": str(failed_task.id),
            "original_error": failed_task.error_message,
        },
    )

    return {
        "success": True,
        "revision_task_id": str(revision_task.id),
        "message": f"Revision task created for '{failed_task.title}'",
    }


async def get_retry_status(
    db: AsyncSession,
    run_id: uuid.UUID,
) -> dict[str, Any]:
    """Get retry status summary for all tasks in a run."""
    result = await db.execute(
        select(Task).where(Task.run_id == run_id).order_by(Task.order_index)
    )
    tasks = list(result.scalars().all())

    failed_tasks = []
    retried_tasks = []
    exhausted_tasks = []

    for task in tasks:
        if task.status == TaskStatus.FAILED:
            check = await can_retry(db, task)
            entry = {
                "task_id": str(task.id),
                "title": task.title,
                "task_type": task.task_type,
                "retry_count": task.retry_count,
                "max_retries": task.max_retries,
                "policy": task.retry_policy,
                "error_message": task.error_message,
                "can_retry": check["can_retry"],
                "suggested_action": check["suggested_action"],
            }
            failed_tasks.append(entry)
            if not check["can_retry"]:
                exhausted_tasks.append(entry)

        if task.retry_count > 0:
            retried_tasks.append({
                "task_id": str(task.id),
                "title": task.title,
                "retry_count": task.retry_count,
                "max_retries": task.max_retries,
                "current_status": task.status.value,
            })

    return {
        "total_tasks": len(tasks),
        "failed_count": len(failed_tasks),
        "exhausted_count": len(exhausted_tasks),
        "retried_count": len(retried_tasks),
        "failed_tasks": failed_tasks,
        "exhausted_tasks": exhausted_tasks,
        "retried_tasks": retried_tasks,
        "needs_escalation": len(exhausted_tasks) > 0,
    }
