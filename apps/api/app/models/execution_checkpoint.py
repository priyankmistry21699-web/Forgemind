"""FM-121: Execution Checkpoint model — meaningful run progress state captures.

Checkpoints represent stable, reviewable progress snapshots for a run,
including completion summaries, validation/approval state, and architecture
context. They enable safe resume, review packaging, and delivery confidence.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import String, Text, DateTime, Enum, ForeignKey, Integer, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class CheckpointType(str, enum.Enum):
    MANUAL = "manual"
    AUTO_PHASE = "auto_phase"
    PRE_APPROVAL = "pre_approval"
    PRE_DELIVERY = "pre_delivery"
    POST_VALIDATION = "post_validation"


class ExecutionCheckpoint(Base):
    """A meaningful progress snapshot for a run."""

    __tablename__ = "execution_checkpoints"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    task_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="SET NULL"),
        nullable=True,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    checkpoint_type: Mapped[CheckpointType] = mapped_column(
        Enum(CheckpointType, name="checkpoint_type"),
        default=CheckpointType.MANUAL,
        nullable=False,
        index=True,
    )
    summary: Mapped[str] = mapped_column(Text, nullable=False)

    # Structured snapshot payloads
    status_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    artifact_refs: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    validation_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    approval_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    architecture_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)

    # Sequence within a run's checkpoint history
    sequence_number: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    created_by: Mapped[str | None] = mapped_column(String(100), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    run: Mapped["Run"] = relationship()  # noqa: F821
    project: Mapped["Project"] = relationship()  # noqa: F821

    def __repr__(self) -> str:
        return f"<ExecutionCheckpoint {self.checkpoint_type.value} seq={self.sequence_number}>"
