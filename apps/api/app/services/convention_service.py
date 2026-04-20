"""Convention service — organizational conventions engine.

FM-167: CRUD for conventions, retrieval for agent prompt injection,
and compliance checking against run outputs.
"""

import uuid
import logging

from sqlalchemy import select, func as sa_func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.search_knowledge import (
    Convention,
    ConventionCategory,
    ConventionEnforcement,
)
from app.models.task import Task
from app.models.artifact import Artifact
from app.models.run import Run

logger = logging.getLogger(__name__)


async def create_convention(
    db: AsyncSession,
    *,
    project_id: uuid.UUID | None = None,
    category: ConventionCategory,
    name: str,
    description: str | None = None,
    rule_text: str,
    enforcement_level: ConventionEnforcement = ConventionEnforcement.ADVISORY,
    author_id: uuid.UUID | None = None,
) -> Convention:
    """Create a new convention."""
    conv = Convention(
        project_id=project_id,
        category=category,
        name=name,
        description=description,
        rule_text=rule_text,
        enforcement_level=enforcement_level,
        active=True,
        author_id=author_id,
    )
    db.add(conv)
    await db.flush()
    return conv


async def get_convention(
    db: AsyncSession, convention_id: uuid.UUID
) -> Convention | None:
    result = await db.execute(select(Convention).where(Convention.id == convention_id))
    return result.scalar_one_or_none()


async def list_conventions(
    db: AsyncSession,
    *,
    project_id: uuid.UUID | None = None,
    category: ConventionCategory | None = None,
    active_only: bool = True,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[Convention], int]:
    """List conventions, optionally filtered by project and category."""
    filters = []
    if project_id is not None:
        filters.append(Convention.project_id == project_id)
    if category is not None:
        filters.append(Convention.category == category)
    if active_only:
        filters.append(Convention.active.is_(True))

    where = and_(*filters) if filters else True

    count_q = select(sa_func.count()).select_from(
        select(Convention.id).where(where).subquery()
    )
    total = (await db.execute(count_q)).scalar_one()

    result = await db.execute(
        select(Convention)
        .where(where)
        .order_by(Convention.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return list(result.scalars().all()), total


async def update_convention(
    db: AsyncSession,
    convention_id: uuid.UUID,
    **kwargs,
) -> Convention | None:
    """Update a convention's fields."""
    conv = await get_convention(db, convention_id)
    if not conv:
        return None
    for key, value in kwargs.items():
        if value is not None and hasattr(conv, key):
            setattr(conv, key, value)
    await db.flush()
    return conv


async def delete_convention(db: AsyncSession, convention_id: uuid.UUID) -> bool:
    conv = await get_convention(db, convention_id)
    if not conv:
        return False
    await db.delete(conv)
    await db.flush()
    return True


async def get_active_conventions_for_injection(
    db: AsyncSession,
    project_id: uuid.UUID,
) -> list[dict]:
    """Get active conventions formatted for agent prompt injection.

    Returns a list of dicts with category, name, rule_text, enforcement_level.
    """
    result = await db.execute(
        select(Convention)
        .where(
            Convention.project_id == project_id,
            Convention.active.is_(True),
        )
        .order_by(Convention.category, Convention.name)
    )
    conventions = list(result.scalars().all())

    return [
        {
            "category": c.category.value,
            "name": c.name,
            "rule_text": c.rule_text,
            "enforcement_level": c.enforcement_level.value,
        }
        for c in conventions
    ]


async def check_conventions_compliance(
    db: AsyncSession,
    run_id: uuid.UUID,
) -> dict:
    """Check a run's outputs against active conventions.

    Evaluates task outputs and artifact content against convention rules.
    Returns a compliance report with violations.
    """
    # Get run and project
    run_result = await db.execute(select(Run).where(Run.id == run_id))
    run = run_result.scalar_one_or_none()
    if not run:
        return {
            "run_id": str(run_id),
            "checked_count": 0,
            "violations": [],
            "passed": True,
        }

    # Get active conventions for this project
    convs_result = await db.execute(
        select(Convention).where(
            Convention.project_id == run.project_id,
            Convention.active.is_(True),
        )
    )
    conventions = list(convs_result.scalars().all())

    if not conventions:
        return {
            "run_id": str(run_id),
            "checked_count": 0,
            "violations": [],
            "passed": True,
        }

    # Get run artifacts content for checking
    arts_result = await db.execute(select(Artifact).where(Artifact.run_id == run_id))
    artifacts = list(arts_result.scalars().all())

    # Get tasks for checking
    tasks_result = await db.execute(select(Task).where(Task.run_id == run_id))
    tasks = list(tasks_result.scalars().all())

    # Build a text corpus from this run
    corpus_parts = []
    for art in artifacts:
        if art.content:
            corpus_parts.append(art.content)
    for task in tasks:
        if task.title:
            corpus_parts.append(task.title)
        if task.description:
            corpus_parts.append(task.description)

    corpus = "\n".join(corpus_parts).lower()
    violations = []

    for conv in conventions:
        # Simple rule-text-based compliance check:
        # Check if the rule text mentions patterns that should/shouldn't appear
        rule_lower = conv.rule_text.lower()

        # Convention rules often contain "must"/"should"/"avoid"/"never" directives
        # We do a basic keyword-in-corpus check for "avoid X" / "never use X" patterns
        violated = False
        detail = ""

        if "avoid" in rule_lower or "never" in rule_lower or "prohibit" in rule_lower:
            # Extract the prohibited terms (words after avoid/never/prohibit)
            for marker in ["avoid ", "never use ", "never ", "prohibit "]:
                if marker in rule_lower:
                    rest = rule_lower.split(marker, 1)[1].split(".")[0].strip()
                    # Check if the prohibited term appears in the corpus
                    prohibited_terms = [t.strip() for t in rest.split(",")]
                    for term in prohibited_terms:
                        if term and len(term) > 2 and term in corpus:
                            violated = True
                            detail = f"Prohibited term '{term}' found in run outputs"
                            break

        if "must include" in rule_lower or "require" in rule_lower:
            for marker in ["must include ", "require "]:
                if marker in rule_lower:
                    rest = rule_lower.split(marker, 1)[1].split(".")[0].strip()
                    required_terms = [t.strip() for t in rest.split(",")]
                    for term in required_terms:
                        if term and len(term) > 2 and term not in corpus:
                            violated = True
                            detail = f"Required term '{term}' not found in run outputs"
                            break

        if violated:
            violations.append(
                {
                    "convention_id": str(conv.id),
                    "convention_name": conv.name,
                    "enforcement_level": conv.enforcement_level.value,
                    "rule_text": conv.rule_text,
                    "violation_detail": detail,
                }
            )

    has_required_violations = any(
        v["enforcement_level"] == ConventionEnforcement.REQUIRED.value
        for v in violations
    )

    return {
        "run_id": str(run_id),
        "checked_count": len(conventions),
        "violations": violations,
        "passed": not has_required_violations,
    }
