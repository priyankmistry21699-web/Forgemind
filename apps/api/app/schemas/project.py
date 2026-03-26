import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.project import ProjectStatus


# ---------- Request schemas ----------
class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    status: ProjectStatus | None = None


# ---------- Response schemas ----------
class ProjectRead(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    status: ProjectStatus
    owner_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectList(BaseModel):
    items: list[ProjectRead]
    total: int
