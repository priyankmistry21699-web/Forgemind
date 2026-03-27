"""Execution chat service v2 — enhanced context assembly + topic detection + LLM.

FM-044 enhancements:
- Topic detection for targeted context building
- Blocker/failure explanation with connector readiness context
- Next-step suggestions based on run state
- Approval impact analysis
- Retry/revision guidance with adaptive retry context
- Artifact comparison support
"""

import uuid
import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.services import run_memory_service
from app.services import connector_service
from app.services import adaptive_retry_service
from app.core.llm import llm_completion

logger = logging.getLogger(__name__)

CHAT_SYSTEM_PROMPT = """\
You are ForgeMind's execution assistant (v2).
You help operators understand what is happening in a project run.
You have access to the current run's tasks, artifacts, approvals, events,
connector readiness states, and retry history.

Your capabilities:
- Explain blockers and failures with root cause analysis
- Suggest next steps based on the current run state
- Analyse approval impact on execution flow
- Provide retry and revision guidance
- Compare artifacts across tasks

Answer concisely and factually based on the provided context.
If you don't know something, say so. Never fabricate information.
Use structured formatting (bullets, headers) for complex answers.
"""

# ---------------------------------------------------------------------------
# Topic detection
# ---------------------------------------------------------------------------

class ChatTopic:
    BLOCKER = "blocker"
    FAILURE = "failure"
    APPROVAL = "approval"
    ARTIFACT = "artifact"
    RETRY = "retry"
    CONNECTOR = "connector"
    NEXT_STEP = "next_step"
    STATUS = "status"
    GENERAL = "general"


TOPIC_KEYWORDS: dict[str, list[str]] = {
    ChatTopic.BLOCKER: ["block", "stuck", "waiting", "deadlock", "stall"],
    ChatTopic.FAILURE: ["fail", "error", "crash", "bug", "broken", "exception"],
    ChatTopic.APPROVAL: ["approv", "pending", "review", "sign-off", "gate"],
    ChatTopic.ARTIFACT: ["artifact", "output", "result", "deliverable", "produced"],
    ChatTopic.RETRY: ["retry", "rerun", "again", "attempt", "revision", "redo"],
    ChatTopic.CONNECTOR: ["connector", "credential", "integration", "token", "secret", "oauth"],
    ChatTopic.NEXT_STEP: ["next", "what should", "recommend", "suggest", "do now", "plan"],
    ChatTopic.STATUS: ["status", "progress", "how far", "overview", "summary"],
}


def detect_topics(message: str) -> list[str]:
    """Detect conversation topics from a user message."""
    lower = message.lower()
    topics = []
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            topics.append(topic)
    return topics or [ChatTopic.GENERAL]


# ---------------------------------------------------------------------------
# Context builders
# ---------------------------------------------------------------------------

async def _build_run_context(db: AsyncSession, run_id: uuid.UUID) -> str:
    """Assemble a text context from the run memory service."""
    summary = await run_memory_service.get_run_summary(db, run_id)
    if "error" in summary:
        return "Run not found."
    return run_memory_service.build_context_for_chat(summary)


async def _build_connector_context(db: AsyncSession, run_id: uuid.UUID) -> str:
    """Build connector readiness context for the run's project."""
    from app.models.run import Run
    from sqlalchemy import select

    run_result = await db.execute(select(Run).where(Run.id == run_id))
    run = run_result.scalar_one_or_none()
    if run is None:
        return ""

    readiness = await connector_service.get_project_readiness(db, run.project_id)
    if readiness["total"] == 0:
        return "No connectors linked to this project."

    lines = [f"=== Connector Readiness ({readiness['total']}) ==="]
    lines.append(
        f"  Ready: {readiness['ready_count']} | Configured: {readiness['configured_count']} "
        f"| Blocked: {readiness['blocked_count']} | Missing: {readiness['missing_count']}"
    )
    lines.append(f"  All required ready: {'Yes' if readiness['all_required_ready'] else 'NO'}")

    for link in readiness["links"]:
        status_marker = "OK" if link["readiness"].value == "ready" else link["readiness"].value.upper()
        lines.append(
            f"  - [{status_marker}] {link['connector_name']} ({link['connector_slug']}) "
            f"— {link['priority'].value}"
        )
        if link["blocker_reason"]:
            lines.append(f"    Blocker: {link['blocker_reason']}")

    return "\n".join(lines)


async def _build_retry_context(db: AsyncSession, run_id: uuid.UUID) -> str:
    """Build retry/revision context for the run."""
    status = await adaptive_retry_service.get_retry_status(db, run_id)
    if status["failed_count"] == 0 and status["retried_count"] == 0:
        return ""

    lines = ["=== Retry Status ==="]
    lines.append(
        f"  Failed: {status['failed_count']} | Retried: {status['retried_count']} "
        f"| Exhausted: {status['exhausted_count']}"
    )
    if status["needs_escalation"]:
        lines.append("  ⚠ Escalation needed: some tasks have exhausted all retries")

    for ft in status["failed_tasks"]:
        lines.append(
            f"  - {ft['title']} [{ft['policy']}] "
            f"retries: {ft['retry_count']}/{ft['max_retries']} "
            f"→ {ft['suggested_action']}"
        )
        if ft.get("error_message"):
            lines.append(f"    Error: {ft['error_message'][:200]}")

    return "\n".join(lines)


async def _build_next_step_suggestions(
    db: AsyncSession, run_id: uuid.UUID
) -> str:
    """Generate next-step suggestions based on run state."""
    summary = await run_memory_service.get_run_summary(db, run_id)
    if "error" in summary:
        return ""

    suggestions: list[str] = []

    # Check approvals
    pending_approvals = summary.get("approval_summary", {}).get("status_counts", {}).get("pending", 0)
    if pending_approvals > 0:
        suggestions.append(f"Review {pending_approvals} pending approval(s) to unblock execution")

    # Check failures
    failures = summary.get("failure_context", [])
    if failures:
        retry_status = await adaptive_retry_service.get_retry_status(db, run_id)
        retryable = [f for f in retry_status["failed_tasks"] if f["can_retry"]]
        exhausted = retry_status["exhausted_tasks"]
        if retryable:
            suggestions.append(f"Retry {len(retryable)} failed task(s) that have retries available")
        if exhausted:
            suggestions.append(f"Create revision tasks for {len(exhausted)} task(s) that exhausted retries")

    # Check connector blockers
    blockers = await connector_service.get_run_connector_blockers(db, run_id)
    required_blockers = [b for b in blockers if b["priority"] == "required"]
    if required_blockers:
        suggestions.append(
            f"Configure {len(required_blockers)} required connector(s): "
            + ", ".join(b["connector_name"] for b in required_blockers)
        )

    # Check progress
    progress = summary.get("progress", 0)
    if progress == 1.0:
        suggestions.append("Run is complete! Review final artifacts and close the run")
    elif not suggestions:
        task_counts = summary.get("task_summary", {}).get("status_counts", {})
        ready = task_counts.get("ready", 0)
        running = task_counts.get("running", 0)
        if ready > 0:
            suggestions.append(f"{ready} task(s) are READY for agent assignment")
        elif running > 0:
            suggestions.append(f"{running} task(s) currently running — monitor progress")
        else:
            suggestions.append("Check task dependencies and resolve any blockers")

    if not suggestions:
        return ""

    lines = ["=== Suggested Next Steps ==="]
    for i, s in enumerate(suggestions, 1):
        lines.append(f"  {i}. {s}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main chat function
# ---------------------------------------------------------------------------

async def chat_about_run(
    db: AsyncSession,
    run_id: uuid.UUID,
    user_message: str,
) -> str:
    """Answer a user question about a specific run using enhanced context + LLM."""
    topics = detect_topics(user_message)

    # Build base context
    context = await _build_run_context(db, run_id)

    # Add topic-specific context
    extra_sections: list[str] = []

    if ChatTopic.CONNECTOR in topics or ChatTopic.BLOCKER in topics:
        connector_ctx = await _build_connector_context(db, run_id)
        if connector_ctx:
            extra_sections.append(connector_ctx)

    if ChatTopic.RETRY in topics or ChatTopic.FAILURE in topics:
        retry_ctx = await _build_retry_context(db, run_id)
        if retry_ctx:
            extra_sections.append(retry_ctx)

    if ChatTopic.NEXT_STEP in topics:
        next_steps = await _build_next_step_suggestions(db, run_id)
        if next_steps:
            extra_sections.append(next_steps)

    # Always include next steps for general/status queries
    if ChatTopic.STATUS in topics or ChatTopic.GENERAL in topics:
        next_steps = await _build_next_step_suggestions(db, run_id)
        if next_steps:
            extra_sections.append(next_steps)

    if extra_sections:
        context += "\n\n" + "\n\n".join(extra_sections)

    prompt = (
        f"=== Run Context ===\n{context}\n\n"
        f"=== Detected Topics: {', '.join(topics)} ===\n\n"
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

    # Enhanced stub fallback when LLM is unavailable
    return _build_stub_response(context, user_message, topics, extra_sections)


def _build_stub_response(
    context: str,
    question: str,
    topics: list[str],
    extra_sections: list[str],
) -> str:
    """Generate an enhanced rule-based response when LLM is unavailable."""
    lower = question.lower()

    if ChatTopic.BLOCKER in topics:
        lines = [l for l in context.split("\n") if "[blocked]" in l.lower() or "MISSING" in l or "BLOCKED" in l]
        if lines:
            return "The following items are currently blocking progress:\n" + "\n".join(lines[:10])
        return "No tasks or connectors are currently blocked."

    if ChatTopic.FAILURE in topics:
        lines = [l for l in context.split("\n") if "[failed]" in l.lower() or "ERROR:" in l or "Error:" in l]
        if lines:
            result = "Failed items:\n" + "\n".join(lines[:10])
            # Add retry guidance
            retry_lines = [l for l in context.split("\n") if "retry" in l.lower() or "retries" in l.lower()]
            if retry_lines:
                result += "\n\nRetry context:\n" + "\n".join(retry_lines[:5])
            return result
        return "No tasks have failed."

    if ChatTopic.RETRY in topics:
        retry_lines = [s for s in extra_sections if "Retry Status" in s]
        if retry_lines:
            return retry_lines[0]
        return "No retry information available for this run."

    if ChatTopic.APPROVAL in topics:
        lines = [l for l in context.split("\n") if "[pending]" in l.lower() or "pending" in l.lower()]
        if lines:
            return "Pending approvals:\n" + "\n".join(lines[:10])
        return "No pending approvals."

    if ChatTopic.CONNECTOR in topics:
        conn_lines = [s for s in extra_sections if "Connector Readiness" in s]
        if conn_lines:
            return conn_lines[0]
        return "No connector information available."

    if ChatTopic.ARTIFACT in topics:
        lines = [l for l in context.split("\n") if "] " in l and ("architecture" in l.lower() or "implementation" in l.lower() or "review" in l.lower() or "test_report" in l.lower() or "plan_summary" in l.lower())]
        if lines:
            return "Artifacts produced:\n" + "\n".join(lines[:10])
        return "No artifacts have been produced yet."

    if ChatTopic.NEXT_STEP in topics:
        step_lines = [s for s in extra_sections if "Suggested Next Steps" in s]
        if step_lines:
            return step_lines[0]
        return "No specific next steps to suggest at this time."

    # Default: return the context summary
    return f"Here is the current run status:\n\n{context[:2000]}"
