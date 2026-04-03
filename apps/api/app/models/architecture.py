"""Architecture graph models - nodes, edges, and snapshots.

FM-081: Foundational data model for representing software architecture
as a structured graph of components, dependencies, and relationships.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import String, Text, DateTime, Enum, ForeignKey, Float, Integer, func
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base


# ── Enums ────────────────────────────────────────────────────────

class NodeType(str, enum.Enum):
    WORKSPACE = "workspace"
    PROJECT = "project"
    REPOSITORY = "repository"
    PACKAGE = "package"
    MODULE = "module"
    SERVICE = "service"
    COMPONENT = "component"
    API = "api"
    INTERFACE = "interface"
    DATASTORE = "datastore"
    RESOURCE = "resource"
    EXTERNAL_DEPENDENCY = "external_dependency"


class EdgeType(str, enum.Enum):
    DEPENDS_ON = "depends_on"
    CALLS = "calls"
    OWNS = "owns"
    READS = "reads"
    WRITES = "writes"
    EXPOSES = "exposes"
    IMPORTS = "imports"
    DEPLOYS_TO = "deploys_to"
    EMITS_EVENT_TO = "emits_event_to"
    CONSUMES_EVENT_FROM = "consumes_event_from"


class SourceType(str, enum.Enum):
    INFERRED = "inferred"
    DECLARED = "declared"
    IMPORTED = "imported"


class NodeStatus(str, enum.Enum):
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    REMOVED = "removed"


class DriftSeverity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DriftStatus(str, enum.Enum):
    OPEN = "open"
    RESOLVED = "resolved"
    IGNORED = "ignored"


class RuleCategory(str, enum.Enum):
    IMPORT = "import"
    LAYER = "layer"
    OWNERSHIP = "ownership"
    DEPENDENCY = "dependency"
    BOUNDARY = "boundary"


class RuleResultStatus(str, enum.Enum):
    PASS = "pass"
    VIOLATION = "violation"


class ImpactSeverity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ── Models ───────────────────────────────────────────────────────

class ArchitectureNode(Base):
    __tablename__ = "architecture_nodes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    workspace_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    repo_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("repo_connections.id", ondelete="SET NULL"),
        nullable=True,
    )

    node_type: Mapped[NodeType] = mapped_column(
        Enum(NodeType, name="arch_node_type"), nullable=False, index=True
    )
    key: Mapped[str] = mapped_column(String(500), nullable=False)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    language: Mapped[str | None] = mapped_column(String(50), nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)
    source_type: Mapped[SourceType] = mapped_column(
        Enum(SourceType, name="arch_source_type"), nullable=False,
        default=SourceType.INFERRED,
    )
    status: Mapped[NodeStatus] = mapped_column(
        Enum(NodeStatus, name="arch_node_status"), nullable=False,
        default=NodeStatus.ACTIVE, index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
        onupdate=func.now(), nullable=False,
    )

    def __repr__(self) -> str:
        return f"<ArchitectureNode {self.name} ({self.node_type.value})>"


class ArchitectureEdge(Base):
    __tablename__ = "architecture_edges"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    workspace_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    from_node_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("architecture_nodes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    to_node_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("architecture_nodes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    edge_type: Mapped[EdgeType] = mapped_column(
        Enum(EdgeType, name="arch_edge_type"), nullable=False, index=True
    )
    confidence_score: Mapped[float] = mapped_column(
        Float, default=1.0, nullable=False
    )
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)
    source_type: Mapped[SourceType] = mapped_column(
        Enum(SourceType, name="arch_edge_source_type"), nullable=False,
        default=SourceType.INFERRED,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<ArchitectureEdge {self.edge_type.value}: {self.from_node_id} -> {self.to_node_id}>"


class ArchitectureSnapshot(Base):
    __tablename__ = "architecture_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    workspace_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="SET NULL"),
        nullable=True,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(String(500), nullable=False)
    source: Mapped[str | None] = mapped_column(String(200), nullable=True)
    summary: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    node_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    edge_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    snapshot_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<ArchitectureSnapshot {self.name}>"


# ── FM-083: Drift Detection ─────────────────────────────────────

class ArchitectureDrift(Base):
    __tablename__ = "architecture_drifts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    drift_type: Mapped[str] = mapped_column(String(200), nullable=False)
    severity: Mapped[DriftSeverity] = mapped_column(
        Enum(DriftSeverity, name="drift_severity"), nullable=False, index=True,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    source_snapshot_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("architecture_snapshots.id", ondelete="SET NULL"),
        nullable=True,
    )
    comparison_target: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[DriftStatus] = mapped_column(
        Enum(DriftStatus, name="drift_status"), nullable=False,
        default=DriftStatus.OPEN, index=True,
    )
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)

    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self) -> str:
        return f"<ArchitectureDrift {self.title} ({self.severity.value})>"


# ── FM-084: Architecture Rules ───────────────────────────────────

class ArchitectureRule(Base):
    __tablename__ = "architecture_rules"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[RuleCategory] = mapped_column(
        Enum(RuleCategory, name="arch_rule_category"), nullable=False, index=True,
    )
    rule_config: Mapped[dict] = mapped_column(JSON, nullable=False)
    enabled: Mapped[bool] = mapped_column(default=True, nullable=False)
    severity: Mapped[DriftSeverity] = mapped_column(
        Enum(DriftSeverity, name="arch_rule_severity"), nullable=False,
        default=DriftSeverity.MEDIUM,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
        onupdate=func.now(), nullable=False,
    )

    def __repr__(self) -> str:
        return f"<ArchitectureRule {self.name} ({self.category.value})>"


class ArchitectureRuleResult(Base):
    __tablename__ = "architecture_rule_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    rule_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("architecture_rules.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    status: Mapped[RuleResultStatus] = mapped_column(
        Enum(RuleResultStatus, name="arch_rule_result_status"), nullable=False,
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    violating_node_ids: Mapped[list | None] = mapped_column(JSON, nullable=True)
    violating_edge_ids: Mapped[list | None] = mapped_column(JSON, nullable=True)

    evaluated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<ArchitectureRuleResult {self.status.value} for rule {self.rule_id}>"


# ── FM-087: Change Impact Assessment ────────────────────────────

class ChangeImpactAssessment(Base):
    __tablename__ = "change_impact_assessments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    target_node_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("architecture_nodes.id", ondelete="SET NULL"),
        nullable=True,
    )
    target_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    target_key: Mapped[str | None] = mapped_column(String(500), nullable=True)

    severity: Mapped[ImpactSeverity] = mapped_column(
        Enum(ImpactSeverity, name="impact_severity"), nullable=False,
    )
    blast_radius: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    impacted_nodes: Mapped[list | None] = mapped_column(JSON, nullable=True)
    impacted_services: Mapped[list | None] = mapped_column(JSON, nullable=True)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<ChangeImpactAssessment {self.severity.value} radius={self.blast_radius}>"
