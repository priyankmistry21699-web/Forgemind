"""FM-212/218/222/223/226/227/230: Wave 17+18 agent intelligence tables.

Creates:
  - agent_memory_entries
  - llm_call_logs
  - plan_revisions
  - review_comments
  - security_findings
  + artifact columns: storage_key, storage_size_bytes

Revision ID: wave17_18_agent_intelligence
Revises: fm171_175_governance_sso
Create Date: 2026-05-06
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "wave17_18_agent_intelligence"
down_revision = "fm171_175_governance_sso"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- agent_memory_entries ---
    op.create_table(
        "agent_memory_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "run_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("runs.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("agent_type", sa.String(100), nullable=False),
        sa.Column("key", sa.String(500), nullable=False),
        sa.Column("value_json", postgresql.JSON, nullable=True),
        sa.Column("embedding_vector", postgresql.JSON, nullable=True),
        sa.Column("relevance_score", sa.Float, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_agent_memory_entries_project_id", "agent_memory_entries", ["project_id"]
    )
    op.create_index(
        "ix_agent_memory_entries_agent_type", "agent_memory_entries", ["agent_type"]
    )

    # --- llm_call_logs ---
    op.create_table(
        "llm_call_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "run_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("runs.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "task_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tasks.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("model", sa.String(200), nullable=False),
        sa.Column("prompt_tokens", sa.Integer, default=0, nullable=False),
        sa.Column("completion_tokens", sa.Integer, default=0, nullable=False),
        sa.Column("cost_usd", sa.Float, default=0.0, nullable=False),
        sa.Column("latency_ms", sa.Integer, nullable=True),
        sa.Column("task_type", sa.String(100), nullable=True),
        sa.Column("success", sa.Boolean, default=True, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_llm_call_logs_run_id", "llm_call_logs", ["run_id"])
    op.create_index("ix_llm_call_logs_model", "llm_call_logs", ["model"])

    # --- plan_revisions ---
    plan_revision_trigger = sa.Enum(
        "agent_failure",
        "approval_rejection",
        "manual",
        "budget_exceeded",
        name="plan_revision_trigger",
    )
    op.create_table(
        "plan_revisions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "run_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "failed_task_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tasks.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("trigger", plan_revision_trigger, nullable=False),
        sa.Column("error_context", sa.Text, nullable=True),
        sa.Column("original_task_ids", postgresql.JSON, nullable=True),
        sa.Column("revised_task_ids", postgresql.JSON, nullable=True),
        sa.Column("retry_count", sa.Integer, default=0, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_plan_revisions_run_id", "plan_revisions", ["run_id"])

    # --- review_comments ---
    review_comment_severity = sa.Enum(
        "info", "warning", "error", "critical", name="review_comment_severity"
    )
    op.create_table(
        "review_comments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "run_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("runs.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "pr_link_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("pull_request_links.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("file_path", sa.String(1000), nullable=True),
        sa.Column("line_number", sa.Integer, nullable=True),
        sa.Column("severity", review_comment_severity, nullable=False),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("github_comment_id", sa.String(100), nullable=True),
        sa.Column("resolved", sa.Boolean, default=False, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_review_comments_run_id", "review_comments", ["run_id"])

    # --- security_findings ---
    finding_severity = sa.Enum(
        "low", "medium", "high", "critical", name="finding_severity"
    )
    finding_source = sa.Enum(
        "bandit", "npm_audit", "semgrep", "manual", name="finding_source"
    )
    op.create_table(
        "security_findings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "run_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("runs.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("severity", finding_severity, nullable=False),
        sa.Column("source", finding_source, nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("file_path", sa.String(1000), nullable=True),
        sa.Column("line_number", sa.Integer, nullable=True),
        sa.Column("cwe_id", sa.String(50), nullable=True),
        sa.Column("cve_id", sa.String(50), nullable=True),
        sa.Column("remediation", sa.Text, nullable=True),
        sa.Column("resolved", sa.Boolean, default=False, nullable=False),
        sa.Column(
            "approval_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("approval_requests.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("raw_output", postgresql.JSON, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_security_findings_project_id", "security_findings", ["project_id"]
    )
    op.create_index(
        "ix_security_findings_severity", "security_findings", ["severity"]
    )

    # --- artifact additions (FM-218) ---
    op.add_column("artifacts", sa.Column("storage_key", sa.String(500), nullable=True))
    op.add_column(
        "artifacts", sa.Column("storage_size_bytes", sa.Integer, nullable=True)
    )


def downgrade() -> None:
    op.drop_column("artifacts", "storage_size_bytes")
    op.drop_column("artifacts", "storage_key")

    op.drop_index("ix_security_findings_severity", table_name="security_findings")
    op.drop_index("ix_security_findings_project_id", table_name="security_findings")
    op.drop_table("security_findings")
    op.execute("DROP TYPE IF EXISTS finding_severity")
    op.execute("DROP TYPE IF EXISTS finding_source")

    op.drop_index("ix_review_comments_run_id", table_name="review_comments")
    op.drop_table("review_comments")
    op.execute("DROP TYPE IF EXISTS review_comment_severity")

    op.drop_index("ix_plan_revisions_run_id", table_name="plan_revisions")
    op.drop_table("plan_revisions")
    op.execute("DROP TYPE IF EXISTS plan_revision_trigger")

    op.drop_index("ix_llm_call_logs_model", table_name="llm_call_logs")
    op.drop_index("ix_llm_call_logs_run_id", table_name="llm_call_logs")
    op.drop_table("llm_call_logs")

    op.drop_index(
        "ix_agent_memory_entries_agent_type", table_name="agent_memory_entries"
    )
    op.drop_index(
        "ix_agent_memory_entries_project_id", table_name="agent_memory_entries"
    )
    op.drop_table("agent_memory_entries")
