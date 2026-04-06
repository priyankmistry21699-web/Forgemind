# FM-129 — Architecture-Aware Release Risk Summary

## Goal

Provide risk assessment for releases based on execution state, approvals, and architecture signals.

## What Was Implemented

### Backend
- `release_risk_service.py` — multi-signal risk analysis (task failures, rejections, architecture drift)
- REST endpoint for risk summary generation

### Local CLI (strengthened)
- `confidence` command — 8 scoring signals: task completion rate (30), spec (10), plan (10), checkpoints (5), run complete (15), approvals resolved (10), no rejections (5), delivery artifact (10)
- `review` command — full risk analysis with HIGH/MEDIUM/LOW risk classification, task failure details, and release recommendation
- `checkpoint save` — captures real state: status_snapshot, artifact_refs, approval_snapshot from cached run data
- `local_handoff.import_snapshot()` — now restores checkpoints directory (symmetric with export)

## Key Files

- `apps/api/app/services/release_risk_service.py`
- `apps/local/forgemind_local/cli.py`
- `apps/local/forgemind_local/local_handoff.py`

## Status

✅ Complete
