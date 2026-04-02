"""LLM client — thin wrapper around LiteLLM for planner calls.

Provides async functions to call the configured LLM model.
Falls back gracefully if LiteLLM is unavailable or no API key is set.
This module is dependency-free (litellm is a soft-optional import).
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

_LITELLM_AVAILABLE = False
try:
    import litellm
    litellm.drop_params = True
    _LITELLM_AVAILABLE = True
except ImportError:
    logger.warning("litellm not installed — LLM calls will use stub responses")


@dataclass
class LLMConfig:
    """Configuration for LLM calls."""
    model: str = "gpt-4o"
    temperature: float = 0.4
    max_tokens: int = 4096


async def llm_completion(
    prompt: str,
    *,
    system: str | None = None,
    config: LLMConfig | None = None,
    model: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
    response_format: dict[str, Any] | None = None,
) -> str | None:
    """Call the LLM and return the assistant message content.

    Returns None on failure (missing key, network error, etc.) so the
    caller can fall back to stub data.
    """
    if not _LITELLM_AVAILABLE:
        logger.info("LiteLLM not available, returning None")
        return None

    cfg = config or LLMConfig()
    resolved_model = model or cfg.model
    resolved_temp = temperature if temperature is not None else cfg.temperature
    resolved_max = max_tokens or cfg.max_tokens

    messages: list[dict[str, str]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    kwargs: dict[str, Any] = {
        "model": resolved_model,
        "messages": messages,
        "temperature": resolved_temp,
        "max_tokens": resolved_max,
    }
    if response_format:
        kwargs["response_format"] = response_format

    try:
        response = await litellm.acompletion(**kwargs)
        content = response.choices[0].message.content
        if content:
            logger.debug("LLM raw response (first 500 chars): %s", content[:500])
        return content
    except Exception:
        logger.exception("LLM call failed for model=%s", resolved_model)
        return None


async def llm_json_completion(
    prompt: str,
    *,
    system: str | None = None,
    config: LLMConfig | None = None,
    model: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> dict[str, Any] | None:
    """Call the LLM expecting a JSON response. Returns parsed dict or None."""
    raw = await llm_completion(
        prompt,
        system=system,
        config=config,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        response_format={"type": "json_object"},
    )
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        logger.warning("LLM returned non-JSON content: %s", raw[:200] if raw else "None")
        return None
