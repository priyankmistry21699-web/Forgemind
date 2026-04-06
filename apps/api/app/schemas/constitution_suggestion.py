"""FM-117: Constitution Suggestion schemas."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.constitution_suggestion import SuggestionStatus


class ConstitutionSuggestionRead(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    title: str
    rationale: str
    suggested_text: str
    category: str
    status: SuggestionStatus
    source_metadata: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ConstitutionSuggestionList(BaseModel):
    items: list[ConstitutionSuggestionRead]
    total: int


class ConstitutionSuggestionResolve(BaseModel):
    """Body to accept or reject a suggestion."""

    action: str = Field(..., pattern=r"^(accept|reject)$")
