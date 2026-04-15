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
from app.models.enterprise_governance import AuditLog, AuditActorType, AuditOutcome
from app.models.artifact import Artifact
from app.models.notification import Notification

logger = logging.getLogger(__name__)

# Entity types that have full retention evaluation + delete logic.
SUPPORTED_ENTITY_TYPES = {"run", "audit_log", "artifact", "notification"}


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


async def _count_entities(db: AsyncSession, model, conditions):
    """Count entities matching conditions."""
    count_q = select(sa_func.count()).select_from(model).where(and_(*conditions))
    return (await db.execute(count_q)).scalar() or 0


async def _delete_entities(db: AsyncSession, model, conditions, entity_type, workspace_id, cutoff):
    """Delete entities and log the action."""
    from sqlalchemy import delete as sa_delete

    del_q = sa_delete(model).where(and_(*conditions))
    del_result = await db.execute(del_q)
    deleted_count = del_result.rowcount
    logger.info(
        "retention: EXECUTED delete for %s workspace=%s cutoff=%s deleted=%d",
        entity_type, workspace_id, cutoff.isoformat(), deleted_count,
    )
    return deleted_count


async def _archive_entities(
    db: AsyncSession, workspace_id, policy, affected_count, cutoff
):
    """Mark entities as archived and record an audit trail (FM-176).

    Sets archived_at on matching entities so they are excluded from normal
    queries, then creates an immutable audit log entry for compliance.
    """
    # Actually stamp archived_at on supported entity types
    now = datetime.now(timezone.utc)
    model_cls, conditions = await _build_conditions(
        db, policy.entity_type, policy, workspace_id, cutoff,
    )

    if hasattr(model_cls, "archived_at"):
        from sqlalchemy import update
        conditions.append(model_cls.archived_at.is_(None))
        stmt = (
            update(model_cls)
            .where(and_(*conditions))
            .values(archived_at=now)
        )
        result = await db.execute(stmt)
        affected_count = result.rowcount

    entry = AuditLog(
        actor_type=AuditActorType.SYSTEM,
        action="retention.archive",
        resource_type=policy.entity_type,
        workspace_id=workspace_id,
        project_id=policy.project_id,
        details={
            "policy_id": str(policy.id),
            "retention_days": policy.retention_days,
            "cutoff_date": cutoff.isoformat(),
            "affected_count": affected_count,
            "action": "archive",
        },
        outcome=AuditOutcome.SUCCESS,
    )
    db.add(entry)
    await db.flush()
    logger.info(
        "retention: ARCHIVED %s workspace=%s cutoff=%s count=%d",
        policy.entity_type, workspace_id, cutoff.isoformat(), affected_count,
    )
    return affected_count


async def _build_conditions(db, entity_type, policy, workspace_id, cutoff):
    """Build query conditions for a given entity type."""
    if entity_type == "run":
        conditions = [Run.created_at < cutoff]
        if policy.project_id:
            conditions.append(Run.project_id == policy.project_id)
        else:
            from app.models.project import Project
            ws_projects = select(Project.id).where(Project.workspace_id == workspace_id)
            conditions.append(Run.project_id.in_(ws_projects))
        return Run, conditions

    elif entity_type == "audit_log":
        conditions = [
            AuditLog.workspace_id == workspace_id,
            AuditLog.created_at < cutoff,
        ]
        return AuditLog, conditions

    elif entity_type == "artifact":
        from app.models.project import Project
        conditions = [Artifact.created_at < cutoff]
        if policy.project_id:
            conditions.append(Artifact.project_id == policy.project_id)
        else:
            ws_projects = select(Project.id).where(Project.workspace_id == workspace_id)
            conditions.append(Artifact.project_id.in_(ws_projects))
        return Artifact, conditions

    elif entity_type == "notification":
        from app.models.membership import WorkspaceMember
        ws_users = select(WorkspaceMember.user_id).where(
            WorkspaceMember.workspace_id == workspace_id
        )
        conditions = [
            Notification.user_id.in_(ws_users),
            Notification.created_at < cutoff,
        ]
        return Notification, conditions

    return None, []


async def evaluate_retention(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    *,
    dry_run: bool = True,
) -> dict:
    """Evaluate retention policies and identify entities to archive/delete.

    Args:
        dry_run: If True, only report what would be affected. If False,
                 actually delete/archive matching entities.

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
        deleted_count = 0
        archived_count = 0

        model, conditions = await _build_conditions(
            db, policy.entity_type, policy, workspace_id, cutoff
        )

        if model is not None and conditions:
            affected_count = await _count_entities(db, model, conditions)

            if not dry_run and affected_count > 0:
                if policy.action == RetentionAction.DELETE:
                    deleted_count = await _delete_entities(
                        db, model, conditions,
                        policy.entity_type, workspace_id, cutoff,
                    )
                elif policy.action == RetentionAction.ARCHIVE:
                    archived_count = await _archive_entities(
                        db, workspace_id, policy, affected_count, cutoff,
                    )

        results.append({
            "policy_id": str(policy.id),
            "entity_type": policy.entity_type,
            "retention_days": policy.retention_days,
            "action": policy.action.value,
            "cutoff_date": cutoff.isoformat(),
            "affected_count": affected_count,
            "deleted_count": deleted_count,
            "archived_count": archived_count,
            "dry_run": dry_run,
        })

    return {
        "workspace_id": str(workspace_id),
        "evaluated_at": now.isoformat(),
        "policies_evaluated": len(policies),
        "results": results,
        "total_affected": sum(r["affected_count"] for r in results),
        "total_deleted": sum(r["deleted_count"] for r in results),
        "total_archived": sum(r["archived_count"] for r in results),
        "dry_run": dry_run,
    }
