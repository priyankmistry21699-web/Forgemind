"""Audit log service — immutable, append-only audit trail.

FM-173: Records all state-changing actions for compliance and traceability.
Entries cannot be updated or deleted via the API.
"""

import csv
import io
import logging
import uuid
from datetime import datetime

from sqlalchemy import select, func as sa_func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enterprise_governance import AuditLog, AuditActorType, AuditOutcome

logger = logging.getLogger(__name__)


async def log_event(
    db: AsyncSession,
    *,
    actor_id: uuid.UUID | None,
    actor_type: AuditActorType = AuditActorType.USER,
    action: str,
    resource_type: str,
    resource_id: uuid.UUID | None = None,
    workspace_id: uuid.UUID | None = None,
    project_id: uuid.UUID | None = None,
    details: dict | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    outcome: AuditOutcome = AuditOutcome.SUCCESS,
) -> AuditLog:
    """Create an immutable audit log entry."""
    entry = AuditLog(
        actor_id=actor_id,
        actor_type=actor_type,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        workspace_id=workspace_id,
        project_id=project_id,
        details=details,
        ip_address=ip_address,
        user_agent=user_agent,
        outcome=outcome,
    )
    db.add(entry)
    await db.flush()
    logger.info(
        "audit: action=%s resource=%s/%s outcome=%s actor=%s",
        action,
        resource_type,
        resource_id,
        outcome.value,
        actor_id,
    )
    return entry


async def list_audit_logs(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    *,
    action: str | None = None,
    resource_type: str | None = None,
    resource_id: uuid.UUID | None = None,
    actor_id: uuid.UUID | None = None,
    outcome: AuditOutcome | None = None,
    project_id: uuid.UUID | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    offset: int = 0,
    limit: int = 50,
) -> tuple[list[AuditLog], int]:
    """Query audit logs with filters. Returns (items, total_count)."""
    conditions = [AuditLog.workspace_id == workspace_id]

    if action:
        conditions.append(AuditLog.action == action)
    if resource_type:
        conditions.append(AuditLog.resource_type == resource_type)
    if resource_id:
        conditions.append(AuditLog.resource_id == resource_id)
    if actor_id:
        conditions.append(AuditLog.actor_id == actor_id)
    if outcome:
        conditions.append(AuditLog.outcome == outcome)
    if project_id:
        conditions.append(AuditLog.project_id == project_id)
    if date_from:
        conditions.append(AuditLog.created_at >= date_from)
    if date_to:
        conditions.append(AuditLog.created_at <= date_to)

    where_clause = and_(*conditions)

    count_q = select(sa_func.count()).select_from(AuditLog).where(where_clause)
    total = (await db.execute(count_q)).scalar() or 0

    items_q = (
        select(AuditLog)
        .where(where_clause)
        .order_by(AuditLog.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    rows = (await db.execute(items_q)).scalars().all()

    return list(rows), total


async def export_audit_logs_csv(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    *,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    limit: int = 10000,
) -> str:
    """Export audit logs as CSV string for compliance downloads."""
    conditions = [AuditLog.workspace_id == workspace_id]
    if date_from:
        conditions.append(AuditLog.created_at >= date_from)
    if date_to:
        conditions.append(AuditLog.created_at <= date_to)

    q = (
        select(AuditLog)
        .where(and_(*conditions))
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
    )
    rows = (await db.execute(q)).scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "id", "actor_id", "actor_type", "action", "resource_type",
        "resource_id", "project_id", "outcome", "ip_address",
        "user_agent", "created_at",
    ])
    for row in rows:
        writer.writerow([
            str(row.id),
            str(row.actor_id) if row.actor_id else "",
            row.actor_type.value,
            row.action,
            row.resource_type,
            str(row.resource_id) if row.resource_id else "",
            str(row.project_id) if row.project_id else "",
            row.outcome.value,
            row.ip_address or "",
            row.user_agent or "",
            row.created_at.isoformat() if row.created_at else "",
        ])

    return output.getvalue()


async def get_audit_stats(
    db: AsyncSession,
    workspace_id: uuid.UUID,
) -> dict:
    """Return summary statistics for auditing dashboard."""
    total_q = (
        select(sa_func.count())
        .select_from(AuditLog)
        .where(AuditLog.workspace_id == workspace_id)
    )
    total = (await db.execute(total_q)).scalar() or 0

    # Counts by outcome
    outcome_q = (
        select(AuditLog.outcome, sa_func.count())
        .where(AuditLog.workspace_id == workspace_id)
        .group_by(AuditLog.outcome)
    )
    outcome_rows = (await db.execute(outcome_q)).all()
    by_outcome = {row[0].value: row[1] for row in outcome_rows}

    # Counts by action (top 10)
    action_q = (
        select(AuditLog.action, sa_func.count())
        .where(AuditLog.workspace_id == workspace_id)
        .group_by(AuditLog.action)
        .order_by(sa_func.count().desc())
        .limit(10)
    )
    action_rows = (await db.execute(action_q)).all()
    top_actions = {row[0]: row[1] for row in action_rows}

    return {
        "total_entries": total,
        "by_outcome": by_outcome,
        "top_actions": top_actions,
    }
