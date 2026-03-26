import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class PromptIntakeRequest(BaseModel):
    """User submits a natural-language prompt describing what they want built."""

    prompt: str = Field(
        ..., min_length=10, max_length=5000, description="Natural-language project description"
    )
    project_name: str | None = Field(
        default=None, max_length=255, description="Optional explicit project name"
    )


class PromptIntakeResponse(BaseModel):
    """Returned after the planner processes a prompt."""

    project_id: uuid.UUID
    run_id: uuid.UUID
    tasks_created: int
    message: str
    created_at: datetime

    model_config = {"from_attributes": True}
