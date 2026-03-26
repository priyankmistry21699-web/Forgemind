"""initial schema — users, projects, runs, tasks

Revision ID: 0001
Revises:
Create Date: 2026-03-26 00:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Enum types
project_status = postgresql.ENUM(
    "draft", "planning", "active", "paused", "completed", "failed",
    name="project_status",
    create_type=False,
)
run_status = postgresql.ENUM(
    "pending", "planning", "running", "paused", "completed", "failed",
    name="run_status",
    create_type=False,
)
task_status = postgresql.ENUM(
    "pending", "blocked", "ready", "running", "completed", "failed", "skipped",
    name="task_status",
    create_type=False,
)


def upgrade() -> None:
    # Create enum types first
    op.execute("CREATE TYPE project_status AS ENUM ('draft', 'planning', 'active', 'paused', 'completed', 'failed')")
    op.execute("CREATE TYPE run_status AS ENUM ('pending', 'planning', 'running', 'paused', 'completed', 'failed')")
    op.execute("CREATE TYPE task_status AS ENUM ('pending', 'blocked', 'ready', 'running', 'completed', 'failed', 'skipped')")

    # Users
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(320), unique=True, index=True, nullable=False),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("clerk_id", sa.String(255), unique=True, index=True, nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Projects
    op.create_table(
        "projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", project_status, nullable=False, server_default="draft", index=True),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Runs
    op.create_table(
        "runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("run_number", sa.Integer(), nullable=False),
        sa.Column("status", run_status, nullable=False, server_default="pending", index=True),
        sa.Column("trigger", sa.String(50), nullable=False, server_default="manual"),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Tasks
    op.create_table(
        "tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("task_type", sa.String(50), nullable=False, server_default="generic"),
        sa.Column("status", task_status, nullable=False, server_default="pending", index=True),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("depends_on", postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=True),
        sa.Column("parent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("tasks")
    op.drop_table("runs")
    op.drop_table("projects")
    op.drop_table("users")
    op.execute("DROP TYPE task_status")
    op.execute("DROP TYPE run_status")
    op.execute("DROP TYPE project_status")
