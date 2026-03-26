"""Coder agent — produces implementation draft artifacts."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from app.core.llm import llm_completion
from worker.agents.base import build_handoff_context

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.models.task import Task
    from app.models.agent import Agent

logger = logging.getLogger("forgemind.worker.agents.coder")

SYSTEM_PROMPT = (
    "You are an expert software developer. Given a task description and any prior work context "
    "(especially architecture documents), produce a clear implementation draft including: "
    "code structure, key functions/classes, and inline comments explaining the approach. "
    "Follow the architecture decisions from upstream artifacts. Write code in appropriate language with Markdown formatting."
)


async def handle(db: "AsyncSession", task: "Task", agent: "Agent") -> dict:
    context = await build_handoff_context(db, task)
    content = await llm_completion(
        prompt=context,
        system=SYSTEM_PROMPT,
    )
    if content is None:
        content = (
            f"# Implementation Draft — {task.title}\n\n"
            f"[Stub] No LLM available. This is a placeholder implementation.\n\n"
            f"```python\n# TODO: Implement {task.title}\npass\n```"
        )

    return {
        "artifact_title": f"Implementation: {task.title}",
        "artifact_content": content,
        "artifact_type": "implementation",
    }
