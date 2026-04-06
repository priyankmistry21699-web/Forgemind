"""FM-121: Add execution_checkpoints table.

Revision ID: 0024
Revises: 0023
Create Date: 2026-04-06

New tables:
- execution_checkpoints: run-scoped progress snapshots with status, artifact,
  validation, approval, and architecture JSON payloads.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0024"
down_revision = "0023"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "execution_checkpoints",
        sa.Column(
            "id",
            sa.Uuid(),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("task_id", sa.Uuid(), nullable=True),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=500), nullable=True),
        sa.Column(
            "checkpoint_type",
            sa.Enum(
                "manual",
                "auto_phase",
                "pre_approval",
                "pre_delivery",
                "post_validation",
                name="checkpoint_type",
            ),
            nullable=False,
            server_default="manual",
        ),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("status_snapshot", postgresql.JSON(), nullable=True),
        sa.Column("artifact_refs", postgresql.JSON(), nullable=True),
        sa.Column("validation_snapshot", postgresql.JSON(), nullable=True),
        sa.Column("approval_snapshot", postgresql.JSON(), nullable=True),
        sa.Column("architecture_snapshot", postgresql.JSON(), nullable=True),
        sa.Column("metadata", postgresql.JSON(), nullable=True),
        sa.Column("sequence_number", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_by", sa.String(length=100), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["run_id"], ["runs.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["task_id"], ["tasks.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["project_id"], ["projects.id"], ondelete="CASCADE"
        ),
    )
    op.create_index(
        "ix_execution_checkpoints_run_id",
        "execution_checkpoints",
        ["run_id"],
    )
    op.create_index(
        "ix_execution_checkpoints_project_id",
        "execution_checkpoints",
        ["project_id"],
    )
    op.create_index(
        "ix_execution_checkpoints_checkpoint_type",
        "execution_checkpoints",
        ["checkpoint_type"],
    )


def downgrade() -> None:
    op.drop_index("ix_execution_checkpoints_checkpoint_type")
    op.drop_index("ix_execution_checkpoints_project_id")
    op.drop_index("ix_execution_checkpoints_run_id")
    op.drop_table("execution_checkpoints")
    op.execute("DROP TYPE IF EXISTS checkpoint_type")
