"""FM-221: Multi-model LLM routing.

ModelRouter selects the best model for each LLM call based on:
1. Task-type hints (planner, coder, reviewer, …)
2. Budget pressure — downgrade when a run has spent > 80% of its budget
3. Provider health — skip providers that recently errored

Configuration via LITELLM_ROUTER_CONFIG JSON env var:
    {
      "rules": [
        {"task_type": "planner", "model": "gpt-4o"},
        {"task_type": "coder",   "model": "claude-3-5-sonnet-20241022"},
        {"task_type": "default", "model": "gpt-4o-mini"}
      ],
      "fallback_chain": ["gpt-4o", "claude-3-5-sonnet-20241022", "gpt-4o-mini"],
      "budget_downgrade_model": "gpt-4o-mini",
      "budget_threshold_pct": 0.8
    }
"""

from __future__ import annotations

import json
import logging
import os
import time
from collections import defaultdict
from typing import Any

logger = logging.getLogger(__name__)

_DEFAULT_CONFIG: dict[str, Any] = {
    "rules": [
        {"task_type": "planner", "model": "gpt-4o"},
        {"task_type": "architect", "model": "gpt-4o"},
        {"task_type": "coder", "model": "gpt-4o-mini"},
        {"task_type": "reviewer", "model": "gpt-4o-mini"},
        {"task_type": "tester", "model": "gpt-4o-mini"},
        {"task_type": "default", "model": "gpt-4o-mini"},
    ],
    "fallback_chain": ["gpt-4o", "gpt-4o-mini", "claude-3-5-sonnet-20241022"],
    "budget_downgrade_model": "gpt-4o-mini",
    "budget_threshold_pct": 0.8,
}

_config: dict[str, Any] = {}
_provider_errors: dict[str, list[float]] = defaultdict(list)  # model → error timestamps
_selection_log: list[dict[str, Any]] = []


def _load_config() -> dict[str, Any]:
    raw = os.getenv("LITELLM_ROUTER_CONFIG", "")
    if raw:
        try:
            return {**_DEFAULT_CONFIG, **json.loads(raw)}
        except Exception as exc:
            logger.warning("model_router: invalid LITELLM_ROUTER_CONFIG (%s)", exc)
    return _DEFAULT_CONFIG.copy()


def _get_config() -> dict[str, Any]:
    global _config
    if not _config:
        _config = _load_config()
    return _config


def _is_healthy(model: str, error_window_seconds: int = 60) -> bool:
    """Return False if model had ≥3 errors in the last window."""
    cutoff = time.monotonic() - error_window_seconds
    recent = [t for t in _provider_errors.get(model, []) if t > cutoff]
    return len(recent) < 3


def record_provider_error(model: str) -> None:
    """Called when a model call fails — used to trigger fallback routing."""
    _provider_errors[model].append(time.monotonic())
    # Trim old entries
    cutoff = time.monotonic() - 300
    _provider_errors[model] = [t for t in _provider_errors[model] if t > cutoff]


def select_model(
    *,
    task_type: str = "default",
    budget_used_pct: float = 0.0,
    preferred_model: str | None = None,
) -> str:
    """Return the best model string for a given task context."""
    cfg = _get_config()
    rules: list[dict] = cfg.get("rules", [])
    fallback_chain: list[str] = cfg.get("fallback_chain", [])
    budget_threshold: float = cfg.get("budget_threshold_pct", 0.8)
    budget_model: str = cfg.get("budget_downgrade_model", "gpt-4o-mini")

    # 1. Budget pressure → downgrade
    if budget_used_pct >= budget_threshold:
        model = budget_model
        _log_selection(task_type, model, "budget_pressure")
        return model

    # 2. Preferred model override (if healthy)
    if preferred_model and _is_healthy(preferred_model):
        _log_selection(task_type, preferred_model, "preferred")
        return preferred_model

    # 3. Task-type rules
    default_model = "gpt-4o-mini"
    for rule in rules:
        if rule.get("task_type") == task_type:
            candidate = rule["model"]
            if _is_healthy(candidate):
                _log_selection(task_type, candidate, "rule")
                return candidate
            break
        if rule.get("task_type") == "default":
            default_model = rule["model"]

    # 4. Fallback chain
    for m in fallback_chain:
        if _is_healthy(m):
            _log_selection(task_type, m, "fallback")
            return m

    # 5. Last resort
    _log_selection(task_type, default_model, "last_resort")
    return default_model


def _log_selection(task_type: str, model: str, reason: str) -> None:
    entry = {
        "task_type": task_type,
        "model": model,
        "reason": reason,
        "ts": time.time(),
    }
    _selection_log.append(entry)
    if len(_selection_log) > 200:
        _selection_log.pop(0)


def get_router_status() -> dict[str, Any]:
    """Return current routing config and recent selections for /admin/model-router/status."""
    cfg = _get_config()
    recent_selections = list(reversed(_selection_log[-20:]))
    unhealthy = {m: len(errs) for m, errs in _provider_errors.items() if errs}
    return {
        "config": cfg,
        "unhealthy_models": unhealthy,
        "recent_selections": recent_selections,
    }


def reload_config() -> None:
    """Force config reload from environment (useful after env change)."""
    global _config
    _config = _load_config()
    logger.info("model_router: config reloaded")
