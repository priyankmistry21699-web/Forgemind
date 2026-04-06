# FM-105 — Structured SPEC Generation

## Goal

Generate formal specification artifacts using LLM with constitution context injection and stub fallback.

## What Was Implemented

- `spec_service.py` with 2 public functions:
  - `generate_spec(db, *, run_id, project_id, user_prompt)` — LLM-powered SPEC generation with constitution injection, stub fallback if LLM unavailable
  - `get_spec_for_run(db, run_id)` — retrieve existing SPEC artifact
- Calls `constitution_service.get_constitution_for_prompt()` for constitution context injection
- Creates `ArtifactType.SPEC` artifact with structured markdown (Problem/Objective, Scope, Constraints, Assumptions, Acceptance Criteria, Risks, Architecture Summary)
- Auto-transitions run from PENDING → SPECIFYING
- Emits `EventType.SPEC_CREATED` execution event

## Files Changed/Added

- `apps/api/app/services/spec_service.py` — SPEC generation service

## Test Coverage

- `TestFM105_SpecGeneration` — 4 tests (generate stub, generate with prompt, get spec for run, get spec returns none)

## Result

✅ Complete — 4 tests passing
