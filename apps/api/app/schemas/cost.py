"""Cost tracking schemas — response models for cost and token usage.

FM-047: Pydantic models for cost records and summaries.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel


class CostRecordRead(BaseModel):
    id: uuid.UUID
    model_name: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float
    project_id: uuid.UUID | None
    run_id: uuid.UUID | None
    task_id: uuid.UUID | None
    caller: str
    created_at: datetime

    model_config = {"from_attributes": True}


class CostRecordList(BaseModel):
    items: list[CostRecordRead]
    total: int
