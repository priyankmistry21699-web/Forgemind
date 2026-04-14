"""Search, knowledge, conventions & recommendations models — FM-161 through FM-169.

New tables:
- search_index: Full-text search index across all entity types
- conventions: Organizational conventions for agent prompt injection
- recommendations: Smart action recommendations for projects
"""

import uuid
import enum
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Boolean,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSON as PG_JSON

from app.db.base_class import Base


# ── FM-161: Search Index ─────────────────────────────────────────


class SearchEntityType(str, enum.Enum):
    """Types of entities that can be indexed for search."""

    TASK = "task"
    ARTIFACT = "artifact"
    COMMENT = "comment"
    RUN = "run"
    PROJECT = "project"
    KNOWLEDGE = "knowledge"
    ANNOTATION = "annotation"
    APPROVAL = "approval"
    RELEASE_PACKAGE = "release_package"
    SPEC = "spec"


class SearchIndex(Base):
    """Full-text search index entry.

    Each row represents one indexed entity with pre-computed searchable text.
    """

    __tablename__ = "search_index"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_type = Column(
        Enum(SearchEntityType, name="searchentitytype"), nullable=False, index=True
    )
    entity_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    project_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    run_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("runs.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Searchable text fields
    title = Column(String(500), nullable=False, default="")
    body = Column(Text, nullable=False, default="")
    entity_status = Column(String(50), nullable=True)
    entity_meta = Column(PG_JSON, nullable=True)

    # Author / owner
    author_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("ix_search_index_entity", "entity_type", "entity_id", unique=True),
    )


# ── FM-167: Conventions ─────────────────────────────────────────


class ConventionCategory(str, enum.Enum):
    NAMING = "naming"
    ARCHITECTURE = "architecture"
    QUALITY = "quality"
    SECURITY = "security"
    DOCUMENTATION = "documentation"


class ConventionEnforcement(str, enum.Enum):
    ADVISORY = "advisory"
    RECOMMENDED = "recommended"
    REQUIRED = "required"


class Convention(Base):
    """Organizational convention for agent prompt injection and compliance checks."""

    __tablename__ = "conventions"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    category = Column(
        Enum(ConventionCategory, name="conventioncategory"), nullable=False
    )
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    rule_text = Column(Text, nullable=False)
    enforcement_level = Column(
        Enum(ConventionEnforcement, name="conventionenforcement"),
        nullable=False,
        default=ConventionEnforcement.ADVISORY,
    )
    active = Column(Boolean, nullable=False, default=True)
    author_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


# ── FM-169: Recommendations ──────────────────────────────────────


class RecommendationType(str, enum.Enum):
    KNOWLEDGE_GAP = "knowledge_gap"
    STALE_RUN = "stale_run"
    SIMILAR_PROJECT = "similar_project"
    CONVENTION_VIOLATION = "convention_violation"
    MISSING_APPROVAL = "missing_approval"
    REUSABLE_PATTERN = "reusable_pattern"
    TECH_DEBT = "tech_debt"


class Recommendation(Base):
    """Smart recommendation generated from project state analysis."""

    __tablename__ = "recommendations"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    rec_type = Column(
        Enum(RecommendationType, name="recommendationtype"), nullable=False
    )
    title = Column(String(500), nullable=False)
    body = Column(Text, nullable=False)
    entity_type = Column(String(50), nullable=True)
    entity_id = Column(PG_UUID(as_uuid=True), nullable=True)
    priority = Column(Integer, nullable=False, default=5)
    dismissed = Column(Boolean, nullable=False, default=False)
    feedback = Column(String(50), nullable=True)  # helpful / not_helpful / later

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
