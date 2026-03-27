"""Project knowledge schemas — request/response models.

FM-048: Pydantic models for project knowledge base.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.project_knowledge import KnowledgeType


class ProjectKnowledgeRead(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    source_run_id: uuid.UUID | None
    source_task_id: uuid.UUID | None
    knowledge_type: KnowledgeType
    title: str
    content: str
    tags: list | None
    metadata_: dict | None = Field(None, alias="metadata_")
    relevance_score: float
    usage_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}


class ProjectKnowledgeList(BaseModel):
    items: list[ProjectKnowledgeRead]
    total: int


class ProjectKnowledgeCreate(BaseModel):
    knowledge_type: KnowledgeType
    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1)
    tags: list[str] | None = None
    metadata_: dict | None = None
    source_run_id: uuid.UUID | None = None
    source_task_id: uuid.UUID | None = None


class KnowledgeExtractionResult(BaseModel):
    """Result of automated knowledge extraction from a run."""
    run_id: uuid.UUID
    extracted_count: int
    items: list[ProjectKnowledgeRead]


class KnowledgeContext(BaseModel):
    """Assembled knowledge context for agent enrichment."""
    project_id: uuid.UUID
    total_entries: int
    context_text: str
    entries: list[ProjectKnowledgeRead]
