import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.notification import (
    NotificationType,
    NotificationPriority,
    DeliveryChannel,
    DeliveryStatus,
)


# ── Notifications ────────────────────────────────────────────────


class NotificationCreate(BaseModel):
    notification_type: NotificationType
    priority: NotificationPriority = NotificationPriority.NORMAL
    title: str = Field(..., min_length=1, max_length=500)
    body: str | None = None
    resource_type: str | None = None
    resource_id: uuid.UUID | None = None
    metadata_: dict | None = None


class NotificationRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    notification_type: NotificationType
    priority: NotificationPriority
    title: str
    body: str | None
    is_read: bool
    category: str | None = None
    group_key: str | None = None
    dismissed_at: datetime | None = None
    resource_type: str | None
    resource_id: uuid.UUID | None
    metadata_: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationList(BaseModel):
    items: list[NotificationRead]
    total: int
    unread_count: int


# ── FM-149: Grouped & Digest schemas ────────────────────────────


class GroupedNotificationItem(BaseModel):
    group_key: str | None
    count: int
    latest_id: str
    latest_title: str
    notification_type: str
    latest_created_at: str


class GroupedNotificationList(BaseModel):
    items: list[GroupedNotificationItem]
    total: int


# ── Delivery Config ──────────────────────────────────────────────


class DeliveryConfigCreate(BaseModel):
    channel: DeliveryChannel
    status: DeliveryStatus = DeliveryStatus.ACTIVE
    config: dict | None = None


class DeliveryConfigRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    channel: DeliveryChannel
    status: DeliveryStatus
    config: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}


class DeliveryConfigList(BaseModel):
    items: list[DeliveryConfigRead]
    total: int
