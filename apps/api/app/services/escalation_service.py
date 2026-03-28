import uuid
from typing import Any

from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.escalation import EscalationRule, EscalationEvent


# ── Rules ────────────────────────────────────────────────────────

async def create_rule(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    name: str,
    trigger: str,
    action: str,
    rules: dict | None = None,
    cooldown_minutes: int = 30,
    is_active: bool = True,
) -> EscalationRule:
    rule = EscalationRule(
        project_id=project_id,
        name=name,
        trigger=trigger,
        action=action,
        rules=rules,
        cooldown_minutes=cooldown_minutes,
        is_active=is_active,
    )
    db.add(rule)
    await db.flush()
    await db.refresh(rule)
    return rule


async def get_rule(
    db: AsyncSession, rule_id: uuid.UUID
) -> EscalationRule | None:
    result = await db.execute(
        select(EscalationRule).where(EscalationRule.id == rule_id)
    )
    return result.scalar_one_or_none()


async def list_rules(
    db: AsyncSession,
    project_id: uuid.UUID,
    *,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[EscalationRule], int]:
    query = select(EscalationRule).where(
        EscalationRule.project_id == project_id
    )
    total = (await db.execute(
        select(sa_func.count()).select_from(query.subquery())
    )).scalar_one()
    result = await db.execute(
        query.order_by(EscalationRule.created_at.desc()).offset(offset).limit(limit)
    )
    return list(result.scalars().all()), total


async def update_rule(
    db: AsyncSession,
    rule_id: uuid.UUID,
    **updates: Any,
) -> EscalationRule | None:
    rule = await get_rule(db, rule_id)
    if rule is None:
        return None
    allowed = {"name", "trigger", "action", "rules", "cooldown_minutes", "is_active"}
    for k, v in updates.items():
        if k in allowed and v is not None:
            setattr(rule, k, v)
    await db.flush()
    await db.refresh(rule)
    return rule


async def delete_rule(
    db: AsyncSession, rule_id: uuid.UUID
) -> bool:
    rule = await get_rule(db, rule_id)
    if rule is None:
        return False
    await db.delete(rule)
    await db.flush()
    return True


# ── Events ───────────────────────────────────────────────────────

async def trigger_escalation(
    db: AsyncSession,
    *,
    rule_id: uuid.UUID,
    project_id: uuid.UUID,
    trigger_data: dict | None = None,
    action_taken: str | None = None,
) -> EscalationEvent:
    event = EscalationEvent(
        rule_id=rule_id,
        project_id=project_id,
        trigger_data=trigger_data,
        action_taken=action_taken,
    )
    db.add(event)
    await db.flush()
    await db.refresh(event)
    return event


async def list_events(
    db: AsyncSession,
    project_id: uuid.UUID,
    *,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[EscalationEvent], int]:
    query = select(EscalationEvent).where(
        EscalationEvent.project_id == project_id
    )
    total = (await db.execute(
        select(sa_func.count()).select_from(query.subquery())
    )).scalar_one()
    result = await db.execute(
        query.order_by(EscalationEvent.created_at.desc()).offset(offset).limit(limit)
    )
    return list(result.scalars().all()), total
