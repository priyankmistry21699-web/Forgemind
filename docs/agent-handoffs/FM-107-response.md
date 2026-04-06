# FM-107 — ADR-Aware Planning

## Goal

Enrich generated plans with architecture context from the project's graph, drift findings, and structural health data.

## What Was Implemented

- `adr_service.py` with 3 public functions + 1 helper:
  - `build_adr_section(db, *, project_id, spec_content)` — queries `ArchitectureNode`, `ArchitectureEdge`, `ArchitectureDrift`, `ArchitectureRuleResult`; returns ADR markdown or None
  - `enrich_plan_with_adr(db, *, project_id, plan_content, spec_content)` — appends ADR section to plan content
  - `get_architecture_context_for_prompt(db, project_id)` — concise LLM-friendly architecture summary
  - `_format_adr_section()` — generates ADR-001 (Structural Overview), ADR-002 (Drift Report), ADR-003 (Rule Compliance)
- Integrated into `plan_artifact_service.generate_plan_artifact()` pipeline
- Returns None if no architecture data exists (graceful no-op)

## Files Changed/Added

- `apps/api/app/services/adr_service.py` — ADR-aware planning service

## Test Coverage

- `TestFM107_ADREnrichment` — 3 tests (no data returns None, with nodes returns ADR markdown, enrichment appends to plan)

## Design Notes

- Queries `NodeStatus.ACTIVE` nodes, `DriftStatus.OPEN` drifts, `RuleResultStatus.VIOLATION` rule results
- ADR sections organized as formal Architecture Decision Records (ADR-001, ADR-002, ADR-003)

## Result

✅ Complete — 3 tests passing
