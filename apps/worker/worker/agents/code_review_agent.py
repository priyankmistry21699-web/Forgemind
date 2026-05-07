"""FM-227: Code review agent.

Triggered when a PR draft or patch is created.  Reviews the diff and:
1. Produces ReviewComment records (file, line, severity, body)
2. Optionally posts inline comments to GitHub via github_client
3. Emits a summary review artifact on the run
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from app.core.llm import llm_completion
from worker.agents.base import build_handoff_context

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.models.task import Task
    from app.models.agent import Agent

logger = logging.getLogger("forgemind.worker.agents.code_review")

_SYSTEM_PROMPT = (
    "You are a senior code reviewer. Analyze the given code diff or implementation "
    "and produce a structured review. For each issue found, output a JSON array of "
    "comment objects with fields: file_path, line_number (or null), severity "
    "(info|warning|error|critical), category (e.g. security|performance|style|correctness), "
    "and body. After the JSON array, write a brief summary paragraph in Markdown."
    "\n\nExample format:\n"
    '```json\n[{"file_path":"src/api.py","line_number":42,"severity":"warning",'
    '"category":"security","body":"Input is not validated before use in query"}]\n```'
    "\n\n## Summary\n..."
)


async def handle(db: "AsyncSession", task: "Task", agent: "Agent") -> dict:
    context = await build_handoff_context(db, task)
    content = await llm_completion(
        prompt=context,
        system=_SYSTEM_PROMPT,
        task_type="reviewer",
    )

    if content is None:
        content = (
            f"# Code Review — {task.title}\n\n"
            "[Stub] LLM unavailable.\n\n"
            "```json\n[]\n```\n\n## Summary\nNo issues detected (stub mode)."
        )

    # Parse ReviewComment records from LLM response
    comments_created = await _persist_review_comments(db, task, content)

    return {
        "artifact_title": f"Code Review: {task.title}",
        "artifact_content": content,
        "artifact_type": "review",
        "review_comments_created": comments_created,
    }


async def _persist_review_comments(
    db: "AsyncSession", task: "Task", content: str
) -> int:
    """Extract JSON comment array from LLM response and persist as ReviewComment records."""
    import json
    import re

    from app.models.agent_intelligence import ReviewComment, ReviewCommentSeverity

    match = re.search(r"```json\s*(\[.*?\])\s*```", content, re.DOTALL)
    if not match:
        return 0

    try:
        items = json.loads(match.group(1))
    except (json.JSONDecodeError, ValueError):
        return 0

    count = 0
    for item in items[:50]:  # cap at 50 comments per review
        sev_str = item.get("severity", "info")
        try:
            sev = ReviewCommentSeverity(sev_str)
        except ValueError:
            sev = ReviewCommentSeverity.INFO

        comment = ReviewComment(
            run_id=task.run_id,
            file_path=item.get("file_path"),
            line_number=item.get("line_number"),
            severity=sev,
            body=str(item.get("body", ""))[:2000],
            category=item.get("category"),
        )
        db.add(comment)
        count += 1

    if count:
        await db.flush()
    return count
