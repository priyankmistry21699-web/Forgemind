"""FM-161-170: Search, Knowledge & Organizational Memory tables

Revision ID: fm161_170_search_knowledge
Revises: (latest)
Create Date: 2026-04-13

New tables:
- search_index: Full-text search index
- conventions: Organizational conventions
- recommendations: Smart action recommendations

Column additions:
- artifacts: parent_version_id, version_tag (FM-168)
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON


revision = "fm161_170_search_knowledge"
down_revision = "0026"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── search_index ─────────────────────────────────────────
    op.create_table(
        "search_index",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "entity_type",
            sa.Enum(
                "task",
                "artifact",
                "comment",
                "run",
                "project",
                "knowledge",
                "annotation",
                "approval",
                "release_package",
                "spec",
                name="searchentitytype",
            ),
            nullable=False,
        ),
        sa.Column("entity_id", UUID(as_uuid=True), nullable=False),
        sa.Column(
            "project_id",
            UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "run_id",
            UUID(as_uuid=True),
            sa.ForeignKey("runs.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("title", sa.String(500), nullable=False, server_default=""),
        sa.Column("body", sa.Text, nullable=False, server_default=""),
        sa.Column("entity_status", sa.String(50), nullable=True),
        sa.Column("entity_meta", JSON, nullable=True),
        sa.Column(
            "author_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
    )
    op.create_index("ix_search_index_entity_type", "search_index", ["entity_type"])
    op.create_index("ix_search_index_entity_id", "search_index", ["entity_id"])
    op.create_index("ix_search_index_project_id", "search_index", ["project_id"])
    op.create_index(
        "ix_search_index_entity",
        "search_index",
        ["entity_type", "entity_id"],
        unique=True,
    )

    # ── conventions ──────────────────────────────────────────
    op.create_table(
        "conventions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "category",
            sa.Enum(
                "naming",
                "architecture",
                "quality",
                "security",
                "documentation",
                name="conventioncategory",
            ),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("rule_text", sa.Text, nullable=False),
        sa.Column(
            "enforcement_level",
            sa.Enum(
                "advisory", "recommended", "required", name="conventionenforcement"
            ),
            nullable=False,
            server_default="advisory",
        ),
        sa.Column("active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column(
            "author_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
    )
    op.create_index("ix_conventions_project_id", "conventions", ["project_id"])

    # ── recommendations ──────────────────────────────────────
    op.create_table(
        "recommendations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "rec_type",
            sa.Enum(
                "knowledge_gap",
                "stale_run",
                "similar_project",
                "convention_violation",
                "missing_approval",
                "reusable_pattern",
                "tech_debt",
                name="recommendationtype",
            ),
            nullable=False,
        ),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=True),
        sa.Column("entity_id", UUID(as_uuid=True), nullable=True),
        sa.Column("priority", sa.Integer, nullable=False, server_default="5"),
        sa.Column("dismissed", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("feedback", sa.String(50), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
    )
    op.create_index("ix_recommendations_project_id", "recommendations", ["project_id"])

    # ── artifact columns (FM-168) ────────────────────────────
    op.add_column(
        "artifacts",
        sa.Column(
            "parent_version_id",
            UUID(as_uuid=True),
            sa.ForeignKey("artifacts.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "artifacts",
        sa.Column("version_tag", sa.String(100), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("artifacts", "version_tag")
    op.drop_column("artifacts", "parent_version_id")
    op.drop_table("recommendations")
    op.drop_table("conventions")
    op.drop_table("search_index")
    # Drop enums
    sa.Enum(name="searchentitytype").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="conventioncategory").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="conventionenforcement").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="recommendationtype").drop(op.get_bind(), checkfirst=True)
