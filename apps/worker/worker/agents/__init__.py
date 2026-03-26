"""Agent dispatcher — routes tasks to the appropriate fixed agent implementation.

This module is the bridge between the worker loop and individual agent logic.
FM-025 will populate this with real agent implementations.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.models.task import Task
    from app.models.agent import Agent

logger = logging.getLogger("forgemind.worker.agents")


async def dispatch_agent(
    db: "AsyncSession",
    task: "Task",
    agent: "Agent",
) -> dict:
    """Dispatch a task to the appropriate agent and return the result.

    Returns a dict with optional keys:
        artifact_title: str
        artifact_content: str
        artifact_type: str  (must match ArtifactType enum values)
    """
    # Import agent implementations (FM-025 will add real ones)
    from worker.agents.registry import AGENT_HANDLERS

    handler = AGENT_HANDLERS.get(agent.slug)
    if handler is None:
        logger.warning("No handler registered for agent '%s', using stub", agent.slug)
        return {
            "artifact_title": f"Stub output for {task.title}",
            "artifact_content": f"[Stub] Agent '{agent.slug}' processed task: {task.title}\n\nNo real execution logic yet.",
            "artifact_type": "other",
        }

    return await handler(db, task, agent)
