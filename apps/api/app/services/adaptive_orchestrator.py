"""Adaptive execution orchestrator — smarter task/agent orchestration.

Transitions ForgeMind from a linear executor to an adaptive system that:
- Prioritises tasks intelligently (critical-path first, unblocked first)
- Reacts to failures with auto-retry and agent re-routing
- Handles approval rejections by requeueing tasks
- Uses run memory context for richer decisions
"""

import logging
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task, TaskStatus
from app.models.approval_request import ApprovalRequest, ApprovalStatus
from app.models.run import Run, RunStatus
from app.services import run_memory_service, composition_service
from app.services import event_service
from app.models.execution_event import EventType

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

MAX_AUTO_RETRIES = 2  # max automatic retries before leaving task failed
CRITICAL_TASK_TYPES = {"architecture", "codegen"}  # prioritised in scheduling

# FM-112: Map RunStatus → WorkflowPhase name for phase-aware routing
_STATUS_TO_PHASE: dict[RunStatus, str] = {
    RunStatus.SPECIFYING: "specify",
    RunStatus.PLANNING: "plan",
    RunStatus.RUNNING: "implement",
    RunStatus.COMPLETED: "validate",
}


# ---------------------------------------------------------------------------
# Smarter task selection
# ---------------------------------------------------------------------------


async def select_next_tasks(
    db: AsyncSession,
    *,
    max_tasks: int = 3,
) -> list[Task]:
    """Select the best next tasks to execute, considering priority.

    Priority ordering:
    1. Failed tasks eligible for auto-retry (retry_count < MAX_AUTO_RETRIES)
    2. Critical task types that are READY (architecture, codegen)
    3. Remaining READY tasks by order_index (earliest first)
    """
    selected: list[Task] = []

    # 1. Failed tasks eligible for auto-retry
    failed_result = await db.execute(
        select(Task).where(Task.status == TaskStatus.FAILED).order_by(Task.created_at)
    )
    failed_tasks = list(failed_result.scalars().all())
    for t in failed_tasks:
        retry_count = _get_retry_count(t)
        if retry_count < MAX_AUTO_RETRIES and len(selected) < max_tasks:
            selected.append(t)

    remaining_slots = max_tasks - len(selected)
    if remaining_slots <= 0:
        return selected

    # 2. READY tasks — critical types first, then by order_index
    ready_result = await db.execute(
        select(Task).where(Task.status == TaskStatus.READY).order_by(Task.order_index)
    )
    ready_tasks = list(ready_result.scalars().all())

    # Partition: critical first
    critical = [t for t in ready_tasks if t.task_type in CRITICAL_TASK_TYPES]
    non_critical = [t for t in ready_tasks if t.task_type not in CRITICAL_TASK_TYPES]

    for t in critical + non_critical:
        if len(selected) >= max_tasks:
            break
        if t not in selected:
            selected.append(t)

    return selected


def _get_retry_count(task: Task) -> int:
    """Extract retry count from error_message metadata convention.

    We track retries by appending '[retry N]' to the error message.
    """
    msg = task.error_message or ""
    if "[retry " not in msg:
        return 0
    try:
        idx = msg.rindex("[retry ")
        end = msg.index("]", idx)
        return int(msg[idx + 7 : end])
    except (ValueError, IndexError):
        return 0


# ---------------------------------------------------------------------------
# Auto-retry with agent re-routing
# ---------------------------------------------------------------------------


async def auto_retry_task(
    db: AsyncSession,
    task: Task,
) -> Task | None:
    """Auto-retry a failed task, optionally re-routing to a different agent.

    Returns the reset task, or None if max retries exceeded.
    """
    retry_count = _get_retry_count(task) + 1
    if retry_count > MAX_AUTO_RETRIES:
        logger.info(
            "Task %s exceeded max auto-retries (%d), leaving as FAILED",
            task.id,
            MAX_AUTO_RETRIES,
        )
        return None

    # FM-112: Try phase-aware routing first, then fall back to capability-based
    previous_agent = task.assigned_agent_slug
    new_agent_slug = None

    run = await db.get(Run, task.run_id)
    if run:
        phase = _STATUS_TO_PHASE.get(run.status, "implement")
        new_agent_slug, _ = await composition_service.resolve_agent_for_phase(
            db,
            run.project_id,
            phase,
            fallback_task_type=task.task_type,
        )

    if new_agent_slug is None:
        new_agent_slug = await composition_service.resolve_agent_for_task(
            db,
            task.task_type,
            agent_hint=None,  # ignore hint to try alternatives
        )
    if new_agent_slug == previous_agent:
        new_agent_slug = None  # will use whatever the worker picks

    # Reset to READY
    task.status = TaskStatus.READY
    task.error_message = f"{task.error_message or 'error'} [retry {retry_count}]"
    task.assigned_agent_slug = new_agent_slug
    await db.flush()

    # Emit event
    if run is None:
        run_r = await db.execute(select(Run).where(Run.id == task.run_id))
        run = run_r.scalar_one()
    await event_service.emit_event(
        db,
        event_type=EventType.TASK_CLAIMED,
        summary=(
            f"Auto-retry #{retry_count} for task '{task.title}'"
            + (f" (re-routed to {new_agent_slug})" if new_agent_slug else "")
        ),
        project_id=run.project_id,
        run_id=task.run_id,
        task_id=task.id,
        metadata={"action": "auto_retry", "retry_count": retry_count},
    )

    run_memory_service.invalidate_run_cache(task.run_id)
    await db.refresh(task)
    logger.info(
        "Auto-retried task %s (retry #%d, agent=%s)",
        task.id,
        retry_count,
        new_agent_slug or "default",
    )
    return task


# ---------------------------------------------------------------------------
# Approval rejection handling
# ---------------------------------------------------------------------------


async def handle_approval_rejections(db: AsyncSession) -> int:
    """Process rejected approvals — requeue the associated task for rework.

    Returns the number of tasks requeued.
    """
    # Find recently-rejected approvals that haven't been handled yet
    result = await db.execute(
        select(ApprovalRequest).where(
            ApprovalRequest.status == ApprovalStatus.REJECTED,
        )
    )
    rejected = list(result.scalars().all())

    requeued = 0
    for approval in rejected:
        if approval.task_id is None:
            continue

        task_result = await db.execute(select(Task).where(Task.id == approval.task_id))
        task = task_result.scalar_one_or_none()
        if task is None:
            continue

        # Only requeue completed tasks (rejection means rework is needed)
        if task.status != TaskStatus.COMPLETED:
            continue

        task.status = TaskStatus.READY
        task.error_message = "Rework required: approval rejected" + (
            f" — {approval.decision_comment}" if approval.decision_comment else ""
        )
        task.assigned_agent_slug = None
        await db.flush()

        # Mark approval as handled by changing status to indicate processing
        # (We reuse REJECTED status; the task reset is the side-effect)

        run_r = await db.execute(select(Run).where(Run.id == task.run_id))
        run_obj = run_r.scalar_one_or_none()
        if run_obj:
            await event_service.emit_event(
                db,
                event_type=EventType.TASK_CLAIMED,
                summary=(f"Task '{task.title}' requeued after approval rejection"),
                project_id=run_obj.project_id,
                run_id=task.run_id,
                task_id=task.id,
                metadata={
                    "action": "rejection_requeue",
                    "approval_id": str(approval.id),
                },
            )
            run_memory_service.invalidate_run_cache(task.run_id)

        requeued += 1

    return requeued


# ---------------------------------------------------------------------------
# Adaptive cycle — called by the worker loop
# ---------------------------------------------------------------------------


async def run_adaptive_cycle(
    db: AsyncSession,
    *,
    max_tasks: int = 3,
) -> dict[str, Any]:
    """Run one cycle of adaptive orchestration.

    Returns a report dict: {retried, requeued, selected_tasks}
    """
    # 1. Handle approval rejections → requeue tasks
    requeued = await handle_approval_rejections(db)
    if requeued:
        await db.commit()
        logger.info("Requeued %d task(s) due to approval rejections", requeued)

    # 2. Select next tasks (includes auto-retry candidates)
    tasks = await select_next_tasks(db, max_tasks=max_tasks)

    retried = 0
    final_tasks: list[Task] = []

    for task in tasks:
        if task.status == TaskStatus.FAILED:
            # Auto-retry
            result = await auto_retry_task(db, task)
            if result:
                retried += 1
                final_tasks.append(result)
        else:
            final_tasks.append(task)

    if retried:
        await db.commit()

    return {
        "retried": retried,
        "requeued": requeued,
        "selected_tasks": final_tasks,
    }


# ---------------------------------------------------------------------------
# FM-226: Autonomous re-planning
# ---------------------------------------------------------------------------

MAX_REPLAN_RETRIES = 3  # before giving up and leaving the task FAILED


async def trigger_replan(
    db: AsyncSession,
    *,
    run_id: uuid.UUID,
    failed_task_id: uuid.UUID,
    error_context: str = "",
) -> dict:
    """Trigger a re-plan when a task fails beyond MAX_AUTO_RETRIES.

    1. Records a PlanRevision audit entry
    2. Calls planner_service.replan to produce a revised sub-DAG
    3. Returns a summary of the revised tasks

    Falls back gracefully if the planner is unavailable.
    """
    from app.models.agent_intelligence import PlanRevision, PlanRevisionTrigger
    from app.services import planner_service

    run = await db.get(Run, run_id)
    if run is None:
        return {"status": "error", "detail": "run not found"}

    # Fetch current failed task IDs for the run
    result = await db.execute(
        select(Task).where(
            Task.run_id == run_id,
            Task.status == TaskStatus.FAILED,
        )
    )
    failed_tasks = list(result.scalars().all())
    original_ids = [str(t.id) for t in failed_tasks]

    # Record plan revision
    revision = PlanRevision(
        run_id=run_id,
        failed_task_id=failed_task_id,
        trigger=PlanRevisionTrigger.AGENT_FAILURE,
        error_context=error_context[:1000],
        original_task_ids=original_ids,
        retry_count=len(original_ids),
    )
    db.add(revision)
    await db.flush()

    # Emit event
    await event_service.emit_event(
        db,
        event_type=EventType.TASK_CLAIMED,
        summary=f"Re-plan triggered for run (failed_task={failed_task_id})",
        project_id=run.project_id,
        run_id=run_id,
        metadata={"action": "replan", "revision_id": str(revision.id)},
    )

    # Attempt LLM re-plan (graceful fallback if unavailable)
    try:
        replan_result = await planner_service.replan(
            db,
            run_id=run_id,
            failed_task_id=failed_task_id,
            error_context=error_context,
        )
        revised_ids = [str(t.id) for t in replan_result.get("new_tasks", [])]
        revision.revised_task_ids = revised_ids
        await db.flush()
        return {
            "status": "replanned",
            "revision_id": str(revision.id),
            "new_task_count": len(revised_ids),
        }
    except Exception as exc:
        logger.warning("replan failed (%s) — marking run as degraded", exc)
        return {
            "status": "replan_failed",
            "revision_id": str(revision.id),
            "error": str(exc),
        }
