# FM-083 — Drift Detection Engine

## Summary

Implemented drift detection that compares the current architecture graph against saved snapshots or architectural conventions. Detects new/removed components, cross-layer imports, and undocumented nodes. Supports resolve and ignore workflows for drift management.

## Deliverables

### Service (`apps/api/app/services/drift_detection_service.py`)

- **`detect_drift(db, project_id, snapshot_id=None)`** — Compare current graph vs. snapshot (if provided) or run convention checks; creates ArchitectureDrift records
- **`_compare_with_snapshot(db, project_id, snapshot)`** — Diff current node/edge sets against a saved snapshot's data; detects new components and removed components
- **`_detect_convention_drift(db, project_id)`** — Detect cross-layer import violations (e.g., routes importing models directly) and undocumented components
- **`list_drifts(db, project_id, status=None, severity=None)`** — Retrieve drift records with optional status/severity filtering
- **`resolve_drift(db, drift_id)`** — Mark a drift as resolved with timestamp
- **`ignore_drift(db, drift_id)`** — Mark a drift as ignored

### Route Endpoints (4)

- `POST /projects/{pid}/architecture/drift/detect` — Trigger drift detection
- `GET /projects/{pid}/architecture/drift` — List drift records
- `POST /projects/{pid}/architecture/drift/{did}/resolve` — Resolve a drift
- `POST /projects/{pid}/architecture/drift/{did}/ignore` — Ignore a drift

## Tests

5 tests covering:

- `TestDriftDetectionService` (3 tests) — convention drift detection, resolve workflow, ignore workflow
- `TestDriftDetectionRoutes` (2 tests) — detect drift route, list drifts route
- `TestSnapshotComparisonDrift` (2 tests) — detects new components, detects removed components (via snapshot diff)

## Test Results

- **Total**: 482 passing
- **Regression**: None
