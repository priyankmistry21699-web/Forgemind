"""FM-098 — Offline-first / resilient local state.

Provides local caching, mode management (offline/hybrid/remote), and a
deferred sync queue so ForgeMind Local remains useful without connectivity.
"""

from __future__ import annotations

import datetime as _dt
import json
import os
import uuid
from typing import Any

from forgemind_local.config import load_config, save_config

# ── Cache ──────────────────────────────────────────────────────────


def _cache_dir(repo_root: str) -> str:
    return os.path.join(repo_root, ".forgemind", "cache")


def cache_put(repo_root: str, key: str, data: Any, *, ttl_s: int = 3600) -> None:
    """Store a value in the local cache with an optional TTL."""
    d = _cache_dir(repo_root)
    os.makedirs(d, exist_ok=True)
    entry = {
        "key": key,
        "data": data,
        "cached_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "expires_at": (
            _dt.datetime.now(_dt.timezone.utc) + _dt.timedelta(seconds=ttl_s)
        ).isoformat(),
    }
    path = os.path.join(d, f"{key}.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(entry, fh, indent=2, default=str)


def cache_get(repo_root: str, key: str) -> Any | None:
    """Retrieve a cached value if it exists and hasn't expired."""
    path = os.path.join(_cache_dir(repo_root), f"{key}.json")
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as fh:
        entry = json.load(fh)
    expires = _dt.datetime.fromisoformat(entry["expires_at"])
    if _dt.datetime.now(_dt.timezone.utc) > expires:
        os.remove(path)
        return None
    return entry["data"]


def cache_clear(repo_root: str) -> int:
    """Clear all cached items. Returns count removed."""
    d = _cache_dir(repo_root)
    if not os.path.isdir(d):
        return 0
    count = 0
    for f in os.listdir(d):
        if f.endswith(".json"):
            os.remove(os.path.join(d, f))
            count += 1
    return count


# ── Sync queue ─────────────────────────────────────────────────────


def _queue_dir(repo_root: str) -> str:
    return os.path.join(repo_root, ".forgemind", "state", "sync_queue")


def queue_event(repo_root: str, event_type: str, payload: dict[str, Any]) -> str:
    """Enqueue a sync event for later replay when connectivity returns."""
    d = _queue_dir(repo_root)
    os.makedirs(d, exist_ok=True)
    event_id = str(uuid.uuid4())
    event = {
        "event_id": event_id,
        "event_type": event_type,
        "payload": payload,
        "queued_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "synced": False,
    }
    with open(os.path.join(d, f"{event_id}.json"), "w", encoding="utf-8") as fh:
        json.dump(event, fh, indent=2, default=str)
    return event_id


def list_queue(repo_root: str) -> list[dict[str, Any]]:
    """List all pending (unsynced) queue items."""
    d = _queue_dir(repo_root)
    if not os.path.isdir(d):
        return []
    items: list[dict[str, Any]] = []
    for fname in sorted(os.listdir(d)):
        if fname.endswith(".json"):
            with open(os.path.join(d, fname), encoding="utf-8") as fh:
                item = json.load(fh)
            if not item.get("synced"):
                items.append(item)
    return items


def mark_synced(repo_root: str, event_id: str) -> None:
    """Mark a queued event as synced."""
    path = os.path.join(_queue_dir(repo_root), f"{event_id}.json")
    if not os.path.isfile(path):
        return
    with open(path, encoding="utf-8") as fh:
        item = json.load(fh)
    item["synced"] = True
    item["synced_at"] = _dt.datetime.now(_dt.timezone.utc).isoformat()
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(item, fh, indent=2, default=str)


def clear_synced(repo_root: str) -> int:
    """Remove all synced events from the queue. Returns count removed."""
    d = _queue_dir(repo_root)
    if not os.path.isdir(d):
        return 0
    count = 0
    for fname in os.listdir(d):
        if fname.endswith(".json"):
            path = os.path.join(d, fname)
            with open(path, encoding="utf-8") as fh:
                item = json.load(fh)
            if item.get("synced"):
                os.remove(path)
                count += 1
    return count


# ── Mode management ────────────────────────────────────────────────

VALID_MODES = {"offline", "hybrid", "remote"}


def get_mode(repo_root: str) -> str:
    """Return current operational mode."""
    cfg = load_config(repo_root)
    return cfg.mode if cfg else "offline"


def set_mode(repo_root: str, mode: str) -> str:
    """Set operational mode. Returns the new mode."""
    if mode not in VALID_MODES:
        raise ValueError(f"Invalid mode '{mode}'. Valid: {VALID_MODES}")
    cfg = load_config(repo_root)
    if cfg is None:
        raise RuntimeError("Not initialised. Run `forgemind init` first.")
    cfg.mode = mode
    save_config(cfg)
    return mode


def is_online(repo_root: str) -> bool:
    """Check if the current mode allows remote operations."""
    return get_mode(repo_root) in ("hybrid", "remote")
