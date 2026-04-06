"""FM-111: Phase Agent Profile — maps workflow phases to preferred agents per project."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Text, Integer, DateTime, Enum, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class WorkflowPhase(str, enum.Enum):
    """Constrained set of lifecycle phases that can be assigned to agents."""

    SPECIFY = "specify"
    PLAN = "plan"
    TASKS = "tasks"
    IMPLEMENT = "implement"
    REVIEW = "review"
    VALIDATE = "validate"


class PhaseAgentProfile(Base):
    """Persists per-project agent assignments for each workflow phase.

    A project can have at most one agent assigned per phase.
    """

    __tablename__ = "phase_agent_profiles"
    __table_args__ = (UniqueConstraint("project_id", "phase", name="uq_project_phase"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    phase: Mapped[WorkflowPhase] = mapped_column(
        Enum(WorkflowPhase, name="workflow_phase"),
        nullable=False,
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
    )
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_default: Mapped[bool] = mapped_column(default=False, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

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
    project: Mapped["Project"] = relationship(overlaps="phase_profiles")  # noqa: F821
    agent: Mapped["Agent"] = relationship()  # noqa: F821

    def __repr__(self) -> str:
        return f"<PhaseAgentProfile project={self.project_id} phase={self.phase.value}>"
