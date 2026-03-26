"""Connector service — registry, recommendation, and requirement analysis."""

import uuid
import logging
from typing import Any

from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.connector import Connector, ConnectorStatus

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Default connector definitions — seeded on first access
# ---------------------------------------------------------------------------

DEFAULT_CONNECTORS = [
    {
        "name": "GitHub",
        "slug": "github",
        "description": "Source code hosting, pull requests, and CI/CD triggers.",
        "connector_type": "source_control",
        "capabilities": ["git_clone", "pull_request", "code_review", "ci_trigger"],
    },
    {
        "name": "Docker",
        "slug": "docker",
        "description": "Container builds, image registry, and deployment targets.",
        "connector_type": "container",
        "capabilities": ["image_build", "container_run", "registry_push"],
    },
    {
        "name": "PostgreSQL",
        "slug": "postgresql",
        "description": "Relational database for application data.",
        "connector_type": "database",
        "capabilities": ["sql_query", "migration", "schema_management"],
    },
    {
        "name": "Redis",
        "slug": "redis",
        "description": "In-memory cache and message broker.",
        "connector_type": "cache",
        "capabilities": ["caching", "pub_sub", "session_store"],
    },
    {
        "name": "AWS S3 / MinIO",
        "slug": "object-storage",
        "description": "Object storage for files, artifacts, and blobs.",
        "connector_type": "storage",
        "capabilities": ["file_upload", "file_download", "presigned_url"],
    },
    {
        "name": "Slack",
        "slug": "slack",
        "description": "Team notifications and approval alerts.",
        "connector_type": "notification",
        "capabilities": ["message_send", "channel_notify", "approval_alert"],
    },
    {
        "name": "Jira",
        "slug": "jira",
        "description": "Project tracking and issue management integration.",
        "connector_type": "project_management",
        "capabilities": ["issue_create", "issue_update", "sprint_tracking"],
    },
]

# ---------------------------------------------------------------------------
# Keyword-based recommendation mapping
# ---------------------------------------------------------------------------

STACK_CONNECTOR_MAP: dict[str, list[dict[str, str]]] = {
    "github": [{"slug": "github", "priority": "required", "reason": "Source code hosting and collaboration"}],
    "git": [{"slug": "github", "priority": "required", "reason": "Version control system integration"}],
    "docker": [{"slug": "docker", "priority": "required", "reason": "Containerized deployment"}],
    "kubernetes": [{"slug": "docker", "priority": "required", "reason": "Container orchestration requires Docker"}],
    "postgres": [{"slug": "postgresql", "priority": "required", "reason": "Primary database"}],
    "postgresql": [{"slug": "postgresql", "priority": "required", "reason": "Primary database"}],
    "redis": [{"slug": "redis", "priority": "recommended", "reason": "Caching and message broker"}],
    "s3": [{"slug": "object-storage", "priority": "recommended", "reason": "Object/file storage"}],
    "minio": [{"slug": "object-storage", "priority": "recommended", "reason": "Local object storage"}],
    "slack": [{"slug": "slack", "priority": "optional", "reason": "Team notifications"}],
    "jira": [{"slug": "jira", "priority": "optional", "reason": "Issue tracking integration"}],
    "api": [{"slug": "github", "priority": "recommended", "reason": "API projects benefit from CI/CD"}],
    "web": [{"slug": "docker", "priority": "recommended", "reason": "Web apps benefit from containerized deployment"}],
    "microservice": [
        {"slug": "docker", "priority": "required", "reason": "Microservices require containerization"},
        {"slug": "redis", "priority": "recommended", "reason": "Inter-service communication"},
    ],
}


async def seed_default_connectors(db: AsyncSession) -> None:
    """Insert default connectors if the connectors table is empty."""
    count_result = await db.execute(
        select(sa_func.count()).select_from(select(Connector).subquery())
    )
    if count_result.scalar_one() > 0:
        return

    for conn_data in DEFAULT_CONNECTORS:
        connector = Connector(
            name=conn_data["name"],
            slug=conn_data["slug"],
            description=conn_data["description"],
            connector_type=conn_data["connector_type"],
            status=ConnectorStatus.AVAILABLE,
            capabilities=conn_data["capabilities"],
        )
        db.add(connector)
    await db.flush()


async def list_connectors(db: AsyncSession) -> tuple[list[Connector], int]:
    """List all registered connectors."""
    count_result = await db.execute(
        select(sa_func.count()).select_from(select(Connector).subquery())
    )
    total = count_result.scalar_one()

    result = await db.execute(select(Connector).order_by(Connector.name))
    connectors = list(result.scalars().all())
    return connectors, total


async def get_connector_by_slug(db: AsyncSession, slug: str) -> Connector | None:
    """Get a connector by its slug."""
    result = await db.execute(select(Connector).where(Connector.slug == slug))
    return result.scalar_one_or_none()


def recommend_connectors(
    recommended_stack: dict[str, str] | None,
    project_description: str | None,
) -> list[dict[str, Any]]:
    """Recommend connectors based on project stack and description.

    Returns a deduplicated list of recommendations with priority and reason.
    """
    search_text = ""
    if recommended_stack:
        search_text += " ".join(recommended_stack.values()).lower()
    if project_description:
        search_text += " " + project_description.lower()

    seen_slugs: set[str] = set()
    recommendations: list[dict[str, Any]] = []

    for keyword, recs in STACK_CONNECTOR_MAP.items():
        if keyword in search_text:
            for rec in recs:
                if rec["slug"] not in seen_slugs:
                    seen_slugs.add(rec["slug"])
                    recommendations.append(rec)

    # Sort: required > recommended > optional
    priority_order = {"required": 0, "recommended": 1, "optional": 2}
    recommendations.sort(key=lambda r: priority_order.get(r["priority"], 3))

    return recommendations


async def get_project_connector_requirements(
    db: AsyncSession,
    recommended_stack: dict[str, str] | None,
    project_description: str | None,
) -> list[dict[str, Any]]:
    """Get connector requirements for a project, checking configured status."""
    recs = recommend_connectors(recommended_stack, project_description)

    for rec in recs:
        connector = await get_connector_by_slug(db, rec["slug"])
        rec["connector_name"] = connector.name if connector else rec["slug"]
        rec["configured"] = (
            connector is not None
            and connector.status == ConnectorStatus.CONFIGURED
        )

    return recs
