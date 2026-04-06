"""FM-121: Execution Checkpoint schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.execution_checkpoint import CheckpointType


class CheckpointRead(BaseModel):
    id: uuid.UUID
    run_id: uuid.UUID
    task_id: uuid.UUID | None
    project_id: uuid.UUID
    name: str | None
    checkpoint_type: CheckpointType
    summary: str
    status_snapshot: dict | None
    artifact_refs: dict | None
    validation_snapshot: dict | None
    approval_snapshot: dict | None
    architecture_snapshot: dict | None
    metadata_: dict | None = Field(None, alias="metadata_")
    sequence_number: int
    created_by: str | None
    created_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}


class CheckpointList(BaseModel):
    items: list[CheckpointRead]
    total: int


class CheckpointCreate(BaseModel):
    name: str | None = Field(None, max_length=500)
    checkpoint_type: CheckpointType = CheckpointType.MANUAL
    summary: str = Field(..., min_length=1)
    task_id: uuid.UUID | None = None
    status_snapshot: dict | None = None
    artifact_refs: dict | None = None
    validation_snapshot: dict | None = None
    approval_snapshot: dict | None = None
    architecture_snapshot: dict | None = None
    metadata_: dict | None = Field(None, alias="metadata")
    created_by: str | None = Field(None, max_length=100)

    model_config = {"populate_by_name": True}
