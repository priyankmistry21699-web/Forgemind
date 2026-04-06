# FM-106 — PLAN Artifact Export & Linking

## Goal

Create PLAN artifacts linked to their SPEC via FK, with markdown and JSON export capabilities.

## What Was Implemented

- `plan_artifact_service.py` with 4 public functions:
  - `generate_plan_artifact(db, *, run_id, project_id, user_prompt)` — creates PLAN linked to SPEC, calls `adr_service.enrich_plan_with_adr()` for ADR enrichment
  - `get_plan_for_run(db, run_id)` — retrieve existing PLAN artifact
  - `export_plan_markdown(db, run_id)` — export PLAN content as markdown
  - `get_plan_export_data(db, run_id)` — export PLAN as JSON dict
- Requires SPEC artifact first (raises `ValueError` if absent)
- Sets `spec_artifact_id` FK on PLAN artifact for PLAN→SPEC linking
- Auto-transitions run from SPECIFYING → PLANNING
- Emits `EventType.PLAN_CREATED` execution event

## Files Changed/Added

- `apps/api/app/services/plan_artifact_service.py` — PLAN generation and export service

## Test Coverage

- `TestFM106_PlanArtifact` — 4 tests (plan requires spec, plan links to spec, markdown export, returns none without plan)

## Result

✅ Complete — 4 tests passing
