"""FM-241/246/247: Platform operations models.

ResourceQuota    — FM-241: per-workspace resource limits
DigestSchedule   — FM-246: notification digest configuration
PIIPattern       — FM-247: PII detection pattern rules
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base


# ---------------------------------------------------------------------------
# FM-241: Resource quotas
# ---------------------------------------------------------------------------

class ResourceQuota(Base):
    """Per-workspace resource limits."""

    __tablename__ = "resource_quotas"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    max_concurrent_runs: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_projects: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_monthly_cost_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_api_calls_per_minute: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_storage_gb: Mapped[float | None] = mapped_column(Float, nullable=True)
    enforce: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<ResourceQuota workspace={self.workspace_id}>"


# ---------------------------------------------------------------------------
# FM-246: Notification digests
# ---------------------------------------------------------------------------

class DigestFrequency(str, enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    DISABLED = "disabled"


class DigestSchedule(Base):
    """User digest configuration — daily/weekly summary emails."""

    __tablename__ = "digest_schedules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    frequency: Mapped[DigestFrequency] = mapped_column(
        Enum(DigestFrequency, name="digest_frequency"),
        default=DigestFrequency.DAILY,
        nullable=False,
    )
    hour_utc: Mapped[int] = mapped_column(Integer, default=8, nullable=False)
    include_costs: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    include_approvals: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    include_security: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<DigestSchedule user={self.user_id} {self.frequency.value}>"


# ---------------------------------------------------------------------------
# FM-247: PII detection patterns
# ---------------------------------------------------------------------------

class PIIPatternType(str, enum.Enum):
    REGEX = "regex"
    KEYWORD = "keyword"
    ML = "ml"


class PIIPattern(Base):
    """PII detection pattern — used to scan artifact content."""

    __tablename__ = "pii_patterns"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    pattern_type: Mapped[PIIPatternType] = mapped_column(
        Enum(PIIPatternType, name="pii_pattern_type"), nullable=False
    )
    pattern: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)  # email, ssn, phone, etc.
    severity: Mapped[str] = mapped_column(String(20), default="high", nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<PIIPattern {self.name} [{self.category}]>"
