import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.escalation import (
    EscalationRuleCreate, EscalationRuleUpdate, EscalationRuleRead, EscalationRuleList,
    EscalationEventRead, EscalationEventList,
)
from app.services import escalation_service

router = APIRouter()


# ── Rules ────────────────────────────────────────────────────────

@router.post(
    "/projects/{project_id}/escalation/rules",
    response_model=EscalationRuleRead,
    status_code=201,
)
async def create_rule(
    project_id: uuid.UUID,
    data: EscalationRuleCreate,
    db: AsyncSession = Depends(get_db),
) -> EscalationRuleRead:
    rule = await escalation_service.create_rule(
        db, project_id=project_id, name=data.name,
        trigger=data.trigger, action=data.action,
        rules=data.rules, cooldown_minutes=data.cooldown_minutes,
        is_active=data.is_active,
    )
    return EscalationRuleRead.model_validate(rule)


@router.get(
    "/projects/{project_id}/escalation/rules",
    response_model=EscalationRuleList,
)
async def list_rules(
    project_id: uuid.UUID,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> EscalationRuleList:
    items, total = await escalation_service.list_rules(
        db, project_id, limit=limit, offset=offset,
    )
    return EscalationRuleList(
        items=[EscalationRuleRead.model_validate(r) for r in items],
        total=total,
    )


@router.get("/escalation/rules/{rule_id}", response_model=EscalationRuleRead)
async def get_rule(
    rule_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> EscalationRuleRead:
    rule = await escalation_service.get_rule(db, rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="Rule not found")
    return EscalationRuleRead.model_validate(rule)


@router.patch("/escalation/rules/{rule_id}", response_model=EscalationRuleRead)
async def update_rule(
    rule_id: uuid.UUID,
    data: EscalationRuleUpdate,
    db: AsyncSession = Depends(get_db),
) -> EscalationRuleRead:
    rule = await escalation_service.update_rule(
        db, rule_id, **data.model_dump(exclude_unset=True),
    )
    if rule is None:
        raise HTTPException(status_code=404, detail="Rule not found")
    return EscalationRuleRead.model_validate(rule)


@router.delete("/escalation/rules/{rule_id}", status_code=204)
async def delete_rule(
    rule_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    deleted = await escalation_service.delete_rule(db, rule_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Rule not found")


# ── Events ───────────────────────────────────────────────────────

@router.get(
    "/projects/{project_id}/escalation/events",
    response_model=EscalationEventList,
)
async def list_events(
    project_id: uuid.UUID,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> EscalationEventList:
    items, total = await escalation_service.list_events(
        db, project_id, limit=limit, offset=offset,
    )
    return EscalationEventList(
        items=[EscalationEventRead.model_validate(e) for e in items],
        total=total,
    )
