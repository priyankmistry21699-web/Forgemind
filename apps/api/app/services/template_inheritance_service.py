"""FM-116: Template inheritance service — resolves config from template → project.

Inheritance resolution order:
  1. System defaults (empty / safe baseline)
  2. Template defaults (if project was created from a template)
  3. Project overrides (explicit user configuration)

Each layer only overrides what it explicitly provides; unset fields
fall through to the previous layer.
"""

import uuid
import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.project_template import ProjectTemplate
from app.models.project_constitution import ProjectConstitution
from app.models.phase_agent_profile import PhaseAgentProfile, WorkflowPhase
from app.models.agent import Agent, AgentStatus
from app.services import constitution_service, phase_agent_profile_service, project_template_service
from app.schemas.phase_agent_profile import PhaseAgentProfileCreate
from app.schemas.constitution import ConstitutionCreate

from sqlalchemy import select

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# System defaults — baseline when no template is used
# ---------------------------------------------------------------------------

SYSTEM_DEFAULTS: dict[str, Any] = {
    "governance": {
        "require_spec_approval": False,
        "require_plan_approval": False,
        "auto_approve_minor_changes": True,
    },
}


# ---------------------------------------------------------------------------
# Core resolution
# ---------------------------------------------------------------------------


def resolve_governance_config(
    template: ProjectTemplate | None,
    project_override: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Resolve governance config: system → template → project override.

    Returns the merged config dict.
    """
    config = dict(SYSTEM_DEFAULTS["governance"])

    if template and template.default_governance_config:
        config.update(template.default_governance_config)

    if project_override:
        config.update(project_override)

    return config


# ---------------------------------------------------------------------------
# Template application — used during project creation (FM-115)
# ---------------------------------------------------------------------------


async def apply_template_to_project(
    db: AsyncSession,
    project: Project,
    template: ProjectTemplate,
) -> dict[str, Any]:
    """Apply a template's defaults to a newly created project.

    Seeds:
      - Constitution (if template provides one)
      - Phase-agent profiles (if template defines them)

    Returns a summary of what was applied.
    """
    applied: dict[str, Any] = {"template_slug": template.slug, "seeded": []}

    # 1. Seed constitution from template
    if template.constitution_template:
        tpl = template.constitution_template
        await constitution_service.create_or_update_constitution(
            db,
            project.id,
            ConstitutionCreate(
                content=tpl.get("content", ""),
                title=tpl.get("title"),
                summary=tpl.get("summary"),
            ),
        )
        applied["seeded"].append("constitution")

    # 2. Seed phase-agent profiles
    if template.default_phase_profiles:
        seeded_phases = await _seed_phase_profiles(
            db, project.id, template.default_phase_profiles
        )
        if seeded_phases:
            applied["seeded"].append("phase_profiles")
            applied["phase_profiles_created"] = seeded_phases

    return applied


async def _seed_phase_profiles(
    db: AsyncSession,
    project_id: uuid.UUID,
    profile_defs: list[dict[str, Any]],
) -> list[str]:
    """Create phase profiles from template definitions.

    Each definition should have: phase, agent_slug, and optionally priority.
    Agent is resolved by slug; missing/inactive agents are skipped.
    """
    seeded = []
    for pdef in profile_defs:
        phase_str = pdef.get("phase", "")
        agent_slug = pdef.get("agent_slug", "")
        priority = pdef.get("priority", 0)

        # Validate phase
        try:
            phase = WorkflowPhase(phase_str)
        except ValueError:
            logger.warning("Skipping invalid phase '%s' in template", phase_str)
            continue

        # Resolve agent by slug
        result = await db.execute(
            select(Agent).where(Agent.slug == agent_slug, Agent.status == AgentStatus.ACTIVE)
        )
        agent = result.scalar_one_or_none()
        if agent is None:
            logger.warning("Skipping phase %s — agent '%s' not found/active", phase_str, agent_slug)
            continue

        await phase_agent_profile_service.upsert_profile(
            db,
            project_id,
            PhaseAgentProfileCreate(
                phase=phase,
                agent_id=agent.id,
                priority=priority,
                is_default=True,
                notes=f"Seeded from template",
            ),
        )
        seeded.append(phase_str)

    return seeded
