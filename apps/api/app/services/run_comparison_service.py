"""Run comparison service — side-by-side run analysis.

FM-166: Compare two runs to identify divergent outcomes,
common task types, and execution differences.
"""

import uuid
import logging

from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.run import Run
from app.models.task import Task
from app.models.artifact import Artifact

logger = logging.getLogger(__name__)


async def compare_runs(
    db: AsyncSession,
    run_a_id: uuid.UUID,
    run_b_id: uuid.UUID,
) -> dict | None:
    """Compare two runs side-by-side.

    Returns a comparison summary including:
    - Status of each run
    - Task counts and types
    - Common task types between runs
    - Divergent outcomes (tasks with same type but different results)
    - Summary narrative
    """
    # Load both runs
    ra_result = await db.execute(select(Run).where(Run.id == run_a_id))
    run_a = ra_result.scalar_one_or_none()
    rb_result = await db.execute(select(Run).where(Run.id == run_b_id))
    run_b = rb_result.scalar_one_or_none()

    if not run_a or not run_b:
        return None

    # Load tasks for each run
    tasks_a_result = await db.execute(select(Task).where(Task.run_id == run_a_id))
    tasks_a = list(tasks_a_result.scalars().all())

    tasks_b_result = await db.execute(select(Task).where(Task.run_id == run_b_id))
    tasks_b = list(tasks_b_result.scalars().all())

    # Compute task type sets
    types_a = {t.task_type for t in tasks_a if t.task_type}
    types_b = {t.task_type for t in tasks_b if t.task_type}
    common_types = sorted(types_a & types_b)

    # Find divergent outcomes — same task_type but different status
    divergent = []
    for task_type in common_types:
        a_tasks = [t for t in tasks_a if t.task_type == task_type]
        b_tasks = [t for t in tasks_b if t.task_type == task_type]

        for ta in a_tasks:
            for tb in b_tasks:
                if ta.status != tb.status:
                    divergent.append(
                        {
                            "task_type": task_type,
                            "run_a_task": ta.title,
                            "run_a_status": ta.status.value if ta.status else "unknown",
                            "run_b_task": tb.title,
                            "run_b_status": tb.status.value if tb.status else "unknown",
                        }
                    )

    # Artifact counts
    art_a_count = (
        await db.execute(
            select(sa_func.count()).select_from(
                select(Artifact.id).where(Artifact.run_id == run_a_id).subquery()
            )
        )
    ).scalar_one()

    art_b_count = (
        await db.execute(
            select(sa_func.count()).select_from(
                select(Artifact.id).where(Artifact.run_id == run_b_id).subquery()
            )
        )
    ).scalar_one()

    # Build summary
    summary_parts = [
        f"Run A (#{run_a.run_number}): {run_a.status.value}, {len(tasks_a)} tasks, {art_a_count} artifacts.",
        f"Run B (#{run_b.run_number}): {run_b.status.value}, {len(tasks_b)} tasks, {art_b_count} artifacts.",
    ]
    if common_types:
        summary_parts.append(f"Common task types: {', '.join(common_types)}.")
    if divergent:
        summary_parts.append(f"{len(divergent)} divergent outcome(s) found.")
    else:
        summary_parts.append("No divergent outcomes detected.")

    return {
        "run_a_id": str(run_a_id),
        "run_b_id": str(run_b_id),
        "run_a_status": run_a.status.value,
        "run_b_status": run_b.status.value,
        "run_a_task_count": len(tasks_a),
        "run_b_task_count": len(tasks_b),
        "run_a_artifact_count": art_a_count,
        "run_b_artifact_count": art_b_count,
        "common_task_types": common_types,
        "divergent_outcomes": divergent,
        "summary": " ".join(summary_parts),
    }
