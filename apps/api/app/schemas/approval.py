"""Approval schemas — request and response models for approval workflow."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.approval_request import ApprovalStatus


# ---------- Response schemas ----------
class ApprovalRead(BaseModel):
    id: uuid.UUID
    status: ApprovalStatus
    title: str
    description: str | None
    project_id: uuid.UUID
    run_id: uuid.UUID | None
    task_id: uuid.UUID | None
    artifact_id: uuid.UUID | None
    decided_by: str | None
    decision_comment: str | None
    decided_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ApprovalList(BaseModel):
    items: list[ApprovalRead]
    total: int


# ---------- Request schemas ----------
class ApprovalCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: str | None = None
    project_id: uuid.UUID
    run_id: uuid.UUID | None = None
    task_id: uuid.UUID | None = None
    artifact_id: uuid.UUID | None = None


class ApprovalDecision(BaseModel):
    status: ApprovalStatus
    decided_by: str | None = Field(None, max_length=100)
    decision_comment: str | None = None
