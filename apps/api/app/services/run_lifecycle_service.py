"""Run lifecycle service — health checks, auto-completion, stuck run detection.

FM-046: Monitors run health and manages lifecycle transitions:
- Detect stuck runs (no progress for configurable duration)
- Auto-complete runs when all tasks are done
- Auto-fail runs when unrecoverable failures exist
- Health check summaries for operator dashboards

FM-101: Spec-driven lifecycle gating:
- SPECIFYING phase must produce a SPEC artifact before PLANNING
- PLANNING phase must produce a PLAN artifact before RUNNING
"""

import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.run import Run, RunStatus
from app.models.task import Task, TaskStatus
from app.models.artifact import Artifact, ArtifactType
from app.models.execution_event import EventType
from app.services import event_service
from app.models.execution_checkpoint import CheckpointType

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configurable thresholds
# ---------------------------------------------------------------------------

STUCK_RUN_THRESHOLD_MINUTES = 60  # No progress for 60 min = stuck
AUTO_FAIL_EXHAUSTED_RETRIES = True  # Fail run if blocking tasks exhausted retries

# FM-101: Valid lifecycle transitions
VALID_TRANSITIONS: dict[RunStatus, set[RunStatus]] = {
    RunStatus.PENDING: {RunStatus.SPECIFYING, RunStatus.FAILED},
    RunStatus.SPECIFYING: {RunStatus.PLANNING, RunStatus.FAILED, RunStatus.PAUSED},
    RunStatus.PLANNING: {RunStatus.RUNNING, RunStatus.FAILED, RunStatus.PAUSED},
    RunStatus.RUNNING: {RunStatus.COMPLETED, RunStatus.FAILED, RunStatus.PAUSED},
    RunStatus.PAUSED: {
        RunStatus.SPECIFYING,
        RunStatus.PLANNING,
        RunStatus.RUNNING,
        RunStatus.FAILED,
    },
    RunStatus.COMPLETED: set(),
    RunStatus.FAILED: {RunStatus.PENDING},  # allow restart
}


# ---------------------------------------------------------------------------
# FM-101: Lifecycle gating helpers
# ---------------------------------------------------------------------------


async def has_spec_artifact(
    db: AsyncSession,
    *,
    run_id: uuid.UUID | None = None,
    project_id: uuid.UUID | None = None,
) -> bool:
    """Check whether a SPEC artifact exists for the given run or project."""
    query = select(Artifact.id).where(Artifact.artifact_type == ArtifactType.SPEC)
    if run_id is not None:
        query = query.where(Artifact.run_id == run_id)
    elif project_id is not None:
        query = query.where(Artifact.project_id == project_id)
    else:
        return False
    result = await db.execute(query.limit(1))
    return result.scalar_one_or_none() is not None


async def has_plan_artifact(
    db: AsyncSession,
    *,
    run_id: uuid.UUID | None = None,
    project_id: uuid.UUID | None = None,
) -> bool:
    """Check whether a PLAN artifact exists for the given run or project."""
    query = select(Artifact.id).where(Artifact.artifact_type == ArtifactType.PLAN)
    if run_id is not None:
        query = query.where(Artifact.run_id == run_id)
    elif project_id is not None:
        query = query.where(Artifact.project_id == project_id)
    else:
        return False
    result = await db.execute(query.limit(1))
    return result.scalar_one_or_none() is not None


async def validate_transition(
    db: AsyncSession,
    run_id: uuid.UUID,
    target_status: RunStatus,
) -> dict[str, Any]:
    """Validate whether a run lifecycle transition is allowed.

    Enforces:
      - SPECIFYING → PLANNING requires a SPEC artifact
      - PLANNING → RUNNING requires a PLAN artifact
    """
    run_result = await db.execute(select(Run).where(Run.id == run_id))
    run = run_result.scalar_one_or_none()
    if run is None:
        return {"allowed": False, "reason": "Run not found"}

    current = run.status

    if target_status not in VALID_TRANSITIONS.get(current, set()):
        return {
            "allowed": False,
            "reason": f"Transition from {current.value} to {target_status.value} is not allowed",
        }

    # Gate: SPECIFYING → PLANNING requires SPEC
    if current == RunStatus.SPECIFYING and target_status == RunStatus.PLANNING:
        if not await has_spec_artifact(db, run_id=run_id):
            return {
                "allowed": False,
                "reason": "Cannot transition to PLANNING without a SPEC artifact",
            }
        # FM-109: Check SPEC approval if an approval was requested
        from app.services import spec_plan_approval_service

        if not await spec_plan_approval_service.is_spec_approved(db, run_id):
            return {
                "allowed": False,
                "reason": "SPEC artifact has a pending or rejected approval. Approve the SPEC first.",
            }

    # Gate: PLANNING → RUNNING requires PLAN
    if current == RunStatus.PLANNING and target_status == RunStatus.RUNNING:
        if not await has_plan_artifact(db, run_id=run_id):
            return {
                "allowed": False,
                "reason": "Cannot transition to RUNNING without a PLAN artifact",
            }
        # FM-109: Check PLAN approval if an approval was requested
        from app.services import spec_plan_approval_service

        if not await spec_plan_approval_service.is_plan_approved(db, run_id):
            return {
                "allowed": False,
                "reason": "PLAN artifact has a pending or rejected approval. Approve the PLAN first.",
            }
        # FM-108: Spec-to-plan validation gate
        from app.services import spec_plan_validation_service

        validation_result = await spec_plan_validation_service.validate_spec_plan(
            db, run_id
        )
        if not validation_result.valid:
            error_msgs = [
                i.message for i in validation_result.issues if i.severity == "error"
            ]
            return {
                "allowed": False,
                "reason": "PLAN does not pass spec-to-plan validation: "
                + "; ".join(error_msgs),
                "validation": validation_result.to_dict(),
            }

    return {"allowed": True, "reason": "Transition allowed"}


async def transition_run(
    db: AsyncSession,
    run_id: uuid.UUID,
    target_status: RunStatus,
) -> dict[str, Any]:
    """Attempt to transition a run to a new lifecycle status with gating."""
    validation = await validate_transition(db, run_id, target_status)
    if not validation["allowed"]:
        return {"transitioned": False, **validation}

    run_result = await db.execute(select(Run).where(Run.id == run_id))
    run = run_result.scalar_one_or_none()
    if run is None:
        return {"transitioned": False, "reason": "Run not found"}

    old_status = run.status
    run.status = target_status
    await db.flush()

    await event_service.emit_event(
        db,
        event_type=EventType.RUN_STARTED
        if target_status == RunStatus.RUNNING
        else EventType.TASK_STARTED,
        summary=f"Run #{run.run_number} transitioned {old_status.value} → {target_status.value}",
        project_id=run.project_id,
        run_id=run.id,
        metadata={
            "action": "lifecycle_transition",
            "from_status": old_status.value,
            "to_status": target_status.value,
        },
    )

    # FM-122: Auto-checkpoint on phase transition
    await _try_auto_checkpoint_on_transition(
        db, run, old_status.value, target_status.value
    )

    return {
        "transitioned": True,
        "from_status": old_status.value,
        "to_status": target_status.value,
    }


async def _try_auto_checkpoint_on_transition(
    db: AsyncSession,
    run: Run,
    old_status: str,
    new_status: str,
) -> None:
    """FM-122: Create an AUTO_PHASE checkpoint on meaningful phase transitions."""
    try:
        from app.services import execution_checkpoint_service as cp_svc

        await cp_svc.create_auto_checkpoint(
            db,
            run_id=run.id,
            project_id=run.project_id,
            checkpoint_type=CheckpointType.AUTO_PHASE,
            summary=f"Phase transition: {old_status} → {new_status}",
        )
    except Exception:
        logger.warning(
            "Auto-checkpoint failed for run %s on %s → %s",
            run.id,
            old_status,
            new_status,
            exc_info=True,
        )


class RunHealth:
    HEALTHY = "healthy"
    DEGRADED = "degraded"  # Some failures but progress possible
    STUCK = "stuck"  # No progress for extended time
    CRITICAL = "critical"  # Blocking failures, cannot proceed
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
            "health": RunHealth.COMPLETED
            if run.status == RunStatus.COMPLETED
            else RunHealth.FAILED,
            "progress": 1.0 if run.status == RunStatus.COMPLETED else None,
            "task_breakdown": {},
            "stuck_since": None,
            "blocking_issues": [],
            "suggested_actions": [],
        }

    # Get task breakdown
    task_result = await db.execute(select(Task).where(Task.run_id == run_id))
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
            t
            for t in tasks
            if t.depends_on
            and (ft.id in t.depends_on or ft_id_str in t.depends_on)
            and t.status in (TaskStatus.BLOCKED, TaskStatus.PENDING)
        ]
        if downstream:
            blocking_issues.append(
                f"Failed task '{ft.title}' blocks {len(downstream)} downstream task(s)"
            )

    # Exhausted retries
    exhausted = [
        t
        for t in failed_tasks
        if t.retry_count >= t.max_retries and t.retry_policy != "no_retry"
    ]
    if exhausted:
        blocking_issues.append(f"{len(exhausted)} task(s) exhausted all retries")

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
        suggested_actions.append(
            "Run appears stuck — check for pending approvals or unresolvable blockers"
        )
    if health == RunHealth.CRITICAL:
        suggested_actions.append(
            "Run is in critical state — retry or create revision tasks for blocking failures"
        )
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

    task_result = await db.execute(select(Task).where(Task.run_id == run_id))
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
    # FM-122: PRE_DELIVERY checkpoint before final state change
    try:
        from app.services import execution_checkpoint_service as cp_svc

        await cp_svc.create_auto_checkpoint(
            db,
            run_id=run.id,
            project_id=run.project_id,
            checkpoint_type=CheckpointType.PRE_DELIVERY,
            summary=f"Pre-delivery snapshot — {len(tasks)} tasks terminal",
        )
    except Exception:
        logger.warning("Pre-delivery checkpoint failed for run %s", run_id, exc_info=True)

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

    task_result = await db.execute(select(Task).where(Task.run_id == run_id))
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
                t
                for t in tasks
                if t.depends_on
                and (ft.id in t.depends_on or ft_id_str in t.depends_on)
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
    Also triggers escalation rules (FM-057) for STUCK/CRITICAL runs.
    """
    result = await db.execute(
        select(Run).where(
            Run.status.in_(
                [
                    RunStatus.RUNNING,
                    RunStatus.PLANNING,
                    RunStatus.PAUSED,
                    RunStatus.SPECIFYING,
                ]
            )
        )
    )
    active_runs = list(result.scalars().all())

    summaries = []
    for run in active_runs:
        health = await get_run_health(db, run.id)
        summaries.append(health)

        # FM-057: Trigger escalation for unhealthy runs
        if health.get("health") in (RunHealth.STUCK, RunHealth.CRITICAL):
            try:
                from app.services import escalation_service

                trigger_type = (
                    "run_stuck"
                    if health["health"] == RunHealth.STUCK
                    else "retry_exhausted"
                )
                await escalation_service.trigger_escalation(
                    db,
                    project_id=run.project_id,
                    trigger_type=trigger_type,
                    trigger_data={
                        "run_id": str(run.id),
                        "health": health["health"],
                        "blocking_issues": health.get("blocking_issues", []),
                    },
                    action_taken=f"Escalation triggered: run health is {health['health']}",
                )
            except Exception:
                logger.warning(
                    "Escalation trigger failed for run %s", run.id, exc_info=True
                )

    return summaries
