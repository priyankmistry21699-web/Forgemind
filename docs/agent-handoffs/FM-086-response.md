# FM-086 — Design Doc Synthesis

## Summary

Implemented a service that generates Markdown architecture design documents from the current architecture graph, drift records, and rule violation data. Produces a structured summary of a project's architectural state.

## Deliverables

### Service (`apps/api/app/services/design_doc_service.py`)

- **`generate_design_doc(db, project_id)`** — Query project's architecture graph (nodes, edges), drift records, and rule results; produce a structured Markdown document including:
  - Node inventory with type/layer breakdown
  - Edge statistics and relationship summary
  - Drift summary (open drifts by severity)
  - Rule violation highlights
  - Generated timestamp

### Schema

- `DesignDocRead` — title, content (Markdown), generated_at
- `DesignDocList` — paginated list

### Route Endpoint (1)

- `POST /projects/{pid}/architecture/design-doc` — Generate design doc

## Tests

3 tests covering:

- `TestDesignDocService` (2 tests) — empty project doc, project with nodes doc
- `TestDesignDocRoutes` (1 test) — generate design doc route

## Test Results

- **Total**: 482 passing
- **Regression**: None
