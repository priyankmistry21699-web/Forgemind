"""ProjectKnowledge model — cross-run learnings and project knowledge base.

FM-048: Stores extracted knowledge from completed runs — patterns,
decisions, lessons learned, and reusable context for future runs.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import String, Text, DateTime, Enum, ForeignKey, Float, Integer, func
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base


class KnowledgeType(str, enum.Enum):
    PATTERN = "pattern"                # Reusable design pattern discovered
    DECISION = "decision"              # Key decision made during a run
    LESSON_LEARNED = "lesson_learned"  # Failure/success insight
    DEPENDENCY = "dependency"          # Discovered dependency/requirement
    BEST_PRACTICE = "best_practice"    # Verified best practice
    ARCHITECTURE = "architecture"      # Architecture insight
    CONSTRAINT = "constraint"          # Known constraint or limitation


class ProjectKnowledge(Base):
    __tablename__ = "project_knowledge"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Source — which run produced this knowledge
    source_run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("runs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    source_task_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Knowledge content
    knowledge_type: Mapped[KnowledgeType] = mapped_column(
        Enum(KnowledgeType, name="knowledge_type"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tags: Mapped[list | None] = mapped_column(JSON, nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)

    # Relevance scoring
    relevance_score: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<ProjectKnowledge {self.title[:50]} ({self.knowledge_type.value})>"
