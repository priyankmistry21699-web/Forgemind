import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth_stub import get_current_user_id
from app.db.session import get_db
from app.schemas.workspace import WorkspaceCreate, WorkspaceUpdate, WorkspaceRead, WorkspaceList
from app.services import workspace_service

router = APIRouter()


@router.post("/workspaces", response_model=WorkspaceRead, status_code=201)
async def create_workspace(
    data: WorkspaceCreate,
    db: AsyncSession = Depends(get_db),
    owner_id: uuid.UUID = Depends(get_current_user_id),
) -> WorkspaceRead:
    existing = await workspace_service.get_workspace_by_slug(db, data.slug)
    if existing:
        raise HTTPException(status_code=409, detail="Slug already in use")
    ws = await workspace_service.create_workspace(
        db, name=data.name, slug=data.slug, owner_id=owner_id,
        description=data.description, settings=data.settings,
    )
    return WorkspaceRead.model_validate(ws)


@router.get("/workspaces", response_model=WorkspaceList)
async def list_workspaces(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    owner_id: uuid.UUID = Depends(get_current_user_id),
) -> WorkspaceList:
    items, total = await workspace_service.list_workspaces(
        db, owner_id, limit=limit, offset=offset,
    )
    return WorkspaceList(
        items=[WorkspaceRead.model_validate(w) for w in items],
        total=total,
    )


@router.get("/workspaces/{workspace_id}", response_model=WorkspaceRead)
async def get_workspace(
    workspace_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> WorkspaceRead:
    ws = await workspace_service.get_workspace(db, workspace_id)
    if ws is None:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return WorkspaceRead.model_validate(ws)


@router.patch("/workspaces/{workspace_id}", response_model=WorkspaceRead)
async def update_workspace(
    workspace_id: uuid.UUID,
    data: WorkspaceUpdate,
    db: AsyncSession = Depends(get_db),
) -> WorkspaceRead:
    ws = await workspace_service.update_workspace(
        db, workspace_id, **data.model_dump(exclude_unset=True),
    )
    if ws is None:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return WorkspaceRead.model_validate(ws)


@router.delete("/workspaces/{workspace_id}", status_code=204)
async def delete_workspace(
    workspace_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    deleted = await workspace_service.delete_workspace(db, workspace_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Workspace not found")
