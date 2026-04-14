"""FM-171/175/178b: Workspace governance settings column,
SSO configurations table, and IP enforcement support.

Revision ID: fm171_175_governance_sso
Revises: fm171_180_enterprise_governance
Create Date: 2026-04-14
"""

from alembic import op
import sqlalchemy as sa

revision = "fm171_175_governance_sso"
down_revision = "fm171_180_enterprise_governance"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── FM-171: Governance settings JSON column on workspaces ──
    op.add_column(
        "workspaces",
        sa.Column("governance_settings", sa.JSON(), nullable=True),
    )

    # ── FM-175: SSO Configuration table ────────────────────────
    op.create_table(
        "sso_configurations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "workspace_id",
            sa.Uuid(),
            sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("provider_type", sa.String(20), nullable=False),
        sa.Column("display_name", sa.String(200), nullable=False),
        sa.Column("metadata_url", sa.Text(), nullable=True),
        sa.Column("entity_id", sa.String(500), nullable=True),
        sa.Column("sso_url", sa.Text(), nullable=True),
        sa.Column("certificate", sa.Text(), nullable=True),
        sa.Column("client_id", sa.String(300), nullable=True),
        sa.Column("client_secret_vault_ref", sa.String(200), nullable=True),
        sa.Column("issuer_url", sa.Text(), nullable=True),
        sa.Column("scopes", sa.JSON(), nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("1"),
        ),
        sa.Column(
            "auto_provision",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("1"),
        ),
        sa.Column(
            "created_by",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
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
    op.drop_table("sso_configurations")
    op.drop_column("workspaces", "governance_settings")
