"""FM-228: Documentation agent.

Triggered via POST /api/v1/projects/{id}/generate-docs.
Reads all route files + service docstrings and generates:
  - README.md
  - API_REFERENCE.md
  - ARCHITECTURE.md

Each document is saved as an Artifact of type DOCUMENTATION.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from app.core.llm import llm_completion

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.models.task import Task
    from app.models.agent import Agent

logger = logging.getLogger("forgemind.worker.agents.doc")

_SYSTEM_PROMPT = (
    "You are a technical writer.  Given a code context, generate clear, well-structured "
    "Markdown documentation.  For README.md: include overview, features, quickstart, and "
    "configuration.  For API_REFERENCE.md: list endpoints grouped by domain with request/"
    "response schemas.  For ARCHITECTURE.md: describe system components and data flow."
)


async def handle(db: "AsyncSession", task: "Task", agent: "Agent") -> dict:
    from worker.agents.base import build_handoff_context

    context = await build_handoff_context(db, task)
    doc_type = (task.description or "").lower()

    if "api" in doc_type:
        doc_name = "API_REFERENCE.md"
        prompt = f"Generate API_REFERENCE.md for this project:\n{context}"
    elif "arch" in doc_type:
        doc_name = "ARCHITECTURE.md"
        prompt = f"Generate ARCHITECTURE.md for this project:\n{context}"
    else:
        doc_name = "README.md"
        prompt = f"Generate README.md for this project:\n{context}"

    content = await llm_completion(
        prompt=prompt,
        system=_SYSTEM_PROMPT,
        task_type="planner",
    )

    if content is None:
        content = f"# {doc_name.replace('.md', '')}\n\n[Stub] LLM unavailable."

    return {
        "artifact_title": doc_name,
        "artifact_content": content,
        "artifact_type": "documentation",
    }
