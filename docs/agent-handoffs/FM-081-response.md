# FM-081 — Architecture Graph Foundation

## Summary

Established the core data model and CRUD infrastructure for ForgeMind's architecture intelligence subsystem. Created 7 SQLAlchemy models (ArchitectureNode, ArchitectureEdge, ArchitectureSnapshot, ArchitectureDrift, ArchitectureRule, ArchitectureRuleResult, ChangeImpactAssessment), 9 enums, 28 Pydantic schemas, and a full graph CRUD service with 12 route endpoints. Migration 0022 creates 7 tables and 11 DB enum types.

## Deliverables

### Models (`apps/api/app/models/architecture.py`)

- **ArchitectureNode** — 12 node types (service, module, route, model, schema, middleware, utility, config, test, migration, component, page); key, name, path, language, metadata, source_type, status columns; workspace_id + project_id FKs
- **ArchitectureEdge** — 10 edge types (imports, calls, depends_on, extends, implements, composes, routes_to, reads_from, writes_to, configures); from_node_id/to_node_id FKs, confidence_score, source_type
- **ArchitectureSnapshot** — Point-in-time graph capture with name, source, summary, node_count, edge_count, snapshot_data JSON
- **ArchitectureDrift** — Drift records with severity (info/warning/error/critical), status (open/resolved/ignored), source_snapshot FK
- **ArchitectureRule** — 5 categories (import_rule, layer_rule, dependency_rule, ownership_rule, boundary_rule); rule_config JSON, severity, enabled flag
- **ArchitectureRuleResult** — Evaluation outcomes with pass/fail status, violating_node_ids, violating_edge_ids
- **ChangeImpactAssessment** — Impact records with target_node, severity, blast_radius, impacted_nodes/services, rationale, confidence_score

### Schemas (`apps/api/app/schemas/architecture.py`)

- 28 Pydantic models: ArchitectureNodeCreate/Read/List/Update, ArchitectureEdgeCreate/Read/List, ArchitectureSnapshotRead/List, ArchitectureGraphRead, NeighborRead, TopologyMapRequest, TopologySummary, ArchitectureDriftRead/List, ArchitectureRuleCreate/Read/List, ArchitectureRuleResultRead/List, DesignDocRead/List, ImpactAnalysisRequest, ChangeImpactAssessmentRead, RefactorRecommendation/List, HealthScoreDetails, StructuralHealthScore

### Service (`apps/api/app/services/architecture_service.py`)

- `create_node`, `get_node`, `list_nodes`, `update_node`, `delete_node`
- `create_edge`, `list_edges`, `delete_edge`
- `get_neighbors`, `get_full_graph`
- `create_snapshot`, `get_snapshot`, `list_snapshots`

### Routes (`apps/api/app/api/routes/architecture.py`)

- 12 endpoints for graph CRUD: node CRUD (5), edge CRUD (3), graph query (1), neighbors (1), snapshot CRUD (2)

### Migration (`apps/api/alembic/versions/2026_04_03_0022_add_architecture_tables.py`)

- 7 tables: architecture_nodes, architecture_edges, architecture_snapshots, architecture_drifts, architecture_rules, architecture_rule_results, change_impact_assessments
- 11 DB enum types: arch_node_type, arch_edge_type, arch_source_type, arch_edge_source_type, arch_node_status, drift_severity, drift_status, arch_rule_category, arch_rule_severity, arch_rule_result_status, impact_severity

### DB Registration (`apps/api/app/db/base.py`)

- All 7 architecture models imported and registered for Alembic metadata discovery

### Router Registration (`apps/api/app/api/router.py`)

- `architecture_router` registered with tag `"architecture"`

## Tests

19 tests covering:

- `TestArchitectureGraphService` (8 tests) — node/edge CRUD, neighbors, full graph, snapshots
- `TestArchitectureGraphRoutes` (11 tests) — all 12 endpoints via HTTP client

## Test Results

- **Total**: 482 passing
- **Regression**: None
