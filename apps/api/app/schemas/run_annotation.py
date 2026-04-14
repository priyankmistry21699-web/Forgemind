"""Schemas for run annotations (FM-146)."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.run_annotation import AnnotationType


class AnnotationCreate(BaseModel):
    annotation_type: AnnotationType
    body: str = Field(..., min_length=1, max_length=5000)
    pinned_event_id: uuid.UUID | None = None


class AnnotationUpdate(BaseModel):
    body: str = Field(..., min_length=1, max_length=5000)


class AnnotationRead(BaseModel):
    id: uuid.UUID
    run_id: uuid.UUID
    author_id: uuid.UUID
    annotation_type: AnnotationType
    body: str
    pinned_event_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AnnotationList(BaseModel):
    items: list[AnnotationRead]
    total: int
