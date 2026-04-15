import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user_id
from app.db.session import get_db
from app.schemas.notification import (
    NotificationCreate,
    NotificationRead,
    NotificationList,
    GroupedNotificationList,
    GroupedNotificationItem,
    DeliveryConfigCreate,
    DeliveryConfigRead,
    DeliveryConfigList,
)
from app.services import notification_service
from app.services import notification_digest_service

router = APIRouter()


@router.post("/notifications", response_model=NotificationRead, status_code=201)
async def create_notification(
    data: NotificationCreate,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> NotificationRead:
    n = await notification_service.create_notification(
        db,
        user_id=user_id,
        notification_type=data.notification_type,
        title=data.title,
        priority=data.priority,
        body=data.body,
        resource_type=data.resource_type,
        resource_id=data.resource_id,
        metadata_=data.metadata_,
    )
    return NotificationRead.model_validate(n)


@router.get("/notifications", response_model=NotificationList)
async def list_notifications(
    unread_only: bool = Query(False),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> NotificationList:
    items, total, unread_count = await notification_service.list_notifications(
        db,
        user_id,
        unread_only=unread_only,
        limit=limit,
        offset=offset,
    )
    return NotificationList(
        items=[NotificationRead.model_validate(n) for n in items],
        total=total,
        unread_count=unread_count,
    )


@router.post("/notifications/{notification_id}/read", response_model=NotificationRead)
async def mark_read(
    notification_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> NotificationRead:
    n = await notification_service.mark_notification_read(db, notification_id)
    if n is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    return NotificationRead.model_validate(n)


@router.post("/notifications/read-all")
async def mark_all_read(
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> dict:
    count = await notification_service.mark_all_read(db, user_id)
    return {"marked": count}


# ── FM-149: Dismiss, Grouped, Digest ────────────────────────────


@router.post(
    "/notifications/{notification_id}/dismiss", response_model=NotificationRead
)
async def dismiss_notification(
    notification_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> NotificationRead:
    n = await notification_digest_service.dismiss_notification(
        db, notification_id, user_id
    )
    if n is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    return NotificationRead.model_validate(n)


@router.get("/notifications/grouped", response_model=GroupedNotificationList)
async def get_grouped_notifications(
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> GroupedNotificationList:
    items = await notification_digest_service.get_grouped_notifications(db, user_id)
    return GroupedNotificationList(
        items=[GroupedNotificationItem(**i) for i in items],
        total=len(items),
    )


@router.get("/notifications/digest", response_model=list[NotificationRead])
async def get_digest_preview(
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> list[NotificationRead]:
    items = await notification_digest_service.get_digest_preview(db, user_id)
    return [NotificationRead.model_validate(n) for n in items]


# ── Delivery Config ──────────────────────────────────────────────


@router.post(
    "/notifications/delivery", response_model=DeliveryConfigRead, status_code=201
)
async def create_delivery_config(
    data: DeliveryConfigCreate,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> DeliveryConfigRead:
    c = await notification_service.create_delivery_config(
        db,
        user_id=user_id,
        channel=data.channel,
        status=data.status,
        config=data.config,
    )
    return DeliveryConfigRead.model_validate(c)


@router.get("/notifications/delivery", response_model=DeliveryConfigList)
async def list_delivery_configs(
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> DeliveryConfigList:
    items, total = await notification_service.list_delivery_configs(db, user_id)
    return DeliveryConfigList(
        items=[DeliveryConfigRead.model_validate(c) for c in items],
        total=total,
    )


# ── FM-142: Notification Preferences ────────────────────────────


class _PreferenceBody(BaseModel):
    notification_type: str
    enabled: bool = True
    muted_until: str | None = None
    channel_overrides: dict | None = None


@router.get("/notifications/preferences")
async def get_preferences(
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> dict:
    """Get all notification preferences for the current user (FM-142)."""
    prefs = await notification_service.get_preferences(db, user_id)
    return {
        "items": [
            {
                "id": str(p.id),
                "notification_type": p.notification_type.value
                if hasattr(p.notification_type, "value")
                else p.notification_type,
                "enabled": p.enabled,
                "muted_until": p.muted_until.isoformat() if p.muted_until else None,
                "channel_overrides": p.channel_overrides,
            }
            for p in prefs
        ],
        "total": len(prefs),
    }


@router.put("/notifications/preferences")
async def upsert_preference(
    data: _PreferenceBody,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> dict:
    """Create or update a notification preference for a specific type (FM-142)."""
    pref = await notification_service.upsert_preference(
        db,
        user_id=user_id,
        notification_type=data.notification_type,
        enabled=data.enabled,
        muted_until=data.muted_until,
        channel_overrides=data.channel_overrides,
    )
    await db.commit()
    return {
        "id": str(pref.id),
        "notification_type": pref.notification_type.value
        if hasattr(pref.notification_type, "value")
        else pref.notification_type,
        "enabled": pref.enabled,
        "muted_until": pref.muted_until.isoformat() if pref.muted_until else None,
        "channel_overrides": pref.channel_overrides,
    }
