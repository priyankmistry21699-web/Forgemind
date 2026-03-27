"""add project_connector_links table

Revision ID: 0009
Revises: 0008
Create Date: 2026-03-28 00:09:00.000000+00:00

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "project_connector_links",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "connector_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("connectors.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "priority",
            sa.Enum("required", "recommended", "optional", name="connector_priority"),
            nullable=False,
            server_default="recommended",
        ),
        sa.Column(
            "readiness",
            sa.Enum("missing", "configured", "blocked", "ready", name="connector_readiness"),
            nullable=False,
            server_default="missing",
        ),
        sa.Column("config_snapshot", postgresql.JSON, nullable=True),
        sa.Column("blocker_reason", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("project_id", "connector_id", name="uq_project_connector"),
    )


def downgrade() -> None:
    op.drop_table("project_connector_links")
    op.execute("DROP TYPE IF EXISTS connector_priority")
    op.execute("DROP TYPE IF EXISTS connector_readiness")
