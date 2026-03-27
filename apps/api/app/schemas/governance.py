"""Governance policy schemas — request/response models.

FM-048: Pydantic models for governance policies.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.governance_policy import PolicyTrigger, PolicyAction


class GovernancePolicyRead(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    trigger: PolicyTrigger
    action: PolicyAction
    rules: dict | None
    project_id: uuid.UUID | None
    enabled: bool
    priority: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class GovernancePolicyList(BaseModel):
    items: list[GovernancePolicyRead]
    total: int


class GovernancePolicyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    trigger: PolicyTrigger
    action: PolicyAction
    rules: dict | None = None
    project_id: uuid.UUID | None = None
    enabled: bool = True
    priority: int = 0


class GovernancePolicyUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    trigger: PolicyTrigger | None = None
    action: PolicyAction | None = None
    rules: dict | None = None
    enabled: bool | None = None
    priority: int | None = None


class PolicyEvaluation(BaseModel):
    """Result of evaluating governance policies."""
    task_type: str
    project_id: uuid.UUID
    action: PolicyAction
    matched_policy: str | None = None
