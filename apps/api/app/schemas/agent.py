import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.agent import AgentStatus


class AgentRead(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    description: str | None
    status: AgentStatus
    capabilities: list[str] | None
    supported_task_types: list[str] | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AgentList(BaseModel):
    items: list[AgentRead]
    total: int
