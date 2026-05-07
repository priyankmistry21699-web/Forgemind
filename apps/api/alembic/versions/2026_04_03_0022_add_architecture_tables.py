"""FM-081–090: Add architecture intelligence tables.

Revision ID: 0022
Revises: 0021
Create Date: 2026-04-03

New tables:
- architecture_nodes: graph nodes representing components
- architecture_edges: directed edges between components
- architecture_snapshots: point-in-time architecture captures
- architecture_drifts: detected structural drift records
- architecture_rules: configurable architecture rules
- architecture_rule_results: evaluation results per rule
- change_impact_assessments: blast-radius analysis records

New enum types: arch_node_type, arch_edge_type, arch_source_type,
arch_edge_source_type, arch_node_status, drift_severity, drift_status,
arch_rule_category, arch_rule_severity, arch_rule_result_status,
impact_severity
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM as PgEnum, JSON, UUID

revision = "0022"
down_revision = "0021"
branch_labels = None
depends_on = None


# Enums use ``create_type=False`` so the implicit creation triggered by
# ``op.create_table`` does NOT re-issue ``CREATE TYPE`` (which would fail on
# fresh Postgres with DuplicateObjectError because the explicit
# ``.create(..., checkfirst=True)`` call has already created the type).
# The explicit creation below remains the only place enums are created.


def upgrade() -> None:
    # ── New enum types ───────────────────────────────────────────
    arch_node_type = PgEnum(
        "workspace",
        "project",
        "repository",
        "package",
        "module",
        "service",
        "component",
        "api",
        "interface",
        "datastore",
        "resource",
        "external_dependency",
        name="arch_node_type",
        create_type=False,
    )
    arch_node_type.create(op.get_bind(), checkfirst=True)

    arch_edge_type = PgEnum(
        "depends_on",
        "calls",
        "owns",
        "reads",
        "writes",
        "exposes",
        "imports",
        "deploys_to",
        "emits_event_to",
        "consumes_event_from",
        name="arch_edge_type",
        create_type=False,
    )
    arch_edge_type.create(op.get_bind(), checkfirst=True)

    arch_source_type = PgEnum(
        "inferred",
        "declared",
        "imported",
        name="arch_source_type",
        create_type=False,
    )
    arch_source_type.create(op.get_bind(), checkfirst=True)

    arch_edge_source_type = PgEnum(
        "inferred",
        "declared",
        "imported",
        name="arch_edge_source_type",
        create_type=False,
    )
    arch_edge_source_type.create(op.get_bind(), checkfirst=True)

    arch_node_status = PgEnum(
        "active",
        "deprecated",
        "removed",
        name="arch_node_status",
        create_type=False,
    )
    arch_node_status.create(op.get_bind(), checkfirst=True)

    drift_severity = PgEnum(
        "low",
        "medium",
        "high",
        "critical",
        name="drift_severity",
        create_type=False,
    )
    drift_severity.create(op.get_bind(), checkfirst=True)

    drift_status = PgEnum(
        "open",
        "resolved",
        "ignored",
        name="drift_status",
        create_type=False,
    )
    drift_status.create(op.get_bind(), checkfirst=True)

    arch_rule_category = PgEnum(
        "import",
        "layer",
        "ownership",
        "dependency",
        "boundary",
        name="arch_rule_category",
        create_type=False,
    )
    arch_rule_category.create(op.get_bind(), checkfirst=True)

    arch_rule_severity = PgEnum(
        "low",
        "medium",
        "high",
        "critical",
        name="arch_rule_severity",
        create_type=False,
    )
    arch_rule_severity.create(op.get_bind(), checkfirst=True)

    arch_rule_result_status = PgEnum(
        "pass",
        "violation",
        name="arch_rule_result_status",
        create_type=False,
    )
    arch_rule_result_status.create(op.get_bind(), checkfirst=True)

    impact_severity = PgEnum(
        "low",
        "medium",
        "high",
        "critical",
        name="impact_severity",
        create_type=False,
    )
    impact_severity.create(op.get_bind(), checkfirst=True)

    # ── architecture_nodes ───────────────────────────────────────
    op.create_table(
        "architecture_nodes",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "workspace_id",
            UUID(as_uuid=True),
            sa.ForeignKey("workspaces.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "project_id",
            UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "repo_id",
            UUID(as_uuid=True),
            sa.ForeignKey("repo_connections.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("node_type", arch_node_type, nullable=False, index=True),
        sa.Column("key", sa.String(500), nullable=False),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("path", sa.String(1000), nullable=True),
        sa.Column("language", sa.String(50), nullable=True),
        sa.Column("metadata", JSON, nullable=True),
        sa.Column(
            "source_type", arch_source_type, nullable=False, server_default="inferred"
        ),
        sa.Column(
            "status",
            arch_node_status,
            nullable=False,
            server_default="active",
            index=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    # ── architecture_edges ───────────────────────────────────────
    op.create_table(
        "architecture_edges",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "workspace_id",
            UUID(as_uuid=True),
            sa.ForeignKey("workspaces.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "project_id",
            UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "from_node_id",
            UUID(as_uuid=True),
            sa.ForeignKey("architecture_nodes.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "to_node_id",
            UUID(as_uuid=True),
            sa.ForeignKey("architecture_nodes.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("edge_type", arch_edge_type, nullable=False, index=True),
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("metadata", JSON, nullable=True),
        sa.Column(
            "source_type",
            arch_edge_source_type,
            nullable=False,
            server_default="inferred",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    # ── architecture_snapshots ───────────────────────────────────
    op.create_table(
        "architecture_snapshots",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "workspace_id",
            UUID(as_uuid=True),
            sa.ForeignKey("workspaces.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "project_id",
            UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("source", sa.String(200), nullable=True),
        sa.Column("summary", JSON, nullable=True),
        sa.Column("node_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("edge_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("snapshot_data", JSON, nullable=True),
        sa.Column(
            "generated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    # ── architecture_drifts ──────────────────────────────────────
    op.create_table(
        "architecture_drifts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("drift_type", sa.String(200), nullable=False),
        sa.Column("severity", drift_severity, nullable=False, index=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "source_snapshot_id",
            UUID(as_uuid=True),
            sa.ForeignKey("architecture_snapshots.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("comparison_target", sa.String(500), nullable=True),
        sa.Column(
            "status", drift_status, nullable=False, server_default="open", index=True
        ),
        sa.Column("metadata", JSON, nullable=True),
        sa.Column(
            "detected_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ── architecture_rules ───────────────────────────────────────
    op.create_table(
        "architecture_rules",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=True,
            index=True,
        ),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", arch_rule_category, nullable=False, index=True),
        sa.Column("rule_config", JSON, nullable=False),
        sa.Column(
            "enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")
        ),
        sa.Column(
            "severity", arch_rule_severity, nullable=False, server_default="medium"
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    # ── architecture_rule_results ────────────────────────────────
    op.create_table(
        "architecture_rule_results",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "rule_id",
            UUID(as_uuid=True),
            sa.ForeignKey("architecture_rules.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "project_id",
            UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("status", arch_rule_result_status, nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("details", JSON, nullable=True),
        sa.Column("violating_node_ids", JSON, nullable=True),
        sa.Column("violating_edge_ids", JSON, nullable=True),
        sa.Column(
            "evaluated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    # ── change_impact_assessments ────────────────────────────────
    op.create_table(
        "change_impact_assessments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "target_node_id",
            UUID(as_uuid=True),
            sa.ForeignKey("architecture_nodes.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("target_path", sa.String(1000), nullable=True),
        sa.Column("target_key", sa.String(500), nullable=True),
        sa.Column("severity", impact_severity, nullable=False),
        sa.Column("blast_radius", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("impacted_nodes", JSON, nullable=True),
        sa.Column("impacted_services", JSON, nullable=True),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("metadata", JSON, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )


def downgrade() -> None:
    # ── Drop tables (reverse creation order) ─────────────────────
    op.drop_table("change_impact_assessments")
    op.drop_table("architecture_rule_results")
    op.drop_table("architecture_rules")
    op.drop_table("architecture_drifts")
    op.drop_table("architecture_snapshots")
    op.drop_table("architecture_edges")
    op.drop_table("architecture_nodes")

    # ── Drop enum types ──────────────────────────────────────────
    sa.Enum(name="impact_severity").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="arch_rule_result_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="arch_rule_severity").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="arch_rule_category").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="drift_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="drift_severity").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="arch_node_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="arch_edge_source_type").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="arch_source_type").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="arch_edge_type").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="arch_node_type").drop(op.get_bind(), checkfirst=True)
