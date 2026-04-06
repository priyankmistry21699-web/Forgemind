# FM-111 — Phase Agent Profile Data Model

## Goal

Define the data model for per-project, per-phase agent assignments enabling phase-aware routing.

## What Was Implemented

- `PhaseAgentProfile` ORM model (`apps/api/app/models/phase_agent_profile.py`)
- `WorkflowPhase` enum: specify, plan, tasks, implement, review, validate
- `UniqueConstraint(project_id, phase)` — one agent per phase per project
- Full CRUD service (`phase_agent_profile_service.py`): upsert, list, get_agent_slug_for_phase, delete, bulk_set_profiles
- Agent validation — confirms agent exists and is active before assignment
- Pydantic schemas for request/response serialization
- REST routes at `/api/projects/{id}/phase-agent-profiles`
- Alembic migration #23 adds `phase_agent_profiles` table

## Files

- `apps/api/app/models/phase_agent_profile.py`
- `apps/api/app/services/phase_agent_profile_service.py`
- `apps/api/app/schemas/phase_agent_profile.py`
- `apps/api/app/routes/phase_agent_profile_routes.py`
- `apps/api/alembic/versions/023_*.py`

## Status

✅ Complete. See also [FM-111-120-response.md](FM-111-120-response.md) for full milestone context.
