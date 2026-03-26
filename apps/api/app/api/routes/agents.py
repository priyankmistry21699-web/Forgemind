import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.agent import AgentRead, AgentList
from app.services import agent_service

router = APIRouter()


@router.get("/agents", response_model=AgentList)
async def list_agents(
    db: AsyncSession = Depends(get_db),
) -> AgentList:
    """List all registered agents."""
    agents, total = await agent_service.list_agents(db)
    return AgentList(
        items=[AgentRead.model_validate(a) for a in agents],
        total=total,
    )


@router.get("/agents/{agent_id}", response_model=AgentRead)
async def get_agent(
    agent_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> AgentRead:
    """Retrieve a single agent by ID."""
    agent = await agent_service.get_agent(db, agent_id)
    return AgentRead.model_validate(agent)
