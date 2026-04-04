# FM-098 — State Management & Sync Queue

## Summary

Implemented local state management with TTL-based caching, an offline event sync queue, and workspace mode management. All state is JSON-file-backed in `.forgemind/`.

## Deliverables

### Service (`apps/local/forgemind_local/local_state.py` — 159 lines)

#### Cache (`.forgemind/cache/`)

- **`cache_put(repo_root, key, value, ttl_s=3600)`** — store JSON value with TTL
- **`cache_get(repo_root, key)`** — retrieve if not expired; returns None otherwise
- **`cache_clear(repo_root)`** — remove all cache entries

#### Sync Queue (`.forgemind/state/sync_queue/`)

- **`queue_event(repo_root, event_type, payload)`** — persist event as timestamped JSON file
- **`list_queue(repo_root)`** — list all pending (unsynced) events
- **`mark_synced(repo_root, event_id)`** — mark event as synced
- **`clear_synced(repo_root)`** — remove synced events

#### Mode Management (`.forgemind/state/mode.json`)

- **`get_mode(repo_root)`** — returns current mode (default: "offline")
- **`set_mode(repo_root, mode)`** — validates against `{"offline", "hybrid", "remote"}`; raises ValueError for invalid
- **`is_online(repo_root)`** — True if mode is "hybrid" or "remote"

## Important Note

The sync queue stores events for future offline→online handoff, but **no sync consumer is implemented yet**. This is infrastructure-ready for a future FM task to build the actual bridge between ForgeMind Local and the backend API.

## Tests

9 tests in `TestLocalState`:
- cache_put_and_get, cache_expired, cache_clear, queue_and_list, mark_synced_and_clear, mode_get_default, mode_set_and_get, mode_invalid_raises, is_online

## Test Results

- **Total**: 535 passing
