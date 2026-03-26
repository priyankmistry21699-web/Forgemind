"""Composition service — capability-based agent team assembly.

Analyzes a plan's task set and determines which agent roles are required,
composes an optimal team from available agents, and supports dynamic role
selection beyond the fixed core agents.
"""

import logging
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import Agent, AgentStatus

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Capability taxonomy — maps high-level capabilities to concrete skills
# ---------------------------------------------------------------------------

CAPABILITY_TAXONOMY: dict[str, list[str]] = {
    "planning": ["prompt_analysis", "plan_generation", "requirements_analysis"],
    "architecture": ["architecture_design", "system_modeling", "tech_stack_selection"],
    "codegen": ["code_generation", "scaffolding", "feature_implementation"],
    "review": ["code_review", "artifact_review", "quality_assessment"],
    "testing": ["test_planning", "test_generation", "test_execution"],
    "deployment": ["deployment_planning", "infrastructure_setup", "ci_cd"],
    "documentation": ["doc_generation", "api_docs", "user_guides"],
    "security": ["security_review", "vulnerability_assessment", "threat_modeling"],
}


def derive_required_capabilities(phases: list[dict[str, Any]]) -> dict[str, int]:
    """Derive required capability groups from a list of plan phases.

    Returns a dict mapping capability group → count of tasks needing it.
    """
    requirements: dict[str, int] = {}
    for phase in phases:
        task_type = phase.get("task_type", "generic")
        # Direct match
        if task_type in CAPABILITY_TAXONOMY:
            requirements[task_type] = requirements.get(task_type, 0) + 1
        else:
            # Try to infer from title/description keywords
            text = f"{phase.get('title', '')} {phase.get('description', '')}".lower()
            for cap_group, skills in CAPABILITY_TAXONOMY.items():
                if cap_group in text or any(s.replace("_", " ") in text for s in skills):
                    requirements[cap_group] = requirements.get(cap_group, 0) + 1
                    break
    return requirements


async def get_available_agents(db: AsyncSession) -> list[Agent]:
    """Get all active agents."""
    result = await db.execute(
        select(Agent).where(Agent.status == AgentStatus.ACTIVE)
    )
    return list(result.scalars().all())


def score_agent_for_capability(
    agent: Agent,
    capability_group: str,
) -> float:
    """Score how well an agent matches a capability group (0.0 to 1.0)."""
    if not agent.capabilities and not agent.supported_task_types:
        return 0.0

    score = 0.0

    # Direct task_type match — strongest signal
    if agent.supported_task_types and capability_group in agent.supported_task_types:
        score += 0.6

    # Capability overlap — check how many of the taxonomy skills the agent has
    taxonomy_skills = set(CAPABILITY_TAXONOMY.get(capability_group, []))
    if taxonomy_skills and agent.capabilities:
        agent_caps = set(agent.capabilities)
        overlap = len(taxonomy_skills & agent_caps)
        if taxonomy_skills:
            score += 0.4 * (overlap / len(taxonomy_skills))

    return min(score, 1.0)


async def compose_team(
    db: AsyncSession,
    phases: list[dict[str, Any]],
) -> dict[str, Any]:
    """Compose an agent team for a given set of plan phases.

    Returns a team composition dict with:
        required_capabilities: dict of capability_group → count
        assignments: dict of capability_group → agent slug
        coverage: float (0.0-1.0) — fraction of requirements covered
        gaps: list of capability groups with no suitable agent
    """
    requirements = derive_required_capabilities(phases)
    agents = await get_available_agents(db)

    assignments: dict[str, str] = {}
    gaps: list[str] = []

    for cap_group in requirements:
        best_agent: Agent | None = None
        best_score = 0.0

        for agent in agents:
            s = score_agent_for_capability(agent, cap_group)
            if s > best_score:
                best_score = s
                best_agent = agent

        if best_agent and best_score > 0.0:
            assignments[cap_group] = best_agent.slug
        else:
            gaps.append(cap_group)

    total = len(requirements)
    covered = total - len(gaps)
    coverage = covered / total if total > 0 else 1.0

    return {
        "required_capabilities": requirements,
        "assignments": assignments,
        "coverage": coverage,
        "gaps": gaps,
        "agent_count": len(set(assignments.values())),
    }


async def resolve_agent_for_task(
    db: AsyncSession,
    task_type: str,
    agent_hint: str | None = None,
) -> str | None:
    """Resolve the best agent slug for a task, using hint or capability matching.

    Priority:
    1. agent_hint if the agent exists and is active
    2. Capability-based scoring against active agents
    3. None if no match
    """
    agents = await get_available_agents(db)

    # 1. Try hint first
    if agent_hint:
        for agent in agents:
            if agent.slug == agent_hint:
                return agent.slug

    # 2. Capability-based scoring
    best_slug: str | None = None
    best_score = 0.0
    for agent in agents:
        s = score_agent_for_capability(agent, task_type)
        if s > best_score:
            best_score = s
            best_slug = agent.slug

    return best_slug if best_score > 0.0 else None
