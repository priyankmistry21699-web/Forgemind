"""Enterprise governance routes — audit logs, policy evaluation,
compliance reports, IP allowlisting, and retention policies.

FM-171–180: Enterprise Governance, Permissions & Compliance (Wave 13).
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user_id
from app.db.session import get_db
from app.services.authz_service import check_workspace_permission, Action
from app.services.authz_service import (
    create_custom_role,
    list_custom_roles,
    update_custom_role,
)
from app.services import (
    audit_log_service,
    governance_engine_service,
    compliance_report_service,
    ip_allowlist_service,
    retention_policy_service,
    sso_configuration_service,
)
from app.services.authz_service import (
    check_project_permission,
    get_user_permissions,
)
from app.schemas.enterprise_governance import (
    AuditLogRead,
    AuditLogList,
    PolicyEvaluationRead,
    PolicyEvaluationList,
    PolicyEvaluateRequest,
    PolicyEvaluateResponse,
    ComplianceReportRead,
    ComplianceReportList,
    ComplianceReportCreate,
    IpAllowlistRead,
    IpAllowlistList,
    IpAllowlistCreate,
    RetentionPolicyRead,
    RetentionPolicyList,
    RetentionPolicyCreate,
    RetentionPolicyUpdate,
    GovernanceSettingsRead,
    GovernanceSettingsUpdate,
    SSOConfigurationRead,
    SSOConfigurationList,
    SSOConfigurationCreate,
    PermissionsIntrospectionResponse,
)
from app.models.enterprise_governance import (
    AuditOutcome,
    PolicyEvalResult,
    ComplianceReportType,
)

router = APIRouter()


# ══════════════════════════════════════════════════════════════════
# Audit Log (FM-173)
# ══════════════════════════════════════════════════════════════════


@router.get(
    "/workspaces/{workspace_id}/audit-log",
    response_model=AuditLogList,
)
async def list_audit_log(
    workspace_id: uuid.UUID,
    action: str | None = Query(None),
    resource_type: str | None = Query(None),
    resource_id: uuid.UUID | None = Query(None),
    actor_id: uuid.UUID | None = Query(None),
    outcome: AuditOutcome | None = Query(None),
    project_id: uuid.UUID | None = Query(None),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """List audit log entries for a workspace with filters.

    Requires WORKSPACE_VIEW_AUDIT permission.
    """
    await check_workspace_permission(
        db, workspace_id, current_user_id, Action.WORKSPACE_VIEW_AUDIT
    )

    items, total = await audit_log_service.list_audit_logs(
        db,
        workspace_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        actor_id=actor_id,
        outcome=outcome,
        project_id=project_id,
        date_from=date_from,
        date_to=date_to,
        offset=offset,
        limit=limit,
    )

    return AuditLogList(
        items=[AuditLogRead.model_validate(i) for i in items],
        total=total,
    )


@router.get(
    "/workspaces/{workspace_id}/audit-log/export",
    response_class=PlainTextResponse,
)
async def export_audit_log(
    workspace_id: uuid.UUID,
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    limit: int = Query(10000, ge=1, le=100000),
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Export audit log as CSV for compliance downloads.

    Requires WORKSPACE_VIEW_AUDIT permission.
    """
    await check_workspace_permission(
        db, workspace_id, current_user_id, Action.WORKSPACE_VIEW_AUDIT
    )

    csv_content = await audit_log_service.export_audit_logs_csv(
        db,
        workspace_id,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
    )

    return PlainTextResponse(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=audit_log.csv"},
    )


@router.get(
    "/workspaces/{workspace_id}/audit-log/stats",
)
async def get_audit_stats(
    workspace_id: uuid.UUID,
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get audit log statistics for dashboard display.

    Requires WORKSPACE_VIEW_AUDIT permission.
    """
    await check_workspace_permission(
        db, workspace_id, current_user_id, Action.WORKSPACE_VIEW_AUDIT
    )

    return await audit_log_service.get_audit_stats(db, workspace_id)


# ══════════════════════════════════════════════════════════════════
# Governance Policy Evaluation (FM-174)
# ══════════════════════════════════════════════════════════════════


@router.post(
    "/projects/{project_id}/policies/evaluate",
    response_model=PolicyEvaluateResponse,
)
async def evaluate_project_policies(
    project_id: uuid.UUID,
    body: PolicyEvaluateRequest,
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Evaluate all applicable governance policies for a proposed action.

    Returns whether the action is allowed, with details of each
    policy evaluation. Requires PROJECT_VIEW permission.
    """
    await check_project_permission(db, project_id, current_user_id, Action.PROJECT_VIEW)

    result = await governance_engine_service.evaluate_policies(
        db,
        project_id=project_id,
        trigger_action=body.trigger_action,
        resource_type=body.resource_type,
        resource_id=body.resource_id,
        actor_id=current_user_id,
        context=body.context,
    )
    await db.commit()

    return PolicyEvaluateResponse(
        allowed=result["allowed"],
        evaluations=[
            PolicyEvaluationRead.model_validate(e) for e in result["evaluations"]
        ],
        blocked_by=result["blocked_by"],
        warnings=result["warnings"],
    )


@router.get(
    "/projects/{project_id}/policy-evaluations",
    response_model=PolicyEvaluationList,
)
async def list_project_policy_evaluations(
    project_id: uuid.UUID,
    policy_id: uuid.UUID | None = Query(None),
    result: PolicyEvalResult | None = Query(None),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """List policy evaluation records for a project.

    Requires PROJECT_VIEW permission.
    """
    await check_project_permission(db, project_id, current_user_id, Action.PROJECT_VIEW)

    items, total = await governance_engine_service.list_evaluations(
        db,
        project_id=project_id,
        policy_id=policy_id,
        result_filter=result,
        date_from=date_from,
        date_to=date_to,
        offset=offset,
        limit=limit,
    )

    return PolicyEvaluationList(
        items=[PolicyEvaluationRead.model_validate(i) for i in items],
        total=total,
    )


@router.get(
    "/workspaces/{workspace_id}/policy-evaluations",
    response_model=PolicyEvaluationList,
)
async def list_workspace_policy_evaluations(
    workspace_id: uuid.UUID,
    policy_id: uuid.UUID | None = Query(None),
    result: PolicyEvalResult | None = Query(None),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """List policy evaluations across a workspace.

    Requires WORKSPACE_VIEW_AUDIT permission.
    """
    await check_workspace_permission(
        db, workspace_id, current_user_id, Action.WORKSPACE_VIEW_AUDIT
    )

    items, total = await governance_engine_service.list_evaluations(
        db,
        workspace_id=workspace_id,
        policy_id=policy_id,
        result_filter=result,
        date_from=date_from,
        date_to=date_to,
        offset=offset,
        limit=limit,
    )

    return PolicyEvaluationList(
        items=[PolicyEvaluationRead.model_validate(i) for i in items],
        total=total,
    )


# ══════════════════════════════════════════════════════════════════
# Compliance Reports (FM-177)
# ══════════════════════════════════════════════════════════════════


@router.post(
    "/workspaces/{workspace_id}/compliance-reports",
    response_model=ComplianceReportRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_compliance_report(
    workspace_id: uuid.UUID,
    body: ComplianceReportCreate,
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Generate a compliance report.

    Requires WORKSPACE_VIEW_AUDIT permission.
    """
    await check_workspace_permission(
        db, workspace_id, current_user_id, Action.WORKSPACE_VIEW_AUDIT
    )

    report = await compliance_report_service.generate_report(
        db,
        workspace_id=workspace_id,
        report_type=body.report_type,
        title=body.title,
        description=body.description,
        generated_by=current_user_id,
        project_id=body.project_id,
        parameters=body.parameters,
    )
    await db.commit()

    return ComplianceReportRead.model_validate(report)


@router.get(
    "/workspaces/{workspace_id}/compliance-reports",
    response_model=ComplianceReportList,
)
async def list_compliance_reports(
    workspace_id: uuid.UUID,
    report_type: ComplianceReportType | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """List compliance reports for a workspace.

    Requires WORKSPACE_VIEW_AUDIT permission.
    """
    await check_workspace_permission(
        db, workspace_id, current_user_id, Action.WORKSPACE_VIEW_AUDIT
    )

    items, total = await compliance_report_service.list_reports(
        db,
        workspace_id,
        report_type=report_type,
        offset=offset,
        limit=limit,
    )

    return ComplianceReportList(
        items=[ComplianceReportRead.model_validate(i) for i in items],
        total=total,
    )


@router.get(
    "/workspaces/{workspace_id}/compliance-reports/{report_id}",
    response_model=ComplianceReportRead,
)
async def get_compliance_report(
    workspace_id: uuid.UUID,
    report_id: uuid.UUID,
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific compliance report.

    Requires WORKSPACE_VIEW_AUDIT permission.
    """
    await check_workspace_permission(
        db, workspace_id, current_user_id, Action.WORKSPACE_VIEW_AUDIT
    )

    report = await compliance_report_service.get_report(db, report_id)
    if report is None or report.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Report not found")

    return ComplianceReportRead.model_validate(report)


# ══════════════════════════════════════════════════════════════════
# IP Allowlist (FM-178)
# ══════════════════════════════════════════════════════════════════


@router.get(
    "/workspaces/{workspace_id}/ip-allowlist",
    response_model=IpAllowlistList,
)
async def list_ip_allowlist(
    workspace_id: uuid.UUID,
    active_only: bool = Query(False),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """List IP allowlist entries for a workspace.

    Requires WORKSPACE_MANAGE_GOVERNANCE permission.
    """
    await check_workspace_permission(
        db, workspace_id, current_user_id, Action.WORKSPACE_MANAGE_GOVERNANCE
    )

    items, total = await ip_allowlist_service.list_allowlist_entries(
        db,
        workspace_id,
        active_only=active_only,
        offset=offset,
        limit=limit,
    )

    return IpAllowlistList(
        items=[IpAllowlistRead.model_validate(i) for i in items],
        total=total,
    )


@router.post(
    "/workspaces/{workspace_id}/ip-allowlist",
    response_model=IpAllowlistRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_ip_allowlist_entry(
    workspace_id: uuid.UUID,
    body: IpAllowlistCreate,
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Add an IP allowlist entry.

    Requires WORKSPACE_MANAGE_GOVERNANCE permission.
    """
    await check_workspace_permission(
        db, workspace_id, current_user_id, Action.WORKSPACE_MANAGE_GOVERNANCE
    )

    try:
        entry = await ip_allowlist_service.add_allowlist_entry(
            db,
            workspace_id=workspace_id,
            cidr=body.cidr,
            description=body.description,
            is_active=body.is_active,
            created_by=current_user_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    await db.commit()
    return IpAllowlistRead.model_validate(entry)


@router.delete(
    "/workspaces/{workspace_id}/ip-allowlist/{entry_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_ip_allowlist_entry(
    workspace_id: uuid.UUID,
    entry_id: uuid.UUID,
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Remove an IP allowlist entry.

    Requires WORKSPACE_MANAGE_GOVERNANCE permission.
    """
    await check_workspace_permission(
        db, workspace_id, current_user_id, Action.WORKSPACE_MANAGE_GOVERNANCE
    )

    deleted = await ip_allowlist_service.remove_allowlist_entry(db, entry_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Entry not found")

    await db.commit()


@router.patch(
    "/workspaces/{workspace_id}/ip-allowlist/{entry_id}/toggle",
    response_model=IpAllowlistRead,
)
async def toggle_ip_allowlist_entry(
    workspace_id: uuid.UUID,
    entry_id: uuid.UUID,
    is_active: bool = Query(...),
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Activate or deactivate an IP allowlist entry.

    Requires WORKSPACE_MANAGE_GOVERNANCE permission.
    """
    await check_workspace_permission(
        db, workspace_id, current_user_id, Action.WORKSPACE_MANAGE_GOVERNANCE
    )

    entry = await ip_allowlist_service.toggle_allowlist_entry(db, entry_id, is_active)
    if entry is None:
        raise HTTPException(status_code=404, detail="Entry not found")

    await db.commit()
    return IpAllowlistRead.model_validate(entry)


# ══════════════════════════════════════════════════════════════════
# Retention Policies (FM-176)
# ══════════════════════════════════════════════════════════════════


@router.get(
    "/workspaces/{workspace_id}/retention-policies",
    response_model=RetentionPolicyList,
)
async def list_retention_policies(
    workspace_id: uuid.UUID,
    entity_type: str | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """List retention policies for a workspace.

    Requires WORKSPACE_MANAGE_GOVERNANCE permission.
    """
    await check_workspace_permission(
        db, workspace_id, current_user_id, Action.WORKSPACE_MANAGE_GOVERNANCE
    )

    items, total = await retention_policy_service.list_retention_policies(
        db,
        workspace_id,
        entity_type=entity_type,
        offset=offset,
        limit=limit,
    )

    return RetentionPolicyList(
        items=[RetentionPolicyRead.model_validate(i) for i in items],
        total=total,
    )


@router.post(
    "/workspaces/{workspace_id}/retention-policies",
    response_model=RetentionPolicyRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_retention_policy(
    workspace_id: uuid.UUID,
    body: RetentionPolicyCreate,
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Create a retention policy.

    Requires WORKSPACE_MANAGE_GOVERNANCE permission.
    """
    await check_workspace_permission(
        db, workspace_id, current_user_id, Action.WORKSPACE_MANAGE_GOVERNANCE
    )

    try:
        policy = await retention_policy_service.create_retention_policy(
            db,
            workspace_id=workspace_id,
            entity_type=body.entity_type,
            retention_days=body.retention_days,
            action=body.action,
            is_active=body.is_active,
            legal_hold=body.legal_hold,
            project_id=body.project_id,
            created_by=current_user_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    await db.commit()
    return RetentionPolicyRead.model_validate(policy)


@router.put(
    "/workspaces/{workspace_id}/retention-policies/{policy_id}",
    response_model=RetentionPolicyRead,
)
async def update_retention_policy(
    workspace_id: uuid.UUID,
    policy_id: uuid.UUID,
    body: RetentionPolicyUpdate,
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Update a retention policy.

    Requires WORKSPACE_MANAGE_GOVERNANCE permission.
    """
    await check_workspace_permission(
        db, workspace_id, current_user_id, Action.WORKSPACE_MANAGE_GOVERNANCE
    )

    policy = await retention_policy_service.update_retention_policy(
        db,
        policy_id,
        retention_days=body.retention_days,
        action=body.action,
        is_active=body.is_active,
        legal_hold=body.legal_hold,
    )
    if policy is None:
        raise HTTPException(status_code=404, detail="Retention policy not found")

    await db.commit()
    return RetentionPolicyRead.model_validate(policy)


@router.delete(
    "/workspaces/{workspace_id}/retention-policies/{policy_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_retention_policy(
    workspace_id: uuid.UUID,
    policy_id: uuid.UUID,
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Delete a retention policy.

    Requires WORKSPACE_MANAGE_GOVERNANCE permission.
    """
    await check_workspace_permission(
        db, workspace_id, current_user_id, Action.WORKSPACE_MANAGE_GOVERNANCE
    )

    deleted = await retention_policy_service.delete_retention_policy(db, policy_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Retention policy not found")

    await db.commit()


@router.post(
    "/workspaces/{workspace_id}/retention-policies/evaluate",
)
async def evaluate_retention_policies(
    workspace_id: uuid.UUID,
    dry_run: bool = Query(True),
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Evaluate retention policies and show what would be affected.

    Requires WORKSPACE_MANAGE_GOVERNANCE permission.
    """
    await check_workspace_permission(
        db, workspace_id, current_user_id, Action.WORKSPACE_MANAGE_GOVERNANCE
    )

    return await retention_policy_service.evaluate_retention(
        db, workspace_id, dry_run=dry_run
    )


# ══════════════════════════════════════════════════════════════════
# Workspace Governance Settings (FM-171)
# ══════════════════════════════════════════════════════════════════


@router.get(
    "/workspaces/{workspace_id}/governance-settings",
    response_model=GovernanceSettingsRead,
)
async def get_governance_settings(
    workspace_id: uuid.UUID,
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get workspace governance settings.

    Requires WORKSPACE_VIEW_AUDIT permission.
    """
    await check_workspace_permission(
        db, workspace_id, current_user_id, Action.WORKSPACE_VIEW_AUDIT
    )

    from app.models.workspace import Workspace

    ws = await db.get(Workspace, workspace_id)
    if ws is None:
        raise HTTPException(status_code=404, detail="Workspace not found")

    gov = ws.governance_settings or {}
    return GovernanceSettingsRead(**gov)


@router.put(
    "/workspaces/{workspace_id}/governance-settings",
    response_model=GovernanceSettingsRead,
)
async def update_governance_settings(
    workspace_id: uuid.UUID,
    body: GovernanceSettingsUpdate,
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Update workspace governance settings.

    Requires WORKSPACE_MANAGE_GOVERNANCE permission.
    """
    await check_workspace_permission(
        db, workspace_id, current_user_id, Action.WORKSPACE_MANAGE_GOVERNANCE
    )

    from app.models.workspace import Workspace

    ws = await db.get(Workspace, workspace_id)
    if ws is None:
        raise HTTPException(status_code=404, detail="Workspace not found")

    gov = dict(ws.governance_settings or {})
    updates = body.model_dump(exclude_unset=True)
    gov.update(updates)
    ws.governance_settings = gov
    db.add(ws)
    await db.commit()

    return GovernanceSettingsRead(**gov)


# ══════════════════════════════════════════════════════════════════
# Role Permissions Introspection (FM-172)
# ══════════════════════════════════════════════════════════════════


@router.get(
    "/workspaces/{workspace_id}/my-permissions",
    response_model=PermissionsIntrospectionResponse,
)
async def get_my_permissions(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID | None = Query(None),
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get the current user's roles and computed permissions.

    Returns all actions the user can perform in the given
    workspace (and optionally project).
    """
    perms = await get_user_permissions(
        db,
        workspace_id=workspace_id,
        user_id=current_user_id,
        project_id=project_id,
    )
    return PermissionsIntrospectionResponse(**perms)


# ── FM-172: Custom Role Management ───────────────────────────────


class _CustomRoleCreate(BaseModel):
    name: str
    scope: str = "project"
    description: str | None = None
    permissions: list[str]


class _CustomRoleUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    permissions: list[str] | None = None
    is_active: bool | None = None


@router.post("/workspaces/{workspace_id}/custom-roles", status_code=201)
async def create_role(
    workspace_id: uuid.UUID,
    body: _CustomRoleCreate,
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Create a custom role with specific permissions (FM-172)."""
    await check_workspace_permission(
        db, workspace_id, current_user_id, Action.WORKSPACE_MANAGE_MEMBERS
    )
    try:
        role = await create_custom_role(
            db,
            workspace_id=workspace_id,
            name=body.name,
            scope=body.scope,
            description=body.description,
            permissions=body.permissions,
            created_by=current_user_id,
        )
        await db.commit()
        return {
            "id": str(role.id),
            "name": role.name,
            "scope": role.scope,
            "description": role.description,
            "permissions": role.permissions,
            "is_active": role.is_active,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/workspaces/{workspace_id}/custom-roles")
async def list_roles(
    workspace_id: uuid.UUID,
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """List all custom roles in a workspace (FM-172)."""
    # H-7: verify caller is a workspace member before exposing role configs
    await check_workspace_permission(
        db, workspace_id, current_user_id, Action.WORKSPACE_VIEW
    )
    roles = await list_custom_roles(db, workspace_id)
    return {
        "items": [
            {
                "id": str(r.id),
                "name": r.name,
                "scope": r.scope,
                "description": r.description,
                "permissions": r.permissions,
                "is_active": r.is_active,
            }
            for r in roles
        ],
        "total": len(roles),
    }


@router.patch("/custom-roles/{role_id}")
async def update_role(
    role_id: uuid.UUID,
    body: _CustomRoleUpdate,
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Update a custom role (FM-172)."""
    # C-2: resolve workspace from role and check WORKSPACE_MANAGE_MEMBERS
    from app.services.authz_service import get_custom_role as _get_role

    existing = await _get_role(db, role_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Custom role not found")
    await check_workspace_permission(
        db, existing.workspace_id, current_user_id, Action.WORKSPACE_MANAGE_MEMBERS
    )
    try:
        role = await update_custom_role(
            db,
            role_id,
            name=body.name,
            description=body.description,
            permissions=body.permissions,
            is_active=body.is_active,
        )
        await db.commit()
        return {
            "id": str(role.id),
            "name": role.name,
            "scope": role.scope,
            "description": role.description,
            "permissions": role.permissions,
            "is_active": role.is_active,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ══════════════════════════════════════════════════════════════════
# SSO Configuration (FM-175)
# ══════════════════════════════════════════════════════════════════


@router.get(
    "/workspaces/{workspace_id}/sso-configurations",
    response_model=SSOConfigurationList,
)
async def list_sso_configurations(
    workspace_id: uuid.UUID,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """List SSO configurations for a workspace.

    Requires WORKSPACE_MANAGE_GOVERNANCE permission.
    """
    await check_workspace_permission(
        db, workspace_id, current_user_id, Action.WORKSPACE_MANAGE_GOVERNANCE
    )

    items, total = await sso_configuration_service.list_sso_configs(
        db, workspace_id, offset=offset, limit=limit
    )

    return SSOConfigurationList(
        items=[SSOConfigurationRead.model_validate(i) for i in items],
        total=total,
    )


@router.post(
    "/workspaces/{workspace_id}/sso-configurations",
    response_model=SSOConfigurationRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_sso_configuration(
    workspace_id: uuid.UUID,
    body: SSOConfigurationCreate,
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Create an SSO provider configuration.

    NOTE: This stores IdP connection parameters. Live SAML/OIDC
    authentication flows require external libraries and are not
    yet implemented.

    Requires WORKSPACE_MANAGE_GOVERNANCE permission.
    """
    await check_workspace_permission(
        db, workspace_id, current_user_id, Action.WORKSPACE_MANAGE_GOVERNANCE
    )

    config = await sso_configuration_service.create_sso_config(
        db,
        workspace_id=workspace_id,
        provider_type=body.provider_type,
        display_name=body.display_name,
        metadata_url=body.metadata_url,
        client_id=body.client_id,
        issuer_url=body.issuer_url,
        is_active=body.is_active,
        auto_provision=body.auto_provision,
        created_by=current_user_id,
    )
    await db.commit()

    return SSOConfigurationRead.model_validate(config)


@router.delete(
    "/workspaces/{workspace_id}/sso-configurations/{config_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_sso_configuration(
    workspace_id: uuid.UUID,
    config_id: uuid.UUID,
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Delete an SSO configuration.

    Requires WORKSPACE_MANAGE_GOVERNANCE permission.
    """
    await check_workspace_permission(
        db, workspace_id, current_user_id, Action.WORKSPACE_MANAGE_GOVERNANCE
    )

    deleted = await sso_configuration_service.delete_sso_config(db, config_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="SSO configuration not found")

    await db.commit()


# ---------------------------------------------------------------------------
# FM-175: SSO validation, enforcement, and OIDC login initiation
# ---------------------------------------------------------------------------


@router.get("/workspaces/{workspace_id}/sso-configurations/{config_id}/validate")
async def validate_sso_configuration(
    workspace_id: uuid.UUID,
    config_id: uuid.UUID,
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Validate an SSO configuration has all required fields (FM-175)."""
    await check_workspace_permission(
        db, workspace_id, current_user_id, Action.WORKSPACE_VIEW
    )
    config = await sso_configuration_service.get_sso_config(db, config_id)
    if config is None:
        raise HTTPException(status_code=404, detail="SSO configuration not found")

    errors = sso_configuration_service.validate_sso_config(config)
    jit = sso_configuration_service.check_jit_provisioning_ready(config)
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "jit_provisioning": jit,
    }


@router.get("/workspaces/{workspace_id}/sso-enforcement")
async def check_sso_enforcement(
    workspace_id: uuid.UUID,
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Check SSO enforcement status for a workspace (FM-175)."""
    await check_workspace_permission(
        db, workspace_id, current_user_id, Action.WORKSPACE_VIEW
    )
    return await sso_configuration_service.check_sso_enforcement(db, workspace_id)


@router.get("/workspaces/{workspace_id}/sso-login-url")
async def get_sso_login_url(
    workspace_id: uuid.UUID,
    redirect_uri: str,
    _current_user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get the SSO login redirect URL for a workspace (FM-175).

    For OIDC providers, returns the authorization URL.
    For SAML providers, returns the IdP SSO URL.
    """
    # H-5: require auth; validate redirect_uri to prevent open-redirect OAuth abuse
    if not redirect_uri.startswith("/"):
        from urllib.parse import urlparse

        parsed = urlparse(redirect_uri)
        from app.core.config import settings

        allowed_origins = {
            urlparse(o.strip()).netloc
            for o in settings.cors_origins.split(",")
            if o.strip()
        }
        if parsed.netloc not in allowed_origins:
            raise HTTPException(
                status_code=400,
                detail="Invalid redirect URI — must be a relative path or match an allowed origin",
            )
    config = await sso_configuration_service.get_active_sso_for_workspace(
        db,
        workspace_id,
    )
    if config is None:
        raise HTTPException(status_code=404, detail="No active SSO configuration")

    ptype = config.provider_type
    if isinstance(ptype, str):
        ptype = ptype.lower()

    if ptype in ("oidc", "SSOProviderType.OIDC"):
        url = sso_configuration_service.build_oidc_authorize_url(
            config,
            redirect_uri=redirect_uri,
        )
        if url is None:
            raise HTTPException(
                status_code=422,
                detail="OIDC config incomplete (missing client_id or issuer_url)",
            )
        return {"provider_type": "oidc", "login_url": url}

    # SAML: return the IdP SSO URL directly
    if config.sso_url:
        return {"provider_type": "saml", "login_url": config.sso_url}

    raise HTTPException(
        status_code=422,
        detail="SSO configuration incomplete (missing sso_url for SAML)",
    )
