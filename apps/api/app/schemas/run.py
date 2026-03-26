import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.run import RunStatus


class RunRead(BaseModel):
    id: uuid.UUID
    run_number: int
    status: RunStatus
    trigger: str
    project_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RunList(BaseModel):
    items: list[RunRead]
    total: int
