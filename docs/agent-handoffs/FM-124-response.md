# FM-124 — Mid-Run Branch / WIP Snapshot Support

## Goal

Allow creating checkpoints at arbitrary points during execution for debugging and WIP preservation.

## What Was Implemented

- Manual checkpoint creation via POST `/runs/{run_id}/checkpoints`
- Sequence numbering for checkpoint ordering
- Status snapshot, artifact refs, and approval snapshot captured at creation time
- `_build_status_snapshot()` and `_build_approval_snapshot()` helpers for live state capture

## Key Files

- `apps/api/app/services/execution_checkpoint_service.py`
- `apps/api/app/routers/execution_checkpoints.py`

## Status

✅ Complete
