# FM-123 — Resume from Checkpoint with Real Execution Restart

## Goal

Make `resume_from_checkpoint()` actually restart execution — reset failed/blocked tasks to READY and set the run back to RUNNING.

## What Was Implemented

- Resume validates run is in a resumable state (PAUSED, FAILED, or RUNNING)
- Resets all FAILED/BLOCKED tasks to READY, clears error messages
- Sets run status to RUNNING if it was PAUSED or FAILED
- Emits `LIFECYCLE_TRANSITION` event recording the resume action
- Returns continuation context with tasks_reset list and run_status_change

## Key Files

- `apps/api/app/services/execution_checkpoint_service.py`

## Status

✅ Complete
