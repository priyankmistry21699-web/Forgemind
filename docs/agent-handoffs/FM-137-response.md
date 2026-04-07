# FM-137 — Operational Timeline View

## Goal

Unified chronological timeline of all release-related events.

## What Was Implemented

- Merged timeline from: run lifecycle, execution events, checkpoints, approvals, release packages, gate results, tasks
- Sorted chronologically with category counts
- REST endpoint at `GET /runs/{run_id}/operational-timeline`

## Key Files

- `apps/api/app/services/operational_timeline_service.py`
- `apps/api/app/api/routes/release_ops.py`

## Status

✅ Complete
