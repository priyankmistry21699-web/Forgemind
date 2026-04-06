# FM-107 — ADR-Aware Planning

## Summary

Built the ADR service that queries the architecture graph (nodes, edges, drifts, rule violations) and generates ADR sections (ADR-001 Structural Overview, ADR-002 Drift Report, ADR-003 Rule Compliance) to enrich generated plans with architectural context.

## Deliverables

- `adr_service.py` — `build_adr_section(db, project_id, spec_content)`, `enrich_plan_with_adr(db, project_id, plan_content)`, `get_architecture_context_for_prompt(db, project_id)`
- ADR-001: Structural overview from ArchitectureNode/Edge data
- ADR-002: Drift report from ArchitectureDrift records
- ADR-003: Rule compliance from ArchitectureRuleResult records
- `_format_adr_section()` helper for consistent markdown formatting
- Integration with plan generation pipeline

## Known Gaps

- None — ADR enrichment tests added

## Test Results

- Covered by `TestFM107_ADREnrichment` (added tests for ADR section generation)
