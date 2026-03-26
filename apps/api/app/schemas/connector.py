"""Connector schemas — Pydantic models for connector API."""

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.connector import ConnectorStatus


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
