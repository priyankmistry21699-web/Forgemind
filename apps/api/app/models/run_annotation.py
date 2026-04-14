"""RunAnnotation model — collaborative annotations on run timelines.

FM-146: Collaborative Run Annotations.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Text, DateTime, Enum, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base


class AnnotationType(str, enum.Enum):
    NOTE = "note"
    WARNING = "warning"
    DECISION = "decision"
    QUESTION = "question"


class RunAnnotation(Base):
    __tablename__ = "run_annotations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    annotation_type: Mapped[AnnotationType] = mapped_column(
        Enum(AnnotationType, name="annotation_type"),
        nullable=False,
        index=True,
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
    pinned_event_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
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

    def __repr__(self) -> str:
        return f"<RunAnnotation {self.annotation_type.value} on run={self.run_id}>"
