"""Execution chat service — context assembly + LLM summarization for run Q&A."""

import uuid
import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.services import run_memory_service
from app.core.llm import llm_completion

logger = logging.getLogger(__name__)

CHAT_SYSTEM_PROMPT = """\
You are ForgeMind's execution assistant.
You help operators understand what is happening in a project run.
You have access to the current run's tasks, artifacts, approvals, and events.
Answer concisely and factually based on the provided context.
If you don't know something, say so. Never fabricate information.
"""


async def _build_run_context(db: AsyncSession, run_id: uuid.UUID) -> str:
    """Assemble a text context from the run memory service."""
    summary = await run_memory_service.get_run_summary(db, run_id)
    if "error" in summary:
        return "Run not found."
    return run_memory_service.build_context_for_chat(summary)


async def chat_about_run(
    db: AsyncSession,
    run_id: uuid.UUID,
    user_message: str,
) -> str:
    """Answer a user question about a specific run using context + LLM."""
    context = await _build_run_context(db, run_id)

    prompt = (
        f"=== Run Context ===\n{context}\n\n"
        f"=== Operator Question ===\n{user_message}"
    )

    response = await llm_completion(
        prompt,
        system=CHAT_SYSTEM_PROMPT,
        max_tokens=1024,
        temperature=0.3,
    )

    if response:
        return response

    # Stub fallback when LLM is unavailable
    return _build_stub_response(context, user_message)


def _build_stub_response(context: str, question: str) -> str:
    """Generate a simple rule-based response when LLM is unavailable."""
    lower = question.lower()

    if "block" in lower or "stuck" in lower:
        # Find blocked tasks
        lines = [l for l in context.split("\n") if "[blocked]" in l.lower()]
        if lines:
            return "The following tasks are currently blocked:\n" + "\n".join(lines)
        return "No tasks are currently blocked."

    if "fail" in lower or "error" in lower:
        lines = [l for l in context.split("\n") if "[failed]" in l.lower() or "ERROR:" in l]
        if lines:
            return "Failed tasks:\n" + "\n".join(lines)
        return "No tasks have failed."

    if "approv" in lower or "pending" in lower:
        lines = [l for l in context.split("\n") if "[pending]" in l.lower()]
        if lines:
            return "Pending approvals:\n" + "\n".join(lines)
        return "No pending approvals."

    if "artifact" in lower or "output" in lower:
        lines = [l for l in context.split("\n") if l.startswith("- [") and "===" not in l and "Artifacts" not in l]
        artifact_lines = [l for l in context.split("\n") if "] " in l and ("architecture" in l.lower() or "implementation" in l.lower() or "review" in l.lower() or "test_report" in l.lower() or "plan_summary" in l.lower())]
        if artifact_lines:
            return "Artifacts produced:\n" + "\n".join(artifact_lines[:10])
        return "No artifacts have been produced yet."

    # Default: return the context summary
    return f"Here is the current run status:\n\n{context[:2000]}"
