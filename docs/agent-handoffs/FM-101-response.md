# FM-101 — SPEC Artifact & SPECIFYING Status

## Summary

Extended the artifact and run models with SPEC/PLAN artifact types, SPECIFYING run status, and lifecycle gating that enforces SPEC→PLAN→RUN ordering. Runs cannot transition to PLANNING without a SPEC artifact, and cannot start RUNNING without a validated PLAN.

## Deliverables

- `ArtifactType.SPEC` and `ArtifactType.PLAN` enum values added to artifact model
- `RunStatus.SPECIFYING` added to run status enum
- `spec_artifact_id` FK on Run model linking runs to their SPEC
- Lifecycle transition validation gates in run service
- Schema updates for new types and statuses

## Known Gaps

- None — core model extension, fully covered by FM-110 tests

## Test Results

- Covered by `TestFM101_ArtifactTypes` (5 tests) and `TestFM101_LifecycleGating` (6 tests)
