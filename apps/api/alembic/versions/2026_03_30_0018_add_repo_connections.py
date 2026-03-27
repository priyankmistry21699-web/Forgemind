"""add repo_connections table

Revision ID: 0018
Revises: 0017
Create Date: 2026-03-30 00:18:00.000000+00:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON

revision = "0018"
down_revision = "0017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "repo_connections",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("provider", sa.Enum("github", "gitlab", "bitbucket", "local", name="repo_provider"), nullable=False),
        sa.Column("repo_url", sa.String(500), nullable=False),
        sa.Column("repo_name", sa.String(200), nullable=False),
        sa.Column("default_branch", sa.String(100), nullable=False, server_default="main"),
        sa.Column("status", sa.Enum("connected", "disconnected", "error", "pending", name="repo_connection_status"), nullable=False, index=True),
        sa.Column("credential_env_key", sa.String(200), nullable=True),
        sa.Column("config", JSON, nullable=True),
        sa.Column("workspace_path", sa.String(500), nullable=True),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("repo_connections")
