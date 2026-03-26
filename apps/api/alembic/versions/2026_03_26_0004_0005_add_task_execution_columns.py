"""add execution tracking columns to tasks

Revision ID: 0005
Revises: 0004
Create Date: 2026-03-26 00:04:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tasks", sa.Column("assigned_agent_slug", sa.String(50), nullable=True))
    op.add_column("tasks", sa.Column("error_message", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("tasks", "error_message")
    op.drop_column("tasks", "assigned_agent_slug")
