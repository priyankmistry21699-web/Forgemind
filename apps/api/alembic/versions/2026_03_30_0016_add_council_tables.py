"""add council_sessions and council_votes tables

Revision ID: 0016
Revises: 0015
Create Date: 2026-03-30 00:16:00.000000+00:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON

revision = "0016"
down_revision = "0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "council_sessions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("run_id", UUID(as_uuid=True), sa.ForeignKey("runs.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("task_id", UUID(as_uuid=True), sa.ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True),
        sa.Column("topic", sa.String(500), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("context", JSON, nullable=True),
        sa.Column("status", sa.Enum("convened", "deliberating", "decided", "deadlocked", "escalated", name="council_status"), nullable=False, index=True),
        sa.Column("decision_method", sa.Enum("consensus", "majority", "supermajority", "weighted", name="decision_method"), nullable=False),
        sa.Column("final_decision", sa.String(50), nullable=True),
        sa.Column("decision_rationale", sa.Text, nullable=True),
        sa.Column("decision_metadata", JSON, nullable=True),
        sa.Column("convened_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "council_votes",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("session_id", UUID(as_uuid=True), sa.ForeignKey("council_sessions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("agent_slug", sa.String(50), nullable=False),
        sa.Column("decision", sa.Enum("approve", "reject", "abstain", "modify", name="vote_decision"), nullable=False),
        sa.Column("reasoning", sa.Text, nullable=True),
        sa.Column("confidence", sa.Float, nullable=False, server_default="0.5"),
        sa.Column("weight", sa.Float, nullable=False, server_default="1.0"),
        sa.Column("suggested_modifications", JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("council_votes")
    op.drop_table("council_sessions")
