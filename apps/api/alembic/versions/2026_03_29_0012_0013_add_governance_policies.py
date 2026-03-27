"""add governance_policies table

Revision ID: 0013
Revises: 0012
Create Date: 2026-03-29 00:13:00.000000+00:00

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON

# revision identifiers, used by Alembic.
revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "governance_policies",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column(
            "trigger",
            sa.Enum(
                "task_type", "cost_threshold", "artifact_type",
                "agent_action", "custom",
                name="policy_trigger",
            ),
            nullable=False,
        ),
        sa.Column(
            "action",
            sa.Enum(
                "require_approval", "auto_approve", "block", "notify",
                name="policy_action",
            ),
            nullable=False,
        ),
        sa.Column("rules", JSON, nullable=True),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=True),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("priority", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_governance_policies_trigger", "governance_policies", ["trigger"])
    op.create_index("ix_governance_policies_project_id", "governance_policies", ["project_id"])


def downgrade() -> None:
    op.drop_index("ix_governance_policies_project_id", table_name="governance_policies")
    op.drop_index("ix_governance_policies_trigger", table_name="governance_policies")
    op.drop_table("governance_policies")
    op.execute("DROP TYPE IF EXISTS policy_trigger")
    op.execute("DROP TYPE IF EXISTS policy_action")
