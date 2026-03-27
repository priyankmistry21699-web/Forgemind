"""Replay snapshot schemas — request/response models.

FM-046: Pydantic models for replay snapshots and trace inspection.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ReplaySnapshotRead(BaseModel):
    id: uuid.UUID
    task_id: uuid.UUID
    run_id: uuid.UUID
    project_id: uuid.UUID
    agent_slug: str
    input_snapshot: dict | None
    prompt_snapshot: str | None
    model_used: str | None
    temperature: float | None
    output_snapshot: dict | None
    error: str | None
    tokens_used: int
    duration_ms: int
    cost_usd: float
    replay_hash: str | None
    is_replay: bool
    original_snapshot_id: uuid.UUID | None
    sequence_number: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ReplaySnapshotList(BaseModel):
    items: list[ReplaySnapshotRead]
    total: int


class ReplaySnapshotCreate(BaseModel):
    task_id: uuid.UUID
    run_id: uuid.UUID
    project_id: uuid.UUID
    agent_slug: str
    input_snapshot: dict | None = None
    prompt_snapshot: str | None = None
    model_used: str | None = None
    temperature: float | None = None
    output_snapshot: dict | None = None
    error: str | None = None
    tokens_used: int = 0
    duration_ms: int = 0
    cost_usd: float = 0.0


class ReplayRequest(BaseModel):
    """Request to replay a specific snapshot."""
    snapshot_id: uuid.UUID


class ReplayCompare(BaseModel):
    """Comparison between original and replayed execution."""
    original: ReplaySnapshotRead
    replay: ReplaySnapshotRead
    output_match: bool
    diff_summary: str | None


class ExecutionTrace(BaseModel):
    """Full execution trace for a run — ordered sequence of snapshots."""
    run_id: uuid.UUID
    total_steps: int
    snapshots: list[ReplaySnapshotRead]
    total_tokens: int
    total_cost_usd: float
    total_duration_ms: int
