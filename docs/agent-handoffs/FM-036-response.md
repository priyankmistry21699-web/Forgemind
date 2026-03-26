# FM-036 — Dynamic Agent Composition Foundations

## What was done

Created a capability-based composition layer that enables ForgeMind to dynamically select and compose agent teams based on task requirements rather than fixed role assignments.

## Files created

- `apps/api/app/services/composition_service.py` — Full composition service:
  - `CAPABILITY_TAXONOMY`: 8 capability groups (planning, architecture, codegen, review, testing, deployment, documentation, security) mapped to 25+ concrete skills
  - `derive_required_capabilities(phases)`: Analyzes plan phases → capability requirements
  - `score_agent_for_capability(agent, cap_group)`: Scores 0.0–1.0 (0.6 task_type + 0.4 capability overlap)
  - `compose_team(db, phases)`: Returns team composition with assignments, coverage, and gaps
  - `resolve_agent_for_task(db, task_type, agent_hint)`: Priority chain: hint → scoring → None

- `apps/api/app/api/routes/composition.py` — REST endpoints:
  - `GET /composition/capabilities` → taxonomy listing
  - `GET /runs/{run_id}/composition` → analyzes run's tasks into team composition

## Files modified

- `apps/api/app/api/router.py` — Mounted composition_router
- `apps/worker/worker/main.py` — Updated task resolution to use composition_service first, with legacy fallback

## Design decisions

- Agent hint from planner takes priority over capability scoring (preserves planner intent)
- Scoring is additive: task_type match gives 0.6, capability overlap adds up to 0.4
- Falls back to legacy agent_service when composition returns None (backward compatible)
