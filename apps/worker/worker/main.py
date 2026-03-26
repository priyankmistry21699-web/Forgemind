"""ForgeMind Worker — lightweight background task execution loop.

Polls for READY tasks, resolves the appropriate agent, claims the task,
and dispatches it for execution.

Usage:
    python -m worker.main              # from apps/worker/
    python -m apps.worker.worker.main  # from repo root (if sys.path allows)

Or via Docker Compose (forgemind-worker service).
"""

from __future__ import annotations

import asyncio
import logging
import sys
import os

# Ensure the API package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "api"))

from app.core.config import settings  # noqa: E402
from app.db.session import async_session_factory  # noqa: E402
from app.services import agent_service, task_service  # noqa: E402
from app.services import execution_service  # noqa: E402
from app.services import composition_service  # noqa: E402
from app.services import run_memory_service  # noqa: E402
from app.services import adaptive_orchestrator  # noqa: E402
from app.models.task import TaskStatus  # noqa: E402

# Will be populated by FM-025
from worker.agents import dispatch_agent  # noqa: E402

logger = logging.getLogger("forgemind.worker")

POLL_INTERVAL_SECONDS = int(os.environ.get("WORKER_POLL_INTERVAL", "5"))
MAX_TASKS_PER_CYCLE = int(os.environ.get("WORKER_MAX_TASKS_PER_CYCLE", "3"))


async def process_ready_tasks() -> int:
    """Find ready tasks across all runs, claim and execute them.

    Uses the adaptive orchestrator to:
    - Handle approval rejections (requeue tasks)
    - Auto-retry failed tasks with agent re-routing
    - Prioritise critical-path and unblocked tasks

    Returns the number of tasks processed in this cycle.
    """
    processed = 0

    async with async_session_factory() as db:
        # Run adaptive orchestration cycle
        cycle = await adaptive_orchestrator.run_adaptive_cycle(
            db, max_tasks=MAX_TASKS_PER_CYCLE
        )

        if cycle["requeued"]:
            logger.info("Adaptive: requeued %d task(s) from rejected approvals", cycle["requeued"])
        if cycle["retried"]:
            logger.info("Adaptive: auto-retried %d failed task(s)", cycle["retried"])

        ready_tasks = cycle["selected_tasks"]

        for task in ready_tasks:
            # Resolve which agent should handle this task
            # Priority: assigned_agent_slug (from planner) → capability scoring
            agent_slug = await composition_service.resolve_agent_for_task(
                db, task.task_type, agent_hint=task.assigned_agent_slug
            )
            if agent_slug is None:
                # Fallback: try legacy task-type matching
                agent = await agent_service.resolve_agent_for_task_type(
                    db, task.task_type
                )
                agent_slug = agent.slug if agent else None

            if agent_slug is None:
                logger.warning(
                    "No agent found for task_type=%s (task=%s), skipping",
                    task.task_type,
                    task.id,
                )
                continue

            agent = await agent_service.get_agent_by_slug(db, agent_slug)
            if agent is None:
                logger.warning(
                    "Agent slug '%s' not found in registry, skipping task %s",
                    agent_slug,
                    task.id,
                )
                continue

            try:
                # Claim the task
                await execution_service.claim_task(db, task.id, agent.slug)
                await db.commit()
                logger.info(
                    "Claimed task %s for agent %s", task.title[:60], agent.slug
                )

                # Dispatch to the agent for execution
                result_data = await dispatch_agent(db, task, agent)

                # Complete the task with the agent's output
                await execution_service.complete_task(
                    db,
                    task.id,
                    artifact_title=result_data.get("artifact_title"),
                    artifact_content=result_data.get("artifact_content"),
                    artifact_type=result_data.get("artifact_type"),
                )
                await db.commit()
                logger.info(
                    "Completed task %s (agent=%s, handoff_context=upstream)",
                    task.title[:60],
                    agent.slug,
                )
                run_memory_service.invalidate_run_cache(task.run_id)
                processed += 1

            except Exception:
                await db.rollback()
                logger.exception("Failed to process task %s", task.id)
                try:
                    async with async_session_factory() as err_db:
                        await execution_service.fail_task(
                            err_db, task.id, "Worker execution error"
                        )
                        await err_db.commit()
                        run_memory_service.invalidate_run_cache(task.run_id)
                except Exception:
                    logger.exception("Could not mark task %s as failed", task.id)

    return processed


async def worker_loop() -> None:
    """Main polling loop — runs indefinitely."""
    logger.info(
        "ForgeMind worker started (poll=%ds, max_per_cycle=%d)",
        POLL_INTERVAL_SECONDS,
        MAX_TASKS_PER_CYCLE,
    )

    while True:
        try:
            processed = await process_ready_tasks()
            if processed > 0:
                logger.info("Cycle complete: %d task(s) processed", processed)
        except Exception:
            logger.exception("Error in worker cycle")

        await asyncio.sleep(POLL_INTERVAL_SECONDS)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )
    asyncio.run(worker_loop())


if __name__ == "__main__":
    main()
