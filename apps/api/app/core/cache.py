"""FM-216: Two-tier caching layer.

Tier 1: In-process LRU dict (zero latency, process-local, configurable TTL).
Tier 2: Redis (shared across workers, optional — degrades to tier-1 only).

Usage:
    from app.core.cache import cached, invalidate, get_cache_stats

    @cached("project:{project_id}", ttl=60)
    async def get_project_cached(project_id: str) -> dict: ...

    await invalidate("project:{project_id}", project_id=str(pid))

Environment:
    CACHE_TTL_DEFAULT  — default 60 s
    CACHE_ENABLED      — set "false" to bypass entirely (useful in tests)
"""

from __future__ import annotations

import functools
import json
import logging
import os
import time
from collections import OrderedDict
from typing import Any, Awaitable, Callable

logger = logging.getLogger(__name__)

_CACHE_ENABLED = os.getenv("CACHE_ENABLED", "true").lower() != "false"
_DEFAULT_TTL: int = int(os.getenv("CACHE_TTL_DEFAULT", "60"))
_MAX_LOCAL_SIZE: int = int(os.getenv("CACHE_LOCAL_MAX_SIZE", "512"))

# ---------------------------------------------------------------------------
# In-process LRU cache
# ---------------------------------------------------------------------------

_local_cache: OrderedDict[str, tuple[Any, float]] = (
    OrderedDict()
)  # key → (value, expires_at)
_stats: dict[str, int] = {"hits": 0, "misses": 0, "sets": 0, "evictions": 0}


def _local_get(key: str) -> tuple[bool, Any]:
    entry = _local_cache.get(key)
    if entry is None:
        return False, None
    value, expires_at = entry
    if time.monotonic() > expires_at:
        _local_cache.pop(key, None)
        return False, None
    _local_cache.move_to_end(key)
    return True, value


def _local_set(key: str, value: Any, ttl: int) -> None:
    if key in _local_cache:
        _local_cache.move_to_end(key)
    _local_cache[key] = (value, time.monotonic() + ttl)
    while len(_local_cache) > _MAX_LOCAL_SIZE:
        _local_cache.popitem(last=False)
        _stats["evictions"] += 1


def _local_delete(key: str) -> None:
    _local_cache.pop(key, None)


def flush_local_cache() -> int:
    n = len(_local_cache)
    _local_cache.clear()
    return n


# ---------------------------------------------------------------------------
# Redis tier (optional)
# ---------------------------------------------------------------------------

_redis_client = None
_redis_checked = False


async def _get_redis():
    global _redis_client, _redis_checked
    if _redis_checked:
        return _redis_client
    _redis_checked = True
    try:
        import redis.asyncio as aioredis
        from app.core.config import settings

        r = aioredis.from_url(
            settings.redis_url,
            socket_connect_timeout=1,
            socket_timeout=1,
        )
        await r.ping()
        _redis_client = r
        logger.info("cache: Redis tier available at %s", settings.redis_url)
    except Exception as exc:
        logger.info("cache: Redis unavailable (%s) — local cache only", exc)
        _redis_client = None
    return _redis_client


async def _redis_get(key: str) -> tuple[bool, Any]:
    r = await _get_redis()
    if r is None:
        return False, None
    try:
        raw = await r.get(f"fm:{key}")
        if raw is None:
            return False, None
        return True, json.loads(raw)
    except Exception:
        return False, None


async def _redis_set(key: str, value: Any, ttl: int) -> None:
    r = await _get_redis()
    if r is None:
        return
    try:
        await r.setex(f"fm:{key}", ttl, json.dumps(value, default=str))
    except Exception:
        pass


async def _redis_delete(key: str) -> None:
    r = await _get_redis()
    if r is None:
        return
    try:
        await r.delete(f"fm:{key}")
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def cache_get(key: str) -> tuple[bool, Any]:
    """Return (hit, value).  Checks local then Redis."""
    if not _CACHE_ENABLED:
        return False, None
    hit, val = _local_get(key)
    if hit:
        _stats["hits"] += 1
        return True, val
    hit, val = await _redis_get(key)
    if hit:
        _stats["hits"] += 1
        _local_set(key, val, _DEFAULT_TTL)
        return True, val
    _stats["misses"] += 1
    return False, None


async def cache_set(key: str, value: Any, ttl: int = _DEFAULT_TTL) -> None:
    """Store value in both tiers."""
    if not _CACHE_ENABLED:
        return
    _local_set(key, value, ttl)
    await _redis_set(key, value, ttl)
    _stats["sets"] += 1


async def invalidate(key_template: str, **kwargs: Any) -> None:
    """Delete a cache entry.  kwargs fill in {placeholders} in key_template."""
    key = key_template.format(**kwargs) if kwargs else key_template
    _local_delete(key)
    await _redis_delete(key)


def get_cache_stats() -> dict[str, Any]:
    return {
        "enabled": _CACHE_ENABLED,
        "local_size": len(_local_cache),
        "max_local_size": _MAX_LOCAL_SIZE,
        **_stats,
    }


# ---------------------------------------------------------------------------
# Decorator
# ---------------------------------------------------------------------------


def cached(key_template: str, ttl: int = _DEFAULT_TTL):
    """Async function decorator for transparent caching.

    The key_template may contain {arg_name} placeholders that are resolved
    from the decorated function's call arguments.

    Example:
        @cached("project:{project_id}", ttl=60)
        async def get_project(db, project_id: str): ...
    """

    def decorator(fn: Callable[..., Awaitable[Any]]):
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            # Build cache key — use kwargs + positional args by position
            try:
                import inspect

                sig = inspect.signature(fn)
                bound = sig.bind(*args, **kwargs)
                bound.apply_defaults()
                key = key_template.format(**bound.arguments)
            except (KeyError, TypeError):
                # If we can't build the key, skip caching
                return await fn(*args, **kwargs)

            hit, val = await cache_get(key)
            if hit:
                return val

            result = await fn(*args, **kwargs)
            if result is not None:
                await cache_set(key, result, ttl)
            return result

        wrapper._cache_key_template = key_template  # type: ignore[attr-defined]
        return wrapper

    return decorator
