"""GovernancePolicy model — configurable approval and governance rules.

FM-048: Replaces hardcoded approval gates with a policy engine.
Policies define conditions under which approval is required.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import String, Text, DateTime, Enum, ForeignKey, Boolean, Float, func
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base


class PolicyTrigger(str, enum.Enum):
    """What triggers the policy evaluation."""
    TASK_TYPE = "task_type"           # Matches task type (e.g. "architecture")
    COST_THRESHOLD = "cost_threshold" # Total run cost exceeds threshold
    ARTIFACT_TYPE = "artifact_type"   # Artifact of specified type created
    AGENT_ACTION = "agent_action"     # Specific agent performs action
    CUSTOM = "custom"                 # Custom condition in rules JSON


class PolicyAction(str, enum.Enum):
    """What happens when a policy matches."""
    REQUIRE_APPROVAL = "require_approval"
    AUTO_APPROVE = "auto_approve"
    BLOCK = "block"
    NOTIFY = "notify"


class GovernancePolicy(Base):
    __tablename__ = "governance_policies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    trigger: Mapped[PolicyTrigger] = mapped_column(
        Enum(PolicyTrigger, name="policy_trigger"),
        nullable=False,
        index=True,
    )
    action: Mapped[PolicyAction] = mapped_column(
        Enum(PolicyAction, name="policy_action"),
        nullable=False,
    )

    # Configurable rules — JSON object with trigger-specific conditions
    # e.g. {"task_types": ["architecture", "review"]}
    # e.g. {"cost_threshold_usd": 10.0}
    # e.g. {"artifact_types": ["architecture"]}
    rules: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Scope — can be global (null project_id) or per-project
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    priority: Mapped[int] = mapped_column(
        default=0, nullable=False
    )  # Higher = evaluated first

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
        return f"<GovernancePolicy {self.name} ({self.trigger.value} -> {self.action.value})>"
