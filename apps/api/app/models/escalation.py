"""Escalation models — automatic escalation rules and event log.

FM-057: Configurable escalation triggers, actions, and cooldown.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import String, Text, Integer, DateTime, Enum, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base


class EscalationTrigger(str, enum.Enum):
    TASK_TIMEOUT = "task_timeout"
    RUN_FAILURE = "run_failure"
    APPROVAL_TIMEOUT = "approval_timeout"
    BUDGET_EXCEEDED = "budget_exceeded"
    TRUST_SCORE_LOW = "trust_score_low"
    CUSTOM = "custom"


class EscalationAction(str, enum.Enum):
    NOTIFY = "notify"
    PAUSE_RUN = "pause_run"
    REASSIGN = "reassign"
    ESCALATE_USER = "escalate_user"
    AUTO_CANCEL = "auto_cancel"


class EscalationRule(Base):
    __tablename__ = "escalation_rules"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    trigger: Mapped[EscalationTrigger] = mapped_column(
        Enum(EscalationTrigger, name="escalation_trigger"),
        nullable=False,
    )
    action: Mapped[EscalationAction] = mapped_column(
        Enum(EscalationAction, name="escalation_action"),
        nullable=False,
    )
    rules: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    cooldown_minutes: Mapped[int] = mapped_column(
        Integer, default=30, nullable=False
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

    def __repr__(self) -> str:
        return f"<EscalationRule {self.name}>"


class EscalationEvent(Base):
    __tablename__ = "escalation_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    rule_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("escalation_rules.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    trigger_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    action_taken: Mapped[str | None] = mapped_column(String(50), nullable=True)
    resolved: Mapped[bool] = mapped_column(default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<EscalationEvent rule={self.rule_id}>"
