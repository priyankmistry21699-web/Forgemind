"""Retention policy service — data lifecycle management.

FM-176: Configurable retention rules for archiving/deleting old data.
"""

import logging
import uuid
from datetime import datetime, timezone, timedelta

from sqlalchemy import select, func as sa_func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enterprise_governance import RetentionPolicy, RetentionAction
from app.models.run import Run
from app.models.enterprise_governance import AuditLog

logger = logging.getLogger(__name__)

# Entity types that support retention
SUPPORTED_ENTITY_TYPES = {"run", "audit_log", "artifact", "notification", "activity"}


async def create_retention_policy(
    db: AsyncSession,
    *,
    workspace_id: uuid.UUID,
    entity_type: str,
    retention_days: int,
    action: RetentionAction = RetentionAction.ARCHIVE,
    is_active: bool = True,
    legal_hold: bool = False,
    project_id: uuid.UUID | None = None,
    created_by: uuid.UUID,
) -> RetentionPolicy:
    """Create a new retention policy."""
    if entity_type not in SUPPORTED_ENTITY_TYPES:
        raise ValueError(
            f"Unsupported entity type: {entity_type}. "
            f"Supported: {', '.join(sorted(SUPPORTED_ENTITY_TYPES))}"
        )

    policy = RetentionPolicy(
        workspace_id=workspace_id,
        entity_type=entity_type,
        retention_days=retention_days,
        action=action,
        is_active=is_active,
        legal_hold=legal_hold,
        project_id=project_id,
        created_by=created_by,
    )
    db.add(policy)
    await db.flush()

    logger.info(
        "retention: created policy entity_type=%s days=%d action=%s",
        entity_type,
        retention_days,
        action.value,
    )
    return policy


async def list_retention_policies(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    *,
    entity_type: str | None = None,
    offset: int = 0,
    limit: int = 50,
) -> tuple[list[RetentionPolicy], int]:
    """List retention policies for a workspace."""
    conditions = [RetentionPolicy.workspace_id == workspace_id]
    if entity_type:
        conditions.append(RetentionPolicy.entity_type == entity_type)

    where_clause = and_(*conditions)

    count_q = (
        select(sa_func.count())
        .select_from(RetentionPolicy)
        .where(where_clause)
    )
    total = (await db.execute(count_q)).scalar() or 0

    items_q = (
        select(RetentionPolicy)
        .where(where_clause)
        .order_by(RetentionPolicy.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    rows = (await db.execute(items_q)).scalars().all()

    return list(rows), total


async def update_retention_policy(
    db: AsyncSession,
    policy_id: uuid.UUID,
    *,
    retention_days: int | None = None,
    action: RetentionAction | None = None,
    is_active: bool | None = None,
    legal_hold: bool | None = None,
) -> RetentionPolicy | None:
    """Update a retention policy."""
    policy = await db.get(RetentionPolicy, policy_id)
    if policy is None:
        return None

    if retention_days is not None:
        policy.retention_days = retention_days
    if action is not None:
        policy.action = action
    if is_active is not None:
        policy.is_active = is_active
    if legal_hold is not None:
        policy.legal_hold = legal_hold

    await db.flush()
    return policy


async def delete_retention_policy(
    db: AsyncSession,
    policy_id: uuid.UUID,
) -> bool:
    """Delete a retention policy. Returns True if deleted."""
    policy = await db.get(RetentionPolicy, policy_id)
    if policy is None:
        return False
    await db.delete(policy)
    await db.flush()
    return True


async def evaluate_retention(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    *,
    dry_run: bool = True,
) -> dict:
    """Evaluate retention policies and identify entities to archive/delete.

    Args:
        dry_run: If True, only report what would be affected. If False,
                 actually mark entities (not implemented in this pass).

    Returns summary of entities affected per policy.
    """
    policies_q = select(RetentionPolicy).where(
        RetentionPolicy.workspace_id == workspace_id,
        RetentionPolicy.is_active == True,  # noqa: E712
        RetentionPolicy.legal_hold == False,  # noqa: E712
    )
    policies = (await db.execute(policies_q)).scalars().all()

    results = []
    now = datetime.now(timezone.utc)

    for policy in policies:
        cutoff = now - timedelta(days=policy.retention_days)
        affected_count = 0

        if policy.entity_type == "run":
            conditions = [Run.created_at < cutoff]
            if policy.project_id:
                conditions.append(Run.project_id == policy.project_id)
            else:
                from app.models.project import Project

                ws_projects = select(Project.id).where(
                    Project.workspace_id == workspace_id
                )
                conditions.append(Run.project_id.in_(ws_projects))

            count_q = (
                select(sa_func.count())
                .select_from(Run)
                .where(and_(*conditions))
            )
            affected_count = (await db.execute(count_q)).scalar() or 0

        elif policy.entity_type == "audit_log":
            conditions = [
                AuditLog.workspace_id == workspace_id,
                AuditLog.created_at < cutoff,
            ]
            count_q = (
                select(sa_func.count())
                .select_from(AuditLog)
                .where(and_(*conditions))
            )
            affected_count = (await db.execute(count_q)).scalar() or 0

        results.append({
            "policy_id": str(policy.id),
            "entity_type": policy.entity_type,
            "retention_days": policy.retention_days,
            "action": policy.action.value,
            "cutoff_date": cutoff.isoformat(),
            "affected_count": affected_count,
            "dry_run": dry_run,
        })

    return {
        "workspace_id": str(workspace_id),
        "evaluated_at": now.isoformat(),
        "policies_evaluated": len(policies),
        "results": results,
        "total_affected": sum(r["affected_count"] for r in results),
    }
