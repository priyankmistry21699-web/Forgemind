"""FM-061–069: Add code ops enhancements.

Revision ID: 0021
Revises: 0020
Create Date: 2026-03-31

Adds columns to:
- repo_connections: sync metadata + branch strategy fields
- artifacts: code artifact mapping fields
- patch_proposals: target_files, patch_format, proposed_by_agent, readiness_state
- change_reviews: file-level annotations
- sandbox_executions: runner safety fields

New enum types: sync_status, branch_mode, change_type, patch_format, readiness_state
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON, UUID

revision = "0021"
down_revision = "0020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── New enum types ───────────────────────────────────────────
    sync_status = sa.Enum("idle", "syncing", "success", "failed", name="sync_status")
    sync_status.create(op.get_bind(), checkfirst=True)

    branch_mode = sa.Enum("direct", "feature_branch", "review_branch", name="branch_mode")
    branch_mode.create(op.get_bind(), checkfirst=True)

    change_type = sa.Enum("create", "modify", "delete", "conceptual", name="change_type")
    change_type.create(op.get_bind(), checkfirst=True)

    patch_format = sa.Enum("unified", "side_by_side", "raw", name="patch_format")
    patch_format.create(op.get_bind(), checkfirst=True)

    readiness_state = sa.Enum("incomplete", "needs_review", "ready", "blocked", name="readiness_state")
    readiness_state.create(op.get_bind(), checkfirst=True)

    # ── repo_connections: FM-061 sync metadata + FM-066 branch strategy ──
    op.add_column("repo_connections", sa.Column("base_branch", sa.String(200), nullable=True))
    op.add_column("repo_connections", sa.Column("target_branch", sa.String(200), nullable=True))
    op.add_column("repo_connections", sa.Column("linked_paths", JSON, nullable=True))
    op.add_column("repo_connections", sa.Column("last_sync_status", sync_status, nullable=True))
    op.add_column("repo_connections", sa.Column("last_sync_error", sa.Text(), nullable=True))
    op.add_column("repo_connections", sa.Column("last_synced_commit", sa.String(100), nullable=True))
    op.add_column("repo_connections", sa.Column("provider_metadata", JSON, nullable=True))
    op.add_column("repo_connections", sa.Column("branch_mode", branch_mode, nullable=True))
    op.add_column("repo_connections", sa.Column("target_branch_template", sa.String(200), nullable=True))
    op.add_column("repo_connections", sa.Column("last_generated_branch", sa.String(200), nullable=True))

    # ── artifacts: FM-063 code mapping fields ────────────────────
    op.add_column("artifacts", sa.Column(
        "repo_connection_id", UUID(as_uuid=True),
        sa.ForeignKey("repo_connections.id", ondelete="SET NULL"), nullable=True,
    ))
    op.add_column("artifacts", sa.Column("target_path", sa.String(1000), nullable=True))
    op.add_column("artifacts", sa.Column("target_module", sa.String(500), nullable=True))
    op.add_column("artifacts", sa.Column("change_type", change_type, nullable=True))
    op.add_column("artifacts", sa.Column("target_metadata", JSON, nullable=True))

    # ── patch_proposals: FM-064 enhancements ─────────────────────
    op.add_column("patch_proposals", sa.Column("target_files", JSON, nullable=True))
    op.add_column("patch_proposals", sa.Column("patch_format", patch_format, nullable=True))
    op.add_column("patch_proposals", sa.Column("proposed_by_agent", sa.String(200), nullable=True))
    op.add_column("patch_proposals", sa.Column("readiness_state", readiness_state, nullable=True))
    op.add_column("patch_proposals", sa.Column("linked_artifact_ids", JSON, nullable=True))

    # ── change_reviews: FM-065 file annotations ──────────────────
    op.add_column("change_reviews", sa.Column("file_path", sa.String(1000), nullable=True))
    op.add_column("change_reviews", sa.Column("line_start", sa.Integer(), nullable=True))
    op.add_column("change_reviews", sa.Column("line_end", sa.Integer(), nullable=True))
    op.add_column("change_reviews", sa.Column("suggestion", sa.Text(), nullable=True))

    # ── sandbox_executions: FM-069 runner safety ─────────────────
    op.add_column("sandbox_executions", sa.Column("approval_id", UUID(as_uuid=True), nullable=True))
    op.add_column("sandbox_executions", sa.Column("allowed_commands", JSON, nullable=True))
    op.add_column("sandbox_executions", sa.Column("resource_limits", JSON, nullable=True))
    op.add_column("sandbox_executions", sa.Column(
        "isolated", sa.Boolean(), server_default=sa.text("true"), nullable=False,
    ))


def downgrade() -> None:
    # ── sandbox_executions ───────────────────────────────────────
    op.drop_column("sandbox_executions", "isolated")
    op.drop_column("sandbox_executions", "resource_limits")
    op.drop_column("sandbox_executions", "allowed_commands")
    op.drop_column("sandbox_executions", "approval_id")

    # ── change_reviews ───────────────────────────────────────────
    op.drop_column("change_reviews", "suggestion")
    op.drop_column("change_reviews", "line_end")
    op.drop_column("change_reviews", "line_start")
    op.drop_column("change_reviews", "file_path")

    # ── patch_proposals ──────────────────────────────────────────
    op.drop_column("patch_proposals", "linked_artifact_ids")
    op.drop_column("patch_proposals", "readiness_state")
    op.drop_column("patch_proposals", "proposed_by_agent")
    op.drop_column("patch_proposals", "patch_format")
    op.drop_column("patch_proposals", "target_files")

    # ── artifacts ────────────────────────────────────────────────
    op.drop_column("artifacts", "target_metadata")
    op.drop_column("artifacts", "change_type")
    op.drop_column("artifacts", "target_module")
    op.drop_column("artifacts", "target_path")
    op.drop_column("artifacts", "repo_connection_id")

    # ── repo_connections ─────────────────────────────────────────
    op.drop_column("repo_connections", "last_generated_branch")
    op.drop_column("repo_connections", "target_branch_template")
    op.drop_column("repo_connections", "branch_mode")
    op.drop_column("repo_connections", "provider_metadata")
    op.drop_column("repo_connections", "last_synced_commit")
    op.drop_column("repo_connections", "last_sync_error")
    op.drop_column("repo_connections", "last_sync_status")
    op.drop_column("repo_connections", "linked_paths")
    op.drop_column("repo_connections", "target_branch")
    op.drop_column("repo_connections", "base_branch")

    # ── Drop enum types ──────────────────────────────────────────
    sa.Enum(name="readiness_state").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="patch_format").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="change_type").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="branch_mode").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="sync_status").drop(op.get_bind(), checkfirst=True)
