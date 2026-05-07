"""FM-236/237: Budget forecasting and cost attribution service."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func as sa_func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_intelligence import LLMCallLog
from app.models.platform_intelligence import BudgetForecast
from app.models.run import Run


async def generate_forecast(
    db: AsyncSession,
    project_id: uuid.UUID,
    *,
    budget_usd: float | None = None,
) -> BudgetForecast:
    """Generate a spend forecast for the current month."""
    now = datetime.now(timezone.utc)
    month_str = now.strftime("%Y-%m")
    days_in_month = 30  # simplified
    day_of_month = now.day
    days_remaining = max(days_in_month - day_of_month, 1)

    # Total spend so far this month for the project
    run_ids_q = select(Run.id).where(Run.project_id == project_id)
    run_ids = list((await db.execute(run_ids_q)).scalars().all())

    actual_spend = 0.0
    breakdown: dict[str, float] = {}
    if run_ids:
        cost_result = await db.execute(
            select(
                LLMCallLog.task_type,
                sa_func.sum(LLMCallLog.cost_usd).label("cost"),
            )
            .where(LLMCallLog.run_id.in_(run_ids))
            .group_by(LLMCallLog.task_type)
        )
        for row in cost_result.all():
            agent = row.task_type or "unknown"
            breakdown[agent] = round(float(row.cost or 0.0), 6)
            actual_spend += breakdown[agent]

    # Linear extrapolation
    burn_rate = actual_spend / max(day_of_month, 1)
    forecasted = actual_spend + (burn_rate * days_remaining)
    will_exceed = budget_usd is not None and forecasted > budget_usd
    confidence = min(day_of_month / days_in_month, 1.0)

    forecast = BudgetForecast(
        project_id=project_id,
        forecast_month=month_str,
        actual_spend_usd=round(actual_spend, 6),
        forecasted_spend_usd=round(forecasted, 6),
        budget_usd=budget_usd,
        burn_rate_usd_per_day=round(burn_rate, 6),
        days_remaining=days_remaining,
        will_exceed_budget=will_exceed,
        confidence=round(confidence, 3),
        breakdown_by_agent=breakdown,
    )
    db.add(forecast)
    await db.flush()
    return forecast


async def get_run_cost_attribution(
    db: AsyncSession,
    run_id: uuid.UUID,
) -> dict[str, Any]:
    """Detailed cost attribution for a single run broken down by agent/task_type."""
    result = await db.execute(
        select(
            LLMCallLog.task_type,
            sa_func.count(LLMCallLog.id).label("calls"),
            sa_func.sum(LLMCallLog.prompt_tokens).label("prompt_tokens"),
            sa_func.sum(LLMCallLog.completion_tokens).label("completion_tokens"),
            sa_func.sum(LLMCallLog.cost_usd).label("total_cost_usd"),
            sa_func.avg(LLMCallLog.latency_ms).label("avg_latency_ms"),
        )
        .where(LLMCallLog.run_id == run_id)
        .group_by(LLMCallLog.task_type)
    )
    rows = result.all()
    attribution = []
    total = 0.0
    for row in rows:
        cost = float(row.total_cost_usd or 0.0)
        total += cost
        attribution.append(
            {
                "agent": row.task_type or "unknown",
                "calls": row.calls,
                "prompt_tokens": int(row.prompt_tokens or 0),
                "completion_tokens": int(row.completion_tokens or 0),
                "cost_usd": round(cost, 6),
                "avg_latency_ms": round(float(row.avg_latency_ms or 0), 1),
            }
        )
    attribution.sort(key=lambda x: x["cost_usd"], reverse=True)
    return {
        "run_id": str(run_id),
        "total_cost_usd": round(total, 6),
        "by_agent": attribution,
    }
