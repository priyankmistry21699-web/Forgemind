# FM-108 — Spec-to-Plan Validation

## Goal

Validate that generated plans adequately cover their specifications before allowing execution to begin.

## What Was Implemented

- `spec_plan_validation_service.py` with `validate_spec_plan(db, run_id)` function
- `ValidationIssue` dataclass: `rule`, `severity` ("error"/"warning"), `message`
- `SpecPlanValidationResult` dataclass: `run_id`, `spec_id`, `plan_id`, `valid`, `issues`, `coverage` + `to_dict()`
- Validation rules:
  - SPEC exists (error)
  - PLAN exists (error)
  - PLAN linked to SPEC via `spec_artifact_id` (error)
  - SPEC has required sections: Problem/Objective, Scope, Constraints, Acceptance Criteria (error)
  - PLAN has required sections: Overview, Phase (error)
  - PLAN not trivially short (warning)
- Lifecycle gate: PLANNING→RUNNING blocked if validation has errors
- REST endpoint: `GET /lifecycle/runs/{id}/spec-plan/validate`

## Files Changed/Added

- `apps/api/app/services/spec_plan_validation_service.py` — validation service
- `apps/api/app/api/routes/run_lifecycle.py` — validation endpoint

## Test Coverage

- `TestFM108_SpecPlanValidation` — 5 tests (fails without spec, fails without plan, passes with good plan, checks plan link, to_dict)

## Result

✅ Complete — 5 tests passing
