# FM-090 — Structural Health Score

## Summary

Implemented a composite 0–100 structural health score that aggregates architecture quality indicators: coverage, drift penalty, rule compliance, and isolation ratio. Provides an at-a-glance assessment of a project's architectural health.

## Deliverables

### Service (`apps/api/app/services/structural_health_service.py`)

- **`compute_health_score(db, project_id)`** — Calculates a weighted composite score from:
  - **Coverage** (weight ~25%) — Percentage of nodes with classification/documentation
  - **Drift penalty** (weight ~25%) — Deductions for open drifts, weighted by severity (critical = 10pts, error = 5pts, warning = 2pts, info = 1pt)
  - **Rule compliance** (weight ~25%) — Percentage of rule evaluations that pass
  - **Isolation ratio** (weight ~25%) — Proportion of nodes with no edges (lower is better)
- Returns `StructuralHealthScore` with:
  - `score` — 0–100 integer
  - `grade` — Letter grade (A/B/C/D/F)
  - `details` — `HealthScoreDetails` with per-factor breakdown
  - `computed_at` — Timestamp

### Schema

- `HealthScoreDetails` — coverage_score, drift_penalty, compliance_score, isolation_score, total_nodes, open_drifts, rule_pass_rate
- `StructuralHealthScore` — score, grade, details, computed_at

### Route Endpoint (1)

- `GET /projects/{pid}/architecture/health-score` — Get health score

### Grading Scale

| Score  | Grade |
| ------ | ----- |
| 90–100 | A     |
| 80–89  | B     |
| 70–79  | C     |
| 60–69  | D     |
| 0–59   | F     |

## Tests

4 tests covering:

- `TestStructuralHealthScore` (3 tests) — empty project (score=100), project with drifts (score < 100), project with violations
- `TestStructuralHealthRoutes` (1 test) — health score route

## Test Results

- **Total**: 482 passing
- **Regression**: None
