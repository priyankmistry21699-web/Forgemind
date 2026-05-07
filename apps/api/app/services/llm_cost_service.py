"""FM-223: LLM cost tracking and optimizer.

Logs every LLM call with token counts and USD cost.
Provides a per-run cost summary and budget-pressure detection for
the model router (downgrade when > 80% of budget is spent).

Cost table (USD per 1K tokens — update as models evolve):
    gpt-4o             $0.005 input / $0.015 output
    gpt-4o-mini        $0.00015 input / $0.0006 output
    claude-3-5-sonnet  $0.003 input / $0.015 output
    gpt-4-turbo        $0.01 input / $0.03 output
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy import func as sa_func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_intelligence import LLMCallLog

logger = logging.getLogger(__name__)

# Cost per 1K tokens in USD (input, output)
_COST_TABLE: dict[str, tuple[float, float]] = {
    "gpt-4o": (0.005, 0.015),
    "gpt-4o-mini": (0.00015, 0.0006),
    "gpt-4o-2024-11-20": (0.005, 0.015),
    "claude-3-5-sonnet-20241022": (0.003, 0.015),
    "claude-3-haiku-20240307": (0.00025, 0.00125),
    "gemini-1.5-flash": (0.00035, 0.00105),
    "gemini-1.5-pro": (0.0035, 0.0105),
}
_DEFAULT_COST = (0.001, 0.003)


def estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """Return estimated USD cost for a single LLM call."""
    input_rate, output_rate = _COST_TABLE.get(model, _DEFAULT_COST)
    return (prompt_tokens / 1000 * input_rate) + (
        completion_tokens / 1000 * output_rate
    )


async def log_llm_call(
    db: AsyncSession,
    *,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    run_id: uuid.UUID | None = None,
    task_id: uuid.UUID | None = None,
    task_type: str | None = None,
    latency_ms: int | None = None,
    success: bool = True,
) -> LLMCallLog:
    """Persist a single LLM call log entry."""
    cost = estimate_cost(model, prompt_tokens, completion_tokens)
    entry = LLMCallLog(
        run_id=run_id,
        task_id=task_id,
        model=model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        cost_usd=cost,
        latency_ms=latency_ms,
        task_type=task_type,
        success=success,
    )
    db.add(entry)
    await db.flush()
    logger.debug(
        "llm_cost: model=%s prompt=%d completion=%d cost=$%.4f",
        model,
        prompt_tokens,
        completion_tokens,
        cost,
    )
    return entry


async def get_run_cost_summary(
    db: AsyncSession,
    run_id: uuid.UUID,
) -> dict[str, Any]:
    """Return aggregated cost stats for a run."""
    result = await db.execute(
        select(
            LLMCallLog.model,
            sa_func.count(LLMCallLog.id).label("calls"),
            sa_func.sum(LLMCallLog.prompt_tokens).label("prompt_tokens"),
            sa_func.sum(LLMCallLog.completion_tokens).label("completion_tokens"),
            sa_func.sum(LLMCallLog.cost_usd).label("total_cost_usd"),
        )
        .where(LLMCallLog.run_id == run_id)
        .group_by(LLMCallLog.model)
    )
    rows = result.all()

    by_model = []
    total_cost = 0.0
    total_calls = 0
    for row in rows:
        by_model.append(
            {
                "model": row.model,
                "calls": row.calls,
                "prompt_tokens": row.prompt_tokens or 0,
                "completion_tokens": row.completion_tokens or 0,
                "cost_usd": round(row.total_cost_usd or 0.0, 6),
            }
        )
        total_cost += row.total_cost_usd or 0.0
        total_calls += row.calls

    return {
        "run_id": str(run_id),
        "total_cost_usd": round(total_cost, 6),
        "total_calls": total_calls,
        "by_model": by_model,
    }


async def get_run_budget_pressure(
    db: AsyncSession,
    run_id: uuid.UUID,
    *,
    budget_usd: float | None = None,
) -> float:
    """Return budget_used_pct (0.0–1.0) for the model router."""
    if budget_usd is None or budget_usd <= 0:
        return 0.0
    result = await db.execute(
        select(sa_func.sum(LLMCallLog.cost_usd)).where(LLMCallLog.run_id == run_id)
    )
    spent = result.scalar_one() or 0.0
    return min(spent / budget_usd, 1.0)
