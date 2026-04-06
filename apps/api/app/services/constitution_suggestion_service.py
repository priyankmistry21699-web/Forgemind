"""FM-117: Constitution Suggestion service — knowledge-driven constitution improvements.

Analyzes run outcomes, knowledge entries, and project history to generate
actionable constitution suggestions. Suggestions are NEVER auto-applied —
they must be explicitly accepted or rejected by the user.
"""

import uuid
import logging
from typing import Any

from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.constitution_suggestion import ConstitutionSuggestion, SuggestionStatus
from app.models.project_knowledge import ProjectKnowledge, KnowledgeType
from app.models.run import Run, RunStatus
from app.models.task import Task, TaskStatus
from app.services import constitution_service

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Suggestion generation rules
# ---------------------------------------------------------------------------

_SUGGESTION_RULES: list[dict[str, Any]] = [
    {
        "id": "missing-tests",
        "title": "Add requirement for test coverage",
        "category": "quality",
        "condition": "repeated_task_type_failures",
        "task_type": "testing",
        "threshold": 2,
        "suggested_text": "All implementation work must include corresponding test coverage. No feature is complete without tests.",
        "rationale": "Multiple runs have had failures in testing tasks, suggesting tests are being missed or inadequately scoped.",
    },
    {
        "id": "review-gaps",
        "title": "Require code review for all changes",
        "category": "quality",
        "condition": "few_review_tasks",
        "threshold": 0,
        "suggested_text": "All implementation artifacts must undergo review before approval. Code review is mandatory.",
        "rationale": "Completed runs have had few or no review tasks, which increases the risk of defects reaching production.",
    },
    {
        "id": "error-handling",
        "title": "Enforce explicit error handling strategy",
        "category": "reliability",
        "condition": "task_failures_with_errors",
        "threshold": 3,
        "suggested_text": "Every service function must handle expected error cases. Error messages must be actionable and user-visible errors must not expose internal details.",
        "rationale": "Multiple tasks have failed with error messages, suggesting error handling is not being planned upfront.",
    },
    {
        "id": "architecture-review",
        "title": "Require architecture decisions for structural changes",
        "category": "architecture",
        "condition": "architecture_lessons",
        "threshold": 1,
        "suggested_text": "Any work that changes database schema, API contracts, or core data flow must include an architecture decision record (ADR) section in the plan.",
        "rationale": "Project knowledge contains architecture-related lessons, suggesting structural decisions should be formalized.",
    },
    {
        "id": "smaller-phases",
        "title": "Prefer smaller implementation phases",
        "category": "process",
        "condition": "large_task_sets",
        "threshold": 10,
        "suggested_text": "Plans should break implementation into phases of no more than 8 tasks. Large phases increase risk and reduce reviewability.",
        "rationale": "Recent runs have had large task sets which correlate with higher failure rates.",
    },
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def generate_suggestions(
    db: AsyncSession,
    project_id: uuid.UUID,
) -> list[ConstitutionSuggestion]:
    """Analyze project history and generate constitution improvement suggestions.

    Only generates suggestions that don't already exist (by title) for the project.
    """
    suggestions: list[ConstitutionSuggestion] = []

    # Gather signals
    signals = await _gather_project_signals(db, project_id)

    for rule in _SUGGESTION_RULES:
        # Check if suggestion already exists
        existing = await db.execute(
            select(ConstitutionSuggestion).where(
                ConstitutionSuggestion.project_id == project_id,
                ConstitutionSuggestion.title == rule["title"],
                ConstitutionSuggestion.status == SuggestionStatus.PENDING,
            )
        )
        if existing.scalar_one_or_none() is not None:
            continue

        # Evaluate rule condition
        if _evaluate_rule(rule, signals):
            suggestion = ConstitutionSuggestion(
                project_id=project_id,
                title=rule["title"],
                rationale=rule["rationale"],
                suggested_text=rule["suggested_text"],
                category=rule["category"],
                status=SuggestionStatus.PENDING,
                source_metadata={
                    "rule_id": rule["id"],
                    "signals": {k: v for k, v in signals.items() if isinstance(v, (int, float, str, bool))},
                },
            )
            db.add(suggestion)
            suggestions.append(suggestion)

    if suggestions:
        await db.flush()
        logger.info("Generated %d suggestions for project %s", len(suggestions), project_id)

    return suggestions


async def list_suggestions(
    db: AsyncSession,
    project_id: uuid.UUID,
    *,
    status: SuggestionStatus | None = None,
) -> tuple[list[ConstitutionSuggestion], int]:
    """List suggestions for a project, optionally filtered by status."""
    query = select(ConstitutionSuggestion).where(
        ConstitutionSuggestion.project_id == project_id
    )
    if status is not None:
        query = query.where(ConstitutionSuggestion.status == status)

    count_result = await db.execute(
        select(sa_func.count()).select_from(query.subquery())
    )
    total = count_result.scalar_one()

    result = await db.execute(query.order_by(ConstitutionSuggestion.created_at.desc()))
    return list(result.scalars().all()), total


async def resolve_suggestion(
    db: AsyncSession,
    suggestion_id: uuid.UUID,
    action: str,
) -> ConstitutionSuggestion:
    """Accept or reject a suggestion.

    If accepted, appends the suggested text to the project's constitution.
    """
    result = await db.execute(
        select(ConstitutionSuggestion).where(ConstitutionSuggestion.id == suggestion_id)
    )
    suggestion = result.scalar_one_or_none()
    if suggestion is None:
        raise ValueError(f"Suggestion {suggestion_id} not found")

    if suggestion.status != SuggestionStatus.PENDING:
        raise ValueError(f"Suggestion is already {suggestion.status.value}")

    if action == "accept":
        suggestion.status = SuggestionStatus.ACCEPTED
        # Append to constitution
        constitution = await constitution_service.get_constitution(
            db, suggestion.project_id
        )
        if constitution:
            new_content = (
                constitution.content
                + f"\n\n### {suggestion.title}\n{suggestion.suggested_text}"
            )
            from app.schemas.constitution import ConstitutionCreate

            await constitution_service.create_or_update_constitution(
                db,
                suggestion.project_id,
                ConstitutionCreate(
                    content=new_content,
                    title=constitution.title,
                    summary=constitution.summary,
                ),
            )
        else:
            # Create new constitution from suggestion
            await constitution_service.create_or_update_constitution(
                db,
                suggestion.project_id,
                ConstitutionCreate(
                    content=f"### {suggestion.title}\n{suggestion.suggested_text}",
                    title="Project Constitution",
                ),
            )
        logger.info("Accepted suggestion %s for project %s", suggestion_id, suggestion.project_id)

    elif action == "reject":
        suggestion.status = SuggestionStatus.REJECTED
        logger.info("Rejected suggestion %s", suggestion_id)

    else:
        raise ValueError(f"Invalid action '{action}'. Must be 'accept' or 'reject'.")

    db.add(suggestion)
    await db.flush()
    await db.refresh(suggestion)
    return suggestion


# ---------------------------------------------------------------------------
# Signal gathering
# ---------------------------------------------------------------------------


async def _gather_project_signals(
    db: AsyncSession,
    project_id: uuid.UUID,
) -> dict[str, Any]:
    """Collect quantitative signals from project history."""
    signals: dict[str, Any] = {}

    # Count runs by status
    for status in [RunStatus.COMPLETED, RunStatus.FAILED]:
        result = await db.execute(
            select(sa_func.count()).where(
                Run.project_id == project_id, Run.status == status
            )
        )
        signals[f"runs_{status.value}"] = result.scalar_one()

    # Count failed tasks by type
    failed_tasks = await db.execute(
        select(Task.task_type, sa_func.count())
        .join(Run, Task.run_id == Run.id)
        .where(Run.project_id == project_id, Task.status == TaskStatus.FAILED)
        .group_by(Task.task_type)
    )
    failed_by_type: dict[str, int] = {}
    for row in failed_tasks:
        failed_by_type[row[0]] = row[1]
    signals["failed_tasks_by_type"] = failed_by_type

    # Count tasks with errors
    error_count_result = await db.execute(
        select(sa_func.count())
        .select_from(Task)
        .join(Run, Task.run_id == Run.id)
        .where(
            Run.project_id == project_id,
            Task.status == TaskStatus.FAILED,
            Task.error_message.isnot(None),
        )
    )
    signals["tasks_with_errors"] = error_count_result.scalar_one()

    # Count review tasks
    review_count_result = await db.execute(
        select(sa_func.count())
        .select_from(Task)
        .join(Run, Task.run_id == Run.id)
        .where(Run.project_id == project_id, Task.task_type == "review")
    )
    signals["review_task_count"] = review_count_result.scalar_one()

    # Knowledge lessons
    knowledge_result = await db.execute(
        select(sa_func.count()).where(
            ProjectKnowledge.project_id == project_id,
            ProjectKnowledge.knowledge_type == KnowledgeType.ARCHITECTURE,
        )
    )
    signals["architecture_knowledge_count"] = knowledge_result.scalar_one()

    # Max tasks in a single run
    task_counts_sub = (
        select(sa_func.count().label("cnt"))
        .select_from(Task)
        .join(Run, Task.run_id == Run.id)
        .where(Run.project_id == project_id)
        .group_by(Run.id)
        .subquery()
    )
    max_tasks_result = await db.execute(
        select(sa_func.max(task_counts_sub.c.cnt))
    )
    signals["max_tasks_per_run"] = max_tasks_result.scalar_one_or_none() or 0

    return signals


# ---------------------------------------------------------------------------
# Rule evaluation
# ---------------------------------------------------------------------------


def _evaluate_rule(rule: dict[str, Any], signals: dict[str, Any]) -> bool:
    """Check whether a rule's condition is met by the signals."""
    condition = rule["condition"]
    threshold = rule.get("threshold", 0)

    if condition == "repeated_task_type_failures":
        task_type = rule.get("task_type", "")
        failed = signals.get("failed_tasks_by_type", {})
        return failed.get(task_type, 0) >= threshold

    if condition == "few_review_tasks":
        completed_runs = signals.get("runs_completed", 0)
        review_count = signals.get("review_task_count", 0)
        return completed_runs >= 2 and review_count <= threshold

    if condition == "task_failures_with_errors":
        return signals.get("tasks_with_errors", 0) >= threshold

    if condition == "architecture_lessons":
        return signals.get("architecture_knowledge_count", 0) >= threshold

    if condition == "large_task_sets":
        return signals.get("max_tasks_per_run", 0) >= threshold

    return False
