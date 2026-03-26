"""Base agent — shared utilities for fixed execution agents."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

if TYPE_CHECKING:
    from app.models.task import Task
    from app.models.agent import Agent

logger = logging.getLogger("forgemind.worker.agents")


def _task_context(task: "Task") -> str:
    """Build a context string from task metadata for LLM prompts."""
    parts = [f"Task: {task.title}"]
    if task.description:
        parts.append(f"Description: {task.description}")
    parts.append(f"Type: {task.task_type}")
    return "\n".join(parts)


async def build_handoff_context(
    db: AsyncSession,
    task: "Task",
    *,
    max_artifacts: int = 5,
    max_content_chars: int = 3000,
) -> str:
    """Build rich context for an agent by assembling prior artifacts from the run.

    Includes:
    - The task's own metadata
    - Artifacts produced by upstream (completed) tasks in this run
    - Ordered by task execution order for logical flow
    """
    from app.models.task import Task as TaskModel, TaskStatus
    from app.models.artifact import Artifact

    parts = [_task_context(task), ""]

    # Fetch completed upstream tasks with their artifacts
    upstream_result = await db.execute(
        select(TaskModel)
        .where(
            TaskModel.run_id == task.run_id,
            TaskModel.status == TaskStatus.COMPLETED,
            TaskModel.order_index < task.order_index,
        )
        .order_by(TaskModel.order_index)
    )
    upstream_tasks = list(upstream_result.scalars().all())

    if upstream_tasks:
        parts.append("=== Prior Work (upstream artifacts) ===")
        artifact_count = 0
        for ut in upstream_tasks:
            if artifact_count >= max_artifacts:
                break
            art_result = await db.execute(
                select(Artifact)
                .where(Artifact.task_id == ut.id)
                .order_by(Artifact.created_at.desc())
                .limit(1)
            )
            artifact = art_result.scalar_one_or_none()
            if artifact:
                content_preview = (artifact.content or "")[:max_content_chars]
                parts.append(
                    f"\n--- [{artifact.artifact_type.value}] {artifact.title} "
                    f"(by {ut.assigned_agent_slug or 'unknown'}) ---\n"
                    f"{content_preview}"
                )
                artifact_count += 1
        if artifact_count == 0:
            parts.append("No upstream artifacts available.")
        parts.append("")

    return "\n".join(parts)

