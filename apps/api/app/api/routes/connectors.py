"""Connector routes — registry and recommendation endpoints."""

import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.connector import ConnectorRead, ConnectorList, ConnectorRecommendation
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
