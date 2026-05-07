"""FM-231/232: Scheduled and event-driven trigger service."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.scheduling import CronTrigger, CronTriggerStatus, TriggerRule, TriggerRuleEvent


# ---------------------------------------------------------------------------
# Cron triggers
# ---------------------------------------------------------------------------


async def create_cron_trigger(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    name: str,
    cron_expression: str,
    prompt: str | None = None,
    created_by: str | None = None,
) -> CronTrigger:
    trigger = CronTrigger(
        project_id=project_id,
        name=name,
        cron_expression=cron_expression,
        prompt=prompt,
        created_by=created_by,
        status=CronTriggerStatus.ACTIVE,
    )
    db.add(trigger)
    await db.flush()
    return trigger


async def list_cron_triggers(
    db: AsyncSession,
    project_id: uuid.UUID,
) -> list[CronTrigger]:
    result = await db.execute(
        select(CronTrigger)
        .where(CronTrigger.project_id == project_id)
        .order_by(CronTrigger.created_at.desc())
    )
    return list(result.scalars().all())


async def update_cron_trigger_status(
    db: AsyncSession,
    trigger_id: uuid.UUID,
    status: CronTriggerStatus,
) -> CronTrigger | None:
    trigger = await db.get(CronTrigger, trigger_id)
    if trigger is None:
        return None
    trigger.status = status
    await db.flush()
    return trigger


async def record_cron_fire(
    db: AsyncSession,
    trigger_id: uuid.UUID,
) -> CronTrigger | None:
    trigger = await db.get(CronTrigger, trigger_id)
    if trigger is None:
        return None
    trigger.last_fired_at = datetime.now(timezone.utc)
    trigger.fire_count += 1
    await db.flush()
    return trigger


# ---------------------------------------------------------------------------
# Trigger rules
# ---------------------------------------------------------------------------


async def create_trigger_rule(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    name: str,
    event_type: TriggerRuleEvent,
    conditions: dict | None = None,
    action_prompt: str | None = None,
) -> TriggerRule:
    rule = TriggerRule(
        project_id=project_id,
        name=name,
        event_type=event_type,
        conditions=conditions,
        action_prompt=action_prompt,
        enabled=True,
    )
    db.add(rule)
    await db.flush()
    return rule


async def list_trigger_rules(
    db: AsyncSession,
    project_id: uuid.UUID,
) -> list[TriggerRule]:
    result = await db.execute(
        select(TriggerRule)
        .where(TriggerRule.project_id == project_id)
        .order_by(TriggerRule.created_at.desc())
    )
    return list(result.scalars().all())


async def fire_matching_rules(
    db: AsyncSession,
    project_id: uuid.UUID,
    event_type: TriggerRuleEvent,
    event_payload: dict[str, Any],
) -> list[TriggerRule]:
    """Find and mark rules that match the event — caller creates runs."""
    result = await db.execute(
        select(TriggerRule).where(
            TriggerRule.project_id == project_id,
            TriggerRule.event_type == event_type,
            TriggerRule.enabled.is_(True),
        )
    )
    rules = list(result.scalars().all())
    fired = []
    now = datetime.now(timezone.utc)
    for rule in rules:
        # Simple condition matching: if conditions is empty or all keys match payload
        conds = rule.conditions or {}
        if all(event_payload.get(k) == v for k, v in conds.items()):
            rule.fire_count += 1
            rule.last_fired_at = now
            fired.append(rule)
    if fired:
        await db.flush()
    return fired
