"""Agent handler registry — maps agent slugs to their execution handlers.

Each handler is an async function with signature:
    async def handler(db: AsyncSession, task: Task, agent: Agent) -> dict

The returned dict should contain:
    artifact_title: str
    artifact_content: str
    artifact_type: str  (matching ArtifactType enum value)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Awaitable

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.models.task import Task
    from app.models.agent import Agent

from worker.agents.architect_agent import handle as architect_handle
from worker.agents.coder_agent import handle as coder_handle
from worker.agents.reviewer_agent import handle as reviewer_handle
from worker.agents.tester_agent import handle as tester_handle

AgentHandler = Callable[["AsyncSession", "Task", "Agent"], Awaitable[dict]]

# Map of agent slug -> handler function
AGENT_HANDLERS: dict[str, AgentHandler] = {
    "architect": architect_handle,
    "coder": coder_handle,
    "reviewer": reviewer_handle,
    "tester": tester_handle,
}
