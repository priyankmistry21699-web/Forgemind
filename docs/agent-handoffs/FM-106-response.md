# FM-106 — PLAN Artifact Export & Linking

## Summary

Implemented PLAN artifact creation with FK linkage to SPEC artifacts, plus markdown and JSON export endpoints. Auto-transitions runs from SPECIFYING to PLANNING.

## Deliverables

- `plan_artifact_service.py` — `create_plan(db, run_id, spec_artifact_id)`, `export_plan_markdown(db, plan_artifact_id)`, `export_plan_json(db, plan_artifact_id)`
- PLAN→SPEC FK linkage via `spec_artifact_id` on plan artifact
- REST endpoints for plan export: `GET /api/runs/{id}/plan/markdown`, `GET /api/runs/{id}/plan/json`
- Auto-transition: SPECIFYING → PLANNING on plan creation

## Known Gaps

- None

## Test Results

- Covered by `TestFM106_PlanArtifact` (4 tests)
