# FM-108 — Spec-to-Plan Validation

## Summary

Implemented an 8-rule validation service (4 ERROR, 4 WARNING) that verifies plan quality against its SPEC before allowing PLANNING→RUNNING transition. Returns a structured `SpecPlanValidationResult` with per-rule pass/fail details.

## Deliverables

- `spec_plan_validation_service.py` — `validate_spec_plan(db, run_id)` with 8 validation rules
- ERROR rules: plan references SPEC, plan covers all SPEC sections, plan has implementation steps, plan has no empty sections
- WARNING rules: plan mentions testing, plan mentions error handling, plan has reasonable length, plan sections match SPEC order
- `SpecPlanValidationResult` schema with `is_valid`, `errors`, `warnings`, `details`
- Lifecycle gate: PLANNING→RUNNING blocked if validation has ERRORs
- REST endpoint: `POST /api/runs/{id}/lifecycle/validate`

## Known Gaps

- None

## Test Results

- Covered by `TestFM108_SpecPlanValidation` (5 tests)
