"""Council schemas — request/response models for multi-agent council.

FM-047A: Pydantic models for council sessions and votes.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.council import CouncilStatus, DecisionMethod, VoteDecision


class CouncilVoteRead(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    agent_slug: str
    decision: VoteDecision
    reasoning: str | None
    confidence: float
    weight: float
    suggested_modifications: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}


class CouncilSessionRead(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    run_id: uuid.UUID | None
    task_id: uuid.UUID | None
    topic: str
    description: str | None
    context: dict | None
    status: CouncilStatus
    decision_method: DecisionMethod
    final_decision: str | None
    decision_rationale: str | None
    decision_metadata: dict | None
    convened_at: datetime
    decided_at: datetime | None
    votes: list[CouncilVoteRead]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CouncilSessionList(BaseModel):
    items: list[CouncilSessionRead]
    total: int


class ConveneCouncilRequest(BaseModel):
    project_id: uuid.UUID
    run_id: uuid.UUID | None = None
    task_id: uuid.UUID | None = None
    topic: str = Field(..., min_length=1, max_length=500)
    description: str | None = None
    context: dict | None = None
    decision_method: DecisionMethod = DecisionMethod.MAJORITY
    agent_slugs: list[str] = Field(default_factory=list)


class CastVoteRequest(BaseModel):
    agent_slug: str
    decision: VoteDecision
    reasoning: str | None = None
    confidence: float = Field(0.5, ge=0.0, le=1.0)
    suggested_modifications: dict | None = None


class CouncilDecisionResult(BaseModel):
    session_id: uuid.UUID
    status: CouncilStatus
    final_decision: str | None
    decision_rationale: str | None
    vote_summary: dict
