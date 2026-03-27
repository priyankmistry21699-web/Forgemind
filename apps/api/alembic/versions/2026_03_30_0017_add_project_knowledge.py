"""add project_knowledge table

Revision ID: 0017
Revises: 0016
Create Date: 2026-03-30 00:17:00.000000+00:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON

revision = "0017"
down_revision = "0016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "project_knowledge",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("source_run_id", UUID(as_uuid=True), sa.ForeignKey("runs.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("source_task_id", UUID(as_uuid=True), sa.ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True),
        sa.Column("knowledge_type", sa.Enum("pattern", "decision", "lesson_learned", "dependency", "best_practice", "architecture", "constraint", name="knowledge_type"), nullable=False, index=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("tags", JSON, nullable=True),
        sa.Column("metadata", JSON, nullable=True),
        sa.Column("relevance_score", sa.Float, nullable=False, server_default="1.0"),
        sa.Column("usage_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("project_knowledge")
