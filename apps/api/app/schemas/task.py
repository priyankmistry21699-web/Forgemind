import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.task import TaskStatus


# ---------- Response schemas ----------
class TaskRead(BaseModel):
    id: uuid.UUID
    title: str
    description: str | None
    task_type: str
    status: TaskStatus
    order_index: int
    depends_on: list[uuid.UUID] | None
    parent_id: uuid.UUID | None
    run_id: uuid.UUID
    assigned_agent_slug: str | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TaskList(BaseModel):
    items: list[TaskRead]
    total: int


# ---------- Request / action schemas ----------
class TaskStatusUpdate(BaseModel):
    status: TaskStatus


class ReadyTasksResponse(BaseModel):
    """Tasks that have all dependencies satisfied and are ready to execute."""

    items: list[TaskRead]
    total: int


class TaskClaimRequest(BaseModel):
    agent_slug: str


class TaskCompleteRequest(BaseModel):
    artifact_title: str | None = None
    artifact_content: str | None = None
    artifact_type: str | None = None


class TaskFailRequest(BaseModel):
    error_message: str
