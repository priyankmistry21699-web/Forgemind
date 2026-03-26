"""add execution_events table

Revision ID: 0007
Revises: 0006
Create Date: 2026-03-26 00:06:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

event_type_enum = postgresql.ENUM(
    "task_claimed",
    "task_completed",
    "task_failed",
    "artifact_created",
    "approval_requested",
    "approval_resolved",
    "run_started",
    "run_completed",
    "run_failed",
    "plan_generated",
    name="event_type",
    create_type=False,
)


def upgrade() -> None:
    event_type_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "execution_events",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("event_type", event_type_enum, nullable=False),
        sa.Column("summary", sa.String(1000), nullable=False),
        sa.Column("metadata", sa.dialects.postgresql.JSON(), nullable=True),
        sa.Column(
            "project_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "run_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("runs.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "task_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tasks.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "artifact_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("artifacts.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("agent_slug", sa.String(50), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_execution_events_event_type", "execution_events", ["event_type"])
    op.create_index("ix_execution_events_project_id", "execution_events", ["project_id"])
    op.create_index("ix_execution_events_run_id", "execution_events", ["run_id"])


def downgrade() -> None:
    op.drop_index("ix_execution_events_run_id", table_name="execution_events")
    op.drop_index("ix_execution_events_project_id", table_name="execution_events")
    op.drop_index("ix_execution_events_event_type", table_name="execution_events")
    op.drop_table("execution_events")
    event_type_enum.drop(op.get_bind(), checkfirst=True)
