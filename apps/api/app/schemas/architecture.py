"""Architecture schemas - request/response models.

FM-081 to FM-090: Pydantic models for architecture graph, drift,
rules, impact analysis, and design doc synthesis.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.architecture import (
    NodeType,
    EdgeType,
    SourceType,
    NodeStatus,
    DriftSeverity,
    DriftStatus,
    RuleCategory,
    RuleResultStatus,
    ImpactSeverity,
)


# ── FM-081: Graph Foundation ─────────────────────────────────────


class ArchitectureNodeCreate(BaseModel):
    node_type: NodeType
    key: str = Field(..., min_length=1, max_length=500)
    name: str = Field(..., min_length=1, max_length=500)
    path: str | None = None
    language: str | None = None
    metadata_: dict | None = None
    source_type: SourceType = SourceType.INFERRED
    status: NodeStatus = NodeStatus.ACTIVE
    repo_id: uuid.UUID | None = None


class ArchitectureNodeRead(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID | None
    project_id: uuid.UUID
    repo_id: uuid.UUID | None
    node_type: NodeType
    key: str
    name: str
    path: str | None
    language: str | None
    metadata_: dict | None = Field(None, alias="metadata_")
    source_type: SourceType
    status: NodeStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}


class ArchitectureNodeList(BaseModel):
    items: list[ArchitectureNodeRead]
    total: int


class ArchitectureNodeUpdate(BaseModel):
    name: str | None = None
    path: str | None = None
    language: str | None = None
    metadata_: dict | None = None
    source_type: SourceType | None = None
    status: NodeStatus | None = None


class ArchitectureEdgeCreate(BaseModel):
    from_node_id: uuid.UUID
    to_node_id: uuid.UUID
    edge_type: EdgeType
    confidence_score: float = Field(1.0, ge=0.0, le=1.0)
    metadata_: dict | None = None
    source_type: SourceType = SourceType.INFERRED


class ArchitectureEdgeRead(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID | None
    project_id: uuid.UUID
    from_node_id: uuid.UUID
    to_node_id: uuid.UUID
    edge_type: EdgeType
    confidence_score: float
    metadata_: dict | None = Field(None, alias="metadata_")
    source_type: SourceType
    created_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}


class ArchitectureEdgeList(BaseModel):
    items: list[ArchitectureEdgeRead]
    total: int


class ArchitectureSnapshotRead(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID | None
    project_id: uuid.UUID
    name: str
    source: str | None
    summary: dict | None
    node_count: int
    edge_count: int
    generated_at: datetime

    model_config = {"from_attributes": True}


class ArchitectureSnapshotList(BaseModel):
    items: list[ArchitectureSnapshotRead]
    total: int


class ArchitectureGraphRead(BaseModel):
    """Full graph with nodes and edges."""

    project_id: uuid.UUID
    nodes: list[ArchitectureNodeRead]
    edges: list[ArchitectureEdgeRead]
    node_count: int
    edge_count: int


class NeighborRead(BaseModel):
    """A node's neighbors (incoming and outgoing edges)."""

    node: ArchitectureNodeRead
    incoming: list[ArchitectureEdgeRead]
    outgoing: list[ArchitectureEdgeRead]


# ── FM-082: Topology Mapping ────────────────────────────────────


class TopologyMapRequest(BaseModel):
    scan_python: bool = True
    scan_typescript: bool = True
    scan_directories: bool = True
    base_path: str | None = None


class TopologySummary(BaseModel):
    project_id: uuid.UUID
    components_found: int
    edges_found: int
    layers: list[str]
    isolated_nodes: list[str]
    high_centrality_nodes: list[str]


# ── FM-083: Drift Detection ─────────────────────────────────────


class ArchitectureDriftRead(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    drift_type: str
    severity: DriftSeverity
    title: str
    description: str
    source_snapshot_id: uuid.UUID | None
    comparison_target: str | None
    status: DriftStatus
    metadata_: dict | None = Field(None, alias="metadata_")
    detected_at: datetime
    resolved_at: datetime | None

    model_config = {"from_attributes": True, "populate_by_name": True}


class ArchitectureDriftList(BaseModel):
    items: list[ArchitectureDriftRead]
    total: int


# ── FM-084: Architecture Rules ──────────────────────────────────


class ArchitectureRuleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=500)
    description: str | None = None
    category: RuleCategory
    rule_config: dict
    enabled: bool = True
    severity: DriftSeverity = DriftSeverity.MEDIUM


class ArchitectureRuleRead(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID | None
    name: str
    description: str | None
    category: RuleCategory
    rule_config: dict
    enabled: bool
    severity: DriftSeverity
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ArchitectureRuleList(BaseModel):
    items: list[ArchitectureRuleRead]
    total: int


class ArchitectureRuleResultRead(BaseModel):
    id: uuid.UUID
    rule_id: uuid.UUID
    project_id: uuid.UUID
    status: RuleResultStatus
    message: str
    details: dict | None
    violating_node_ids: list | None
    violating_edge_ids: list | None
    evaluated_at: datetime

    model_config = {"from_attributes": True}


class ArchitectureRuleResultList(BaseModel):
    items: list[ArchitectureRuleResultRead]
    total: int


# ── FM-086: Design Doc Synthesis ────────────────────────────────


class DesignDocRead(BaseModel):
    project_id: uuid.UUID | str
    title: str
    content: str
    sections: list[str]
    generated_at: datetime | str


class DesignDocList(BaseModel):
    items: list[DesignDocRead]
    total: int


# ── FM-087: Change Impact Analysis ──────────────────────────────


class ImpactAnalysisRequest(BaseModel):
    node_id: uuid.UUID | None = None
    file_path: str | None = None
    module_key: str | None = None


class ChangeImpactAssessmentRead(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    target_node_id: uuid.UUID | None
    target_path: str | None
    target_key: str | None
    severity: ImpactSeverity
    blast_radius: int
    impacted_nodes: list | None
    impacted_services: list | None
    rationale: str
    confidence_score: float
    metadata_: dict | None = Field(None, alias="metadata_")
    created_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}


# ── FM-088: Refactor Recommendations ────────────────────────────


class RefactorRecommendation(BaseModel):
    recommendation_type: str
    title: str
    description: str
    severity: DriftSeverity
    confidence: float
    affected_nodes: list[str]
    rationale: str


class RefactorRecommendationList(BaseModel):
    items: list[RefactorRecommendation]
    total: int


# ── FM-090: Structural Health Score ─────────────────────────────


class HealthScoreDetails(BaseModel):
    total_nodes: int
    total_edges: int
    declared_nodes: int
    open_drifts: int
    total_rule_evaluations: int
    rule_violations: int
    isolated_nodes: int


class StructuralHealthScore(BaseModel):
    project_id: uuid.UUID | str
    overall_score: float = Field(..., ge=0, le=100)
    component_coverage: float
    drift_penalty: float
    rule_compliance: float
    isolation_ratio: float
    details: HealthScoreDetails
