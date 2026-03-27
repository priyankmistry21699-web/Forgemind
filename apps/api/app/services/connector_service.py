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
        if isinstance(recommended_stack, dict):
            search_text += " ".join(recommended_stack.values()).lower()
        elif isinstance(recommended_stack, list):
            search_text += " ".join(str(v) for v in recommended_stack).lower()
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


# ---------------------------------------------------------------------------
# FM-041: Connector readiness states — per-project link management
# ---------------------------------------------------------------------------

from app.models.project_connector_link import (
    ProjectConnectorLink,
    ConnectorReadiness,
    ConnectorPriority,
)


async def link_connector_to_project(
    db: AsyncSession,
    project_id: uuid.UUID,
    connector_slug: str,
    priority: ConnectorPriority = ConnectorPriority.RECOMMENDED,
    config_snapshot: dict | None = None,
) -> ProjectConnectorLink:
    """Create or update a project-connector link."""
    connector = await get_connector_by_slug(db, connector_slug)
    if connector is None:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Connector '{connector_slug}' not found",
        )

    # Check for existing link
    result = await db.execute(
        select(ProjectConnectorLink).where(
            ProjectConnectorLink.project_id == project_id,
            ProjectConnectorLink.connector_id == connector.id,
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        existing.priority = priority
        if config_snapshot is not None:
            existing.config_snapshot = config_snapshot
        await db.flush()
        await db.refresh(existing)
        return existing

    # Determine initial readiness based on connector status
    initial_readiness = ConnectorReadiness.MISSING
    if connector.status == ConnectorStatus.CONFIGURED:
        initial_readiness = ConnectorReadiness.CONFIGURED

    link = ProjectConnectorLink(
        project_id=project_id,
        connector_id=connector.id,
        priority=priority,
        readiness=initial_readiness,
        config_snapshot=config_snapshot,
    )
    db.add(link)
    await db.flush()
    await db.refresh(link)
    return link


async def get_project_readiness(
    db: AsyncSession,
    project_id: uuid.UUID,
) -> dict[str, Any]:
    """Get readiness summary for all connectors linked to a project."""
    result = await db.execute(
        select(ProjectConnectorLink)
        .where(ProjectConnectorLink.project_id == project_id)
        .order_by(ProjectConnectorLink.created_at)
    )
    links = list(result.scalars().all())

    items: list[dict[str, Any]] = []
    counts = {"ready": 0, "configured": 0, "blocked": 0, "missing": 0}

    for link in links:
        # Fetch connector for slug/name
        conn_result = await db.execute(
            select(Connector).where(Connector.id == link.connector_id)
        )
        connector = conn_result.scalar_one_or_none()

        item = {
            "id": link.id,
            "project_id": link.project_id,
            "connector_id": link.connector_id,
            "connector_slug": connector.slug if connector else "unknown",
            "connector_name": connector.name if connector else "Unknown",
            "priority": link.priority,
            "readiness": link.readiness,
            "config_snapshot": link.config_snapshot,
            "blocker_reason": link.blocker_reason,
            "created_at": link.created_at,
            "updated_at": link.updated_at,
        }
        items.append(item)
        counts[link.readiness.value] = counts.get(link.readiness.value, 0) + 1

    # Check if all required connectors are ready
    required_links = [l for l in links if l.priority == ConnectorPriority.REQUIRED]
    all_required_ready = all(
        l.readiness == ConnectorReadiness.READY for l in required_links
    ) if required_links else True

    return {
        "links": items,
        "total": len(links),
        "ready_count": counts["ready"],
        "configured_count": counts["configured"],
        "blocked_count": counts["blocked"],
        "missing_count": counts["missing"],
        "all_required_ready": all_required_ready,
    }


async def update_connector_readiness(
    db: AsyncSession,
    project_id: uuid.UUID,
    connector_slug: str,
    readiness: ConnectorReadiness,
    blocker_reason: str | None = None,
    config_snapshot: dict | None = None,
) -> ProjectConnectorLink:
    """Update the readiness state of a project-connector link."""
    connector = await get_connector_by_slug(db, connector_slug)
    if connector is None:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Connector '{connector_slug}' not found",
        )

    result = await db.execute(
        select(ProjectConnectorLink).where(
            ProjectConnectorLink.project_id == project_id,
            ProjectConnectorLink.connector_id == connector.id,
        )
    )
    link = result.scalar_one_or_none()
    if link is None:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No link found for connector '{connector_slug}' in this project",
        )

    link.readiness = readiness
    if blocker_reason is not None:
        link.blocker_reason = blocker_reason
    if readiness != ConnectorReadiness.BLOCKED:
        link.blocker_reason = None
    if config_snapshot is not None:
        link.config_snapshot = config_snapshot
    await db.flush()
    await db.refresh(link)
    return link


async def get_run_connector_blockers(
    db: AsyncSession,
    run_id: uuid.UUID,
) -> list[dict[str, Any]]:
    """Get connectors that are blocking a run from proceeding."""
    from app.models.run import Run

    run_result = await db.execute(select(Run).where(Run.id == run_id))
    run = run_result.scalar_one_or_none()
    if run is None:
        return []

    result = await db.execute(
        select(ProjectConnectorLink)
        .where(ProjectConnectorLink.project_id == run.project_id)
        .where(
            ProjectConnectorLink.readiness.in_([
                ConnectorReadiness.MISSING,
                ConnectorReadiness.BLOCKED,
            ])
        )
    )
    blocking_links = list(result.scalars().all())

    blockers: list[dict[str, Any]] = []
    for link in blocking_links:
        conn_result = await db.execute(
            select(Connector).where(Connector.id == link.connector_id)
        )
        connector = conn_result.scalar_one_or_none()
        blockers.append({
            "connector_slug": connector.slug if connector else "unknown",
            "connector_name": connector.name if connector else "Unknown",
            "priority": link.priority.value,
            "readiness": link.readiness.value,
            "blocker_reason": link.blocker_reason,
        })

    return blockers


async def auto_link_connectors_for_project(
    db: AsyncSession,
    project_id: uuid.UUID,
    recommended_stack: dict[str, str] | None,
    project_description: str | None,
) -> list[ProjectConnectorLink]:
    """Auto-link recommended connectors to a project based on stack analysis."""
    recs = recommend_connectors(recommended_stack, project_description)
    links: list[ProjectConnectorLink] = []

    for rec in recs:
        priority_map = {
            "required": ConnectorPriority.REQUIRED,
            "recommended": ConnectorPriority.RECOMMENDED,
            "optional": ConnectorPriority.OPTIONAL,
        }
        priority = priority_map.get(rec["priority"], ConnectorPriority.RECOMMENDED)

        try:
            link = await link_connector_to_project(
                db, project_id, rec["slug"], priority=priority
            )
            links.append(link)
        except Exception:
            logger.warning("Failed to auto-link connector %s", rec["slug"])

    return links
