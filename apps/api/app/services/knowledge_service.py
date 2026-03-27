"""Project knowledge service — multi-run memory and knowledge base.

FM-048: Provides:
- Knowledge CRUD for project-level learning
- Automated knowledge extraction from completed runs
- Knowledge context assembly for agent enrichment
- Relevance-scored retrieval for run context
"""

import uuid
import logging
from typing import Any

from sqlalchemy import select, func as sa_func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project_knowledge import ProjectKnowledge, KnowledgeType
from app.models.run import Run, RunStatus
from app.models.task import Task, TaskStatus
from app.models.artifact import Artifact
from app.models.planner_result import PlannerResult

logger = logging.getLogger(__name__)


async def create_knowledge(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    knowledge_type: KnowledgeType,
    title: str,
    content: str,
    tags: list[str] | None = None,
    metadata: dict | None = None,
    source_run_id: uuid.UUID | None = None,
    source_task_id: uuid.UUID | None = None,
) -> ProjectKnowledge:
    """Create a new knowledge entry."""
    entry = ProjectKnowledge(
        project_id=project_id,
        knowledge_type=knowledge_type,
        title=title,
        content=content,
        tags=tags,
        metadata_=metadata,
        source_run_id=source_run_id,
        source_task_id=source_task_id,
    )
    db.add(entry)
    await db.flush()
    return entry


async def get_knowledge(
    db: AsyncSession,
    knowledge_id: uuid.UUID,
) -> ProjectKnowledge | None:
    """Get a single knowledge entry by ID."""
    result = await db.execute(
        select(ProjectKnowledge).where(ProjectKnowledge.id == knowledge_id)
    )
    return result.scalar_one_or_none()


async def list_knowledge(
    db: AsyncSession,
    project_id: uuid.UUID,
    *,
    knowledge_type: KnowledgeType | None = None,
    tags: list[str] | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[ProjectKnowledge], int]:
    """List knowledge entries for a project with optional filters."""
    query = select(ProjectKnowledge).where(
        ProjectKnowledge.project_id == project_id
    )

    if knowledge_type:
        query = query.where(ProjectKnowledge.knowledge_type == knowledge_type)

    count_result = await db.execute(
        select(sa_func.count()).select_from(query.subquery())
    )
    total = count_result.scalar_one()

    result = await db.execute(
        query.order_by(ProjectKnowledge.relevance_score.desc())
        .offset(offset)
        .limit(limit)
    )
    return list(result.scalars().all()), total


async def extract_knowledge_from_run(
    db: AsyncSession,
    run_id: uuid.UUID,
) -> list[ProjectKnowledge]:
    """Extract knowledge from a completed run.

    Analyzes tasks, artifacts, and planner results to extract
    reusable knowledge entries.
    """
    # Get the run
    run_result = await db.execute(select(Run).where(Run.id == run_id))
    run = run_result.scalar_one_or_none()
    if run is None:
        return []

    project_id = run.project_id
    extracted: list[ProjectKnowledge] = []

    # Extract from completed tasks
    tasks_result = await db.execute(
        select(Task).where(Task.run_id == run_id)
    )
    tasks = list(tasks_result.scalars().all())

    for task in tasks:
        if task.status == TaskStatus.COMPLETED:
            entry = await create_knowledge(
                db,
                project_id=project_id,
                knowledge_type=KnowledgeType.PATTERN,
                title=f"Completed: {task.title}",
                content=f"Task '{task.title}' (type: {task.task_type}) completed successfully"
                        + (f". Agent: {task.assigned_agent_slug}" if task.assigned_agent_slug else ""),
                tags=[task.task_type],
                source_run_id=run_id,
                source_task_id=task.id,
            )
            extracted.append(entry)

        elif task.status == TaskStatus.FAILED:
            entry = await create_knowledge(
                db,
                project_id=project_id,
                knowledge_type=KnowledgeType.LESSON_LEARNED,
                title=f"Failed: {task.title}",
                content=f"Task '{task.title}' (type: {task.task_type}) failed"
                        + (f" after {task.retry_count} retries" if hasattr(task, 'retry_count') and task.retry_count else "")
                        + (f". Error: {task.error_message}" if hasattr(task, 'error_message') and task.error_message else ""),
                tags=[task.task_type, "failure"],
                source_run_id=run_id,
                source_task_id=task.id,
            )
            extracted.append(entry)

    # Extract from planner result
    planner_result = await db.execute(
        select(PlannerResult).where(PlannerResult.run_id == run_id)
    )
    plan = planner_result.scalar_one_or_none()
    if plan and plan.architecture_summary:
        entry = await create_knowledge(
            db,
            project_id=project_id,
            knowledge_type=KnowledgeType.ARCHITECTURE,
            title=f"Architecture from Run #{run.run_number}",
            content=plan.architecture_summary,
            tags=["architecture", "planner"],
            metadata={"recommended_stack": plan.recommended_stack} if plan.recommended_stack else None,
            source_run_id=run_id,
        )
        extracted.append(entry)

    if plan and plan.assumptions:
        entry = await create_knowledge(
            db,
            project_id=project_id,
            knowledge_type=KnowledgeType.CONSTRAINT,
            title=f"Assumptions from Run #{run.run_number}",
            content="\n".join(f"- {a}" for a in plan.assumptions),
            tags=["assumptions", "constraints"],
            source_run_id=run_id,
        )
        extracted.append(entry)

    logger.info("Extracted %d knowledge entries from run %s", len(extracted), run_id)
    return extracted


async def get_knowledge_context(
    db: AsyncSession,
    project_id: uuid.UUID,
    *,
    max_entries: int = 20,
) -> dict[str, Any]:
    """Assemble knowledge context for agent enrichment.

    Returns the most relevant knowledge entries as structured context
    that can be injected into agent prompts.
    """
    result = await db.execute(
        select(ProjectKnowledge)
        .where(ProjectKnowledge.project_id == project_id)
        .order_by(ProjectKnowledge.relevance_score.desc())
        .limit(max_entries)
    )
    entries = list(result.scalars().all())

    # Build context text
    context_parts = []
    for entry in entries:
        context_parts.append(
            f"[{entry.knowledge_type.value.upper()}] {entry.title}\n{entry.content}"
        )

    # Increment usage count for returned entries
    for entry in entries:
        entry.usage_count += 1

    return {
        "project_id": str(project_id),
        "total_entries": len(entries),
        "context_text": "\n\n---\n\n".join(context_parts) if context_parts else "(No knowledge available)",
        "entries": entries,
    }


async def delete_knowledge(
    db: AsyncSession,
    knowledge_id: uuid.UUID,
) -> bool:
    """Delete a knowledge entry."""
    entry = await get_knowledge(db, knowledge_id)
    if entry is None:
        return False
    await db.delete(entry)
    await db.flush()
    return True
