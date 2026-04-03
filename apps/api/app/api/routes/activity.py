import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user_id
from app.db.session import get_db
from app.schemas.activity import (
    ActivityFeedEntryCreate, ActivityFeedEntryRead, ActivityFeedList,
    PresenceUpdate, PresenceRead, PresenceList,
)
from app.services import activity_service
from app.services import user_activity_service
from app.services.authz_service import check_project_permission, check_workspace_permission, Action

router = APIRouter()


# ── Activity Feed ────────────────────────────────────────────────

@router.post("/activity", response_model=ActivityFeedEntryRead, status_code=201)
async def create_activity(
    data: ActivityFeedEntryCreate,
    db: AsyncSession = Depends(get_db),
    actor_id: uuid.UUID = Depends(get_current_user_id),
) -> ActivityFeedEntryRead:
    if data.project_id is not None:
        await check_project_permission(db, data.project_id, actor_id, Action.PROJECT_UPDATE)
    elif data.workspace_id is not None:
        await check_workspace_permission(db, data.workspace_id, actor_id, Action.WORKSPACE_UPDATE)
    entry = await activity_service.create_activity(
        db, actor_id=actor_id, activity_type=data.activity_type,
        summary=data.summary, project_id=data.project_id,
        workspace_id=data.workspace_id, resource_type=data.resource_type,
        resource_id=data.resource_id, metadata_=data.metadata_,
    )
    return ActivityFeedEntryRead.model_validate(entry)


@router.get("/activity", response_model=ActivityFeedList)
async def list_activities(
    project_id: uuid.UUID | None = Query(None),
    workspace_id: uuid.UUID | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> ActivityFeedList:
    if project_id is not None:
        await check_project_permission(db, project_id, user_id, Action.PROJECT_VIEW)
    elif workspace_id is not None:
        await check_workspace_permission(db, workspace_id, user_id, Action.WORKSPACE_VIEW)
    items, total = await activity_service.list_activities(
        db, project_id=project_id, workspace_id=workspace_id,
        limit=limit, offset=offset,
    )
    return ActivityFeedList(
        items=[ActivityFeedEntryRead.model_validate(e) for e in items],
        total=total,
    )


# ── Presence ─────────────────────────────────────────────────────

@router.put("/presence", response_model=PresenceRead)
async def update_presence(
    data: PresenceUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> PresenceRead:
    p = await activity_service.upsert_presence(
        db, user_id=user_id, status=data.status,
        current_resource_type=data.current_resource_type,
        current_resource_id=data.current_resource_id,
    )
    return PresenceRead.model_validate(p)


@router.get("/presence", response_model=PresenceList)
async def list_presence(
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> PresenceList:
    items, total = await activity_service.list_presence(
        db, limit=limit, offset=offset,
    )
    return PresenceList(
        items=[PresenceRead.model_validate(p) for p in items],
        total=total,
    )


@router.get("/presence/{user_id}", response_model=PresenceRead)
async def get_presence(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user_id),
) -> PresenceRead:
    p = await activity_service.get_presence(db, user_id)
    if p is None:
        raise HTTPException(status_code=404, detail="Presence not found")
    return PresenceRead.model_validate(p)


# ── Workspace Activity (FM-058) ─────────────────────────────────

@router.get("/workspaces/{workspace_id}/activity", response_model=ActivityFeedList)
async def get_workspace_activity(
    workspace_id: uuid.UUID,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> ActivityFeedList:
    """Get activity feed scoped to a workspace."""
    await check_workspace_permission(db, workspace_id, user_id, Action.WORKSPACE_VIEW)
    items, total = await activity_service.list_activities(
        db, workspace_id=workspace_id, limit=limit, offset=offset,
    )
    return ActivityFeedList(
        items=[ActivityFeedEntryRead.model_validate(e) for e in items],
        total=total,
    )


# ── User Assignment Context (FM-059) ────────────────────────────

@router.get("/users/{user_id}/context")
async def get_user_context(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user_id),
) -> dict:
    """Get assignment and presence context for a user."""
    return await user_activity_service.get_user_assignment_context(db, user_id)
