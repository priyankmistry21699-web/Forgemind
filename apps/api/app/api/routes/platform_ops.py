"""FM-241/245/247/248: Platform operations endpoints.

GET  /workspaces/{id}/quotas             — FM-241 get quota
PUT  /workspaces/{id}/quotas             — FM-241 upsert quota
GET  /workspaces/{id}/quotas/check       — FM-241 check violations
POST /admin/audit-export                 — FM-245 SIEM export
GET  /artifacts/{id}/pii-scan            — FM-247 PII scan
POST /admin/pii-patterns/seed            — FM-247 seed built-ins
GET  /admin/platform-stats               — FM-248 super-admin stats
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user_id
from app.db.session import get_db
from app.services.authz_service import (
    Action,
    check_project_permission,
    check_workspace_permission,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# FM-241: Resource quotas
# ---------------------------------------------------------------------------


class QuotaIn(BaseModel):
    # VULN-13 fix: bounded field validators to prevent nonsensical quota values
    max_concurrent_runs: int | None = Field(None, ge=1, le=10_000)
    max_projects: int | None = Field(None, ge=1, le=100_000)
    max_monthly_cost_usd: float | None = Field(None, ge=0.0, le=1_000_000.0)
    max_api_calls_per_minute: int | None = Field(None, ge=1, le=100_000)
    max_storage_gb: float | None = Field(None, ge=0.0, le=100_000.0)
    enforce: bool = True


@router.get("/workspaces/{workspace_id}/quotas")
async def get_quota(
    workspace_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> dict:
    # VULN-7 fix: verify caller is a workspace member before reading quotas
    await check_workspace_permission(db, workspace_id, user_id, Action.WORKSPACE_VIEW)

    from app.services.quota_service import get_quota as _get

    quota = await _get(db, workspace_id)
    if quota is None:
        return {"workspace_id": str(workspace_id), "quota_defined": False}
    return {
        "workspace_id": str(workspace_id),
        "quota_defined": True,
        "max_concurrent_runs": quota.max_concurrent_runs,
        "max_projects": quota.max_projects,
        "max_monthly_cost_usd": quota.max_monthly_cost_usd,
        "max_api_calls_per_minute": quota.max_api_calls_per_minute,
        "max_storage_gb": quota.max_storage_gb,
        "enforce": quota.enforce,
    }


@router.put("/workspaces/{workspace_id}/quotas")
async def upsert_quota(
    workspace_id: uuid.UUID,
    body: QuotaIn,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> dict:
    # VULN-7 fix: only workspace owners/admins may modify quotas
    await check_workspace_permission(db, workspace_id, user_id, Action.WORKSPACE_UPDATE)

    from app.services.quota_service import upsert_quota as _upsert

    quota = await _upsert(
        db,
        workspace_id,
        max_concurrent_runs=body.max_concurrent_runs,
        max_projects=body.max_projects,
        max_monthly_cost_usd=body.max_monthly_cost_usd,
        max_api_calls_per_minute=body.max_api_calls_per_minute,
        max_storage_gb=body.max_storage_gb,
        enforce=body.enforce,
    )
    await db.commit()
    return {
        "workspace_id": str(workspace_id),
        "id": str(quota.id),
        "enforce": quota.enforce,
    }


@router.get("/workspaces/{workspace_id}/quotas/check")
async def check_quota(
    workspace_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> dict:
    # VULN-7 fix: verify workspace membership before returning violation data
    await check_workspace_permission(db, workspace_id, user_id, Action.WORKSPACE_VIEW)

    from app.services.quota_service import check_quota_violations

    return await check_quota_violations(db, workspace_id)


# ---------------------------------------------------------------------------
# FM-245: SIEM audit export
# ---------------------------------------------------------------------------


class AuditExportIn(BaseModel):
    workspace_id: uuid.UUID | None = None
    format: str = "jsonl"  # "jsonl" | "csv"
    limit: int = Field(default=10_000, ge=1, le=100_000)


@router.post("/admin/audit-export")
async def export_audit_log(
    body: AuditExportIn,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> Response:
    from sqlalchemy import select
    from app.models.enterprise_governance import AuditLog
    import json

    # VULN-8 fix: scope export to the caller's own workspace; require audit permission
    if body.workspace_id is None:
        raise HTTPException(
            status_code=400,
            detail="workspace_id is required — cross-workspace export is not permitted.",
        )
    await check_workspace_permission(
        db, body.workspace_id, user_id, Action.WORKSPACE_VIEW_AUDIT
    )

    q = (
        select(AuditLog)
        .where(AuditLog.workspace_id == body.workspace_id)
        .order_by(AuditLog.created_at.desc())
        .limit(body.limit)
    )
    result = await db.execute(q)
    logs = result.scalars().all()

    if body.format == "csv":
        lines = ["timestamp,action,actor_id,resource_type,resource_id,workspace_id"]
        for log in logs:
            lines.append(
                f"{log.created_at.isoformat()},{log.action},{log.actor_id},"
                f"{log.resource_type},{log.resource_id},{log.workspace_id}"
            )
        content = "\n".join(lines)
        media_type = "text/csv"
        filename = "audit_export.csv"
    else:
        lines = []
        for log in logs:
            lines.append(
                json.dumps(
                    {
                        "timestamp": log.created_at.isoformat(),
                        "action": log.action,
                        "actor_id": str(log.actor_id) if log.actor_id else None,
                        "resource_type": log.resource_type,
                        "resource_id": str(log.resource_id)
                        if log.resource_id
                        else None,
                        "workspace_id": str(log.workspace_id)
                        if log.workspace_id
                        else None,
                        "details": log.details,
                    }
                )
            )
        content = "\n".join(lines)
        media_type = "application/x-ndjson"
        filename = "audit_export.jsonl"

    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ---------------------------------------------------------------------------
# FM-247: PII detection
# ---------------------------------------------------------------------------


@router.get("/artifacts/{artifact_id}/pii-scan")
async def pii_scan_artifact(
    artifact_id: uuid.UUID,
    mask: bool = False,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> dict:
    # VULN-9 fix: verify project membership before scanning artifact content
    from app.models.artifact import Artifact

    artifact = await db.get(Artifact, artifact_id)
    if artifact is None:
        return {"error": "Artifact not found"}
    await check_project_permission(
        db, artifact.project_id, user_id, Action.PROJECT_VIEW
    )

    from app.services.pii_service import scan_artifact

    return await scan_artifact(db, artifact_id, mask=mask)


@router.post("/admin/pii-patterns/seed", status_code=201)
async def seed_pii_patterns(
    db: AsyncSession = Depends(get_db),
    _: uuid.UUID = Depends(get_current_user_id),
) -> dict:
    from app.services.pii_service import seed_builtin_patterns

    await seed_builtin_patterns(db)
    await db.commit()
    return {"status": "seeded"}


# ---------------------------------------------------------------------------
# FM-248: Platform admin stats
# ---------------------------------------------------------------------------


@router.get("/admin/platform-stats")
async def platform_stats(
    db: AsyncSession = Depends(get_db),
    _: uuid.UUID = Depends(get_current_user_id),
) -> dict:
    from app.services.platform_admin_service import get_platform_stats

    return await get_platform_stats(db)
