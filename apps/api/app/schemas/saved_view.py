"""Schemas for saved views (FM-144)."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.saved_view import ViewVisibility


class SavedViewCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    entity_type: str = Field(..., min_length=1, max_length=50)
    filter_json: dict[str, Any] = {}
    visibility: ViewVisibility = ViewVisibility.PRIVATE


class SavedViewUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    filter_json: dict[str, Any] | None = None
    visibility: ViewVisibility | None = None


class SavedViewRead(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    creator_id: uuid.UUID
    name: str
    entity_type: str
    filter_json: dict[str, Any]
    visibility: ViewVisibility
    created_at: datetime

    model_config = {"from_attributes": True}


class SavedViewList(BaseModel):
    items: list[SavedViewRead]
    total: int
