"""FM-111–117: Add phase routing, project templates, and constitution suggestions.

Revision ID: 0023
Revises: 0022
Create Date: 2026-04-06

New tables:
- project_templates: reusable project presets
- phase_agent_profiles: per-project phase-to-agent assignments
- constitution_suggestions: knowledge-driven constitution improvement proposals

Modified tables:
- projects: add template_id foreign key
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0023"
down_revision = "0022"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- project_templates ---
    op.create_table(
        "project_templates",
        sa.Column(
            "id", sa.Uuid(), nullable=False, server_default=sa.text("gen_random_uuid()")
        ),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "category", sa.String(length=60), nullable=False, server_default="general"
        ),
        sa.Column("constitution_template", sa.Text(), nullable=True),
        sa.Column(
            "default_governance_config",
            postgresql.JSON(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "default_phase_profiles",
            postgresql.JSON(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "suggested_task_types",
            postgresql.JSON(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "spec_defaults", postgresql.JSON(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "plan_defaults", postgresql.JSON(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "is_builtin", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        sa.Column(
            "is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )

    # --- projects.template_id ---
    op.add_column(
        "projects",
        sa.Column("template_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "fk_projects_template_id",
        "projects",
        "project_templates",
        ["template_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # --- phase_agent_profiles ---
    op.create_table(
        "phase_agent_profiles",
        sa.Column(
            "id", sa.Uuid(), nullable=False, server_default=sa.text("gen_random_uuid()")
        ),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column(
            "phase",
            sa.Enum(
                "specify",
                "plan",
                "tasks",
                "implement",
                "review",
                "validate",
                name="workflowphase",
            ),
            nullable=False,
        ),
        sa.Column("agent_id", sa.Uuid(), nullable=False),
        sa.Column(
            "priority", sa.Integer(), nullable=False, server_default=sa.text("0")
        ),
        sa.Column(
            "is_default", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("project_id", "phase", name="uq_project_phase"),
    )
    op.create_index(
        "ix_phase_agent_profiles_project_id", "phase_agent_profiles", ["project_id"]
    )

    # --- constitution_suggestions ---
    op.create_table(
        "constitution_suggestions",
        sa.Column(
            "id", sa.Uuid(), nullable=False, server_default=sa.text("gen_random_uuid()")
        ),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("suggested_text", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=80), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "pending", "accepted", "rejected", "expired", name="suggestionstatus"
            ),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "source_metadata", postgresql.JSON(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
    )
    op.create_index(
        "ix_constitution_suggestions_project_id",
        "constitution_suggestions",
        ["project_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_constitution_suggestions_project_id", table_name="constitution_suggestions"
    )
    op.drop_table("constitution_suggestions")
    op.drop_index(
        "ix_phase_agent_profiles_project_id", table_name="phase_agent_profiles"
    )
    op.drop_table("phase_agent_profiles")
    op.drop_constraint("fk_projects_template_id", "projects", type_="foreignkey")
    op.drop_column("projects", "template_id")
    op.drop_table("project_templates")
    sa.Enum(name="workflowphase").drop(op.get_bind())
    sa.Enum(name="suggestionstatus").drop(op.get_bind())
