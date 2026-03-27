"""Connector schemas — Pydantic models for connector API."""

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.connector import ConnectorStatus
from app.models.project_connector_link import ConnectorReadiness, ConnectorPriority


class ConnectorRead(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    description: str | None
    connector_type: str
    status: ConnectorStatus
    capabilities: list[str] | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ConnectorList(BaseModel):
    items: list[ConnectorRead]
    total: int


class ConnectorRecommendation(BaseModel):
    """A recommended connector for a project."""
    connector_slug: str
    connector_name: str
    reason: str
    priority: str  # "required" | "recommended" | "optional"
    configured: bool


# ── FM-041: Connector Readiness Schemas ──────────────────────────

class ProjectConnectorLinkCreate(BaseModel):
    """Create a connector link for a project."""
    connector_slug: str
    priority: ConnectorPriority = ConnectorPriority.RECOMMENDED
    config_snapshot: dict | None = None


class ProjectConnectorLinkRead(BaseModel):
    """Read a project-connector link with readiness state."""
    id: uuid.UUID
    project_id: uuid.UUID
    connector_id: uuid.UUID
    connector_slug: str
    connector_name: str
    priority: ConnectorPriority
    readiness: ConnectorReadiness
    config_snapshot: dict | None
    blocker_reason: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectConnectorReadinessUpdate(BaseModel):
    """Update the readiness state of a project-connector link."""
    readiness: ConnectorReadiness
    blocker_reason: str | None = None
    config_snapshot: dict | None = None


class ProjectReadinessSummary(BaseModel):
    """Readiness summary for all connectors in a project."""
    links: list[ProjectConnectorLinkRead]
    total: int
    ready_count: int
    configured_count: int
    blocked_count: int
    missing_count: int
    all_required_ready: bool


class RunConnectorBlocker(BaseModel):
    """A connector that is blocking a run from proceeding."""
    connector_slug: str
    connector_name: str
    priority: str
    readiness: str
    blocker_reason: str | None
