"""FM-131–134: Add release_packages, deployment_environments, release_gate_results tables.

Revision ID: 0025
Revises: 0024
Create Date: 2026-04-06

New tables:
- release_packages: versioned release bundles tied to a project + run
- deployment_environments: target environments (dev/staging/prod/canary)
- release_gate_results: per-gate pass/fail records for a release package
"""

from alembic import op
import sqlalchemy as sa

revision = "0025"
down_revision = "0024"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "deployment_environments",
        sa.Column(
            "id",
            sa.Uuid(),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("tier", sa.String(50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("config", sa.JSON(), nullable=True),
        sa.Column("required_gates", sa.JSON(), nullable=True),
        sa.Column("promotion_target_id", sa.Uuid(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["promotion_target_id"],
            ["deployment_environments.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_deployment_environments_project_id", "deployment_environments", ["project_id"])
    op.create_index("ix_deployment_environments_tier", "deployment_environments", ["tier"])

    op.create_table(
        "release_packages",
        sa.Column(
            "id",
            sa.Uuid(),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("version", sa.String(100), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="draft"),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("artifact_manifest", sa.JSON(), nullable=True),
        sa.Column("changelog", sa.JSON(), nullable=True),
        sa.Column("confidence_snapshot", sa.JSON(), nullable=True),
        sa.Column("rollback_metadata", sa.JSON(), nullable=True),
        sa.Column("target_environment_id", sa.Uuid(), nullable=True),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["run_id"], ["runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["target_environment_id"],
            ["deployment_environments.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_release_packages_project_id", "release_packages", ["project_id"])
    op.create_index("ix_release_packages_run_id", "release_packages", ["run_id"])
    op.create_index("ix_release_packages_status", "release_packages", ["status"])

    op.create_table(
        "release_gate_results",
        sa.Column(
            "id",
            sa.Uuid(),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("release_package_id", sa.Uuid(), nullable=False),
        sa.Column("gate_name", sa.String(200), nullable=False),
        sa.Column("gate_status", sa.String(50), nullable=False),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column(
            "evaluated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["release_package_id"],
            ["release_packages.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_release_gate_results_package_id",
        "release_gate_results",
        ["release_package_id"],
    )


def downgrade() -> None:
    op.drop_table("release_gate_results")
    op.drop_table("release_packages")
    op.drop_table("deployment_environments")
