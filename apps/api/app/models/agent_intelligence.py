"""FM-222 / FM-223 / FM-226 / FM-227 / FM-230: Agent intelligence models.

Consolidated module for Wave 18 models:
    AgentMemoryEntry   — FM-222: long-term project-scoped agent memory
    LLMCallLog         — FM-223: per-call LLM cost tracking
    PlanRevision       — FM-226: re-planning audit trail
    ReviewComment      — FM-227: code review inline comments
    SecurityFinding    — FM-230: SAST / dependency scan findings
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base


# ---------------------------------------------------------------------------
# FM-222: Agent long-term memory
# ---------------------------------------------------------------------------


class AgentMemoryEntry(Base):
    """Persistent, project-scoped memory entries written and recalled by agents."""

    __tablename__ = "agent_memory_entries"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("runs.id", ondelete="SET NULL"),
        nullable=True,
    )
    agent_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    key: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    value_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # Cosine-similarity search uses this as a simple float array stored in JSON
    embedding_vector: Mapped[list | None] = mapped_column(JSON, nullable=True)
    relevance_score: Mapped[float | None] = mapped_column(Float, nullable=True)

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
        return f"<AgentMemoryEntry project={self.project_id} agent={self.agent_type} key={self.key}>"


# ---------------------------------------------------------------------------
# FM-223: LLM call cost log
# ---------------------------------------------------------------------------


class LLMCallLog(Base):
    """Per-LLM-call cost and token log for budget tracking."""

    __tablename__ = "llm_call_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("runs.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    task_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="SET NULL"),
        nullable=True,
    )
    model: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    task_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<LLMCallLog model={self.model} cost=${self.cost_usd:.4f}>"


# ---------------------------------------------------------------------------
# FM-226: Plan revision (re-planning audit trail)
# ---------------------------------------------------------------------------


class PlanRevisionTrigger(str, enum.Enum):
    AGENT_FAILURE = "agent_failure"
    APPROVAL_REJECTION = "approval_rejection"
    MANUAL = "manual"
    BUDGET_EXCEEDED = "budget_exceeded"


class PlanRevision(Base):
    """Records each autonomous re-planning event for auditability."""

    __tablename__ = "plan_revisions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    failed_task_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="SET NULL"),
        nullable=True,
    )
    trigger: Mapped[PlanRevisionTrigger] = mapped_column(
        Enum(PlanRevisionTrigger, name="plan_revision_trigger"),
        nullable=False,
    )
    error_context: Mapped[str | None] = mapped_column(Text, nullable=True)
    original_task_ids: Mapped[list | None] = mapped_column(JSON, nullable=True)
    revised_task_ids: Mapped[list | None] = mapped_column(JSON, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<PlanRevision run={self.run_id} trigger={self.trigger.value}>"


# ---------------------------------------------------------------------------
# FM-227: Code review comments
# ---------------------------------------------------------------------------


class ReviewCommentSeverity(str, enum.Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ReviewComment(Base):
    """Inline review comment on a PR draft or patch proposal."""

    __tablename__ = "review_comments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("runs.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    pr_link_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("pull_request_links.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    file_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    line_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    severity: Mapped[ReviewCommentSeverity] = mapped_column(
        Enum(ReviewCommentSeverity, name="review_comment_severity"),
        default=ReviewCommentSeverity.INFO,
        nullable=False,
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    github_comment_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<ReviewComment {self.severity.value} {self.file_path}:{self.line_number}>"


# ---------------------------------------------------------------------------
# FM-230: Security findings
# ---------------------------------------------------------------------------


class FindingSeverity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FindingSource(str, enum.Enum):
    BANDIT = "bandit"
    NPM_AUDIT = "npm_audit"
    SEMGREP = "semgrep"
    MANUAL = "manual"


class SecurityFinding(Base):
    """SAST / dependency vulnerability finding from a security scan agent."""

    __tablename__ = "security_findings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("runs.id", ondelete="SET NULL"),
        nullable=True,
    )
    severity: Mapped[FindingSeverity] = mapped_column(
        Enum(FindingSeverity, name="finding_severity"),
        nullable=False,
        index=True,
    )
    source: Mapped[FindingSource] = mapped_column(
        Enum(FindingSource, name="finding_source"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    line_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cwe_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    cve_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    remediation: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # HIGH/CRITICAL auto-create an approval gate — track it here
    approval_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("approval_requests.id", ondelete="SET NULL"),
        nullable=True,
    )
    raw_output: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<SecurityFinding {self.severity.value} {self.title[:40]}>"
