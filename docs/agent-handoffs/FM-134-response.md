# FM-134 — Release Gates & Operational Policy Checks

## Goal

Configurable release gates evaluated against real run signals, with per-gate pass/fail persistence.

## What Was Implemented

- 9 built-in gates: run_completed, all_tasks_terminal, no_failed_tasks, approvals_clear, confidence_minimum, has_spec_artifact, has_plan_artifact, has_checkpoints, no_rejections
- Environment-configurable gate selection via `required_gates` JSON
- `ReleaseGateResult` ORM model for per-gate persistence
- Auto-transitions package status (draft → ready on all-pass, → gated on any failure)

## Key Files

- `apps/api/app/models/release_ops.py` (ReleaseGateResult model)
- `apps/api/app/services/release_gate_service.py`

## Status

✅ Complete
