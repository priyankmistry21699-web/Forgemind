"""Connector routes — registry, recommendation, and readiness endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.connector import (
    ConnectorRead,
    ConnectorList,
    ConnectorRecommendation,
    ProjectConnectorLinkCreate,
    ProjectConnectorLinkRead,
    ProjectConnectorReadinessUpdate,
    ProjectReadinessSummary,
    RunConnectorBlocker,
)
from app.services import connector_service

router = APIRouter()


@router.get("/connectors", response_model=ConnectorList)
async def list_connectors(
    db: AsyncSession = Depends(get_db),
) -> ConnectorList:
    """List all registered connectors."""
    connectors, total = await connector_service.list_connectors(db)
    return ConnectorList(
        items=[ConnectorRead.model_validate(c) for c in connectors],
        total=total,
    )


class ConnectorRequirements(BaseModel):
    recommendations: list[ConnectorRecommendation]
    total_required: int
    total_configured: int


@router.get(
    "/runs/{run_id}/connectors/requirements",
    response_model=ConnectorRequirements,
)
async def get_connector_requirements(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> ConnectorRequirements:
    """Analyse a run and recommend required external connectors."""
    from app.models.planner_result import PlannerResult
    from app.models.run import Run
    from app.models.project import Project
    from sqlalchemy import select

    # Get planner result for stack info
    pr_result = await db.execute(
        select(PlannerResult).where(PlannerResult.run_id == run_id)
    )
    planner_result = pr_result.scalar_one_or_none()

    stack = planner_result.recommended_stack if planner_result else None

    # Get project description from run

    run_r = await db.execute(select(Run).where(Run.id == run_id))
    run = run_r.scalar_one_or_none()
    description = None
    if run:
        proj_r = await db.execute(
            select(Project).where(Project.id == run.project_id)
        )
        project = proj_r.scalar_one_or_none()
        if project:
            description = project.description

    reqs = await connector_service.get_project_connector_requirements(
        db, stack, description
    )

    recommendations = [
        ConnectorRecommendation(
            connector_slug=r["slug"],
            connector_name=r["connector_name"],
            reason=r["reason"],
            priority=r["priority"],
            configured=r["configured"],
        )
        for r in reqs
    ]

    return ConnectorRequirements(
        recommendations=recommendations,
        total_required=sum(1 for r in recommendations if r.priority == "required"),
        total_configured=sum(1 for r in recommendations if r.configured),
    )


# ── FM-041: Project connector readiness endpoints ────────────────


@router.post(
    "/projects/{project_id}/connectors",
    response_model=ProjectConnectorLinkRead,
    status_code=status.HTTP_201_CREATED,
)
async def link_connector(
    project_id: uuid.UUID,
    body: ProjectConnectorLinkCreate,
    db: AsyncSession = Depends(get_db),
) -> ProjectConnectorLinkRead:
    """Link a connector to a project with a priority level."""
    link = await connector_service.link_connector_to_project(
        db,
        project_id,
        body.connector_slug,
        priority=body.priority,
        config_snapshot=body.config_snapshot,
    )
    # Fetch connector for slug/name
    connector = await connector_service.get_connector_by_slug(db, body.connector_slug)
    return ProjectConnectorLinkRead(
        id=link.id,
        project_id=link.project_id,
        connector_id=link.connector_id,
        connector_slug=connector.slug if connector else "unknown",
        connector_name=connector.name if connector else "Unknown",
        priority=link.priority,
        readiness=link.readiness,
        config_snapshot=link.config_snapshot,
        blocker_reason=link.blocker_reason,
        created_at=link.created_at,
        updated_at=link.updated_at,
    )


@router.get(
    "/projects/{project_id}/connectors/readiness",
    response_model=ProjectReadinessSummary,
)
async def get_readiness(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> ProjectReadinessSummary:
    """Get readiness summary for all connectors linked to a project."""
    summary = await connector_service.get_project_readiness(db, project_id)
    return ProjectReadinessSummary(
        links=[ProjectConnectorLinkRead(**item) for item in summary["links"]],
        total=summary["total"],
        ready_count=summary["ready_count"],
        configured_count=summary["configured_count"],
        blocked_count=summary["blocked_count"],
        missing_count=summary["missing_count"],
        all_required_ready=summary["all_required_ready"],
    )


@router.patch(
    "/projects/{project_id}/connectors/{connector_slug}/readiness",
    response_model=ProjectConnectorLinkRead,
)
async def update_readiness(
    project_id: uuid.UUID,
    connector_slug: str,
    body: ProjectConnectorReadinessUpdate,
    db: AsyncSession = Depends(get_db),
) -> ProjectConnectorLinkRead:
    """Update the readiness state of a project-connector link."""
    link = await connector_service.update_connector_readiness(
        db,
        project_id,
        connector_slug,
        readiness=body.readiness,
        blocker_reason=body.blocker_reason,
        config_snapshot=body.config_snapshot,
    )
    connector = await connector_service.get_connector_by_slug(db, connector_slug)
    return ProjectConnectorLinkRead(
        id=link.id,
        project_id=link.project_id,
        connector_id=link.connector_id,
        connector_slug=connector.slug if connector else "unknown",
        connector_name=connector.name if connector else "Unknown",
        priority=link.priority,
        readiness=link.readiness,
        config_snapshot=link.config_snapshot,
        blocker_reason=link.blocker_reason,
        created_at=link.created_at,
        updated_at=link.updated_at,
    )


class RunConnectorBlockers(BaseModel):
    blockers: list[RunConnectorBlocker]
    total: int
    has_required_blockers: bool


@router.get(
    "/runs/{run_id}/connectors/blockers",
    response_model=RunConnectorBlockers,
)
async def get_run_blockers(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> RunConnectorBlockers:
    """Get connectors that are blocking a run from proceeding."""
    blockers = await connector_service.get_run_connector_blockers(db, run_id)
    return RunConnectorBlockers(
        blockers=[RunConnectorBlocker(**b) for b in blockers],
        total=len(blockers),
        has_required_blockers=any(b["priority"] == "required" for b in blockers),
    )
