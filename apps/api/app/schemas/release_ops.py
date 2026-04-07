"""FM-131–137: Release operations Pydantic schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.release_ops import (
    EnvironmentTier,
    GateStatus,
    ReleaseStatus,
)


# ---------------------------------------------------------------------------
# FM-131: Release Package schemas
# ---------------------------------------------------------------------------


class ReleasePackageCreate(BaseModel):
    version: str = Field(..., min_length=1, max_length=100)
    summary: str = Field(..., min_length=1)
    target_environment_id: uuid.UUID | None = None
    artifact_manifest: dict | None = None
    changelog: dict | None = None
    created_by: str | None = Field(None, max_length=100)


class ReleasePackageUpdate(BaseModel):
    version: str | None = Field(None, max_length=100)
    summary: str | None = None
    status: ReleaseStatus | None = None
    target_environment_id: uuid.UUID | None = None
    artifact_manifest: dict | None = None
    changelog: dict | None = None
    rollback_metadata: dict | None = None


class ReleasePackageRead(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    run_id: uuid.UUID
    version: str
    status: ReleaseStatus
    summary: str
    artifact_manifest: dict | None
    changelog: dict | None
    confidence_snapshot: dict | None
    rollback_metadata: dict | None
    target_environment_id: uuid.UUID | None
    created_by: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ReleasePackageList(BaseModel):
    items: list[ReleasePackageRead]
    total: int


# ---------------------------------------------------------------------------
# FM-132: Deployment Environment schemas
# ---------------------------------------------------------------------------


class EnvironmentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    tier: EnvironmentTier = EnvironmentTier.DEVELOPMENT
    description: str | None = None
    config: dict | None = None
    required_gates: dict | None = None
    promotion_target_id: uuid.UUID | None = None


class EnvironmentUpdate(BaseModel):
    name: str | None = Field(None, max_length=200)
    tier: EnvironmentTier | None = None
    description: str | None = None
    config: dict | None = None
    required_gates: dict | None = None
    promotion_target_id: uuid.UUID | None = None
    is_active: bool | None = None


class EnvironmentRead(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    name: str
    tier: EnvironmentTier
    description: str | None
    config: dict | None
    required_gates: dict | None
    promotion_target_id: uuid.UUID | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EnvironmentList(BaseModel):
    items: list[EnvironmentRead]
    total: int


# ---------------------------------------------------------------------------
# FM-134: Release Gate Result schemas
# ---------------------------------------------------------------------------


class GateResultRead(BaseModel):
    id: uuid.UUID
    release_package_id: uuid.UUID
    gate_name: str
    gate_status: GateStatus
    detail: str | None
    metadata_: dict | None = Field(None, alias="metadata_")
    evaluated_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}


class GateResultList(BaseModel):
    items: list[GateResultRead]
    total: int
