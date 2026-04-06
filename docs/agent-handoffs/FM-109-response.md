# FM-109 — Approval Integration

## Summary

Extended the approval system to support SPEC and PLAN artifact approvals. Approval requests are idempotent and opt-in — they only gate lifecycle transitions when explicitly requested. Enforces approval gates before SPECIFYING→PLANNING and PLANNING→RUNNING transitions.

## Deliverables

- `spec_plan_approval_service.py` — `request_spec_approval(db, run_id)`, `request_plan_approval(db, run_id)`, `check_approval_status(db, artifact_id)`
- Idempotent approval requests — re-requesting returns existing pending approval
- Opt-in gating — transitions only blocked when approval was explicitly requested
- Integration with existing `ApprovalRequest` model and approval workflow
- REST endpoints: `POST /api/runs/{id}/lifecycle/approve-spec`, `POST /api/runs/{id}/lifecycle/approve-plan`

## Known Gaps

- None

## Test Results

- Covered by `TestFM109_SpecPlanApproval` (8 tests)
