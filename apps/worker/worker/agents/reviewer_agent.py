"""Reviewer agent — produces code/artifact review summaries."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from app.core.llm import llm_completion
from worker.agents.base import build_handoff_context

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.models.task import Task
    from app.models.agent import Agent

logger = logging.getLogger("forgemind.worker.agents.reviewer")

SYSTEM_PROMPT = (
    "You are an expert code reviewer. Given a task description and any prior work context "
    "(especially implementation code and architecture documents), "
    "produce a thorough review covering: correctness, code quality, "
    "potential issues, security concerns, and improvement suggestions. "
    "Reference specific upstream artifacts when critiquing. Write in Markdown format with clear sections."
)


async def handle(db: "AsyncSession", task: "Task", agent: "Agent") -> dict:
    context = await build_handoff_context(db, task)
    content = await llm_completion(
        prompt=context,
        system=SYSTEM_PROMPT,
    )
    if content is None:
        content = (
            f"# Review — {task.title}\n\n"
            f"[Stub] No LLM available. This is a placeholder review.\n\n"
            f"## Correctness\n- TBD\n\n## Quality\n- TBD\n\n## Suggestions\n- TBD"
        )

    return {
        "artifact_title": f"Review: {task.title}",
        "artifact_content": content,
        "artifact_type": "review",
    }
