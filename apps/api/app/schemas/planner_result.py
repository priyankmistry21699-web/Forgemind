import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, field_validator


class PlannerResultRead(BaseModel):
    id: uuid.UUID
    run_id: uuid.UUID
    overview: str | None
    architecture_summary: str | None
    recommended_stack: dict[str, str] | None
    assumptions: list[str] | None
    next_steps: list[str] | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @field_validator("recommended_stack", mode="before")
    @classmethod
    def coerce_stack_values(cls, v: Any) -> dict[str, str] | None:
        if v is None:
            return None
        if not isinstance(v, dict):
            return None
        return {str(k): str(val) for k, val in v.items() if k is not None}

    @field_validator("assumptions", "next_steps", mode="before")
    @classmethod
    def coerce_string_lists(cls, v: Any) -> list[str] | None:
        if v is None:
            return None
        if not isinstance(v, list):
            return None
        return [str(item) for item in v if item is not None]
