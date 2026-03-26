# FM-039 — Execution Memory & Contextual Reasoning

## What was done

Created a unified execution memory service that provides cached, structured summaries of run state for use by the chat service, agents, operators, and the adaptive orchestrator.

## Files created

- `apps/api/app/services/run_memory_service.py` — Core memory service:
  - `get_run_summary(db, run_id)`: Builds or retrieves cached run summary with task/artifact/approval/event breakdowns and progress percentage
  - `get_failure_analysis(db, run_id)`: Analyzes failures — identifies blocking failures, suggests recovery actions
  - `build_context_for_chat(summary)`: Converts structured summary to text context for LLM consumption
  - `invalidate_run_cache(run_id)`: Cache invalidation on state changes
  - In-memory LRU cache with configurable max size (100 entries)

- `apps/api/app/api/routes/memory.py` — REST endpoints:
  - `GET /runs/{run_id}/memory/summary` — Cached run summary (with ?refresh=true)
  - `GET /runs/{run_id}/memory/failures` — Failure analysis with suggested actions
  - `GET /runs/{run_id}/memory/context` — Text context (same format as chat service)

## Files modified

- `apps/api/app/services/chat_service.py` — Refactored `_build_run_context()` to delegate to `run_memory_service` (removed 50+ lines of inline context assembly)
- `apps/api/app/api/router.py` — Mounted memory_router
- `apps/worker/worker/main.py` — Added cache invalidation on task completion and failure

## Design decisions

- Summary is cached per run_id with LRU eviction (simple, works for single-process)
- Chat service reuses the same summary → no duplicate DB queries
- Failure analysis identifies blocking vs non-blocking failures for smarter retry decisions
- Cache invalidated on every task state change (completion, failure) in the worker
