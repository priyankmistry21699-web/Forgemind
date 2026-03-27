"""Trust scoring service — heuristic-based trust and risk assessment.

FM-050: Evaluates trust scores for tasks, artifacts, and runs based on
configurable heuristic rules. Provides risk level classification.
"""

import uuid
import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task, TaskStatus
from app.models.run import Run, RunStatus
from app.models.artifact import Artifact
from app.models.trust_score import TrustScore, RiskLevel, EntityType

logger = logging.getLogger(__name__)


def _classify_risk(trust_score: float) -> RiskLevel:
    """Classify risk level from trust score."""
    if trust_score >= 0.8:
        return RiskLevel.LOW
    elif trust_score >= 0.5:
        return RiskLevel.MEDIUM
    elif trust_score >= 0.3:
        return RiskLevel.HIGH
    else:
        return RiskLevel.CRITICAL


async def assess_task(
    db: AsyncSession,
    task_id: uuid.UUID,
) -> TrustScore:
    """Compute and store trust score for a task.

    Heuristic factors:
    - Completion status: completed = high trust
    - Retry count: more retries = lower trust
    - Has agent assigned: yes = higher trust
    - Error messages: present = lower trust
    """
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if task is None:
        raise ValueError(f"Task {task_id} not found")

    factors: dict[str, Any] = {}
    score_components: list[float] = []

    # Factor 1: Status (weight: 0.4)
    status_scores = {
        TaskStatus.COMPLETED: 1.0,
        TaskStatus.RUNNING: 0.6,
        TaskStatus.READY: 0.5,
        TaskStatus.PENDING: 0.4,
        TaskStatus.BLOCKED: 0.3,
        TaskStatus.SKIPPED: 0.5,
        TaskStatus.FAILED: 0.1,
    }
    status_score = status_scores.get(task.status, 0.3)
    factors["status"] = {"value": task.status.value, "score": status_score, "weight": 0.4}
    score_components.append(status_score * 0.4)

    # Factor 2: Retry burden (weight: 0.25)
    if task.max_retries > 0:
        retry_ratio = task.retry_count / task.max_retries
        retry_score = max(0.0, 1.0 - retry_ratio)
    else:
        retry_score = 1.0 if task.retry_count == 0 else 0.3
    factors["retries"] = {
        "count": task.retry_count,
        "max": task.max_retries,
        "score": retry_score,
        "weight": 0.25,
    }
    score_components.append(retry_score * 0.25)

    # Factor 3: Agent assignment (weight: 0.15)
    agent_score = 0.8 if task.assigned_agent_slug else 0.4
    factors["agent_assigned"] = {
        "slug": task.assigned_agent_slug,
        "score": agent_score,
        "weight": 0.15,
    }
    score_components.append(agent_score * 0.15)

    # Factor 4: Error presence (weight: 0.2)
    error_score = 0.2 if task.error_message else 1.0
    factors["error"] = {
        "has_error": bool(task.error_message),
        "score": error_score,
        "weight": 0.2,
    }
    score_components.append(error_score * 0.2)

    trust = round(sum(score_components), 3)
    confidence = 0.7 if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED) else 0.5

    # Upsert trust score
    existing = await db.execute(
        select(TrustScore).where(
            TrustScore.entity_type == EntityType.TASK,
            TrustScore.entity_id == task_id,
        )
    )
    ts = existing.scalar_one_or_none()
    if ts:
        ts.trust_score = trust
        ts.confidence = confidence
        ts.risk_level = _classify_risk(trust)
        ts.factors = factors
    else:
        ts = TrustScore(
            entity_type=EntityType.TASK,
            entity_id=task_id,
            trust_score=trust,
            confidence=confidence,
            risk_level=_classify_risk(trust),
            factors=factors,
            project_id=None,
            run_id=task.run_id,
        )
        db.add(ts)

    await db.flush()
    return ts


async def assess_run(
    db: AsyncSession,
    run_id: uuid.UUID,
) -> TrustScore:
    """Compute and store trust score for a run.

    Heuristic factors:
    - Task completion ratio
    - Failed task proportion
    - Overall run status
    """
    run_result = await db.execute(select(Run).where(Run.id == run_id))
    run = run_result.scalar_one_or_none()
    if run is None:
        raise ValueError(f"Run {run_id} not found")

    task_result = await db.execute(select(Task).where(Task.run_id == run_id))
    tasks = list(task_result.scalars().all())

    factors: dict[str, Any] = {}
    score_components: list[float] = []

    total = len(tasks)

    # Factor 1: Run status (weight: 0.3)
    run_status_scores = {
        RunStatus.COMPLETED: 1.0,
        RunStatus.RUNNING: 0.6,
        RunStatus.PLANNING: 0.5,
        RunStatus.PENDING: 0.4,
        RunStatus.PAUSED: 0.4,
        RunStatus.FAILED: 0.1,
    }
    run_score = run_status_scores.get(run.status, 0.3)
    factors["run_status"] = {"value": run.status.value, "score": run_score, "weight": 0.3}
    score_components.append(run_score * 0.3)

    # Factor 2: Task completion ratio (weight: 0.4)
    if total > 0:
        completed = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED)
        completion_ratio = completed / total
    else:
        completion_ratio = 0.5  # No tasks yet
    factors["completion_ratio"] = {
        "completed": sum(1 for t in tasks if t.status == TaskStatus.COMPLETED),
        "total": total,
        "score": completion_ratio,
        "weight": 0.4,
    }
    score_components.append(completion_ratio * 0.4)

    # Factor 3: Failure proportion (weight: 0.3)
    if total > 0:
        failed = sum(1 for t in tasks if t.status == TaskStatus.FAILED)
        failure_score = max(0.0, 1.0 - (failed / total) * 2)
    else:
        failure_score = 0.5
    factors["failure_rate"] = {
        "failed": sum(1 for t in tasks if t.status == TaskStatus.FAILED),
        "total": total,
        "score": round(failure_score, 3),
        "weight": 0.3,
    }
    score_components.append(failure_score * 0.3)

    trust = round(sum(score_components), 3)
    confidence = 0.8 if run.status in (RunStatus.COMPLETED, RunStatus.FAILED) else 0.5

    # Upsert
    existing = await db.execute(
        select(TrustScore).where(
            TrustScore.entity_type == EntityType.RUN,
            TrustScore.entity_id == run_id,
        )
    )
    ts = existing.scalar_one_or_none()
    if ts:
        ts.trust_score = trust
        ts.confidence = confidence
        ts.risk_level = _classify_risk(trust)
        ts.factors = factors
    else:
        ts = TrustScore(
            entity_type=EntityType.RUN,
            entity_id=run_id,
            trust_score=trust,
            confidence=confidence,
            risk_level=_classify_risk(trust),
            factors=factors,
            project_id=run.project_id,
            run_id=run.id,
        )
        db.add(ts)

    await db.flush()
    return ts


async def get_trust_score(
    db: AsyncSession,
    entity_type: EntityType,
    entity_id: uuid.UUID,
) -> TrustScore | None:
    """Get the most recent trust score for an entity."""
    result = await db.execute(
        select(TrustScore).where(
            TrustScore.entity_type == entity_type,
            TrustScore.entity_id == entity_id,
        )
    )
    return result.scalar_one_or_none()


async def list_trust_scores(
    db: AsyncSession,
    *,
    project_id: uuid.UUID | None = None,
    run_id: uuid.UUID | None = None,
    risk_level: RiskLevel | None = None,
    entity_type: EntityType | None = None,
) -> list[TrustScore]:
    """List trust scores with optional filters."""
    query = select(TrustScore)

    if project_id:
        query = query.where(TrustScore.project_id == project_id)
    if run_id:
        query = query.where(TrustScore.run_id == run_id)
    if risk_level:
        query = query.where(TrustScore.risk_level == risk_level)
    if entity_type:
        query = query.where(TrustScore.entity_type == entity_type)

    query = query.order_by(TrustScore.trust_score.asc())  # Lowest trust first
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_run_risk_summary(
    db: AsyncSession,
    run_id: uuid.UUID,
) -> dict[str, Any]:
    """Get risk summary for a run including all task trust scores."""
    run_score = await assess_run(db, run_id)

    # Get all task scores for this run
    task_result = await db.execute(select(Task).where(Task.run_id == run_id))
    tasks = list(task_result.scalars().all())

    task_scores = []
    for task in tasks:
        ts = await assess_task(db, task.id)
        task_scores.append({
            "task_id": str(task.id),
            "title": task.title,
            "trust_score": ts.trust_score,
            "risk_level": ts.risk_level.value,
            "confidence": ts.confidence,
        })

    # Sort by trust (lowest first = highest risk first)
    task_scores.sort(key=lambda x: x["trust_score"])

    risk_distribution: dict[str, int] = {}
    for ts in task_scores:
        risk_distribution[ts["risk_level"]] = risk_distribution.get(ts["risk_level"], 0) + 1

    return {
        "run_id": str(run_id),
        "run_trust_score": run_score.trust_score,
        "run_risk_level": run_score.risk_level.value,
        "run_confidence": run_score.confidence,
        "task_risk_distribution": risk_distribution,
        "task_scores": task_scores,
    }
