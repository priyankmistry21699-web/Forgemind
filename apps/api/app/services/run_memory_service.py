"""Run memory service — execution context caching and contextual reasoning.

Provides efficient, cached summaries of run state for use by:
- Execution chatbot (richer context)
- Dynamic agents (prior artifact awareness)
- Operator explanations (what happened and why)
- Retry/rerun decisions (failure context)
"""

import uuid
import logging
from typing import Any

from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.run import Run
from app.models.task import Task, TaskStatus
from app.models.artifact import Artifact
from app.models.execution_event import ExecutionEvent, EventType
from app.models.approval_request import ApprovalRequest

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# In-memory summary cache (per run_id) — cleared on run state changes
# ---------------------------------------------------------------------------

_run_summary_cache: dict[str, dict[str, Any]] = {}
_CACHE_MAX_SIZE = 100


def invalidate_run_cache(run_id: uuid.UUID) -> None:
    """Invalidate the cached summary for a run."""
    _run_summary_cache.pop(str(run_id), None)


def _cache_key(run_id: uuid.UUID) -> str:
    return str(run_id)


async def get_run_summary(
    db: AsyncSession,
    run_id: uuid.UUID,
    *,
    force_refresh: bool = False,
) -> dict[str, Any]:
    """Build or retrieve a cached summary of a run's execution state.

    Returns a structured dict with:
        run: run metadata
        task_summary: counts and status breakdown
        artifact_summary: count and type breakdown
        approval_summary: counts by status
        event_summary: recent event types and counts
        failure_context: details on failed tasks (if any)
        progress: overall completion percentage
    """
    key = _cache_key(run_id)

    if not force_refresh and key in _run_summary_cache:
        return _run_summary_cache[key]

    summary = await _build_run_summary(db, run_id)

    # Evict oldest if cache is full
    if len(_run_summary_cache) >= _CACHE_MAX_SIZE:
        oldest_key = next(iter(_run_summary_cache))
        _run_summary_cache.pop(oldest_key, None)

    _run_summary_cache[key] = summary
    return summary


async def _build_run_summary(
    db: AsyncSession,
    run_id: uuid.UUID,
) -> dict[str, Any]:
    """Build a comprehensive run summary from the database."""

    # Run metadata
    run_result = await db.execute(select(Run).where(Run.id == run_id))
    run = run_result.scalar_one_or_none()
    if run is None:
        return {"error": "Run not found"}

    # Tasks
    task_result = await db.execute(
        select(Task).where(Task.run_id == run_id).order_by(Task.order_index)
    )
    tasks = list(task_result.scalars().all())

    status_counts: dict[str, int] = {}
    failed_tasks: list[dict[str, Any]] = []
    for t in tasks:
        status_counts[t.status.value] = status_counts.get(t.status.value, 0) + 1
        if t.status == TaskStatus.FAILED:
            failed_tasks.append({
                "task_id": str(t.id),
                "title": t.title,
                "task_type": t.task_type,
                "error_message": t.error_message,
                "agent": t.assigned_agent_slug,
            })

    total_tasks = len(tasks)
    completed_tasks = status_counts.get("completed", 0)
    progress = completed_tasks / total_tasks if total_tasks > 0 else 0.0

    # Artifacts
    art_result = await db.execute(
        select(Artifact).where(Artifact.run_id == run_id)
    )
    artifacts = list(art_result.scalars().all())
    artifact_types: dict[str, int] = {}
    for a in artifacts:
        artifact_types[a.artifact_type.value] = (
            artifact_types.get(a.artifact_type.value, 0) + 1
        )

    # Approvals
    approval_result = await db.execute(
        select(ApprovalRequest).where(ApprovalRequest.run_id == run_id)
    )
    approvals = list(approval_result.scalars().all())
    approval_counts: dict[str, int] = {}
    for ap in approvals:
        approval_counts[ap.status.value] = (
            approval_counts.get(ap.status.value, 0) + 1
        )

    # Events (counts by type + latest 10)
    event_count_result = await db.execute(
        select(
            ExecutionEvent.event_type,
            sa_func.count().label("cnt"),
        )
        .where(ExecutionEvent.run_id == run_id)
        .group_by(ExecutionEvent.event_type)
    )
    event_type_counts = {
        row.event_type.value: row.cnt for row in event_count_result.all()
    }

    recent_events_result = await db.execute(
        select(ExecutionEvent)
        .where(ExecutionEvent.run_id == run_id)
        .order_by(ExecutionEvent.created_at.desc())
        .limit(10)
    )
    recent_events = [
        {
            "type": ev.event_type.value,
            "summary": ev.summary,
            "agent": ev.agent_slug,
            "created_at": ev.created_at.isoformat() if ev.created_at else None,
        }
        for ev in recent_events_result.scalars().all()
    ]

    return {
        "run": {
            "id": str(run.id),
            "run_number": run.run_number,
            "status": run.status.value,
            "trigger": run.trigger,
            "project_id": str(run.project_id),
        },
        "task_summary": {
            "total": total_tasks,
            "status_counts": status_counts,
        },
        "artifact_summary": {
            "total": len(artifacts),
            "type_counts": artifact_types,
        },
        "approval_summary": {
            "total": len(approvals),
            "status_counts": approval_counts,
        },
        "event_summary": {
            "type_counts": event_type_counts,
            "recent": recent_events,
        },
        "failure_context": failed_tasks,
        "progress": round(progress, 2),
    }


async def get_failure_analysis(
    db: AsyncSession,
    run_id: uuid.UUID,
) -> dict[str, Any]:
    """Analyse failures in a run for retry/replan decisions.

    Returns:
        has_failures: bool
        failed_tasks: list of failed task details
        blocking_failures: list of tasks blocking downstream work
        suggested_actions: list of recommended next steps
    """
    summary = await get_run_summary(db, run_id, force_refresh=True)

    failed = summary.get("failure_context", [])
    task_result = await db.execute(
        select(Task).where(Task.run_id == run_id).order_by(Task.order_index)
    )
    tasks = list(task_result.scalars().all())
    task_map = {str(t.id): t for t in tasks}

    # Find blocking failures — failed tasks that have downstream dependents
    blocking: list[dict[str, Any]] = []
    for ft in failed:
        tid = ft["task_id"]
        for t in tasks:
            if t.depends_on and uuid.UUID(tid) in t.depends_on:
                if t.status in (TaskStatus.BLOCKED, TaskStatus.PENDING):
                    blocking.append({
                        **ft,
                        "blocks": [str(t.id)],
                    })
                    break

    # Generate suggested actions
    suggestions: list[str] = []
    if blocking:
        suggestions.append(
            f"Retry {len(blocking)} blocking failed task(s) to unblock downstream work."
        )
    if failed and not blocking:
        suggestions.append(
            "Failed tasks are not blocking downstream work. Review errors and retry if needed."
        )
    if summary.get("approval_summary", {}).get("status_counts", {}).get("pending", 0) > 0:
        suggestions.append("Pending approvals may be blocking execution progress.")
    if not failed:
        suggestions.append("No failures detected. Execution is proceeding normally.")

    return {
        "has_failures": len(failed) > 0,
        "failed_tasks": failed,
        "blocking_failures": blocking,
        "suggested_actions": suggestions,
    }


def build_context_for_chat(summary: dict[str, Any]) -> str:
    """Convert a run summary into a text context for the chat service."""
    run_info = summary.get("run", {})
    parts = [
        f"Run #{run_info.get('run_number', '?')} — status: {run_info.get('status', '?')}, trigger: {run_info.get('trigger', '?')}",
        "",
    ]

    # Tasks
    ts = summary.get("task_summary", {})
    parts.append(f"=== Tasks ({ts.get('total', 0)}) ===")
    for status, count in ts.get("status_counts", {}).items():
        parts.append(f"  {status}: {count}")
    parts.append(f"  Progress: {summary.get('progress', 0) * 100:.0f}%")
    parts.append("")

    # Failures
    failures = summary.get("failure_context", [])
    if failures:
        parts.append(f"=== Failures ({len(failures)}) ===")
        for f in failures:
            parts.append(f"  - {f['title']} ({f['task_type']}): {f.get('error_message', 'unknown error')}")
        parts.append("")

    # Artifacts
    art = summary.get("artifact_summary", {})
    if art.get("total", 0) > 0:
        parts.append(f"=== Artifacts ({art['total']}) ===")
        for atype, count in art.get("type_counts", {}).items():
            parts.append(f"  {atype}: {count}")
        parts.append("")

    # Approvals
    appr = summary.get("approval_summary", {})
    if appr.get("total", 0) > 0:
        parts.append(f"=== Approvals ({appr['total']}) ===")
        for astatus, count in appr.get("status_counts", {}).items():
            parts.append(f"  {astatus}: {count}")
        parts.append("")

    # Recent events
    events = summary.get("event_summary", {})
    recent = events.get("recent", [])
    if recent:
        parts.append(f"=== Recent Events ({len(recent)}) ===")
        for ev in recent[:10]:
            parts.append(f"  [{ev['type']}] {ev['summary']}")
        parts.append("")

    return "\n".join(parts)
