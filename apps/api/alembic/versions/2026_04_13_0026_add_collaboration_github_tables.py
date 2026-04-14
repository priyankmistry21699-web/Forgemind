"""FM-141-160: Collaboration, UX & GitHub Integration tables.

Revision ID: 0026
Revises: 0025
Create Date: 2026-04-13

New tables:
- comments (FM-141)
- saved_views (FM-144)
- run_annotations (FM-146)
- approval_delegations (FM-148)
- github_installations (FM-151)
- repository_links (FM-151)
- external_events (FM-152)
- pull_request_links (FM-153)
- ci_pipeline_runs (FM-154)
- issue_links (FM-155)
- code_ownerships (FM-157)

Altered tables:
- tasks: add assignee_id, assigned_at (FM-147)
- approval_requests: add expires_at (FM-148)
- notifications: add category, group_key, dismissed_at (FM-149)
- user_presences: add project_id (FM-145)
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0026"
down_revision = "0025"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -- FM-141: Comments --
    op.create_table(
        "comments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "entity_type",
            sa.Enum(
                "run",
                "task",
                "artifact",
                "release_package",
                "approval_request",
                name="commententitytype",
            ),
            nullable=False,
        ),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "parent_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("comments.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "author_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("body", sa.Text, nullable=False),
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
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_comments_entity", "comments", ["entity_type", "entity_id"])
    op.create_index("ix_comments_author_id", "comments", ["author_id"])

    # -- FM-144: Saved Views --
    op.create_table(
        "saved_views",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "creator_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("filter_json", postgresql.JSON, nullable=True),
        sa.Column(
            "visibility",
            sa.Enum("private", "team", name="viewvisibility"),
            nullable=False,
            server_default="private",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_saved_views_project_id", "saved_views", ["project_id"])

    # -- FM-146: Run Annotations --
    op.create_table(
        "run_annotations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "run_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "author_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "annotation_type",
            sa.Enum("note", "warning", "decision", "question", name="annotationtype"),
            nullable=False,
        ),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column(
            "pinned_event_id",
            postgresql.UUID(as_uuid=True),
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
    op.create_index("ix_run_annotations_run_id", "run_annotations", ["run_id"])

    # -- FM-148: Approval Delegations --
    op.create_table(
        "approval_delegations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "delegator_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "delegate_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("active_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("active_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean, default=True, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # -- FM-147: Task assignment columns --
    op.add_column(
        "tasks",
        sa.Column(
            "assignee_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "tasks",
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_tasks_assignee_id", "tasks", ["assignee_id"])

    # -- FM-148: Approval expiry column --
    op.add_column(
        "approval_requests",
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )

    # -- FM-149: Notification digest columns --
    op.add_column(
        "notifications",
        sa.Column("category", sa.String(50), nullable=True),
    )
    op.add_column(
        "notifications",
        sa.Column("group_key", sa.String(200), nullable=True),
    )
    op.add_column(
        "notifications",
        sa.Column("dismissed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_notifications_category", "notifications", ["category"])

    # -- FM-145: Presence project_id column --
    op.add_column(
        "user_presences",
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_user_presences_project_id", "user_presences", ["project_id"])

    # -- FM-151: GitHub Installations --
    op.create_table(
        "github_installations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("installation_id", sa.BigInteger, nullable=False, unique=True),
        sa.Column("account_login", sa.String(200), nullable=False),
        sa.Column("account_type", sa.String(50), nullable=False),
        sa.Column(
            "connected_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("permissions", postgresql.JSON, nullable=True),
        sa.Column("is_active", sa.Boolean, default=True, nullable=False),
        sa.Column(
            "installed_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # -- FM-151: Repository Links --
    op.create_table(
        "repository_links",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "installation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("github_installations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("github_repo_id", sa.BigInteger, nullable=False),
        sa.Column("full_name", sa.String(300), nullable=False),
        sa.Column("default_branch", sa.String(200), server_default="main"),
        sa.Column("is_active", sa.Boolean, default=True, nullable=False),
        sa.Column(
            "linked_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_repository_links_project_id", "repository_links", ["project_id"]
    )

    # -- FM-152: External Events --
    op.create_table(
        "external_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "source",
            sa.Enum("github", "gitlab", "bitbucket", name="externaleventsource"),
            nullable=False,
        ),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("delivery_id", sa.String(200), nullable=True, unique=True),
        sa.Column(
            "repository_link_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("repository_links.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("payload", postgresql.JSON, nullable=False),
        sa.Column("processed", sa.Boolean, default=False, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # -- FM-153: Pull Request Links --
    op.create_table(
        "pull_request_links",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "repository_link_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("repository_links.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "run_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("runs.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("pr_number", sa.Integer, nullable=False),
        sa.Column("pr_title", sa.String(500), nullable=True),
        sa.Column("pr_url", sa.String(500), nullable=True),
        sa.Column("head_branch", sa.String(200), nullable=True),
        sa.Column("base_branch", sa.String(200), nullable=True),
        sa.Column(
            "status",
            sa.Enum("open", "closed", "merged", "draft", name="prstatus"),
            nullable=False,
            server_default="open",
        ),
        sa.Column("merged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # -- FM-154: CI Pipeline Runs --
    op.create_table(
        "ci_pipeline_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "repository_link_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("repository_links.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("external_run_id", sa.BigInteger, nullable=False),
        sa.Column("workflow_name", sa.String(200), nullable=False),
        sa.Column("head_sha", sa.String(40), nullable=True),
        sa.Column("branch", sa.String(200), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "queued",
                "in_progress",
                "success",
                "failure",
                "cancelled",
                name="cipipelinestatus",
            ),
            nullable=False,
        ),
        sa.Column("conclusion", sa.String(50), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # -- FM-155: Issue Links --
    op.create_table(
        "issue_links",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "repository_link_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("repository_links.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("issue_number", sa.Integer, nullable=False),
        sa.Column("title", sa.String(500), nullable=True),
        sa.Column("issue_url", sa.String(500), nullable=True),
        sa.Column(
            "status",
            sa.Enum("open", "closed", name="issuelinkstatus"),
            nullable=False,
            server_default="open",
        ),
        sa.Column("labels", postgresql.JSON, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # -- FM-157: Code Ownerships --
    op.create_table(
        "code_ownerships",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "repository_link_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("repository_links.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("file_pattern", sa.String(500), nullable=False),
        sa.Column(
            "owner_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("owner_team_name", sa.String(200), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("code_ownerships")
    op.drop_table("issue_links")
    op.drop_table("ci_pipeline_runs")
    op.drop_table("pull_request_links")
    op.drop_table("external_events")
    op.drop_table("repository_links")
    op.drop_table("github_installations")
    op.drop_index("ix_user_presences_project_id", table_name="user_presences")
    op.drop_column("user_presences", "project_id")
    op.drop_index("ix_notifications_category", table_name="notifications")
    op.drop_column("notifications", "dismissed_at")
    op.drop_column("notifications", "group_key")
    op.drop_column("notifications", "category")
    op.drop_column("approval_requests", "expires_at")
    op.drop_index("ix_tasks_assignee_id", table_name="tasks")
    op.drop_column("tasks", "assigned_at")
    op.drop_column("tasks", "assignee_id")
    op.drop_table("approval_delegations")
    op.drop_table("run_annotations")
    op.drop_table("saved_views")
    op.drop_index("ix_comments_author_id", table_name="comments")
    op.drop_index("ix_comments_entity", table_name="comments")
    op.drop_table("comments")
