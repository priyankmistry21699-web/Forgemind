"""Tester agent — produces test plans and test report artifacts."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from app.core.llm import llm_completion
from worker.agents.base import build_handoff_context

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.models.task import Task
    from app.models.agent import Agent

logger = logging.getLogger("forgemind.worker.agents.tester")

SYSTEM_PROMPT = (
    "You are an expert software tester. Given a task description and any prior work context "
    "(especially implementation code and architecture), "
    "produce a comprehensive test plan covering: test strategy, "
    "key test cases (with expected outcomes), edge cases to consider, "
    "and a recommended testing approach. Base your tests on the actual upstream artifacts. Write in Markdown format."
)


async def handle(db: "AsyncSession", task: "Task", agent: "Agent") -> dict:
    context = await build_handoff_context(db, task)
    content = await llm_completion(
        prompt=context,
        system=SYSTEM_PROMPT,
    )
    if content is None:
        content = (
            f"# Test Plan — {task.title}\n\n"
            f"[Stub] No LLM available. This is a placeholder test plan.\n\n"
            f"## Strategy\n- TBD\n\n## Test Cases\n- TBD\n\n## Edge Cases\n- TBD"
        )

    return {
        "artifact_title": f"Test Plan: {task.title}",
        "artifact_content": content,
        "artifact_type": "test_report",
    }
