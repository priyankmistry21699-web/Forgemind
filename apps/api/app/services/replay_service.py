"""Replay and trace inspection service — capture, replay, and compare executions.

FM-046: Provides:
- Snapshot capture for every agent execution
- Full execution trace reconstruction for runs
- Replay of individual snapshots for verification
- Comparison between original and replayed outputs
"""

import hashlib
import json
import uuid
import logging
from typing import Any

from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.replay_snapshot import ReplaySnapshot
from app.models.task import Task
from app.models.run import Run

logger = logging.getLogger(__name__)


def _compute_replay_hash(
    agent_slug: str,
    input_snapshot: dict | None,
    prompt_snapshot: str | None,
    model_used: str | None,
    temperature: float | None,
) -> str:
    """Compute a deterministic hash from execution inputs for deduplication."""
    payload = json.dumps(
        {
            "agent_slug": agent_slug,
            "input": input_snapshot,
            "prompt": prompt_snapshot,
            "model": model_used,
            "temperature": temperature,
        },
        sort_keys=True,
        default=str,
    )
    return hashlib.sha256(payload.encode()).hexdigest()


async def capture_snapshot(
    db: AsyncSession,
    *,
    task_id: uuid.UUID,
    run_id: uuid.UUID,
    project_id: uuid.UUID,
    agent_slug: str,
    input_snapshot: dict | None = None,
    prompt_snapshot: str | None = None,
    model_used: str | None = None,
    temperature: float | None = None,
    output_snapshot: dict | None = None,
    error: str | None = None,
    tokens_used: int = 0,
    duration_ms: int = 0,
    cost_usd: float = 0.0,
    is_replay: bool = False,
    original_snapshot_id: uuid.UUID | None = None,
) -> ReplaySnapshot:
    """Capture an execution snapshot for replay."""
    # Compute sequence number
    count_result = await db.execute(
        select(sa_func.count()).select_from(
            select(ReplaySnapshot)
            .where(ReplaySnapshot.run_id == run_id)
            .subquery()
        )
    )
    seq = count_result.scalar_one()

    replay_hash = _compute_replay_hash(
        agent_slug, input_snapshot, prompt_snapshot, model_used, temperature
    )

    snapshot = ReplaySnapshot(
        task_id=task_id,
        run_id=run_id,
        project_id=project_id,
        agent_slug=agent_slug,
        input_snapshot=input_snapshot,
        prompt_snapshot=prompt_snapshot,
        model_used=model_used,
        temperature=temperature,
        output_snapshot=output_snapshot,
        error=error,
        tokens_used=tokens_used,
        duration_ms=duration_ms,
        cost_usd=cost_usd,
        replay_hash=replay_hash,
        is_replay=is_replay,
        original_snapshot_id=original_snapshot_id,
        sequence_number=seq,
    )
    db.add(snapshot)
    await db.flush()
    return snapshot


async def get_snapshot(
    db: AsyncSession,
    snapshot_id: uuid.UUID,
) -> ReplaySnapshot | None:
    """Retrieve a single replay snapshot by ID."""
    result = await db.execute(
        select(ReplaySnapshot).where(ReplaySnapshot.id == snapshot_id)
    )
    return result.scalar_one_or_none()


async def get_execution_trace(
    db: AsyncSession,
    run_id: uuid.UUID,
) -> dict[str, Any]:
    """Build the full execution trace for a run — ordered list of snapshots."""
    result = await db.execute(
        select(ReplaySnapshot)
        .where(ReplaySnapshot.run_id == run_id)
        .where(ReplaySnapshot.is_replay == False)  # noqa: E712
        .order_by(ReplaySnapshot.sequence_number.asc())
    )
    snapshots = list(result.scalars().all())

    total_tokens = sum(s.tokens_used for s in snapshots)
    total_cost = sum(s.cost_usd for s in snapshots)
    total_duration = sum(s.duration_ms for s in snapshots)

    return {
        "run_id": str(run_id),
        "total_steps": len(snapshots),
        "snapshots": snapshots,
        "total_tokens": total_tokens,
        "total_cost_usd": round(total_cost, 6),
        "total_duration_ms": total_duration,
    }


async def get_task_snapshots(
    db: AsyncSession,
    task_id: uuid.UUID,
) -> list[ReplaySnapshot]:
    """Get all snapshots for a specific task."""
    result = await db.execute(
        select(ReplaySnapshot)
        .where(ReplaySnapshot.task_id == task_id)
        .order_by(ReplaySnapshot.sequence_number.asc())
    )
    return list(result.scalars().all())


async def replay_snapshot(
    db: AsyncSession,
    snapshot_id: uuid.UUID,
) -> dict[str, Any]:
    """Replay a snapshot — re-execute with identical inputs and compare.

    Note: In a real system, this would call the LLM again. Here we create
    a replay record referencing the original. Actual re-execution would be
    triggered by the execution service.
    """
    original = await get_snapshot(db, snapshot_id)
    if original is None:
        return {"error": f"Snapshot {snapshot_id} not found"}

    # Create a replay snapshot (marking it as a replay)
    replay = await capture_snapshot(
        db,
        task_id=original.task_id,
        run_id=original.run_id,
        project_id=original.project_id,
        agent_slug=original.agent_slug,
        input_snapshot=original.input_snapshot,
        prompt_snapshot=original.prompt_snapshot,
        model_used=original.model_used,
        temperature=original.temperature,
        output_snapshot=original.output_snapshot,  # Same output for now
        tokens_used=original.tokens_used,
        duration_ms=original.duration_ms,
        cost_usd=original.cost_usd,
        is_replay=True,
        original_snapshot_id=original.id,
    )

    return {
        "original_id": str(original.id),
        "replay_id": str(replay.id),
        "replay_hash": replay.replay_hash,
        "output_match": True,  # Same output since no real re-execution
        "message": "Replay snapshot created. Wire up LLM re-execution for live comparison.",
    }


async def compare_snapshots(
    db: AsyncSession,
    original_id: uuid.UUID,
    replay_id: uuid.UUID,
) -> dict[str, Any]:
    """Compare original and replay snapshot outputs."""
    original = await get_snapshot(db, original_id)
    replay = await get_snapshot(db, replay_id)

    if original is None or replay is None:
        return {"error": "One or both snapshots not found"}

    orig_out = json.dumps(original.output_snapshot, sort_keys=True, default=str)
    replay_out = json.dumps(replay.output_snapshot, sort_keys=True, default=str)
    output_match = orig_out == replay_out

    diff_summary = None
    if not output_match:
        diff_summary = f"Outputs differ. Original length: {len(orig_out)}, Replay length: {len(replay_out)}"

    return {
        "original_id": str(original_id),
        "replay_id": str(replay_id),
        "output_match": output_match,
        "diff_summary": diff_summary,
        "original_hash": original.replay_hash,
        "replay_hash": replay.replay_hash,
    }


async def list_snapshots(
    db: AsyncSession,
    *,
    run_id: uuid.UUID | None = None,
    task_id: uuid.UUID | None = None,
    project_id: uuid.UUID | None = None,
    include_replays: bool = False,
    limit: int = 100,
    offset: int = 0,
) -> tuple[list[ReplaySnapshot], int]:
    """List snapshots with optional filters."""
    query = select(ReplaySnapshot)

    if run_id:
        query = query.where(ReplaySnapshot.run_id == run_id)
    if task_id:
        query = query.where(ReplaySnapshot.task_id == task_id)
    if project_id:
        query = query.where(ReplaySnapshot.project_id == project_id)
    if not include_replays:
        query = query.where(ReplaySnapshot.is_replay == False)  # noqa: E712

    count_result = await db.execute(
        select(sa_func.count()).select_from(query.subquery())
    )
    total = count_result.scalar_one()

    result = await db.execute(
        query.order_by(ReplaySnapshot.sequence_number.asc())
        .offset(offset)
        .limit(limit)
    )
    return list(result.scalars().all()), total
