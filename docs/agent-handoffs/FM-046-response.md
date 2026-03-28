# FM-046 — Run Replay & Execution Trace

## What was done

Built a replay and execution trace system that captures deterministic snapshots of every agent execution (inputs, prompts, model, temperature, outputs, tokens, cost) and enables side-by-side comparisons and re-execution. Also introduced a run lifecycle service for health monitoring, auto-completion, and auto-failure detection.

## Files created

- `apps/api/app/models/replay_snapshot.py` — `ReplaySnapshot` model:
  - Table `replay_snapshots` with `input_snapshot` (JSON), `prompt_snapshot` (Text), `model_used`, `temperature`, `output_snapshot` (JSON), `error`, `tokens_used`, `duration_ms`, `cost_usd`
  - `replay_hash` (SHA-256, indexed) for deduplication
  - `is_replay` (bool), `original_snapshot_id` (self-FK) linking replays to originals
  - `sequence_number` for ordering within a run
- `apps/api/app/services/replay_service.py` — Replay service:
  - `_compute_replay_hash(...)`: Deterministic SHA-256 from agent_slug + input + prompt + model + temperature
  - `capture_snapshot(db, ...)`: Records execution with auto-incrementing sequence number
  - `get_execution_trace(db, run_id)`: Returns ordered snapshots with aggregated metrics
  - `replay_snapshot(db, snapshot_id)`: Re-executes and compares to original
  - `compare_snapshots(db, id1, id2)`: Compares outputs, returns `output_match` and `diff_summary`
- `apps/api/app/api/routes/replay.py` — Routes: `GET /runs/{id}/trace`, `GET /tasks/{id}/snapshots`, `GET /replay/snapshots/{id}`, `POST /replay/snapshots`
- `apps/api/app/schemas/replay.py` — Read/create schemas for replay snapshots
- `apps/api/app/services/run_lifecycle_service.py` — Run lifecycle service:
  - `RunHealth` constants: `HEALTHY`, `DEGRADED`, `STUCK`, `CRITICAL`, `COMPLETED`, `FAILED`
  - `get_run_health(db, run_id)`: Comprehensive health with blocking issues, stuck detection (60 min threshold)
  - `try_auto_complete_run()`: Completes run when all tasks are terminal
  - `try_auto_fail_run()`: Fails run when exhausted-retry tasks block the DAG
  - `scan_all_runs_health()`: Batch health check for operator dashboards
- `apps/api/app/api/routes/run_lifecycle.py` — Routes: `GET /lifecycle/runs/{id}/health`, `POST /lifecycle/runs/{id}/auto-complete`, `POST /lifecycle/runs/{id}/auto-fail`, `GET /lifecycle/runs/health/scan`
- `apps/api/alembic/versions/2026_03_30_0015_add_replay_snapshots.py` — Migration creating `replay_snapshots` table
- `apps/api/tests/test_fm046_050_v2.py` — Tests: `TestReplaySnapshot` class
- `apps/api/tests/test_fm046_050.py` — Tests: `TestRunHealthCheck`, `TestAutoComplete`, `TestAutoFail` classes

## Files modified

- `apps/api/app/db/base.py` — Added `ReplaySnapshot` import
- `apps/api/app/api/router.py` — Registered `replay_router` and `lifecycle_router`

## Design decisions

- `replay_hash` enables deduplication and deterministic replay identification
- Self-referential FK (`original_snapshot_id`) links replays to originals
- Run health is computed on-demand (not cached) for accuracy
- Stuck detection uses the timestamp of the most recent execution event (60 min threshold)
- Auto-complete/auto-fail are explicit operator actions (POST), not automatic background processes
