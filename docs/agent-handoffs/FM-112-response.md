# FM-112 — Composition Engine Phase-Aware Routing

## Goal

Integrate phase-agent profiles into the agent resolution pipeline so the worker and orchestrator use phase-specific agents.

## What Was Implemented

- `resolve_agent_for_phase()` in `composition_service.py` — looks up PhaseAgentProfile for project/phase, returns `(slug, source)` tuple
- Worker `process_ready_tasks()` now calls `resolve_agent_for_phase()` first, with fallback to `resolve_agent_for_task()`
- Adaptive orchestrator `auto_retry_task()` uses the same phase-aware routing for retry agent selection
- `_STATUS_TO_PHASE` mapping dict: SPECIFYING→specify, PLANNING→plan, RUNNING→implement, COMPLETED→validate

## Files

- `apps/api/app/services/composition_service.py`
- `apps/worker/worker/main.py`
- `apps/api/app/services/adaptive_orchestrator.py`

## Status

✅ Complete. See also [FM-111-120-response.md](FM-111-120-response.md) for full milestone context.
