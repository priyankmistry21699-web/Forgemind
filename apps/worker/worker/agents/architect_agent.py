"""Architect agent — produces architecture and system design artifacts."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from app.core.llm import llm_completion
from worker.agents.base import build_handoff_context

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.models.task import Task
    from app.models.agent import Agent

logger = logging.getLogger("forgemind.worker.agents.architect")

SYSTEM_PROMPT = (
    "You are an expert software architect. Given a task description and any prior work context, "
    "produce a clear, concise architecture document covering: "
    "system components, data flow, technology choices, and key design decisions. "
    "Build upon any upstream artifacts provided. Write in Markdown format."
)


async def handle(db: "AsyncSession", task: "Task", agent: "Agent") -> dict:
    context = await build_handoff_context(db, task)
    content = await llm_completion(
        prompt=context,
        system=SYSTEM_PROMPT,
    )
    if content is None:
        content = (
            f"# Architecture Draft — {task.title}\n\n"
            f"[Stub] No LLM available. This is a placeholder architecture document.\n\n"
            f"## Components\n- TBD\n\n## Data Flow\n- TBD\n\n## Design Decisions\n- TBD"
        )

    return {
        "artifact_title": f"Architecture: {task.title}",
        "artifact_content": content,
        "artifact_type": "architecture",
    }
