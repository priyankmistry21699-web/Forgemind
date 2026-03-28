import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.artifact import ArtifactType, ChangeType


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
    # FM-063: code artifact mapping
    repo_connection_id: uuid.UUID | None
    target_path: str | None
    target_module: str | None
    change_type: ChangeType | None
    target_metadata: dict | None

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
    # FM-063
    repo_connection_id: uuid.UUID | None = None
    target_path: str | None = None
    target_module: str | None = None
    change_type: ChangeType | None = None
    target_metadata: dict | None = None


class ArtifactUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=500)
    content: str | None = None
    meta: dict | None = None
    # FM-063
    repo_connection_id: uuid.UUID | None = None
    target_path: str | None = None
    target_module: str | None = None
    change_type: ChangeType | None = None
    target_metadata: dict | None = None
