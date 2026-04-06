"""FM-111: Phase Agent Profile schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.phase_agent_profile import WorkflowPhase


class PhaseAgentProfileCreate(BaseModel):
    phase: WorkflowPhase
    agent_id: uuid.UUID
    priority: int = 0
    is_default: bool = False
    notes: str | None = None


class PhaseAgentProfileUpdate(BaseModel):
    agent_id: uuid.UUID | None = None
    priority: int | None = None
    is_default: bool | None = None
    notes: str | None = None


class PhaseAgentProfileRead(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    phase: WorkflowPhase
    agent_id: uuid.UUID
    priority: int
    is_default: bool
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PhaseAgentProfileList(BaseModel):
    items: list[PhaseAgentProfileRead]
    total: int
