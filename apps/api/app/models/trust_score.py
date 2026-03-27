"""TrustScore model — per-entity trust and risk assessment records.

FM-050: Stores computed trust scores and risk assessments for tasks,
artifacts, and runs with heuristic-based scoring.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import String, Text, DateTime, Enum, ForeignKey, Float, Integer, func
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base


class RiskLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EntityType(str, enum.Enum):
    TASK = "task"
    ARTIFACT = "artifact"
    RUN = "run"


class TrustScore(Base):
    __tablename__ = "trust_scores"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    entity_type: Mapped[EntityType] = mapped_column(
        Enum(EntityType, name="trust_entity_type"),
        nullable=False,
        index=True,
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )

    # Scores: 0.0 (no trust) to 1.0 (full trust)
    trust_score: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(
        Float, default=0.5, nullable=False
    )  # How confident we are in the score

    risk_level: Mapped[RiskLevel] = mapped_column(
        Enum(RiskLevel, name="risk_level"),
        nullable=False,
        index=True,
    )

    # Breakdown of score factors
    factors: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Optional context
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("runs.id", ondelete="CASCADE"),
        nullable=True,
    )

    assessed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"<TrustScore {self.entity_type.value}:{str(self.entity_id)[:8]} "
            f"trust={self.trust_score:.2f} risk={self.risk_level.value}>"
        )
