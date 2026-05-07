"""FM-231/232: Scheduled and event-driven run triggers.

CronTrigger  — schedule a project run on a cron expression
TriggerRule  — fire a run when an external event matches a condition
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base


class CronTriggerStatus(str, enum.Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    DISABLED = "disabled"


class CronTrigger(Base):
    """Scheduled run trigger — fires on a cron expression."""

    __tablename__ = "cron_triggers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    cron_expression: Mapped[str] = mapped_column(String(100), nullable=False)
    prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[CronTriggerStatus] = mapped_column(
        Enum(CronTriggerStatus, name="cron_trigger_status"),
        default=CronTriggerStatus.ACTIVE,
        nullable=False,
    )
    last_fired_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    next_fire_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    fire_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
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

    def __repr__(self) -> str:
        return f"<CronTrigger {self.name} {self.cron_expression}>"


class TriggerRuleEvent(str, enum.Enum):
    WEBHOOK_RECEIVED = "webhook_received"
    PR_OPENED = "pr_opened"
    PR_MERGED = "pr_merged"
    COMMIT_PUSHED = "commit_pushed"
    APPROVAL_REJECTED = "approval_rejected"
    RUN_COMPLETED = "run_completed"
    SECURITY_FINDING = "security_finding"


class TriggerRule(Base):
    """Event-driven trigger — fires a run when a condition matches an event."""

    __tablename__ = "trigger_rules"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    event_type: Mapped[TriggerRuleEvent] = mapped_column(
        Enum(TriggerRuleEvent, name="trigger_rule_event"), nullable=False, index=True
    )
    conditions: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    action_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    fire_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_fired_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<TriggerRule {self.name} on={self.event_type.value}>"
