# FM-139 — Local Mode Release Awareness

## Goal

CLI commands for local release status, readiness checking, and environment listing.

## What Was Implemented

- `forgemind release list <project_id>` — list cached release packages from `.forgemind/releases/`
- `forgemind release status <run_id>` — 7 local readiness checks from state files (spec, plan, tasks, checkpoints, approvals, confidence, changelog)
- `forgemind release environments <project_id>` — list cached environments from `.forgemind/environments/`

## Key Files

- `apps/local/forgemind_local/cli.py`

## Status

✅ Complete
