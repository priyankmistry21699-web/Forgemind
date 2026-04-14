"""Enterprise governance schemas — request/response models for Wave 13.

FM-171–180: Audit logs, policy evaluations, compliance reports,
IP allowlisting, and retention policies.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enterprise_governance import (
    AuditActorType,
    AuditOutcome,
    PolicyEvalResult,
    ComplianceReportType,
    ComplianceReportStatus,
    RetentionAction,
)


# ── Audit Log (FM-173) ──────────────────────────────────────────


class AuditLogRead(BaseModel):
    id: uuid.UUID
    actor_id: uuid.UUID | None
    actor_type: AuditActorType
    action: str
    resource_type: str
    resource_id: uuid.UUID | None
    workspace_id: uuid.UUID | None
    project_id: uuid.UUID | None
    details: dict | None
    ip_address: str | None
    user_agent: str | None
    outcome: AuditOutcome
    created_at: datetime

    model_config = {"from_attributes": True}


class AuditLogList(BaseModel):
    items: list[AuditLogRead]
    total: int


class AuditLogCreate(BaseModel):
    """Internal schema for creating audit entries programmatically."""

    action: str = Field(..., min_length=1, max_length=200)
    resource_type: str = Field(..., min_length=1, max_length=100)
    resource_id: uuid.UUID | None = None
    workspace_id: uuid.UUID | None = None
    project_id: uuid.UUID | None = None
    details: dict | None = None
    outcome: AuditOutcome = AuditOutcome.SUCCESS


class AuditLogFilter(BaseModel):
    """Query filters for audit log listing."""

    action: str | None = None
    resource_type: str | None = None
    resource_id: uuid.UUID | None = None
    actor_id: uuid.UUID | None = None
    outcome: AuditOutcome | None = None
    project_id: uuid.UUID | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None


# ── Policy Evaluation (FM-174) ──────────────────────────────────


class PolicyEvaluationRead(BaseModel):
    id: uuid.UUID
    policy_id: uuid.UUID
    trigger_action: str
    resource_type: str
    resource_id: uuid.UUID | None
    project_id: uuid.UUID | None
    actor_id: uuid.UUID | None
    result: PolicyEvalResult
    details: dict | None
    enforced: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class PolicyEvaluationList(BaseModel):
    items: list[PolicyEvaluationRead]
    total: int


class PolicyEvaluateRequest(BaseModel):
    """Request to evaluate governance policies for a proposed action."""

    trigger_action: str = Field(..., min_length=1, max_length=200)
    resource_type: str = Field(..., min_length=1, max_length=100)
    resource_id: uuid.UUID | None = None
    context: dict | None = None


class PolicyEvaluateResponse(BaseModel):
    """Aggregated result of evaluating all applicable policies."""

    allowed: bool
    evaluations: list[PolicyEvaluationRead]
    blocked_by: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


# ── Compliance Report (FM-177) ──────────────────────────────────


class ComplianceReportRead(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    report_type: ComplianceReportType
    title: str
    description: str | None
    parameters: dict | None
    content: dict | None
    generated_by: uuid.UUID
    project_id: uuid.UUID | None
    status: ComplianceReportStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class ComplianceReportList(BaseModel):
    items: list[ComplianceReportRead]
    total: int


class ComplianceReportCreate(BaseModel):
    report_type: ComplianceReportType
    title: str = Field(..., min_length=1, max_length=300)
    description: str | None = None
    project_id: uuid.UUID | None = None
    parameters: dict | None = None


# ── IP Allowlist (FM-178) ───────────────────────────────────────


class IpAllowlistRead(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    cidr: str
    description: str | None
    is_active: bool
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class IpAllowlistList(BaseModel):
    items: list[IpAllowlistRead]
    total: int


class IpAllowlistCreate(BaseModel):
    cidr: str = Field(..., min_length=1, max_length=50, pattern=r"^[\d./]+$")
    description: str | None = None
    is_active: bool = True


# ── Retention Policy (FM-176) ───────────────────────────────────


class RetentionPolicyRead(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    entity_type: str
    retention_days: int
    action: RetentionAction
    is_active: bool
    legal_hold: bool
    project_id: uuid.UUID | None
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RetentionPolicyList(BaseModel):
    items: list[RetentionPolicyRead]
    total: int


class RetentionPolicyCreate(BaseModel):
    entity_type: str = Field(..., min_length=1, max_length=100)
    retention_days: int = Field(..., gt=0, le=36500)
    action: RetentionAction = RetentionAction.ARCHIVE
    is_active: bool = True
    legal_hold: bool = False
    project_id: uuid.UUID | None = None


class RetentionPolicyUpdate(BaseModel):
    retention_days: int | None = Field(None, gt=0, le=36500)
    action: RetentionAction | None = None
    is_active: bool | None = None
    legal_hold: bool | None = None
