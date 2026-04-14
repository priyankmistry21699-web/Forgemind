"""Recommendation service — smart action recommendations.

FM-169: Analyzes project state and generates actionable recommendations.

Implements 7 recommendation rules:
1. knowledge_gap — project has runs but no knowledge entries
2. stale_run — runs stuck in non-terminal status for too long
3. convention_violation — conventions exist but haven't been checked
4. missing_approval — pending approvals that are aging
5. reusable_pattern — knowledge entries from other projects that may be relevant
6. tech_debt — failed tasks that may indicate technical debt
7. similar_project — other projects working on related topics
"""

import uuid
import logging

from sqlalchemy import select, func as sa_func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.search_knowledge import Recommendation, RecommendationType
from app.models.project import Project
from app.models.run import Run, RunStatus
from app.models.task import Task, TaskStatus
from app.models.project_knowledge import ProjectKnowledge
from app.models.approval_request import ApprovalRequest, ApprovalStatus
from app.models.search_knowledge import Convention

logger = logging.getLogger(__name__)


async def generate_recommendations(
    db: AsyncSession,
    project_id: uuid.UUID,
) -> list[Recommendation]:
    """Analyze project state and generate new recommendations.

    Only generates recommendations that don't already exist (undismissed).
    """
    generated: list[Recommendation] = []

    # Get existing undismissed recommendations to avoid duplicates
    existing_result = await db.execute(
        select(Recommendation).where(
            Recommendation.project_id == project_id,
            Recommendation.dismissed.is_(False),
        )
    )
    existing_types = {r.rec_type for r in existing_result.scalars().all()}

    # Rule 1: Knowledge gap
    if RecommendationType.KNOWLEDGE_GAP not in existing_types:
        rec = await _check_knowledge_gap(db, project_id)
        if rec:
            generated.append(rec)

    # Rule 2: Stale runs
    if RecommendationType.STALE_RUN not in existing_types:
        rec = await _check_stale_runs(db, project_id)
        if rec:
            generated.append(rec)

    # Rule 3: Convention violations
    if RecommendationType.CONVENTION_VIOLATION not in existing_types:
        rec = await _check_convention_gaps(db, project_id)
        if rec:
            generated.append(rec)

    # Rule 4: Missing approvals
    if RecommendationType.MISSING_APPROVAL not in existing_types:
        rec = await _check_pending_approvals(db, project_id)
        if rec:
            generated.append(rec)

    # Rule 5: Reusable patterns
    if RecommendationType.REUSABLE_PATTERN not in existing_types:
        rec = await _check_reusable_patterns(db, project_id)
        if rec:
            generated.append(rec)

    # Rule 6: Tech debt indicators
    if RecommendationType.TECH_DEBT not in existing_types:
        rec = await _check_tech_debt(db, project_id)
        if rec:
            generated.append(rec)

    # Rule 7: Similar projects
    if RecommendationType.SIMILAR_PROJECT not in existing_types:
        rec = await _check_similar_projects(db, project_id)
        if rec:
            generated.append(rec)

    return generated


async def list_recommendations(
    db: AsyncSession,
    project_id: uuid.UUID,
    *,
    include_dismissed: bool = False,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[Recommendation], int]:
    """List recommendations for a project."""
    filters = [Recommendation.project_id == project_id]
    if not include_dismissed:
        filters.append(Recommendation.dismissed.is_(False))

    where = and_(*filters)

    count_q = select(sa_func.count()).select_from(
        select(Recommendation.id).where(where).subquery()
    )
    total = (await db.execute(count_q)).scalar_one()

    result = await db.execute(
        select(Recommendation)
        .where(where)
        .order_by(Recommendation.priority.asc(), Recommendation.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return list(result.scalars().all()), total


async def dismiss_recommendation(
    db: AsyncSession,
    recommendation_id: uuid.UUID,
    feedback: str | None = None,
) -> Recommendation | None:
    """Dismiss a recommendation with optional feedback."""
    result = await db.execute(
        select(Recommendation).where(Recommendation.id == recommendation_id)
    )
    rec = result.scalar_one_or_none()
    if not rec:
        return None
    rec.dismissed = True
    rec.feedback = feedback
    await db.flush()
    return rec


# ── Rule Implementations ─────────────────────────────────────────


async def _check_knowledge_gap(
    db: AsyncSession, project_id: uuid.UUID
) -> Recommendation | None:
    """Rule 1: Project has completed runs but no knowledge entries."""
    runs_count = (
        await db.execute(
            select(sa_func.count()).select_from(
                select(Run.id)
                .where(Run.project_id == project_id, Run.status == RunStatus.COMPLETED)
                .subquery()
            )
        )
    ).scalar_one()

    if runs_count == 0:
        return None

    knowledge_count = (
        await db.execute(
            select(sa_func.count()).select_from(
                select(ProjectKnowledge.id)
                .where(ProjectKnowledge.project_id == project_id)
                .subquery()
            )
        )
    ).scalar_one()

    if knowledge_count > 0:
        return None

    rec = Recommendation(
        project_id=project_id,
        rec_type=RecommendationType.KNOWLEDGE_GAP,
        title="No knowledge entries extracted",
        body=f"This project has {runs_count} completed run(s) but no knowledge entries. "
        "Consider extracting knowledge from completed runs to build organizational memory.",
        priority=3,
    )
    db.add(rec)
    await db.flush()
    return rec


async def _check_stale_runs(
    db: AsyncSession, project_id: uuid.UUID
) -> Recommendation | None:
    """Rule 2: Runs stuck in non-terminal status."""
    stale_statuses = [RunStatus.RUNNING, RunStatus.PAUSED, RunStatus.PENDING]
    result = await db.execute(
        select(Run).where(
            Run.project_id == project_id,
            Run.status.in_(stale_statuses),
        )
    )
    stale_runs = list(result.scalars().all())

    if not stale_runs:
        return None

    rec = Recommendation(
        project_id=project_id,
        rec_type=RecommendationType.STALE_RUN,
        title=f"{len(stale_runs)} run(s) may need attention",
        body=f"Found {len(stale_runs)} run(s) in non-terminal status "
        f"({', '.join(r.status.value for r in stale_runs[:3])}). "
        "Review and either resume or mark as failed.",
        entity_type="run",
        entity_id=stale_runs[0].id,
        priority=2,
    )
    db.add(rec)
    await db.flush()
    return rec


async def _check_convention_gaps(
    db: AsyncSession, project_id: uuid.UUID
) -> Recommendation | None:
    """Rule 3: Conventions exist but haven't been checked recently."""
    conv_count = (
        await db.execute(
            select(sa_func.count()).select_from(
                select(Convention.id)
                .where(Convention.project_id == project_id, Convention.active.is_(True))
                .subquery()
            )
        )
    ).scalar_one()

    if conv_count == 0:
        return None

    # Check if there are any completed runs (proxy for "should check conventions")
    runs_count = (
        await db.execute(
            select(sa_func.count()).select_from(
                select(Run.id)
                .where(Run.project_id == project_id, Run.status == RunStatus.COMPLETED)
                .subquery()
            )
        )
    ).scalar_one()

    if runs_count == 0:
        return None

    rec = Recommendation(
        project_id=project_id,
        rec_type=RecommendationType.CONVENTION_VIOLATION,
        title="Convention compliance check recommended",
        body=f"This project has {conv_count} active convention(s) and {runs_count} completed run(s). "
        "Run a compliance check to ensure outputs follow organizational conventions.",
        priority=4,
    )
    db.add(rec)
    await db.flush()
    return rec


async def _check_pending_approvals(
    db: AsyncSession, project_id: uuid.UUID
) -> Recommendation | None:
    """Rule 4: Pending approvals that may be blocking work."""
    result = await db.execute(
        select(sa_func.count()).select_from(
            select(ApprovalRequest.id)
            .where(
                ApprovalRequest.project_id == project_id,
                ApprovalRequest.status == ApprovalStatus.PENDING,
            )
            .subquery()
        )
    )
    pending = result.scalar_one()

    if pending == 0:
        return None

    rec = Recommendation(
        project_id=project_id,
        rec_type=RecommendationType.MISSING_APPROVAL,
        title=f"{pending} pending approval(s) may be blocking progress",
        body=f"There are {pending} approval request(s) waiting for review. "
        "Unresolved approvals can block execution and slow down delivery.",
        priority=2,
    )
    db.add(rec)
    await db.flush()
    return rec


async def _check_reusable_patterns(
    db: AsyncSession, project_id: uuid.UUID
) -> Recommendation | None:
    """Rule 5: Knowledge from other projects that may be relevant."""
    # Get this project's task types
    task_types_result = await db.execute(
        select(Task.task_type).where(
            Task.run_id.in_(
                select(Run.id).where(Run.project_id == project_id)
            )
        ).distinct()
    )
    task_types = [r[0] for r in task_types_result.all() if r[0]]

    if not task_types:
        return None

    # Look for knowledge in OTHER projects with matching tags
    other_knowledge = await db.execute(
        select(sa_func.count()).select_from(
            select(ProjectKnowledge.id)
            .where(ProjectKnowledge.project_id != project_id)
            .subquery()
        )
    )
    other_count = other_knowledge.scalar_one()

    if other_count == 0:
        return None

    rec = Recommendation(
        project_id=project_id,
        rec_type=RecommendationType.REUSABLE_PATTERN,
        title="Reusable patterns available from other projects",
        body=f"Found {other_count} knowledge entries from other projects. "
        "Search cross-project knowledge to discover patterns and lessons that may apply here.",
        priority=5,
    )
    db.add(rec)
    await db.flush()
    return rec


async def _check_tech_debt(
    db: AsyncSession, project_id: uuid.UUID
) -> Recommendation | None:
    """Rule 6: Failed tasks that indicate potential tech debt."""
    failed = (
        await db.execute(
            select(sa_func.count()).select_from(
                select(Task.id)
                .where(
                    Task.run_id.in_(
                        select(Run.id).where(Run.project_id == project_id)
                    ),
                    Task.status == TaskStatus.FAILED,
                )
                .subquery()
            )
        )
    ).scalar_one()

    if failed < 2:
        return None

    rec = Recommendation(
        project_id=project_id,
        rec_type=RecommendationType.TECH_DEBT,
        title=f"{failed} failed tasks may indicate technical debt",
        body=f"This project has {failed} failed task(s) across its runs. "
        "Patterns of failure often indicate underlying technical debt. "
        "Consider extracting lessons learned and addressing root causes.",
        priority=3,
    )
    db.add(rec)
    await db.flush()
    return rec


async def _check_similar_projects(
    db: AsyncSession, project_id: uuid.UUID
) -> Recommendation | None:
    """Rule 7: Other projects with similar descriptions."""
    proj_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = proj_result.scalar_one_or_none()
    if not project or not project.description:
        return None

    # Simple keyword match — find other projects with overlapping words
    desc_words = set(project.description.lower().split())
    stopwords = {"the", "a", "an", "is", "are", "and", "or", "to", "for", "of", "in", "with"}
    keywords = [w for w in desc_words if len(w) > 3 and w not in stopwords]

    if not keywords:
        return None

    # Check for other projects
    other_result = await db.execute(
        select(sa_func.count()).select_from(
            select(Project.id)
            .where(Project.id != project_id)
            .subquery()
        )
    )
    others = other_result.scalar_one()

    if others == 0:
        return None

    rec = Recommendation(
        project_id=project_id,
        rec_type=RecommendationType.SIMILAR_PROJECT,
        title="Related projects may have useful context",
        body=f"There are {others} other project(s) in the platform. "
        "Use cross-project search to find related work, patterns, and decisions that may be applicable.",
        priority=6,
    )
    db.add(rec)
    await db.flush()
    return rec
