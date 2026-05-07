"""FM-229: Test generation agent.

Triggered post-commit or manually for a project.
Given a service function signature and body, generates pytest unit test stubs
and creates a CodePatch record for review.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from app.core.llm import llm_completion

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.models.task import Task
    from app.models.agent import Agent

logger = logging.getLogger("forgemind.worker.agents.testgen")

_SYSTEM_PROMPT = (
    "You are a Python test engineer specializing in pytest and FastAPI.  "
    "Given a service module or function, generate comprehensive pytest unit tests that cover: "
    "1) happy path, 2) edge cases, 3) error conditions.  "
    "Use async test functions where needed.  Mock external dependencies.  "
    "Output only valid Python code with no extra explanation."
)


async def handle(db: "AsyncSession", task: "Task", agent: "Agent") -> dict:
    from worker.agents.base import build_handoff_context

    context = await build_handoff_context(db, task)
    content = await llm_completion(
        prompt=f"Generate pytest tests for the following service code:\n{context}",
        system=_SYSTEM_PROMPT,
        task_type="tester",
    )

    if content is None:
        content = (
            f"# Generated Tests — {task.title}\n\n"
            "```python\n"
            "import pytest\n\n"
            f"# [Stub] LLM unavailable — tests for {task.title}\n"
            "async def test_placeholder():\n"
            "    assert True  # TODO: implement\n"
            "```"
        )

    # Create a CodePatch so the tests go through approval before being committed
    patch_created = await _create_test_patch(db, task, content)

    return {
        "artifact_title": f"Generated Tests: {task.title}",
        "artifact_content": content,
        "artifact_type": "test_report",
        "patch_created": patch_created,
    }


async def _create_test_patch(
    db: "AsyncSession", task: "Task", test_content: str
) -> bool:
    """Create a PatchProposal for the generated test file."""
    from app.models.code_ops import PatchProposal, PatchStatus

    patch_file = f"tests/test_generated_{task.title[:40].lower().replace(' ', '_')}.py"
    # Extract Python code from markdown if wrapped in fences
    import re

    m = re.search(r"```python\s*(.*?)```", test_content, re.DOTALL)
    code = m.group(1).strip() if m else test_content

    project_id = task.run.project_id if hasattr(task, "run") and task.run else None
    patch = PatchProposal(
        project_id=project_id,
        title=f"Generated tests: {task.title}",
        description="Auto-generated pytest test stubs by TestGenAgent",
        status=PatchStatus.DRAFT,
        diff_content=f"--- /dev/null\n+++ b/{patch_file}\n@@ -0,0 +1 @@\n+{code[:3000]}",
        target_branch="main",
        proposed_by_agent=task.assigned_agent_slug or "testgen",
    )
    db.add(patch)
    try:
        await db.flush()
        return True
    except Exception as exc:
        logger.warning("testgen: could not create patch (%s)", exc)
        return False
