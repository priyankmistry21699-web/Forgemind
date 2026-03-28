"""add collaboration and code ops tables (FM-051 through FM-069)

Revision ID: 0019
Revises: 0018
Create Date: 2026-03-27 00:19:00.000000+00:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON

revision = "0019"
down_revision = "0018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # FM-051: Workspaces
    op.create_table(
        "workspaces",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("status", sa.Enum("active", "suspended", "archived", name="workspace_status"), nullable=False),
        sa.Column("owner_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("settings", JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # FM-052: Workspace Members
    op.create_table(
        "workspace_members",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", UUID(as_uuid=True), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("role", sa.Enum("owner", "admin", "operator", "reviewer", "viewer", name="workspace_role"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("workspace_id", "user_id", name="uq_workspace_user"),
    )

    # FM-053: Project Members
    op.create_table(
        "project_members",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("role", sa.Enum("lead", "operator", "reviewer", "viewer", name="project_role"), nullable=False),
        sa.Column("is_approver", sa.Boolean, default=False, nullable=False),
        sa.Column("is_reviewer", sa.Boolean, default=False, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("project_id", "user_id", name="uq_project_user"),
    )

    # FM-055: Notifications
    op.create_table(
        "notifications",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("notification_type", sa.Enum(
            "task_assigned", "task_completed", "approval_required", "approval_granted",
            "approval_denied", "run_started", "run_completed", "run_failed",
            "member_added", "member_removed", "escalation", "system",
            name="notification_type",
        ), nullable=False, index=True),
        sa.Column("priority", sa.Enum("low", "normal", "high", "urgent", name="notification_priority"), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("body", sa.Text, nullable=True),
        sa.Column("is_read", sa.Boolean, default=False, nullable=False),
        sa.Column("resource_type", sa.String(50), nullable=True),
        sa.Column("resource_id", UUID(as_uuid=True), nullable=True),
        sa.Column("metadata", JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # FM-056: Delivery Config
    op.create_table(
        "notification_delivery_configs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("channel", sa.Enum("slack", "email", "webhook", name="delivery_channel"), nullable=False),
        sa.Column("status", sa.Enum("active", "paused", "disabled", name="delivery_status"), nullable=False),
        sa.Column("config", JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # FM-057: Escalation Rules
    op.create_table(
        "escalation_rules",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("trigger", sa.Enum(
            "task_timeout", "run_failure", "approval_timeout",
            "budget_exceeded", "trust_score_low", "custom",
            name="escalation_trigger",
        ), nullable=False),
        sa.Column("action", sa.Enum(
            "notify", "pause_run", "reassign", "escalate_user", "auto_cancel",
            name="escalation_action",
        ), nullable=False),
        sa.Column("rules", JSON, nullable=True),
        sa.Column("cooldown_minutes", sa.Integer, default=30, nullable=False),
        sa.Column("is_active", sa.Boolean, default=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # FM-057: Escalation Events
    op.create_table(
        "escalation_events",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("rule_id", UUID(as_uuid=True), sa.ForeignKey("escalation_rules.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("trigger_data", JSON, nullable=True),
        sa.Column("action_taken", sa.String(50), nullable=True),
        sa.Column("resolved", sa.Boolean, default=False, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # FM-058: Activity Feed
    op.create_table(
        "activity_feed_entries",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("actor_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("activity_type", sa.Enum(
            "project_created", "project_updated", "run_started", "run_completed",
            "run_failed", "task_completed", "artifact_created", "member_added",
            "member_removed", "approval_requested", "approval_decided",
            "escalation_triggered", "patch_proposed", "pr_created", "comment",
            name="activity_type",
        ), nullable=False, index=True),
        sa.Column("summary", sa.String(500), nullable=False),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("workspace_id", UUID(as_uuid=True), sa.ForeignKey("workspaces.id", ondelete="SET NULL"), nullable=True),
        sa.Column("resource_type", sa.String(50), nullable=True),
        sa.Column("resource_id", UUID(as_uuid=True), nullable=True),
        sa.Column("metadata", JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # FM-059: User Presence
    op.create_table(
        "user_presences",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True),
        sa.Column("status", sa.String(20), default="online", nullable=False),
        sa.Column("current_resource_type", sa.String(50), nullable=True),
        sa.Column("current_resource_id", UUID(as_uuid=True), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # FM-061: Code Mappings
    op.create_table(
        "code_mappings",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("artifact_id", UUID(as_uuid=True), sa.ForeignKey("artifacts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("file_path", sa.String(1000), nullable=False),
        sa.Column("language", sa.String(50), nullable=True),
        sa.Column("metadata", JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # FM-062: Patch Proposals
    op.create_table(
        "patch_proposals",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("diff_content", sa.Text, nullable=False),
        sa.Column("target_branch", sa.String(200), default="main", nullable=False),
        sa.Column("status", sa.Enum("draft", "proposed", "approved", "rejected", "applied", "superseded", name="patch_status"), nullable=False, index=True),
        sa.Column("rationale", sa.Text, nullable=True),
        sa.Column("created_by", UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # FM-063/066: Change Reviews
    op.create_table(
        "change_reviews",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("patch_id", UUID(as_uuid=True), sa.ForeignKey("patch_proposals.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("reviewer_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("decision", sa.Enum("approve", "request_changes", "comment", name="review_decision"), nullable=False),
        sa.Column("comment", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # FM-064: Branch Strategies
    op.create_table(
        "branch_strategies",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("base_branch", sa.String(200), default="main", nullable=False),
        sa.Column("branch_pattern", sa.String(200), default="forgemind/{task_id}", nullable=False),
        sa.Column("auto_create_branch", sa.Boolean, default=True, nullable=False),
        sa.Column("pr_target_branch", sa.String(200), default="main", nullable=False),
        sa.Column("config", JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # FM-065: PR Drafts
    op.create_table(
        "pr_drafts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("patch_id", UUID(as_uuid=True), sa.ForeignKey("patch_proposals.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("body", sa.Text, nullable=True),
        sa.Column("source_branch", sa.String(200), nullable=False),
        sa.Column("target_branch", sa.String(200), default="main", nullable=False),
        sa.Column("status", sa.Enum("draft", "ready", "submitted", "merged", "closed", name="pr_draft_status"), nullable=False, index=True),
        sa.Column("reviewers", JSON, nullable=True),
        sa.Column("checklist", JSON, nullable=True),
        sa.Column("linked_artifacts", JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # FM-067: Repo Action Approvals
    op.create_table(
        "repo_action_approvals",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("action_type", sa.Enum("patch_apply", "branch_create", "pr_create", "push", "merge", name="repo_action_type"), nullable=False),
        sa.Column("status", sa.String(20), default="pending", nullable=False, index=True),
        sa.Column("reason", sa.Text, nullable=True),
        sa.Column("context", JSON, nullable=True),
        sa.Column("decided_by", UUID(as_uuid=True), nullable=True),
        sa.Column("decision_comment", sa.Text, nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # FM-068/069: Sandbox Executions
    op.create_table(
        "sandbox_executions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("task_id", UUID(as_uuid=True), nullable=True),
        sa.Column("patch_id", UUID(as_uuid=True), nullable=True),
        sa.Column("command", sa.Text, nullable=False),
        sa.Column("working_directory", sa.String(500), nullable=True),
        sa.Column("environment", JSON, nullable=True),
        sa.Column("timeout_seconds", sa.Integer, default=60, nullable=False),
        sa.Column("status", sa.Enum("queued", "running", "completed", "failed", "timeout", name="sandbox_status"), nullable=False, index=True),
        sa.Column("stdout", sa.Text, nullable=True),
        sa.Column("stderr", sa.Text, nullable=True),
        sa.Column("exit_code", sa.Integer, nullable=True),
        sa.Column("duration_ms", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("sandbox_executions")
    op.drop_table("repo_action_approvals")
    op.drop_table("pr_drafts")
    op.drop_table("branch_strategies")
    op.drop_table("change_reviews")
    op.drop_table("patch_proposals")
    op.drop_table("code_mappings")
    op.drop_table("user_presences")
    op.drop_table("activity_feed_entries")
    op.drop_table("escalation_events")
    op.drop_table("escalation_rules")
    op.drop_table("notification_delivery_configs")
    op.drop_table("notifications")
    op.drop_table("project_members")
    op.drop_table("workspace_members")
    op.drop_table("workspaces")
