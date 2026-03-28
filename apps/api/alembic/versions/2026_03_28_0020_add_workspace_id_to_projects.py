"""Add workspace_id to projects table.

Revision ID: 0020
Revises: 0019
Create Date: 2026-03-28

FM-051: Connect projects to workspaces for multi-tenant scoping.
Adds nullable workspace_id FK column to projects table.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "0020"
down_revision = "0019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "projects",
        sa.Column(
            "workspace_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workspaces.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_projects_workspace_id", "projects", ["workspace_id"])


def downgrade() -> None:
    op.drop_index("ix_projects_workspace_id", table_name="projects")
    op.drop_column("projects", "workspace_id")
