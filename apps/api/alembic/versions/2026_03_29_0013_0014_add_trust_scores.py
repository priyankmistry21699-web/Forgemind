"""add trust_scores table

Revision ID: 0014
Revises: 0013
Create Date: 2026-03-29 00:14:00.000000+00:00

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON

# revision identifiers, used by Alembic.
revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "trust_scores",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "entity_type",
            sa.Enum("task", "artifact", "run", name="trust_entity_type"),
            nullable=False,
        ),
        sa.Column("entity_id", UUID(as_uuid=True), nullable=False),
        sa.Column("trust_score", sa.Float, nullable=False),
        sa.Column("confidence", sa.Float, nullable=False, server_default="0.5"),
        sa.Column(
            "risk_level",
            sa.Enum("low", "medium", "high", "critical", name="risk_level"),
            nullable=False,
        ),
        sa.Column("factors", JSON, nullable=True),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=True),
        sa.Column("run_id", UUID(as_uuid=True), sa.ForeignKey("runs.id", ondelete="CASCADE"), nullable=True),
        sa.Column("assessed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_trust_scores_entity_type", "trust_scores", ["entity_type"])
    op.create_index("ix_trust_scores_entity_id", "trust_scores", ["entity_id"])
    op.create_index("ix_trust_scores_risk_level", "trust_scores", ["risk_level"])
    op.create_index("ix_trust_scores_project_id", "trust_scores", ["project_id"])


def downgrade() -> None:
    op.drop_index("ix_trust_scores_project_id", table_name="trust_scores")
    op.drop_index("ix_trust_scores_risk_level", table_name="trust_scores")
    op.drop_index("ix_trust_scores_entity_id", table_name="trust_scores")
    op.drop_index("ix_trust_scores_entity_type", table_name="trust_scores")
    op.drop_table("trust_scores")
    op.execute("DROP TYPE IF EXISTS trust_entity_type")
    op.execute("DROP TYPE IF EXISTS risk_level")
