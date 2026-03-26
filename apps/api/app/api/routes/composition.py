"""Composition routes — team assembly and capability analysis endpoints."""

import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services import composition_service
from app.services import task_service

router = APIRouter()


class TeamComposition(BaseModel):
    required_capabilities: dict[str, int]
    assignments: dict[str, str]
    coverage: float
    gaps: list[str]
    agent_count: int


class CapabilityReport(BaseModel):
    """Available capability groups and taxonomy."""
    capability_groups: dict[str, list[str]]


@router.get("/composition/capabilities", response_model=CapabilityReport)
async def list_capabilities() -> CapabilityReport:
    """List all known capability groups and their skills."""
    return CapabilityReport(
        capability_groups=composition_service.CAPABILITY_TAXONOMY,
    )


@router.get("/runs/{run_id}/composition", response_model=TeamComposition)
async def get_run_composition(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> TeamComposition:
    """Analyse a run's task set and return the recommended agent team composition."""
    tasks, _ = await task_service.list_tasks_by_run(db, run_id)

    phases = [
        {
            "title": t.title,
            "description": t.description,
            "task_type": t.task_type,
        }
        for t in tasks
    ]
    result = await composition_service.compose_team(db, phases)
    return TeamComposition(**result)
