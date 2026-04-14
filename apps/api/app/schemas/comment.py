"""Pydantic schemas for threaded comments (FM-141)."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.comment import CommentEntityType


class CommentCreate(BaseModel):
    entity_type: CommentEntityType
    entity_id: uuid.UUID
    parent_id: uuid.UUID | None = None
    body: str = Field(..., min_length=1, max_length=10000)


class CommentUpdate(BaseModel):
    body: str = Field(..., min_length=1, max_length=10000)


class CommentRead(BaseModel):
    id: uuid.UUID
    entity_type: CommentEntityType
    entity_id: uuid.UUID
    parent_id: uuid.UUID | None
    author_id: uuid.UUID
    body: str
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
    replies: list["CommentRead"] = []

    model_config = {"from_attributes": True}


class CommentList(BaseModel):
    items: list[CommentRead]
    total: int
