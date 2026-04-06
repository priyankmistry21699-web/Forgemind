# FM-122 — Auto-Checkpoint & Phase-Transition Wiring

## Goal

Wire `create_auto_checkpoint()` into the real runtime so checkpoints are emitted automatically at phase transitions, pre-approval gates, and pre-delivery.

## What Was Implemented

- `run_lifecycle_service.transition_run()` emits `AUTO_PHASE` checkpoint after every phase transition
- `execution_service.complete_task()` emits `PRE_APPROVAL` checkpoint before approval creation for high-impact tasks
- `run_lifecycle_service.try_auto_complete_run()` emits `PRE_DELIVERY` checkpoint before setting run to COMPLETED
- All checkpoint calls are wrapped in try/except to never break the main execution flow

## Key Files

- `apps/api/app/services/run_lifecycle_service.py`
- `apps/api/app/services/execution_service.py`

## Status

✅ Complete
