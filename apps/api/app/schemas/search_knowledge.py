"""Schemas for FM-161 through FM-169 — Search, Knowledge, Conventions, Recommendations."""

import uuid
from datetime import datetime
from pydantic import BaseModel, Field

from app.models.search_knowledge import (
    SearchEntityType,
    ConventionCategory,
    ConventionEnforcement,
    RecommendationType,
)


# ── FM-161 / FM-165: Search ──────────────────────────────────────


class SearchResult(BaseModel):
    entity_type: SearchEntityType
    entity_id: uuid.UUID
    project_id: uuid.UUID | None = None
    run_id: uuid.UUID | None = None
    title: str
    snippet: str
    entity_status: str | None = None
    score: float = 0.0
    author_id: uuid.UUID | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class SearchResponse(BaseModel):
    query: str
    total: int
    items: list[SearchResult]
    scope: str | None = None
    filters: dict | None = None
    facets: dict | None = None


# ── FM-162: Semantic / Similar Search ────────────────────────────


class SimilarResult(BaseModel):
    entity_type: SearchEntityType
    entity_id: uuid.UUID
    project_id: uuid.UUID | None = None
    title: str
    snippet: str
    similarity_score: float = 0.0

    model_config = {"from_attributes": True}


class SimilarSearchResponse(BaseModel):
    source_entity_type: str
    source_entity_id: uuid.UUID
    items: list[SimilarResult]
    total: int


# ── FM-167: Conventions ──────────────────────────────────────────


class ConventionCreate(BaseModel):
    category: ConventionCategory
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    rule_text: str = Field(..., min_length=1)
    enforcement_level: ConventionEnforcement = ConventionEnforcement.ADVISORY
    active: bool = True


class ConventionUpdate(BaseModel):
    category: ConventionCategory | None = None
    name: str | None = None
    description: str | None = None
    rule_text: str | None = None
    enforcement_level: ConventionEnforcement | None = None
    active: bool | None = None


class ConventionRead(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID | None = None
    category: ConventionCategory
    name: str
    description: str | None = None
    rule_text: str
    enforcement_level: ConventionEnforcement
    active: bool
    author_id: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ConventionList(BaseModel):
    items: list[ConventionRead]
    total: int


class ComplianceViolation(BaseModel):
    convention_id: uuid.UUID
    convention_name: str
    enforcement_level: ConventionEnforcement
    rule_text: str
    violation_detail: str


class ComplianceCheckResult(BaseModel):
    run_id: uuid.UUID
    checked_count: int
    violations: list[ComplianceViolation]
    passed: bool


# ── FM-168: Artifact Versioning ──────────────────────────────────


class ArtifactVersionEntry(BaseModel):
    id: uuid.UUID
    version: int
    version_tag: str | None = None
    title: str
    artifact_type: str
    created_by: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ArtifactVersionHistory(BaseModel):
    artifact_id: uuid.UUID
    versions: list[ArtifactVersionEntry]
    total: int


class ArtifactDiff(BaseModel):
    artifact_id: uuid.UUID
    version_a: int
    version_b: int
    diff_lines: list[str]
    additions: int
    deletions: int


class ArtifactVersionTag(BaseModel):
    version_tag: str = Field(..., min_length=1, max_length=100)


# ── FM-169: Recommendations ──────────────────────────────────────


class RecommendationRead(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    rec_type: RecommendationType
    title: str
    body: str
    entity_type: str | None = None
    entity_id: uuid.UUID | None = None
    priority: int
    dismissed: bool
    feedback: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class RecommendationList(BaseModel):
    items: list[RecommendationRead]
    total: int


class RecommendationDismiss(BaseModel):
    feedback: str | None = Field(None, pattern="^(helpful|not_helpful|later)$")


# ── FM-166: Run Comparison ───────────────────────────────────────


class RunComparisonSummary(BaseModel):
    run_a_id: uuid.UUID
    run_b_id: uuid.UUID
    run_a_status: str
    run_b_status: str
    run_a_task_count: int
    run_b_task_count: int
    common_task_types: list[str]
    divergent_outcomes: list[dict]
    summary: str


# ── FM-163: Knowledge Search ─────────────────────────────────────


class KnowledgeSearchResponse(BaseModel):
    query: str
    items: list[dict]
    total: int


# ── FM-164: Template Marketplace ─────────────────────────────────


class TemplateMarketplaceEntry(BaseModel):
    id: uuid.UUID
    slug: str
    name: str
    description: str | None = None
    category: str
    is_builtin: bool
    has_knowledge: bool
    has_views: bool
    version: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class TemplateMarketplaceList(BaseModel):
    items: list[TemplateMarketplaceEntry]
    total: int
