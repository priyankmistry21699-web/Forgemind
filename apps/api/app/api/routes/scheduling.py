"""FM-231/232: Scheduling and event-driven trigger endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user_id
from app.db.session import get_db
from app.models.scheduling import CronTriggerStatus, TriggerRuleEvent
from app.services import schedule_service

router = APIRouter()


class CronTriggerIn(BaseModel):
    name: str
    cron_expression: str
    prompt: str | None = None


class TriggerRuleIn(BaseModel):
    name: str
    event_type: TriggerRuleEvent
    conditions: dict | None = None
    action_prompt: str | None = None


# --- Cron triggers ---


@router.get("/projects/{project_id}/schedules")
async def list_schedules(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user_id),
) -> dict:
    triggers = await schedule_service.list_cron_triggers(db, project_id)
    return {
        "items": [
            {
                "id": str(t.id),
                "name": t.name,
                "cron_expression": t.cron_expression,
                "status": t.status.value,
                "fire_count": t.fire_count,
                "last_fired_at": t.last_fired_at.isoformat()
                if t.last_fired_at
                else None,
                "created_at": t.created_at.isoformat(),
            }
            for t in triggers
        ],
        "total": len(triggers),
    }


@router.post("/projects/{project_id}/schedules", status_code=201)
async def create_schedule(
    project_id: uuid.UUID,
    body: CronTriggerIn,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
) -> dict:
    trigger = await schedule_service.create_cron_trigger(
        db,
        project_id=project_id,
        name=body.name,
        cron_expression=body.cron_expression,
        prompt=body.prompt,
        created_by=str(user_id),
    )
    await db.commit()
    return {"id": str(trigger.id), "name": trigger.name, "status": trigger.status.value}


@router.patch("/projects/{project_id}/schedules/{trigger_id}/pause")
async def pause_schedule(
    project_id: uuid.UUID,
    trigger_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user_id),
) -> dict:
    trigger = await schedule_service.update_cron_trigger_status(
        db, trigger_id, CronTriggerStatus.PAUSED
    )
    if trigger is None:
        raise HTTPException(status_code=404, detail="Schedule not found")
    await db.commit()
    return {"id": str(trigger.id), "status": trigger.status.value}


@router.patch("/projects/{project_id}/schedules/{trigger_id}/resume")
async def resume_schedule(
    project_id: uuid.UUID,
    trigger_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user_id),
) -> dict:
    trigger = await schedule_service.update_cron_trigger_status(
        db, trigger_id, CronTriggerStatus.ACTIVE
    )
    if trigger is None:
        raise HTTPException(status_code=404, detail="Schedule not found")
    await db.commit()
    return {"id": str(trigger.id), "status": trigger.status.value}


# --- Trigger rules ---


@router.get("/projects/{project_id}/trigger-rules")
async def list_trigger_rules(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user_id),
) -> dict:
    rules = await schedule_service.list_trigger_rules(db, project_id)
    return {
        "items": [
            {
                "id": str(r.id),
                "name": r.name,
                "event_type": r.event_type.value,
                "enabled": r.enabled,
                "fire_count": r.fire_count,
                "conditions": r.conditions,
            }
            for r in rules
        ],
        "total": len(rules),
    }


@router.post("/projects/{project_id}/trigger-rules", status_code=201)
async def create_trigger_rule(
    project_id: uuid.UUID,
    body: TriggerRuleIn,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user_id),
) -> dict:
    rule = await schedule_service.create_trigger_rule(
        db,
        project_id=project_id,
        name=body.name,
        event_type=body.event_type,
        conditions=body.conditions,
        action_prompt=body.action_prompt,
    )
    await db.commit()
    return {"id": str(rule.id), "name": rule.name, "event_type": rule.event_type.value}
