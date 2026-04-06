# FM-101 — SPEC Artifact & SPECIFYING Status

## Goal

Introduce `SPEC` and `PLAN` as first-class artifact types, add `SPECIFYING` run status, and enforce lifecycle gating (SPEC→PLAN→RUN ordering).

## What Was Implemented

- `ArtifactType.SPEC` and `ArtifactType.PLAN` enum values
- `RunStatus.SPECIFYING` enum value (7-state lifecycle: PENDING → SPECIFYING → PLANNING → RUNNING → COMPLETED)
- `spec_artifact_id` self-referential FK on `Artifact` model for PLAN→SPEC linking
- `run_lifecycle_service.py` with `VALID_TRANSITIONS` state machine, `has_spec_artifact()`, `has_plan_artifact()`, `validate_transition()`, `transition_run()`
- SPECIFYING→PLANNING gated on SPEC artifact existence; PLANNING→RUNNING gated on PLAN artifact existence
- TypeScript types updated: `RunStatus` includes `"specifying"`, `Artifact` includes `spec_artifact_id`

## Files Changed/Added

- `apps/api/app/models/artifact.py` — ArtifactType enum (SPEC, PLAN), spec_artifact_id FK
- `apps/api/app/models/run.py` — RunStatus enum (SPECIFYING)
- `apps/api/app/services/run_lifecycle_service.py` — lifecycle gating service
- `apps/api/app/api/routes/run_lifecycle.py` — `POST /lifecycle/runs/{id}/transition`, `GET .../validate`
- `apps/api/app/schemas/artifact.py` — spec_artifact_id in ArtifactRead/ArtifactCreate
- `packages/schemas/src/artifact.ts` — ArtifactType union includes "spec"/ "plan"
- `packages/schemas/src/run.ts` — RunStatus union includes "specifying"

## Test Coverage

- `TestFM101_ArtifactTypes` — 5 tests (type existence, artifact creation, FK linking)
- `TestFM101_LifecycleGating` — 5 tests (valid transitions, gating enforcement)

## Known Gaps

- None

## Result

✅ Complete — 10 tests passing
