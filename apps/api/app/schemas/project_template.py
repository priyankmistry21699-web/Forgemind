"""FM-114: Project Template schemas."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ProjectTemplateCreate(BaseModel):
    slug: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-z0-9\-]+$")
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    category: str = Field(default="general", max_length=50)
    constitution_template: dict[str, Any] | None = None
    default_governance_config: dict[str, Any] | None = None
    default_phase_profiles: list[dict[str, Any]] | None = None
    suggested_task_types: list[str] | None = None
    spec_defaults: dict[str, Any] | None = None
    plan_defaults: dict[str, Any] | None = None


class ProjectTemplateUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    category: str | None = Field(default=None, max_length=50)
    constitution_template: dict[str, Any] | None = None
    default_governance_config: dict[str, Any] | None = None
    default_phase_profiles: list[dict[str, Any]] | None = None
    suggested_task_types: list[str] | None = None
    spec_defaults: dict[str, Any] | None = None
    plan_defaults: dict[str, Any] | None = None
    is_active: bool | None = None


class ProjectTemplateRead(BaseModel):
    id: uuid.UUID
    slug: str
    name: str
    description: str | None
    category: str
    constitution_template: dict[str, Any] | None
    default_governance_config: dict[str, Any] | None
    default_phase_profiles: list[dict[str, Any]] | None
    suggested_task_types: list[str] | None
    spec_defaults: dict[str, Any] | None
    plan_defaults: dict[str, Any] | None
    is_builtin: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectTemplateList(BaseModel):
    items: list[ProjectTemplateRead]
    total: int
