"""add connectors table

Revision ID: 0008
Revises: 0007
Create Date: 2026-03-27 00:08:00.000000+00:00

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "connectors",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("slug", sa.String(50), nullable=False, unique=True, index=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column(
            "connector_type", sa.String(50), nullable=False, index=True
        ),
        sa.Column(
            "status",
            sa.Enum("available", "configured", "unavailable", name="connector_status"),
            nullable=False,
            server_default="available",
        ),
        sa.Column("capabilities", postgresql.JSON, nullable=True),
        sa.Column("config", postgresql.JSON, nullable=True),
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
    )


def downgrade() -> None:
    op.drop_table("connectors")
    op.execute("DROP TYPE IF EXISTS connector_status")
