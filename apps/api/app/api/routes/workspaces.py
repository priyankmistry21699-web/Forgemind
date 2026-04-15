import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user_id
from app.db.session import get_db
from app.schemas.workspace import (
    WorkspaceCreate,
    WorkspaceUpdate,
    WorkspaceRead,
    WorkspaceList,
)
from app.services import workspace_service
from app.services.authz_service import check_workspace_permission, Action

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
        db,
        name=data.name,
        slug=data.slug,
        owner_id=owner_id,
        description=data.description,
        settings=data.settings,
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
        db,
        owner_id,
        limit=limit,
        offset=offset,
    )
    return WorkspaceList(
        items=[WorkspaceRead.model_validate(w) for w in items],
        total=total,
    )


@router.get("/workspaces/{workspace_id}", response_model=WorkspaceRead)
async def get_workspace(
    workspace_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> WorkspaceRead:
    await check_workspace_permission(db, workspace_id, user_id, Action.WORKSPACE_VIEW)
    ws = await workspace_service.get_workspace(db, workspace_id)
    if ws is None:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return WorkspaceRead.model_validate(ws)


@router.patch("/workspaces/{workspace_id}", response_model=WorkspaceRead)
async def update_workspace(
    workspace_id: uuid.UUID,
    data: WorkspaceUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> WorkspaceRead:
    await check_workspace_permission(db, workspace_id, user_id, Action.WORKSPACE_UPDATE)
    ws = await workspace_service.update_workspace(
        db,
        workspace_id,
        **data.model_dump(exclude_unset=True),
    )
    if ws is None:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return WorkspaceRead.model_validate(ws)


@router.delete("/workspaces/{workspace_id}", status_code=204)
async def delete_workspace(
    workspace_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> None:
    await check_workspace_permission(db, workspace_id, user_id, Action.WORKSPACE_DELETE)
    deleted = await workspace_service.delete_workspace(db, workspace_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Workspace not found")


# ---------------------------------------------------------------------------
# FM-171: Governance Settings CRUD
# ---------------------------------------------------------------------------

VALID_PLAN_TIERS = {"free", "team", "enterprise"}
VALID_COMPLIANCE_LEVELS = {"none", "basic", "soc2", "hipaa"}


class GovernanceSettingsUpdate(BaseModel):
    """Validated governance settings schema."""
    plan_tier: str | None = None
    compliance_level: str | None = None
    sso_enforced: bool | None = None
    ip_enforcement_enabled: bool | None = None
    data_region: str | None = None
    audit_retention_days: int | None = None


@router.get("/workspaces/{workspace_id}/governance")
async def get_governance_settings(
    workspace_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Get workspace governance settings (FM-171)."""
    await check_workspace_permission(db, workspace_id, user_id, Action.WORKSPACE_VIEW)
    ws = await workspace_service.get_workspace(db, workspace_id)
    if ws is None:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return ws.governance_settings or {
        "plan_tier": "free",
        "compliance_level": "none",
        "sso_enforced": False,
        "ip_enforcement_enabled": False,
        "data_region": None,
        "audit_retention_days": None,
    }


@router.put("/workspaces/{workspace_id}/governance")
async def update_governance_settings(
    workspace_id: uuid.UUID,
    data: GovernanceSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Update workspace governance settings with validation (FM-171)."""
    await check_workspace_permission(db, workspace_id, user_id, Action.WORKSPACE_UPDATE)
    ws = await workspace_service.get_workspace(db, workspace_id)
    if ws is None:
        raise HTTPException(status_code=404, detail="Workspace not found")

    updated = dict(ws.governance_settings or {})
    patch = data.model_dump(exclude_unset=True)

    if "plan_tier" in patch and patch["plan_tier"] not in VALID_PLAN_TIERS:
        raise HTTPException(status_code=422, detail=f"plan_tier must be one of {VALID_PLAN_TIERS}")
    if "compliance_level" in patch and patch["compliance_level"] not in VALID_COMPLIANCE_LEVELS:
        raise HTTPException(status_code=422, detail=f"compliance_level must be one of {VALID_COMPLIANCE_LEVELS}")
    if "audit_retention_days" in patch and patch["audit_retention_days"] is not None:
        if patch["audit_retention_days"] < 1 or patch["audit_retention_days"] > 3650:
            raise HTTPException(status_code=422, detail="audit_retention_days must be between 1 and 3650")

    updated.update(patch)
    ws.governance_settings = updated
    await db.flush()
    await db.refresh(ws)
    return ws.governance_settings
