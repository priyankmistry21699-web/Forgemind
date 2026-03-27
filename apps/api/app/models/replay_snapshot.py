"""ReplaySnapshot model — captures every agent execution for replay.

FM-046: Stores input/output snapshots for each task execution,
enabling deterministic replay, comparison, and trace inspection.
"""

import uuid
from datetime import datetime

from sqlalchemy import String, Text, DateTime, Float, Integer, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base


class ReplaySnapshot(Base):
    __tablename__ = "replay_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Context linkage
    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Execution snapshot
    agent_slug: Mapped[str] = mapped_column(String(50), nullable=False)
    input_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    prompt_snapshot: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_used: Mapped[str | None] = mapped_column(String(100), nullable=True)
    temperature: Mapped[float | None] = mapped_column(Float, nullable=True)
    output_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Metrics
    tokens_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Replay identification
    replay_hash: Mapped[str | None] = mapped_column(
        String(64), nullable=True, index=True
    )
    is_replay: Mapped[bool] = mapped_column(
        default=False, nullable=False
    )
    original_snapshot_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("replay_snapshots.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Sequence within a run trace
    sequence_number: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<ReplaySnapshot task_id={self.task_id} seq={self.sequence_number}>"
