# FM-109 — Approval Integration

## Goal

Extend the approval system to support SPEC and PLAN artifact approvals with opt-in lifecycle gating.

## What Was Implemented

- `spec_plan_approval_service.py` with 5 public functions:
  - `request_spec_approval(db, *, run_id, project_id)` — creates approval request for SPEC artifact
  - `request_plan_approval(db, *, run_id, project_id)` — creates approval request for PLAN artifact
  - `is_spec_approved(db, run_id)` — checks if SPEC has been approved (vacuously true if no approval requested)
  - `is_plan_approved(db, run_id)` — checks if PLAN has been approved
  - `get_artifact_approval_status(db, run_id)` — returns dict with spec/plan approval status
- Idempotent: re-requesting returns existing pending approval
- Opt-in gating: transitions only blocked when approval was explicitly requested
- Integrates with existing `ApprovalRequest` model and approval workflow
- REST endpoints:
  - `POST /lifecycle/runs/{id}/spec/approve`
  - `POST /lifecycle/runs/{id}/plan/approve`
  - `GET /lifecycle/runs/{id}/artifact-approvals`

## Files Changed/Added

- `apps/api/app/services/spec_plan_approval_service.py` — approval service
- `apps/api/app/api/routes/run_lifecycle.py` — 3 approval endpoints

## Test Coverage

- `TestFM109_SpecPlanApproval` — 7 tests (spec approved by default, plan approved by default, request spec approval, request returns none without spec, idempotent, approved after resolve, get status)

## Result

✅ Complete — 7 tests passing
