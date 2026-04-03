# FM-088 — Refactor Recommendations

## Summary

Implemented architecture graph analysis that detects structural issues and generates actionable refactoring recommendations. Identifies god-modules, circular dependencies, isolated nodes, drift backlogs, and rule violation backlogs.

## Deliverables

### Service (`apps/api/app/services/refactor_recommendation_service.py`)

- **`generate_recommendations(db, project_id)`** — Analyze project's architecture graph for:
  - **God modules** — Nodes with excessive fan-in (many incoming edges); suggests splitting
  - **Circular dependencies** — Cycles detected via edge traversal; suggests breaking with interfaces or dependency inversion
  - **Isolated nodes** — Nodes with zero edges (no connections); suggests removal or integration
  - **Drift backlogs** — Open/unresolved drift records; suggests prioritizing resolution
  - **Rule violation backlogs** — Accumulated failed rule evaluations; suggests addressing violations

### Schema

- `RefactorRecommendation` — type, title, description, severity, affected_nodes
- `RefactorRecommendationList` — paginated list wrapper

### Route Endpoint (1)

- `GET /projects/{pid}/architecture/recommendations` — Get recommendations

## Tests

4 tests covering:

- `TestRefactorRecommendationService` (3 tests) — empty project, circular dependency detection, isolated node detection
- `TestRefactorRecommendationRoutes` (1 test) — recommendations route

## Test Results

- **Total**: 482 passing
- **Regression**: None
