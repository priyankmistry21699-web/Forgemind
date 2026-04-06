# FM-121 — Execution Checkpoints: Model, Schema & CRUD

## Goal

Introduce typed execution checkpoints that capture run state at key moments.

## What Was Implemented

- `ExecutionCheckpoint` ORM model with `CheckpointType` enum (manual, auto_phase, pre_approval, pre_delivery, post_validation)
- Pydantic schemas: `CheckpointCreate`, `CheckpointUpdate`, `CheckpointRead`
- Full CRUD service in `execution_checkpoint_service.py`
- REST router at `/runs/{run_id}/checkpoints` with create, list, get, update, delete
- Alembic migration `0024_add_execution_checkpoints` with 3 indexes and FK constraints

## Key Files

- `apps/api/app/models/execution_checkpoint.py`
- `apps/api/app/schemas/execution_checkpoint.py`
- `apps/api/app/services/execution_checkpoint_service.py`
- `apps/api/app/routers/execution_checkpoints.py`
- `apps/api/alembic/versions/2026_04_06_0024_add_execution_checkpoints.py`

## Status

✅ Complete
