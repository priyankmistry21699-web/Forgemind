"""add retry columns to tasks table

Revision ID: 0011
Revises: 0010
Create Date: 2026-03-28 00:11:00.000000+00:00

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tasks",
        sa.Column("retry_count", sa.Integer, nullable=False, server_default="0"),
    )
    op.add_column(
        "tasks",
        sa.Column("max_retries", sa.Integer, nullable=False, server_default="3"),
    )
    op.add_column(
        "tasks",
        sa.Column(
            "retry_policy", sa.String(50), nullable=False, server_default="standard"
        ),
    )


def downgrade() -> None:
    op.drop_column("tasks", "retry_count")
    op.drop_column("tasks", "max_retries")
    op.drop_column("tasks", "retry_policy")
