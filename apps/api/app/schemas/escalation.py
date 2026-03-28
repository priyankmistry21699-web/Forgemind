import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.escalation import EscalationTrigger, EscalationAction


class EscalationRuleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    trigger: EscalationTrigger
    action: EscalationAction
    rules: dict | None = None
    cooldown_minutes: int = 30
    is_active: bool = True


class EscalationRuleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    trigger: EscalationTrigger | None = None
    action: EscalationAction | None = None
    rules: dict | None = None
    cooldown_minutes: int | None = None
    is_active: bool | None = None


class EscalationRuleRead(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    name: str
    trigger: EscalationTrigger
    action: EscalationAction
    rules: dict | None
    cooldown_minutes: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EscalationRuleList(BaseModel):
    items: list[EscalationRuleRead]
    total: int


class EscalationEventRead(BaseModel):
    id: uuid.UUID
    rule_id: uuid.UUID
    project_id: uuid.UUID
    trigger_data: dict | None
    action_taken: str | None
    resolved: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class EscalationEventList(BaseModel):
    items: list[EscalationEventRead]
    total: int
