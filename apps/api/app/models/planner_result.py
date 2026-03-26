import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class PlannerResult(Base):
    __tablename__ = "planner_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("runs.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    overview: Mapped[str | None] = mapped_column(Text, nullable=True)
    architecture_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommended_stack: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    assumptions: Mapped[list | None] = mapped_column(JSON, nullable=True)
    next_steps: Mapped[list | None] = mapped_column(JSON, nullable=True)

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
    run: Mapped["Run"] = relationship(back_populates="planner_result")  # noqa: F821

    def __repr__(self) -> str:
        return f"<PlannerResult run_id={self.run_id}>"
