"""FM-102: Project constitution schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ConstitutionRead(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    title: str | None
    content: str
    summary: str | None
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ConstitutionCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=50000)
    title: str | None = Field(None, max_length=500)
    summary: str | None = Field(None, max_length=2000)


class ConstitutionUpdate(BaseModel):
    content: str | None = Field(None, min_length=1, max_length=50000)
    title: str | None = Field(None, max_length=500)
    summary: str | None = Field(None, max_length=2000)
