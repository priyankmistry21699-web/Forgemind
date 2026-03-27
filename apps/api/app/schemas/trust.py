"""Trust scoring schemas — response models for trust and risk assessment.

FM-050: Pydantic models for trust scores.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.trust_score import RiskLevel, EntityType


class TrustScoreRead(BaseModel):
    id: uuid.UUID
    entity_type: EntityType
    entity_id: uuid.UUID
    trust_score: float
    confidence: float
    risk_level: RiskLevel
    factors: dict | None
    project_id: uuid.UUID | None
    run_id: uuid.UUID | None
    assessed_at: datetime

    model_config = {"from_attributes": True}


class TrustScoreList(BaseModel):
    items: list[TrustScoreRead]
    total: int
