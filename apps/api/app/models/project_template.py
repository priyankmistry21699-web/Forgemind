"""FM-114: Project Template — reusable project presets for bootstrapping."""

import uuid
from datetime import datetime

from sqlalchemy import String, Text, Boolean, DateTime, Integer, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base


class ProjectTemplate(Base):
    """Reusable project template carrying config, constitution, phase profiles, etc."""

    __tablename__ = "project_templates"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    slug: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False, default="general")

    # Template configuration payloads (JSON)
    constitution_template: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    default_governance_config: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    default_phase_profiles: Mapped[list | None] = mapped_column(JSON, nullable=True)
    suggested_task_types: Mapped[list | None] = mapped_column(JSON, nullable=True)
    spec_defaults: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    plan_defaults: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    is_builtin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # FM-164: Versioning
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    parent_template_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("project_templates.id", ondelete="SET NULL"),
        nullable=True,
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
        return f"<ProjectTemplate {self.slug}>"
