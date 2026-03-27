"""Cost tracking service — record and query LLM usage costs.

FM-047: Tracks per-call token usage and costs, with budget enforcement
and aggregation queries for cost dashboards.
"""

import uuid
import logging
from typing import Any

from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cost_record import CostRecord

logger = logging.getLogger(__name__)

# Simple cost-per-token rates (USD) — approximate, configurable
MODEL_COSTS: dict[str, dict[str, float]] = {
    "gpt-4o": {"prompt": 2.50 / 1_000_000, "completion": 10.00 / 1_000_000},
    "gpt-4o-mini": {"prompt": 0.15 / 1_000_000, "completion": 0.60 / 1_000_000},
    "gpt-4-turbo": {"prompt": 10.00 / 1_000_000, "completion": 30.00 / 1_000_000},
    "claude-3-opus": {"prompt": 15.00 / 1_000_000, "completion": 75.00 / 1_000_000},
    "claude-3-sonnet": {"prompt": 3.00 / 1_000_000, "completion": 15.00 / 1_000_000},
    "claude-3-haiku": {"prompt": 0.25 / 1_000_000, "completion": 1.25 / 1_000_000},
}

DEFAULT_COST = {"prompt": 1.00 / 1_000_000, "completion": 3.00 / 1_000_000}


def estimate_cost(model_name: str, prompt_tokens: int, completion_tokens: int) -> float:
    """Estimate USD cost from model name and token counts."""
    rates = MODEL_COSTS.get(model_name, DEFAULT_COST)
    return (
        prompt_tokens * rates["prompt"]
        + completion_tokens * rates["completion"]
    )


async def record_usage(
    db: AsyncSession,
    *,
    model_name: str,
    prompt_tokens: int,
    completion_tokens: int,
    project_id: uuid.UUID | None = None,
    run_id: uuid.UUID | None = None,
    task_id: uuid.UUID | None = None,
    caller: str = "unknown",
) -> CostRecord:
    """Record a single LLM call's token usage and cost."""
    total_tokens = prompt_tokens + completion_tokens
    cost_usd = estimate_cost(model_name, prompt_tokens, completion_tokens)

    record = CostRecord(
        model_name=model_name,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        cost_usd=cost_usd,
        project_id=project_id,
        run_id=run_id,
        task_id=task_id,
        caller=caller,
    )
    db.add(record)
    await db.flush()
    return record


async def get_run_cost_summary(
    db: AsyncSession,
    run_id: uuid.UUID,
) -> dict[str, Any]:
    """Get aggregated cost summary for a run."""
    result = await db.execute(
        select(
            sa_func.count(CostRecord.id).label("call_count"),
            sa_func.coalesce(sa_func.sum(CostRecord.prompt_tokens), 0).label("total_prompt_tokens"),
            sa_func.coalesce(sa_func.sum(CostRecord.completion_tokens), 0).label("total_completion_tokens"),
            sa_func.coalesce(sa_func.sum(CostRecord.total_tokens), 0).label("total_tokens"),
            sa_func.coalesce(sa_func.sum(CostRecord.cost_usd), 0.0).label("total_cost_usd"),
        ).where(CostRecord.run_id == run_id)
    )
    row = result.one()
    return {
        "run_id": str(run_id),
        "call_count": row.call_count,
        "total_prompt_tokens": row.total_prompt_tokens,
        "total_completion_tokens": row.total_completion_tokens,
        "total_tokens": row.total_tokens,
        "total_cost_usd": round(float(row.total_cost_usd), 6),
    }


async def get_project_cost_summary(
    db: AsyncSession,
    project_id: uuid.UUID,
) -> dict[str, Any]:
    """Get aggregated cost summary for a project across all runs."""
    result = await db.execute(
        select(
            sa_func.count(CostRecord.id).label("call_count"),
            sa_func.coalesce(sa_func.sum(CostRecord.total_tokens), 0).label("total_tokens"),
            sa_func.coalesce(sa_func.sum(CostRecord.cost_usd), 0.0).label("total_cost_usd"),
        ).where(CostRecord.project_id == project_id)
    )
    row = result.one()
    return {
        "project_id": str(project_id),
        "call_count": row.call_count,
        "total_tokens": row.total_tokens,
        "total_cost_usd": round(float(row.total_cost_usd), 6),
    }


async def get_cost_breakdown_by_model(
    db: AsyncSession,
    *,
    project_id: uuid.UUID | None = None,
    run_id: uuid.UUID | None = None,
) -> list[dict[str, Any]]:
    """Get cost breakdown grouped by model."""
    query = select(
        CostRecord.model_name,
        sa_func.count(CostRecord.id).label("call_count"),
        sa_func.sum(CostRecord.total_tokens).label("total_tokens"),
        sa_func.sum(CostRecord.cost_usd).label("total_cost_usd"),
    ).group_by(CostRecord.model_name)

    if project_id:
        query = query.where(CostRecord.project_id == project_id)
    if run_id:
        query = query.where(CostRecord.run_id == run_id)

    result = await db.execute(query)
    rows = result.all()
    return [
        {
            "model_name": row.model_name,
            "call_count": row.call_count,
            "total_tokens": int(row.total_tokens or 0),
            "total_cost_usd": round(float(row.total_cost_usd or 0), 6),
        }
        for row in rows
    ]


async def list_cost_records(
    db: AsyncSession,
    *,
    project_id: uuid.UUID | None = None,
    run_id: uuid.UUID | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[CostRecord], int]:
    """List individual cost records with filters."""
    query = select(CostRecord)
    if project_id:
        query = query.where(CostRecord.project_id == project_id)
    if run_id:
        query = query.where(CostRecord.run_id == run_id)

    count_result = await db.execute(
        select(sa_func.count()).select_from(query.subquery())
    )
    total = count_result.scalar_one()

    result = await db.execute(
        query.order_by(CostRecord.created_at.desc()).offset(offset).limit(limit)
    )
    records = list(result.scalars().all())
    return records, total
