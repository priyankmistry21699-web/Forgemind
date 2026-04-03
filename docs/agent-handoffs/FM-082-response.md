# FM-082 — Topology Mapping Service

## Summary

Implemented a filesystem scanner that infers architecture nodes and edges from Python and TypeScript source code. Parses import statements, classifies files into architectural layers, and persists discovered topology as graph nodes and edges.

## Deliverables

### Service (`apps/api/app/services/topology_mapper_service.py`)

- **`parse_python_imports(source)`** — Extract import module names from Python source using regex
- **`parse_typescript_imports(source)`** — Extract import paths from TypeScript/JavaScript source
- **`classify_layer(path)`** — Assign files to architectural layers: route, service, model, schema, middleware, utility, config, test, migration, component, page
- **`detect_language(path)`** — Identify file language from extension (.py → python, .ts/.tsx → typescript, .js/.jsx → javascript)
- **`scan_directory_structure(root_path)`** — Walk a filesystem path and discover source files with metadata
- **`compute_topology_summary(scan_results)`** — Aggregate scan results into node/edge counts and layer breakdown
- **`map_topology(db, project_id, request)`** — Full pipeline: scan directory → parse imports → classify layers → create ArchitectureNode and ArchitectureEdge records → return TopologySummary

### Route Endpoint

- `POST /projects/{pid}/architecture/topology/map` — Trigger topology scan for a project

## Tests

7 tests covering:

- `TestTopologyMappingService` (6 tests) — parse Python/TS imports, classify layer, detect language, scan directory, compute summary, map topology persists
- `TestTopologyMappingRoutes` (1 test) — map topology route

## Test Results

- **Total**: 482 passing
- **Regression**: None
