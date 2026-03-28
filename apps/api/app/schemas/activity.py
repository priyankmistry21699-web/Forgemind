import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.activity import ActivityType


# ── Activity Feed ────────────────────────────────────────────────

class ActivityFeedEntryCreate(BaseModel):
    activity_type: ActivityType
    summary: str = Field(..., min_length=1, max_length=500)
    project_id: uuid.UUID | None = None
    workspace_id: uuid.UUID | None = None
    resource_type: str | None = None
    resource_id: uuid.UUID | None = None
    metadata_: dict | None = None


class ActivityFeedEntryRead(BaseModel):
    id: uuid.UUID
    actor_id: uuid.UUID
    activity_type: ActivityType
    summary: str
    project_id: uuid.UUID | None
    workspace_id: uuid.UUID | None
    resource_type: str | None
    resource_id: uuid.UUID | None
    metadata_: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ActivityFeedList(BaseModel):
    items: list[ActivityFeedEntryRead]
    total: int


# ── Presence ─────────────────────────────────────────────────────

class PresenceUpdate(BaseModel):
    status: str = Field(default="online", max_length=20)
    current_resource_type: str | None = None
    current_resource_id: uuid.UUID | None = None


class PresenceRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    status: str
    current_resource_type: str | None
    current_resource_id: uuid.UUID | None
    last_seen_at: datetime

    model_config = {"from_attributes": True}


class PresenceList(BaseModel):
    items: list[PresenceRead]
    total: int
