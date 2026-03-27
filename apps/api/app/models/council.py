"""CouncilSession and CouncilVote models — multi-agent decision engine.

FM-047A: Models for council-based group decision making where multiple
agents debate, vote, and reach consensus on key decisions.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import String, Text, DateTime, Enum, ForeignKey, Float, Integer, func
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class CouncilStatus(str, enum.Enum):
    CONVENED = "convened"          # Council has been assembled
    DELIBERATING = "deliberating"  # Agents are providing opinions
    DECIDED = "decided"            # Consensus/majority reached
    DEADLOCKED = "deadlocked"     # No consensus could be reached
    ESCALATED = "escalated"       # Escalated to human review


class DecisionMethod(str, enum.Enum):
    CONSENSUS = "consensus"        # All agents must agree
    MAJORITY = "majority"          # >50% agreement
    SUPERMAJORITY = "supermajority" # >=2/3 agreement
    WEIGHTED = "weighted"          # Trust-score-weighted vote


class VoteDecision(str, enum.Enum):
    APPROVE = "approve"
    REJECT = "reject"
    ABSTAIN = "abstain"
    MODIFY = "modify"             # Approve with modifications


class CouncilSession(Base):
    __tablename__ = "council_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Context
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("runs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    task_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Council details
    topic: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    context: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    status: Mapped[CouncilStatus] = mapped_column(
        Enum(CouncilStatus, name="council_status"),
        default=CouncilStatus.CONVENED,
        nullable=False,
        index=True,
    )
    decision_method: Mapped[DecisionMethod] = mapped_column(
        Enum(DecisionMethod, name="decision_method"),
        default=DecisionMethod.MAJORITY,
        nullable=False,
    )

    # Result
    final_decision: Mapped[str | None] = mapped_column(String(50), nullable=True)
    decision_rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    decision_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Timing
    convened_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    decided_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    votes: Mapped[list["CouncilVote"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<CouncilSession {self.topic[:50]} ({self.status.value})>"


class CouncilVote(Base):
    __tablename__ = "council_votes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("council_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    agent_slug: Mapped[str] = mapped_column(String(50), nullable=False)
    decision: Mapped[VoteDecision] = mapped_column(
        Enum(VoteDecision, name="vote_decision"),
        nullable=False,
    )
    reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    suggested_modifications: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    session: Mapped["CouncilSession"] = relationship(back_populates="votes")

    def __repr__(self) -> str:
        return f"<CouncilVote {self.agent_slug} → {self.decision.value}>"
