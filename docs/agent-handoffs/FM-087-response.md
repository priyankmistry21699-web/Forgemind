# FM-087 — Change Impact Analysis

## Summary

Implemented BFS-based reverse traversal to compute blast radius for proposed changes. When a node is targeted for modification, the service walks incoming edges to identify all transitively affected nodes, counts impacted services, and assigns severity ratings.

## Deliverables

### Service (`apps/api/app/services/impact_analysis_service.py`)

- **`analyse_impact(db, project_id, request)`** — BFS reverse traversal from target node through incoming edges; counts impacted nodes; extracts impacted service names; assigns severity:
  - 0 dependencies → NONE
  - 1–4 → LOW
  - 5–9 → MEDIUM
  - 10–19 → HIGH
  - 20+ → CRITICAL
- Creates and persists `ChangeImpactAssessment` record with blast_radius, impacted_nodes, impacted_services, rationale, confidence_score

### Model

- `ChangeImpactAssessment` (in `apps/api/app/models/architecture.py`) — target_node_id, target_path, target_key, severity (none/low/medium/high/critical), blast_radius, impacted_nodes (JSON), impacted_services (JSON), rationale, confidence_score, metadata

### Schema

- `ImpactAnalysisRequest` — target_node_id or target_key
- `ChangeImpactAssessmentRead` — full response with severity, blast_radius, impacted lists

### Route Endpoint (1)

- `POST /projects/{pid}/architecture/impact-analysis` — Analyze impact

## Tests

4 tests covering:

- `TestImpactAnalysisService` (3 tests) — unknown target, with dependents, severity escalation (10 deps → HIGH)
- `TestImpactAnalysisRoutes` (1 test) — impact analysis route

## Test Results

- **Total**: 482 passing
- **Regression**: None
