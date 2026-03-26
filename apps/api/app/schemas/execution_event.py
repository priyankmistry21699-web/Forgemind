"""Execution event schemas — response models for the event log."""

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.execution_event import EventType


class ExecutionEventRead(BaseModel):
    id: uuid.UUID
    event_type: EventType
    summary: str
    metadata_: dict | None
    project_id: uuid.UUID | None
    run_id: uuid.UUID | None
    task_id: uuid.UUID | None
    artifact_id: uuid.UUID | None
    agent_slug: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ExecutionEventList(BaseModel):
    items: list[ExecutionEventRead]
    total: int
