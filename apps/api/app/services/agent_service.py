"""Agent service — registry operations and default agent seeding."""

import uuid

from fastapi import HTTPException, status
from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import Agent, AgentStatus


# Default fixed agents seeded on first access
DEFAULT_AGENTS = [
    {
        "name": "Planner",
        "slug": "planner",
        "description": "Analyzes prompts and generates structured project plans with phased task breakdowns.",
        "capabilities": ["prompt_analysis", "plan_generation", "architecture_recommendation"],
        "supported_task_types": ["planning"],
    },
    {
        "name": "Architect",
        "slug": "architect",
        "description": "Produces architecture documents, system design notes, and stack recommendations.",
        "capabilities": ["architecture_design", "system_modeling", "tech_stack_selection"],
        "supported_task_types": ["architecture"],
    },
    {
        "name": "Coder",
        "slug": "coder",
        "description": "Generates implementation drafts, code scaffolds, and feature code.",
        "capabilities": ["code_generation", "scaffolding", "feature_implementation"],
        "supported_task_types": ["codegen", "implementation"],
    },
    {
        "name": "Reviewer",
        "slug": "reviewer",
        "description": "Reviews code and artifacts, produces critique summaries and improvement suggestions.",
        "capabilities": ["code_review", "artifact_review", "quality_assessment"],
        "supported_task_types": ["review", "verification"],
    },
    {
        "name": "Tester",
        "slug": "tester",
        "description": "Creates test plans, generates test cases, and produces test reports.",
        "capabilities": ["test_planning", "test_generation", "test_execution"],
        "supported_task_types": ["testing"],
    },
]


async def seed_default_agents(db: AsyncSession) -> None:
    """Insert default agents if the agents table is empty."""
    count_result = await db.execute(
        select(sa_func.count()).select_from(select(Agent).subquery())
    )
    if count_result.scalar_one() > 0:
        return

    for agent_data in DEFAULT_AGENTS:
        agent = Agent(
            name=agent_data["name"],
            slug=agent_data["slug"],
            description=agent_data["description"],
            status=AgentStatus.ACTIVE,
            capabilities=agent_data["capabilities"],
            supported_task_types=agent_data["supported_task_types"],
        )
        db.add(agent)
    await db.flush()


async def list_agents(db: AsyncSession) -> tuple[list[Agent], int]:
    count_result = await db.execute(
        select(sa_func.count()).select_from(select(Agent).subquery())
    )
    total = count_result.scalar_one()

    result = await db.execute(select(Agent).order_by(Agent.name))
    agents = list(result.scalars().all())
    return agents, total


async def get_agent(db: AsyncSession, agent_id: uuid.UUID) -> Agent:
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found"
        )
    return agent


async def get_agent_by_slug(db: AsyncSession, slug: str) -> Agent | None:
    result = await db.execute(select(Agent).where(Agent.slug == slug))
    return result.scalar_one_or_none()


async def resolve_agent_for_task_type(db: AsyncSession, task_type: str) -> Agent | None:
    """Find the first active agent that supports the given task type."""
    result = await db.execute(
        select(Agent).where(Agent.status == AgentStatus.ACTIVE)
    )
    agents = list(result.scalars().all())
    for agent in agents:
        if agent.supported_task_types and task_type in agent.supported_task_types:
            return agent
    return None
