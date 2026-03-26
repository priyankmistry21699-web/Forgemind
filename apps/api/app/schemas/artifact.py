import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.artifact import ArtifactType


# ---------- Response schemas ----------
class ArtifactRead(BaseModel):
    id: uuid.UUID
    title: str
    artifact_type: ArtifactType
    content: str | None
    meta: dict | None
    version: int
    project_id: uuid.UUID
    run_id: uuid.UUID | None
    task_id: uuid.UUID | None
    created_by: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ArtifactList(BaseModel):
    items: list[ArtifactRead]
    total: int


# ---------- Request schemas ----------
class ArtifactCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    artifact_type: ArtifactType = ArtifactType.OTHER
    content: str | None = None
    meta: dict | None = None
    run_id: uuid.UUID | None = None
    task_id: uuid.UUID | None = None
    created_by: str | None = Field(None, max_length=100)


class ArtifactUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=500)
    content: str | None = None
    meta: dict | None = None
