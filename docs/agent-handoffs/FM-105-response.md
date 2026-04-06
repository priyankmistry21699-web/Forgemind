# FM-105 — Structured SPEC Generation

## Summary

Built the SPEC generation service that produces structured specification artifacts using LLM (with stub fallback). Constitution content is injected into the generation prompt. Emits SPEC_CREATED execution events and auto-transitions runs from PENDING to SPECIFYING.

## Deliverables

- `spec_service.py` — `generate_spec(db, run_id)` with LLM prompt construction, constitution injection, stub fallback
- SPEC artifact creation with `ArtifactType.SPEC`
- `SPEC_CREATED` execution event emission
- Auto-transition: PENDING → SPECIFYING on spec generation start
- Run's `spec_artifact_id` FK set on successful SPEC creation

## Known Gaps

- None

## Test Results

- Covered by `TestFM105_SpecGeneration` (4 tests)
