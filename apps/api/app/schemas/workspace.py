import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.workspace import WorkspaceStatus


class WorkspaceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    settings: dict | None = None


class WorkspaceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    status: WorkspaceStatus | None = None
    settings: dict | None = None


class WorkspaceRead(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    description: str | None
    status: WorkspaceStatus
    owner_id: uuid.UUID
    settings: dict | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WorkspaceList(BaseModel):
    items: list[WorkspaceRead]
    total: int
