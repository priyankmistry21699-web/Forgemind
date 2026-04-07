"""FM-131/132: Release package and environment models.

Defines the ORM models for release operations:
- ReleasePackage — a versioned bundle of artifacts for deployment
- DeploymentEnvironment — a named release target with configuration
- ReleaseGateResult — individual gate check results for a release
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class ReleaseStatus(str, enum.Enum):
    DRAFT = "draft"
    READY = "ready"
    GATED = "gated"
    APPROVED = "approved"
    DEPLOYED = "deployed"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"


class EnvironmentTier(str, enum.Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    CANARY = "canary"


class GateStatus(str, enum.Enum):
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    PENDING = "pending"


# ---------------------------------------------------------------------------
# FM-131: Release Package
# ---------------------------------------------------------------------------


class ReleasePackage(Base):
    __tablename__ = "release_packages"

    id: Mapped[uuid.UUID] = mapped_column(
        default=uuid.uuid4, primary_key=True, index=True
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("runs.id", ondelete="CASCADE"), nullable=False
    )
    version: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[ReleaseStatus] = mapped_column(
        Enum(ReleaseStatus), default=ReleaseStatus.DRAFT, nullable=False
    )
    summary: Mapped[str] = mapped_column(Text, nullable=False)

    # Structured payloads
    artifact_manifest: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    changelog: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    confidence_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    rollback_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Target environment (FK set when deployed)
    target_environment_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("deployment_environments.id", ondelete="SET NULL"), nullable=True
    )

    created_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
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
    project = relationship("Project")
    run = relationship("Run")
    target_environment = relationship("DeploymentEnvironment")
    gate_results = relationship(
        "ReleaseGateResult",
        back_populates="release_package",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_release_packages_project_id", "project_id"),
        Index("ix_release_packages_run_id", "run_id"),
        Index("ix_release_packages_status", "status"),
    )


# ---------------------------------------------------------------------------
# FM-132: Deployment Environment
# ---------------------------------------------------------------------------


class DeploymentEnvironment(Base):
    __tablename__ = "deployment_environments"

    id: Mapped[uuid.UUID] = mapped_column(
        default=uuid.uuid4, primary_key=True, index=True
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    tier: Mapped[EnvironmentTier] = mapped_column(
        Enum(EnvironmentTier), default=EnvironmentTier.DEVELOPMENT, nullable=False
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Environment configuration
    config: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    required_gates: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    promotion_target_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("deployment_environments.id", ondelete="SET NULL"), nullable=True
    )

    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
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
    project = relationship("Project")
    promotion_target = relationship(
        "DeploymentEnvironment", remote_side="DeploymentEnvironment.id"
    )

    __table_args__ = (
        Index("ix_deployment_environments_project_id", "project_id"),
        Index("ix_deployment_environments_tier", "tier"),
    )


# ---------------------------------------------------------------------------
# FM-134: Release Gate Result
# ---------------------------------------------------------------------------


class ReleaseGateResult(Base):
    __tablename__ = "release_gate_results"

    id: Mapped[uuid.UUID] = mapped_column(
        default=uuid.uuid4, primary_key=True, index=True
    )
    release_package_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("release_packages.id", ondelete="CASCADE"), nullable=False
    )
    gate_name: Mapped[str] = mapped_column(String(200), nullable=False)
    gate_status: Mapped[GateStatus] = mapped_column(
        Enum(GateStatus), default=GateStatus.PENDING, nullable=False
    )
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)
    evaluated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    release_package = relationship("ReleasePackage", back_populates="gate_results")

    __table_args__ = (
        Index("ix_release_gate_results_package_id", "release_package_id"),
    )
