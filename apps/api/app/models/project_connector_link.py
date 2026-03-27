"""ProjectConnectorLink model — per-project connector readiness tracking."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import String, Text, DateTime, Enum, ForeignKey, func, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class ConnectorReadiness(str, enum.Enum):
    MISSING = "missing"          # Connector needed but no credentials configured
    CONFIGURED = "configured"    # Credentials/config provided but not verified
    BLOCKED = "blocked"          # Configured but health check failing or expired
    READY = "ready"              # Configured and verified working


class ConnectorPriority(str, enum.Enum):
    REQUIRED = "required"
    RECOMMENDED = "recommended"
    OPTIONAL = "optional"


class ProjectConnectorLink(Base):
    __tablename__ = "project_connector_links"

    __table_args__ = (
        UniqueConstraint("project_id", "connector_id", name="uq_project_connector"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    connector_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("connectors.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    priority: Mapped[ConnectorPriority] = mapped_column(
        Enum(ConnectorPriority, name="connector_priority"),
        default=ConnectorPriority.RECOMMENDED,
        nullable=False,
    )
    readiness: Mapped[ConnectorReadiness] = mapped_column(
        Enum(ConnectorReadiness, name="connector_readiness"),
        default=ConnectorReadiness.MISSING,
        nullable=False,
    )
    config_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    blocker_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

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
    connector: Mapped["Connector"] = relationship()  # noqa: F821
    project: Mapped["Project"] = relationship()  # noqa: F821

    def __repr__(self) -> str:
        return (
            f"<ProjectConnectorLink project={self.project_id} "
            f"connector={self.connector_id} readiness={self.readiness.value}>"
        )
