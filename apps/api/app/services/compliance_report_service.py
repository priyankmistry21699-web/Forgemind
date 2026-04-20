"""Compliance report service — generate audit/compliance bundles.

FM-177: Pre-built report templates (access review, change management,
approval audit, policy compliance) with JSON content generation.
"""

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select, func as sa_func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enterprise_governance import (
    AuditLog,
    ComplianceReport,
    ComplianceReportStatus,
    ComplianceReportType,
    GovernancePolicyEvaluation,
)
from app.models.approval_request import ApprovalRequest
from app.models.membership import WorkspaceMember, ProjectMember
from app.models.project import Project

logger = logging.getLogger(__name__)


async def generate_report(
    db: AsyncSession,
    *,
    workspace_id: uuid.UUID,
    report_type: ComplianceReportType,
    title: str,
    description: str | None = None,
    generated_by: uuid.UUID,
    project_id: uuid.UUID | None = None,
    parameters: dict | None = None,
) -> ComplianceReport:
    """Generate a compliance report of the specified type."""
    report = ComplianceReport(
        workspace_id=workspace_id,
        report_type=report_type,
        title=title,
        description=description,
        generated_by=generated_by,
        project_id=project_id,
        parameters=parameters,
        status=ComplianceReportStatus.GENERATING,
    )
    db.add(report)
    await db.flush()

    try:
        content = await _generate_report_content(
            db,
            workspace_id=workspace_id,
            report_type=report_type,
            project_id=project_id,
            parameters=parameters or {},
        )
        report.content = content
        report.status = ComplianceReportStatus.READY
    except Exception as exc:
        logger.error("compliance_report: generation failed: %s", exc)
        report.content = {"error": str(exc)}
        report.status = ComplianceReportStatus.FAILED

    await db.flush()
    return report


async def _generate_report_content(
    db: AsyncSession,
    *,
    workspace_id: uuid.UUID,
    report_type: ComplianceReportType,
    project_id: uuid.UUID | None,
    parameters: dict,
) -> dict:
    """Generate report content based on type."""
    generated_at = datetime.now(timezone.utc).isoformat()

    if report_type == ComplianceReportType.ACCESS_REVIEW:
        return await _generate_access_review(db, workspace_id, project_id, generated_at)
    elif report_type == ComplianceReportType.CHANGE_MANAGEMENT:
        return await _generate_change_management(
            db, workspace_id, project_id, generated_at
        )
    elif report_type == ComplianceReportType.APPROVAL_AUDIT:
        return await _generate_approval_audit(
            db, workspace_id, project_id, generated_at
        )
    elif report_type == ComplianceReportType.POLICY_COMPLIANCE:
        return await _generate_policy_compliance(
            db, workspace_id, project_id, generated_at
        )
    elif report_type == ComplianceReportType.FULL_GOVERNANCE:
        return await _generate_full_governance(
            db, workspace_id, project_id, generated_at
        )
    else:
        return {"error": f"Unknown report type: {report_type}"}


async def _generate_access_review(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    project_id: uuid.UUID | None,
    generated_at: str,
) -> dict:
    """Access review: list all members and their roles."""
    # Workspace members
    ws_q = select(WorkspaceMember).where(WorkspaceMember.workspace_id == workspace_id)
    ws_members = (await db.execute(ws_q)).scalars().all()

    ws_data = [
        {
            "user_id": str(m.user_id),
            "role": m.role.value,
            "joined_at": m.created_at.isoformat() if m.created_at else None,
        }
        for m in ws_members
    ]

    # Project members for projects in this workspace
    proj_conditions = [Project.workspace_id == workspace_id]
    if project_id:
        proj_conditions.append(Project.id == project_id)

    proj_q = select(Project.id, Project.name).where(and_(*proj_conditions))
    projects = (await db.execute(proj_q)).all()

    project_access = []
    for pid, pname in projects:
        pm_q = select(ProjectMember).where(ProjectMember.project_id == pid)
        pm_members = (await db.execute(pm_q)).scalars().all()
        project_access.append(
            {
                "project_id": str(pid),
                "project_name": pname,
                "members": [
                    {
                        "user_id": str(m.user_id),
                        "role": m.role.value,
                        "is_approver": m.is_approver,
                        "is_reviewer": m.is_reviewer,
                    }
                    for m in pm_members
                ],
            }
        )

    return {
        "report_type": "access_review",
        "generated_at": generated_at,
        "workspace_id": str(workspace_id),
        "workspace_members": ws_data,
        "workspace_member_count": len(ws_data),
        "project_access": project_access,
        "project_count": len(project_access),
    }


async def _generate_change_management(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    project_id: uuid.UUID | None,
    generated_at: str,
) -> dict:
    """Change management: audit log summary of state-changing actions."""
    conditions = [AuditLog.workspace_id == workspace_id]
    if project_id:
        conditions.append(AuditLog.project_id == project_id)

    total_q = select(sa_func.count()).select_from(AuditLog).where(and_(*conditions))
    total = (await db.execute(total_q)).scalar() or 0

    # By action type
    action_q = (
        select(AuditLog.action, sa_func.count())
        .where(and_(*conditions))
        .group_by(AuditLog.action)
        .order_by(sa_func.count().desc())
        .limit(20)
    )
    action_rows = (await db.execute(action_q)).all()

    # By outcome
    outcome_q = (
        select(AuditLog.outcome, sa_func.count())
        .where(and_(*conditions))
        .group_by(AuditLog.outcome)
    )
    outcome_rows = (await db.execute(outcome_q)).all()

    return {
        "report_type": "change_management",
        "generated_at": generated_at,
        "workspace_id": str(workspace_id),
        "total_changes": total,
        "by_action": {row[0]: row[1] for row in action_rows},
        "by_outcome": {row[0].value: row[1] for row in outcome_rows},
    }


async def _generate_approval_audit(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    project_id: uuid.UUID | None,
    generated_at: str,
) -> dict:
    """Approval audit: summary of approval requests and decisions."""
    # Get project IDs in workspace
    if project_id:
        project_ids = [project_id]
    else:
        proj_q = select(Project.id).where(Project.workspace_id == workspace_id)
        project_ids = [row[0] for row in (await db.execute(proj_q)).all()]

    if not project_ids:
        return {
            "report_type": "approval_audit",
            "generated_at": generated_at,
            "workspace_id": str(workspace_id),
            "total_approvals": 0,
            "by_status": {},
        }

    conditions = [ApprovalRequest.project_id.in_(project_ids)]

    total_q = (
        select(sa_func.count()).select_from(ApprovalRequest).where(and_(*conditions))
    )
    total = (await db.execute(total_q)).scalar() or 0

    status_q = (
        select(ApprovalRequest.status, sa_func.count())
        .where(and_(*conditions))
        .group_by(ApprovalRequest.status)
    )
    status_rows = (await db.execute(status_q)).all()

    return {
        "report_type": "approval_audit",
        "generated_at": generated_at,
        "workspace_id": str(workspace_id),
        "total_approvals": total,
        "by_status": {row[0].value: row[1] for row in status_rows},
        "project_count": len(project_ids),
    }


async def _generate_policy_compliance(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    project_id: uuid.UUID | None,
    generated_at: str,
) -> dict:
    """Policy compliance: summary of policy evaluations and pass/fail rates."""
    # Get project IDs in workspace
    if project_id:
        project_ids = [project_id]
    else:
        proj_q = select(Project.id).where(Project.workspace_id == workspace_id)
        project_ids = [row[0] for row in (await db.execute(proj_q)).all()]

    if not project_ids:
        return {
            "report_type": "policy_compliance",
            "generated_at": generated_at,
            "workspace_id": str(workspace_id),
            "total_evaluations": 0,
            "by_result": {},
            "enforcement_count": 0,
        }

    conditions = [GovernancePolicyEvaluation.project_id.in_(project_ids)]

    total_q = (
        select(sa_func.count())
        .select_from(GovernancePolicyEvaluation)
        .where(and_(*conditions))
    )
    total = (await db.execute(total_q)).scalar() or 0

    result_q = (
        select(GovernancePolicyEvaluation.result, sa_func.count())
        .where(and_(*conditions))
        .group_by(GovernancePolicyEvaluation.result)
    )
    result_rows = (await db.execute(result_q)).all()

    enforced_q = (
        select(sa_func.count())
        .select_from(GovernancePolicyEvaluation)
        .where(
            and_(
                *conditions,
                GovernancePolicyEvaluation.enforced == True,  # noqa: E712
            )
        )
    )
    enforced = (await db.execute(enforced_q)).scalar() or 0

    return {
        "report_type": "policy_compliance",
        "generated_at": generated_at,
        "workspace_id": str(workspace_id),
        "total_evaluations": total,
        "by_result": {row[0].value: row[1] for row in result_rows},
        "enforcement_count": enforced,
        "project_count": len(project_ids),
    }


async def _generate_full_governance(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    project_id: uuid.UUID | None,
    generated_at: str,
) -> dict:
    """Full governance report: combines all report types."""
    access = await _generate_access_review(db, workspace_id, project_id, generated_at)
    changes = await _generate_change_management(
        db, workspace_id, project_id, generated_at
    )
    approvals = await _generate_approval_audit(
        db, workspace_id, project_id, generated_at
    )
    policies = await _generate_policy_compliance(
        db, workspace_id, project_id, generated_at
    )

    return {
        "report_type": "full_governance",
        "generated_at": generated_at,
        "workspace_id": str(workspace_id),
        "sections": {
            "access_review": access,
            "change_management": changes,
            "approval_audit": approvals,
            "policy_compliance": policies,
        },
    }


async def list_reports(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    *,
    report_type: ComplianceReportType | None = None,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[ComplianceReport], int]:
    """List compliance reports for a workspace."""
    conditions = [ComplianceReport.workspace_id == workspace_id]
    if report_type:
        conditions.append(ComplianceReport.report_type == report_type)

    where_clause = and_(*conditions)

    count_q = select(sa_func.count()).select_from(ComplianceReport).where(where_clause)
    total = (await db.execute(count_q)).scalar() or 0

    items_q = (
        select(ComplianceReport)
        .where(where_clause)
        .order_by(ComplianceReport.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    rows = (await db.execute(items_q)).scalars().all()

    return list(rows), total


async def get_report(
    db: AsyncSession,
    report_id: uuid.UUID,
) -> ComplianceReport | None:
    """Get a single compliance report by ID."""
    return await db.get(ComplianceReport, report_id)
