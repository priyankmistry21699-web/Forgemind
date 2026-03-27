"""add replay_snapshots table

Revision ID: 0015
Revises: 0014
Create Date: 2026-03-30 00:15:00.000000+00:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON

# revision identifiers, used by Alembic.
revision = "0015"
down_revision = "0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "replay_snapshots",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("task_id", UUID(as_uuid=True), sa.ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("run_id", UUID(as_uuid=True), sa.ForeignKey("runs.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("agent_slug", sa.String(50), nullable=False),
        sa.Column("input_snapshot", JSON, nullable=True),
        sa.Column("prompt_snapshot", sa.Text, nullable=True),
        sa.Column("model_used", sa.String(100), nullable=True),
        sa.Column("temperature", sa.Float, nullable=True),
        sa.Column("output_snapshot", JSON, nullable=True),
        sa.Column("error", sa.Text, nullable=True),
        sa.Column("tokens_used", sa.Integer, nullable=False, server_default="0"),
        sa.Column("duration_ms", sa.Integer, nullable=False, server_default="0"),
        sa.Column("cost_usd", sa.Float, nullable=False, server_default="0"),
        sa.Column("replay_hash", sa.String(64), nullable=True, index=True),
        sa.Column("is_replay", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("original_snapshot_id", UUID(as_uuid=True), sa.ForeignKey("replay_snapshots.id", ondelete="SET NULL"), nullable=True),
        sa.Column("sequence_number", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("replay_snapshots")
