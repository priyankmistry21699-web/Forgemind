# ForgeMind — Roadmap V3: FM-071 to FM-090

> **Status**: COMPLETE — All 20 milestones (FM-071 to FM-090) implemented  
> **Created**: 2026-04-02  
> **Updated**: 2026-04-03  
> **Themes**: Productization, Frontend Parity, Auth Hardening, CI/CD, Observability, Production Readiness, Architecture Intelligence

---

## Context

ForgeMind has completed all currently defined milestones through **FM-090** (90 tasks including sub-variants, 482 tests passing).

FM-071–FM-080 addressed productization gaps identified after FM-070. FM-081–FM-090 added the **Architecture Intelligence** subsystem — a graph-based architecture analysis, drift detection, rule enforcement, and structural health scoring layer.

### Gaps closed by FM-071–080 (after FM-070):

- **11 missing frontend pages** for advanced backend subsystems (trust, replay, council, governance, costs, audit, knowledge, vault, connectors, agents, settings)
- **Auth is stub/dev-mode** — not production-grade
- **No CI/CD** — `.github/workflows/` does not exist
- **No observability** — no metrics, tracing, or monitoring
- **SSE not consumed** — backend streaming exists but frontend doesn't subscribe
- **`packages/` empty** — all 8 subdirs contain only README.md stubs
- **No production deployment config** — no compose prod profile, no health check docs

This roadmap defines FM-071 to FM-080 to close these gaps.

---

## High-Level Objective

By the end of FM-080, ForgeMind should be:

- Fully navigable across all major existing backend capabilities
- Protected by real authentication and enforced RBAC
- Supported by CI/CD and automated quality gates
- Measurably observable at runtime
- Closer to production deployment readiness
- Cleaner as a monorepo with real shared packages

---

## Milestone Overview Table

| FM     | Title                                     | Priority | Theme                                 | Wave |
| ------ | ----------------------------------------- | -------- | ------------------------------------- | ---- |
| FM-071 | Advanced Frontend Parity I                | P0       | trust / replay / council / governance | 1    |
| FM-072 | Advanced Frontend Parity II               | P0       | costs / audit / knowledge / vault     | 1    |
| FM-073 | Platform Admin Frontend Parity            | P0       | connectors / agents / settings        | 1    |
| FM-074 | Real Authentication Integration           | P0       | auth / session / identity             | 2    |
| FM-075 | Route-Level RBAC Enforcement Hardening    | P0       | authorization consistency             | 2    |
| FM-076 | CI/CD Pipeline and Quality Gates          | P0       | automation / regression prevention    | ✅   |
| FM-077 | Real-Time UX Integration                  | P1       | SSE / live updates / subscriptions    | ✅   |
| FM-078 | Observability and Runtime Instrumentation | P1       | metrics / tracing / logs              | ✅   |
| FM-079 | Monorepo Package Extraction               | P1       | shared packages / boundaries          | 3    |
| FM-080 | Production Deployment Foundation          | P1       | deployability / envs / ops baseline   | 3    |

### FM-081–FM-090 — Architecture Intelligence (Wave 4)

| FM     | Title                           | Priority | Theme                                   | Wave |
| ------ | ------------------------------- | -------- | --------------------------------------- | ---- |
| FM-081 | Architecture Graph Foundation   | P0       | graph model / CRUD / snapshots          | 4    |
| FM-082 | Topology Mapping Service        | P0       | filesystem scan / import parsing        | 4    |
| FM-083 | Drift Detection Engine          | P0       | snapshot diff / convention drift        | 4    |
| FM-084 | Architecture Rule Engine        | P0       | rule definition / evaluation / results  | 4    |
| FM-085 | Architecture Dashboard Frontend | P0       | dashboard page / API client / sidebar   | 4    |
| FM-086 | Design Doc Synthesis            | P1       | Markdown doc generation from graph      | 4    |
| FM-087 | Change Impact Analysis          | P1       | BFS traversal / blast radius / severity | 4    |
| FM-088 | Refactor Recommendations        | P1       | god-modules / circular deps / isolation | 4    |
| FM-089 | Architecture Approval Workflow  | P1       | auto-approval for high-severity impacts | 4    |
| FM-090 | Structural Health Score         | P1       | composite 0–100 health metric           | 4    |

---

## Implementation Waves

### Wave 1 — Frontend Parity (FM-071, FM-072, FM-073)

Closes the 11 missing frontend pages. Cleanest, least disruptive first wins. Can be parallelized.

### Wave 2 — Platform Safety (FM-074, FM-075, FM-076)

Makes the platform secure and automatable. Real auth → RBAC enforcement → CI/CD pipeline.

### Wave 3 — Maturity (FM-077, FM-078, FM-079, FM-080)

Makes the product feel live, observable, and production-ready.

### Wave 4 — Architecture Intelligence (FM-081–FM-090)

Adds a graph-based architecture analysis subsystem: model the codebase as nodes and edges, detect drift, enforce architectural rules, score structural health, and generate design documentation and refactor recommendations.

---

## FM-071 — Advanced Frontend Parity I

**Title**: Frontend pages for Trust, Replay, Council, and Governance  
**Priority**: P0  
**Depends on**: None

### Why

Backend APIs exist for trust scoring, replay snapshots, multi-agent council, and governance policies. None are surfaced in the frontend dashboard.

### Scope

**Trust page** (`/dashboard/trust`)

- Trust score list with entity type / risk level filtering
- Risk level badges (low/medium/high/critical)
- Trust factors detail view
- Confidence display

**Replay page** (`/dashboard/replay`)

- Replay snapshot list
- Run execution trace explorer
- Step-by-step comparison view
- Hash/determinism visibility

**Council page** (`/dashboard/council`)

- Council session list with status filtering
- Vote breakdown per session
- Decision method display (consensus/majority/supermajority/weighted)
- Deadlock/escalation visibility

**Governance page** (`/dashboard/governance`)

- Policy list with trigger/action filtering
- Policy detail view
- Enable/disable toggle
- Priority display

### Files to Create

Frontend:

- `apps/web/app/dashboard/trust/page.tsx`
- `apps/web/app/dashboard/replay/page.tsx`
- `apps/web/app/dashboard/council/page.tsx`
- `apps/web/app/dashboard/governance/page.tsx`
- `apps/web/lib/trust.ts`
- `apps/web/lib/replay.ts`
- `apps/web/lib/council.ts`
- `apps/web/lib/governance.ts`
- `apps/web/types/trust.ts`
- `apps/web/types/replay.ts`
- `apps/web/types/council.ts`
- `apps/web/types/governance.ts`

Sidebar update:

- `apps/web/components/layout/sidebar.tsx` — add 4 new nav items

### Backend APIs (already exist)

- `GET /trust/scores` → `TrustScoreList`
- `GET /runs/{run_id}/trace` → `ExecutionTrace`
- `GET /replay/snapshots/{id}` → `ReplaySnapshotRead`
- `GET /council/sessions` → `CouncilSessionList`
- `GET /council/sessions/{id}` → `CouncilSessionRead`
- `GET /governance/policies` → `GovernancePolicyList`
- `GET /governance/policies/{id}` → `GovernancePolicyRead`

### Acceptance Criteria

- [ ] All 4 pages accessible from dashboard sidebar
- [ ] Each page loads real backend data via existing APIs
- [ ] Loading, error, and empty states handled
- [ ] Page-level filtering supported where relevant
- [ ] Links back to project/run context work

### Tests

- [ ] Backend route tests for any new filter/detail endpoints
- [ ] Frontend component smoke tests

---

## FM-072 — Advanced Frontend Parity II

**Title**: Frontend pages for Costs, Audit, Knowledge, and Credential Vault  
**Priority**: P0  
**Depends on**: None

### Scope

**Costs page** (`/dashboard/costs`)

- Cost record list with run/project grouping
- Run and project cost summaries
- Token count breakdowns
- Model cost comparison

**Audit page** (`/dashboard/audit`)

- Audit summary view
- Export buttons (JSON/CSV)
- Action type filtering
- Governance/approval trace links

**Knowledge page** (`/dashboard/knowledge`)

- Project knowledge list
- Type filtering (lesson_learned / pattern_discovered / etc.)
- Confidence/relevance metadata
- Detail view for reusable knowledge

**Vault page** (`/dashboard/vault`)

- Credential metadata list (name, scope, status — **no raw secrets**)
- Connector binding visibility
- Expiry/scope display
- Explicitly safe by design

### Files to Create

Frontend:

- `apps/web/app/dashboard/costs/page.tsx`
- `apps/web/app/dashboard/audit/page.tsx`
- `apps/web/app/dashboard/knowledge/page.tsx`
- `apps/web/app/dashboard/vault/page.tsx`
- `apps/web/lib/costs.ts`
- `apps/web/lib/audit.ts`
- `apps/web/lib/knowledge.ts`
- `apps/web/lib/vault.ts`
- `apps/web/types/cost.ts`
- `apps/web/types/audit.ts`
- `apps/web/types/knowledge.ts`
- `apps/web/types/vault.ts`

Sidebar update: add 4 new nav items

### Backend APIs (already exist)

- `GET /costs` → `CostRecordList`
- `GET /costs/runs/{id}/summary` → cost summary
- `GET /audit/summary` → audit summary
- `GET /audit/export/json` → JSON export
- `GET /audit/export/csv` → CSV export
- `GET /projects/{id}/knowledge` → `ProjectKnowledgeList`
- `GET /vault/credentials` → `CredentialVaultList`

### Acceptance Criteria

- [ ] All 4 pages operational
- [ ] Cost views show aggregated metrics
- [ ] Audit view shows traceable entries with export
- [ ] Knowledge view supports type filtering
- [ ] Vault shows metadata only — never exposes secret material

### Tests

- [ ] Route tests for list/detail behavior
- [ ] Access control tests around vault/audit endpoints

---

## FM-073 — Platform Admin Frontend Parity

**Title**: Frontend pages for Connectors, Agents, and Settings  
**Priority**: P0  
**Depends on**: None

### Scope

**Connectors page** (`/dashboard/connectors`)

- Connector catalog/list
- Readiness state display
- Project linkage visibility
- Credential/vault association

**Agents page** (`/dashboard/agents`)

- Agent registry list
- Capability display
- Status/availability
- Role/type display

**Settings page** (`/dashboard/settings`)

- User preferences
- Notification preferences
- Future hooks for auth/profile config

### Files to Create

Frontend:

- `apps/web/app/dashboard/connectors/page.tsx`
- `apps/web/app/dashboard/agents/page.tsx`
- `apps/web/app/dashboard/settings/page.tsx`
- `apps/web/lib/connectors.ts`
- `apps/web/lib/agents.ts`
- `apps/web/lib/settings.ts`
- `apps/web/types/connector.ts`
- `apps/web/types/agent.ts`
- `apps/web/types/settings.ts`

Sidebar update: enable the 3 existing disabled nav items and fix their hrefs to `/dashboard/...`

### Backend APIs

- `GET /connectors` → `ConnectorList` (exists)
- `GET /agents` → `AgentList` (exists)
- Settings: **no backend endpoint** — may need a new route or client-only storage

### Acceptance Criteria

- [ ] Connectors page reflects readiness/configuration data
- [ ] Agents page surfaces registered agents and capabilities
- [ ] Settings page provides stable base for user preferences
- [ ] All 3 sidebar links active (no longer disabled)

### Tests

- [ ] Backend route coverage for any new endpoints
- [ ] Frontend smoke/load tests

---

## FM-074 — Real Authentication Integration

**Title**: Replace stub/dev auth with real authentication  
**Priority**: P0  
**Depends on**: None (but should land before or with FM-075)

### Scope

Integrate a production-grade auth provider. Possible directions:

- NextAuth/Auth.js
- Clerk
- Auth0
- Custom JWT issuer with secure session handling

### Minimum Required Outcomes

- Real login/logout flow
- Authenticated frontend sessions
- Backend token verification against real identity provider
- User identity binding to backend user model
- No silent dev bypass in production mode

### Files to Modify/Create

Backend:

- `apps/api/app/core/auth.py` — replace/wrap auth stub with real token verification
- `apps/api/app/core/security.py` — if needed for JWT validation
- Route dependencies — ensure all protected routes use real auth context

Frontend:

- Auth provider wrapper / session management
- Login/logout pages or components
- Protected route middleware
- Auth-aware layout/header with user display

### Acceptance Criteria

- [ ] Users must authenticate to access dashboard
- [ ] Backend receives real verified identity on every request
- [ ] User ID / email / role mapping works end-to-end
- [ ] Dev fallback only allowed in explicit dev mode (env flag)

### Tests

- [ ] Auth dependency tests
- [ ] Protected route access tests (authenticated vs unauthenticated)
- [ ] Session/token verification tests

---

## FM-075 — Route-Level RBAC Enforcement Hardening

**Title**: Enforce consistent RBAC across all protected routes  
**Priority**: P0  
**Depends on**: FM-074

### Scope

Audit all route groups and ensure:

- Auth required where appropriate
- Workspace/project membership checks exist
- Admin-only actions protected
- Vault/governance/audit/repo/code-ops properly gated

### Areas to Harden

- workspaces, members
- governance, vault
- repo connections, code ops
- audit, cost analytics
- notifications config, sandbox

### Backend Work

- Route-by-route permission audit
- Central dependency/helpers for authz enforcement
- Normalize 401/403/404 behavior
- Reduce scattered permission checks

### Acceptance Criteria

- [ ] Every protected route has explicit auth/authz policy
- [ ] Unauthorized access returns consistent error semantics
- [ ] Sensitive actions require appropriate role
- [ ] Approval-sensitive code/repo actions remain gated

### Tests

- [ ] Permission matrix tests across major route groups
- [ ] Negative access tests (wrong role → 403)
- [ ] Regression tests for role scopes

---

## FM-076 — CI/CD Pipeline and Quality Gates

**Title**: Introduce CI/CD for lint, typecheck, tests, and builds  
**Priority**: P0  
**Depends on**: None

### Scope

Add GitHub Actions CI pipeline.

### Stages

**Backend** (`apps/api`):

- Python setup + dependency install
- Lint (ruff/flake8)
- Test (pytest)
- Optional: migration check

**Frontend** (`apps/web`):

- Node.js setup + dependency install
- TypeScript typecheck
- Lint (ESLint)
- Build verification

**Optional**:

- Docker build check
- Smoke startup check

### Files to Create

- `.github/workflows/ci.yml`
- Optionally: `.github/workflows/backend.yml`, `.github/workflows/frontend.yml`

### Acceptance Criteria

- [ ] Pushes and PRs trigger CI
- [ ] Failing tests block green build
- [ ] Backend and frontend both validated
- [ ] Reproducible instructions documented

---

## FM-077 — Real-Time UX Integration

**Title**: Consume backend SSE/streaming in frontend  
**Priority**: P1  
**Depends on**: FM-071–073 (pages must exist to display live data)

### Scope

Wire SSE consumption into:

- Run detail page (live task updates)
- Notifications center
- Activity feed (live entries)
- Escalation alerts

### Frontend Work

- SSE subscription client wrappers
- Reconnect + heartbeat handling
- Optimistic vs live state merge
- Expand `apps/web/lib/stream.ts`

### Acceptance Criteria

- [ ] Live run changes visible without refresh
- [ ] Graceful reconnect behavior
- [ ] No duplicate event rendering
- [ ] UI remains stable on disconnect

### Tests

- [ ] Stream client unit tests
- [ ] Backend stream regression tests

---

## FM-078 — Observability and Runtime Instrumentation

**Title**: Add metrics, tracing, and operational visibility  
**Priority**: P1  
**Depends on**: None

### Scope

- Prometheus metrics endpoint (`/metrics`)
- Request latency + error counters (middleware)
- Worker task execution metrics
- Sandbox execution telemetry
- Notification delivery telemetry
- Consistent request IDs across API/worker logs

### Acceptance Criteria

- [ ] Request latency and error metrics exposed
- [ ] Worker task counters visible
- [ ] Sandbox/notification failures measurable
- [ ] Major execution paths have traceable identifiers

### Tests

- [ ] Metric endpoint tests
- [ ] Instrumentation hook smoke tests

---

## FM-079 — Monorepo Package Extraction

**Title**: Turn `packages/` stubs into real shared packages  
**Priority**: P1  
**Depends on**: None

### Current State

All 8 subdirs under `packages/` (shared, types, config, ui, utils, db, ai, auth) contain only README.md.

### Goals

Extract reusable code from apps into at least 2–4 real packages:

- Shared TypeScript types
- Shared utilities/config
- Auth helpers
- Connector abstractions

### Constraints

- Don't over-extract prematurely
- Preserve delivery speed
- Keep ownership boundaries clear

### Acceptance Criteria

- [x] At least 2–4 packages become real with actual code
- [x] App imports become cleaner
- [x] Duplication reduced
- [x] Package purpose documented

### Tests

- [x] Package import/build validation
- [x] No broken app imports
- [x] Lint/typecheck remains green

---

## FM-080 — Production Deployment Foundation

**Title**: Establish a deployable production baseline  
**Priority**: P1  
**Depends on**: FM-076 (CI/CD), FM-078 (observability)

### Scope

- Production Docker Compose profile
- Environment variable contract documentation
- Health/readiness endpoint guidance
- Secrets/config expectations
- Reverse proxy + TLS notes
- Deployment README

### Acceptance Criteria

- [x] Another engineer can deploy from docs
- [x] Production env vars documented
- [x] Health endpoints and startup assumptions documented
- [x] Security-sensitive defaults called out

### Tests

- [x] Startup smoke test in prod-like config
- [x] Container build verification (optionally in CI)

---

## FM-081 — Architecture Graph Foundation

**Title**: Core data model and CRUD for architecture nodes, edges, and snapshots  
**Priority**: P0  
**Depends on**: None

### Scope

- `ArchitectureNode` model with 12 node types (service, module, route, model, schema, middleware, utility, config, test, migration, component, page), key, name, path, language, metadata, source_type, status
- `ArchitectureEdge` model with 10 edge types (imports, calls, depends_on, extends, implements, composes, routes_to, reads_from, writes_to, configures), confidence score, from/to node FKs
- `ArchitectureSnapshot` model for point-in-time graph captures (name, source, summary, node/edge counts, snapshot_data JSON)
- Full CRUD: create/get/list/update/delete nodes; create/list/delete edges
- `get_full_graph()` — returns all nodes + edges for a project
- `get_neighbors()` — returns nodes adjacent to a given node
- Migration 0022 with 7 tables and 11 DB enum types

### Files Created

- `apps/api/app/models/architecture.py` — 7 SQLAlchemy models, 9 enums
- `apps/api/app/schemas/architecture.py` — 28 Pydantic schemas
- `apps/api/app/services/architecture_service.py` — graph CRUD service
- `apps/api/app/api/routes/architecture.py` — 27 route endpoints
- `apps/api/alembic/versions/2026_04_03_0022_add_architecture_tables.py`
- `apps/api/app/db/base.py` — updated with 7 model imports

### Endpoints (12)

- `POST /projects/{pid}/architecture/nodes` — create node
- `GET /projects/{pid}/architecture/nodes` — list nodes
- `GET /projects/{pid}/architecture/nodes/{nid}` — get node
- `PATCH /projects/{pid}/architecture/nodes/{nid}` — update node
- `DELETE /projects/{pid}/architecture/nodes/{nid}` — delete node
- `POST /projects/{pid}/architecture/edges` — create edge
- `GET /projects/{pid}/architecture/edges` — list edges
- `DELETE /projects/{pid}/architecture/edges/{eid}` — delete edge
- `GET /projects/{pid}/architecture/graph` — full graph
- `GET /projects/{pid}/architecture/nodes/{nid}/neighbors` — neighbors
- `POST /projects/{pid}/architecture/snapshots` — create snapshot
- `GET /projects/{pid}/architecture/snapshots` — list snapshots

---

## FM-082 — Topology Mapping Service

**Title**: Filesystem scanner that infers architecture nodes and edges from source code  
**Priority**: P0  
**Depends on**: FM-081

### Scope

- `parse_python_imports()` — extract imports from Python source files
- `parse_typescript_imports()` — extract imports from TypeScript/JavaScript source files
- `classify_layer()` — assign files to architectural layers (route, service, model, schema, middleware, utility, config, test, migration, component, page)
- `detect_language()` — identify file language from extension
- `scan_directory_structure()` — walk a filesystem path and discover source files
- `compute_topology_summary()` — aggregate scan results into counts and layer breakdown
- `map_topology()` — full pipeline: scan → parse → classify → persist nodes + edges

### Files Created

- `apps/api/app/services/topology_mapper_service.py`

### Endpoints (1)

- `POST /projects/{pid}/architecture/topology/map` — trigger topology scan

---

## FM-083 — Drift Detection Engine

**Title**: Compare current architecture graph against snapshots or conventions  
**Priority**: P0  
**Depends on**: FM-081

### Scope

- `ArchitectureDrift` model with severity (info/warning/error/critical), status (open/resolved/ignored), drift_type, source_snapshot reference
- `detect_drift()` — compare current graph vs. snapshot or run convention checks (cross-layer imports, undocumented components, new/removed nodes)
- `_compare_with_snapshot()` — diff current node/edge sets against a saved snapshot
- `_detect_convention_drift()` — detect cross-layer violations and undocumented components
- `list_drifts()` — retrieve drift records filtered by status/severity
- `resolve_drift()` / `ignore_drift()` — update drift status

### Files Created

- `apps/api/app/services/drift_detection_service.py`

### Endpoints (4)

- `POST /projects/{pid}/architecture/drift/detect` — trigger drift detection
- `GET /projects/{pid}/architecture/drift` — list drifts
- `POST /projects/{pid}/architecture/drift/{did}/resolve` — resolve drift
- `POST /projects/{pid}/architecture/drift/{did}/ignore` — ignore drift

---

## FM-084 — Architecture Rule Engine

**Title**: Define architectural rules and evaluate them against the graph  
**Priority**: P0  
**Depends on**: FM-081

### Scope

- `ArchitectureRule` model with 5 categories (import_rule, layer_rule, dependency_rule, ownership_rule, boundary_rule), rule_config JSON, severity, enabled flag
- `ArchitectureRuleResult` model recording evaluation outcomes (pass/fail, message, violating node/edge IDs)
- `create_rule()` / `list_rules()` — rule CRUD
- `evaluate_rule()` — run a rule against the current graph
- Category-specific evaluators: `_evaluate_import_rule()`, `_evaluate_layer_rule()`, `_evaluate_dependency_rule()`, `_evaluate_ownership_rule()`

### Files Created

- `apps/api/app/services/architecture_rule_service.py`

### Endpoints (4)

- `POST /projects/{pid}/architecture/rules` — create rule
- `GET /projects/{pid}/architecture/rules` — list rules
- `POST /projects/{pid}/architecture/rules/{rid}/evaluate` — evaluate rule
- `GET /projects/{pid}/architecture/rule-results` — list results

---

## FM-085 — Architecture Dashboard Frontend

**Title**: Dashboard page, API client, TypeScript types, and sidebar navigation for architecture intelligence  
**Priority**: P0  
**Depends on**: FM-081–084

### Scope

- **Dashboard page** (`/dashboard/architecture`) — displays graph stats, drift summary, rule results, recommendations, and structural health score with stat cards and severity badges
- **API client** (`apps/web/lib/architecture.ts`) — 12 functions: fetchArchitectureGraph, fetchArchitectureNodes, fetchArchitectureEdges, fetchArchitectureSnapshots, mapTopology, detectDrift, fetchDrifts, fetchArchitectureRules, fetchRuleResults, generateDesignDoc, analyseImpact, fetchRecommendations, fetchHealthScore
- **TypeScript types** — packages/schemas/src/architecture.ts (19 interfaces + 8 type unions), apps/web/types/architecture.ts (re-exports)
- **Sidebar navigation** — "Architecture" link in sidebar pointing to `/dashboard/architecture`

### Files Created

- `apps/web/app/dashboard/architecture/page.tsx`
- `apps/web/lib/architecture.ts`
- `apps/web/types/architecture.ts`
- `packages/schemas/src/architecture.ts`

---

## FM-086 — Design Doc Synthesis

**Title**: Generate Markdown architecture documents from graph data  
**Priority**: P1  
**Depends on**: FM-081

### Scope

- `generate_design_doc()` — query project's architecture graph + drift + rule results and produce a structured Markdown design summary
- Includes: node inventory, layer breakdown, edge statistics, drift summary, rule violation highlights
- Returns `DesignDocRead` schema with title, content, generated_at

### Files Created

- `apps/api/app/services/design_doc_service.py`

### Endpoints (1)

- `POST /projects/{pid}/architecture/design-doc` — generate design doc

---

## FM-087 — Change Impact Analysis

**Title**: BFS-based reverse traversal to compute blast radius for proposed changes  
**Priority**: P1  
**Depends on**: FM-081

### Scope

- `ChangeImpactAssessment` model with target_node/path/key, severity (none/low/medium/high/critical), blast_radius count, impacted_nodes/services lists, rationale, confidence_score
- `analyse_impact()` — BFS reverse traversal from target node through incoming edges; counts impacted nodes; escalates severity at thresholds (≥10 deps → HIGH, ≥20 → CRITICAL)
- Stores assessment in DB and returns result

### Files Created

- `apps/api/app/services/impact_analysis_service.py`

### Endpoints (1)

- `POST /projects/{pid}/architecture/impact-analysis` — analyze impact

---

## FM-088 — Refactor Recommendations

**Title**: Analyze architecture graph for structural issues and suggest refactoring  
**Priority**: P1  
**Depends on**: FM-081, FM-083, FM-084

### Scope

- `generate_recommendations()` — analyze graph for:
  - **God modules** — nodes with excessive fan-in (many incoming edges)
  - **Circular dependencies** — cycles detected via edge traversal
  - **Isolated nodes** — nodes with no edges (disconnected components)
  - **Drift backlogs** — open drifts that haven't been resolved
  - **Rule violation backlogs** — accumulated failed rule evaluations
- Returns `RefactorRecommendationList` with type, title, description, severity, affected nodes

### Files Created

- `apps/api/app/services/refactor_recommendation_service.py`

### Endpoints (1)

- `GET /projects/{pid}/architecture/recommendations` — get recommendations

---

## FM-089 — Architecture Approval Workflow

**Title**: Auto-create approval requests when change impact severity is HIGH or CRITICAL  
**Priority**: P1  
**Depends on**: FM-087

### Scope

- `maybe_create_approval()` — checks a `ChangeImpactAssessment`'s severity; if HIGH or CRITICAL, auto-creates an `ApprovalRequest` with architecture context
- `list_architecture_approvals()` — retrieve approval requests whose titles contain "Architecture" or "Impact"
- Integrates with existing approval_service for the actual approval workflow

### Files Created

- `apps/api/app/services/architecture_approval_service.py`

### Endpoints (2)

- `POST /projects/{pid}/architecture/approvals` — request approval (auto-creates if severity warrants)
- `GET /projects/{pid}/architecture/approvals` — list architecture approvals

---

## FM-090 — Structural Health Score

**Title**: Composite 0–100 score aggregating architecture quality indicators  
**Priority**: P1  
**Depends on**: FM-081, FM-083, FM-084

### Scope

- `compute_health_score()` — calculates a weighted score from:
  - **Coverage** — % of nodes documented/classified
  - **Drift penalty** — deductions for open drifts (weighted by severity)
  - **Rule compliance** — % of rule evaluations that pass
  - **Isolation ratio** — proportion of disconnected nodes
- Returns `StructuralHealthScore` with overall score, letter grade, and `HealthScoreDetails` breakdown

### Files Created

- `apps/api/app/services/structural_health_service.py`

### Endpoints (1)

- `GET /projects/{pid}/architecture/health-score` — get health score

---

## FM Tracker

| FM     | Title                                     | Status      |
| ------ | ----------------------------------------- | ----------- |
| FM-071 | Advanced Frontend Parity I                | ✅ Complete |
| FM-072 | Advanced Frontend Parity II               | ✅ Complete |
| FM-073 | Platform Admin Frontend Parity            | ✅ Complete |
| FM-074 | Real Authentication Integration           | ✅ Complete |
| FM-075 | Route-Level RBAC Enforcement Hardening    | ✅ Complete |
| FM-076 | CI/CD Pipeline and Quality Gates          | ✅ Complete |
| FM-077 | Real-Time UX Integration                  | ✅ Complete |
| FM-078 | Observability and Runtime Instrumentation | ✅ Complete |
| FM-079 | Monorepo Package Extraction               | ✅ Complete |
| FM-080 | Production Deployment Foundation          | ✅ Complete |

### Architecture Intelligence (FM-081–FM-090)

| FM     | Title                           | Status      |
| ------ | ------------------------------- | ----------- |
| FM-081 | Architecture Graph Foundation   | ✅ Complete |
| FM-082 | Topology Mapping Service        | ✅ Complete |
| FM-083 | Drift Detection Engine          | ✅ Complete |
| FM-084 | Architecture Rule Engine        | ✅ Complete |
| FM-085 | Architecture Dashboard Frontend | ✅ Complete |
| FM-086 | Design Doc Synthesis            | ✅ Complete |
| FM-087 | Change Impact Analysis          | ✅ Complete |
| FM-088 | Refactor Recommendations        | ✅ Complete |
| FM-089 | Architecture Approval Workflow  | ✅ Complete |
| FM-090 | Structural Health Score         | ✅ Complete |

### ForgeMind Local (FM-091–FM-100)

| FM     | Title                            | Status      |
| ------ | -------------------------------- | ----------- |
| FM-091 | Local Foundation & Config        | ✅ Complete |
| FM-092 | Repo Indexing & Manifest         | ✅ Complete |
| FM-093 | Local Chat Over Codebase         | ✅ Complete |
| FM-094 | Local Execution Sandbox          | ✅ Complete |
| FM-095 | Patch Generation & Management    | ✅ Complete |
| FM-096 | PR Preparation                   | ✅ Complete |
| FM-097 | IDE Integration                  | ✅ Complete |
| FM-098 | State Management & Sync Queue    | ✅ Complete |
| FM-099 | Handoff Snapshots                | ✅ Complete |
| FM-100 | Hardening, Tests & Documentation | ✅ Complete |

---

## Cross-Milestone Dependencies

```
FM-071/072/073 (frontend pages) — independent, parallelizable
        ↓
FM-074 (real auth) — can start in parallel but must gate page access
FM-075 (RBAC) — depends on FM-074 for real identities
FM-076 (CI/CD) — independent, start anytime
        ↓
FM-077 (SSE) — depends on FM-071–073 pages existing
FM-078 (observability) — independent
FM-079 (packages) — independent refactoring
FM-080 (production) — benefits from FM-076 + FM-078
```

---

## Wave 5 — Developer Workstation Mode (FM-091–FM-100)

> **Status:** ✅ Complete
> **Theme:** ForgeMind Local — standalone CLI companion for local repo intelligence, execution, patching, and PR preparation

### Milestone 22 — ForgeMind Local (FM-091 to FM-100)

## FM-091 — Local Foundation: Config, Init & Directory Management

- **Priority:** P0
- **Depends on:** (none — standalone package)

### Why

Developers need a lightweight local companion that can operate offline, without requiring the full API/DB stack.

### Scope

- `LocalConfig` dataclass with YAML serialisation
- `detect_repo_root()` — walks up to find `.git/`
- `ensure_directories()` — creates `.forgemind/{state,cache,index,patches,snapshots}`
- CLI commands: `forgemind init`, `forgemind status`

### Files Created

- `apps/local/forgemind_local/config.py`
- `apps/local/forgemind_local/cli.py` (init + status commands)

### Acceptance Criteria

- [x] `LocalConfig` round-trips through YAML
- [x] `detect_repo_root()` finds `.git/` or returns None
- [x] `ensure_directories()` creates all 5 subdirs
- [x] CLI `init` creates workspace; `status` prints health table

---

## FM-092 — Repo Indexing & Manifest

- **Priority:** P0
- **Depends on:** FM-091

### Scope

- Walk local file tree, classify files by language (30+ extensions)
- Detect entrypoints (6 patterns) and build files (11 patterns)
- Prune 15 ignored directories (node_modules, .git, **pycache**, etc.)
- Persist JSON manifest to `.forgemind/index/repo_manifest.json`
- CLI command: `forgemind attach`

### Files Created

- `apps/local/forgemind_local/repo_index.py`

### Acceptance Criteria

- [x] Manifest contains files, languages, line counts, entrypoints, build files
- [x] Ignored directories are pruned
- [x] Manifest loads from cache when present

---

## FM-093 — Local Chat Over Codebase

- **Priority:** P1
- **Depends on:** FM-092

### Scope

- Keyword search over manifest files and content
- File snippet reading (first N lines)
- Regex intent detection (`show me`, `where is`)
- Optional LiteLLM integration (env var `FORGEMIND_LLM_MODEL`)
- Graceful degradation to rule-based answers when offline
- Returns `{"answer": str, "citations": list[str]}`
- CLI command: `forgemind ask "question"`

### Files Created

- `apps/local/forgemind_local/local_chat.py`

### Acceptance Criteria

- [x] Returns answer dict with citations
- [x] Works offline without LLM
- [x] LLM path available when litellm installed

---

## FM-094 — Local Execution Sandbox

- **Priority:** P0
- **Depends on:** FM-091

### Scope

- 16 blocked command patterns (rm -rf, fork bombs, format c:, etc.)
- 35 safe command prefixes (pytest, ruff, git status, etc.)
- 3 execution policies: safe (allowlist), permissive (anything not blocked), locked (nothing)
- Subprocess with configurable timeout
- JSON run logging to `.forgemind/state/runs/`
- CLI command: `forgemind exec "command"`

### Safety Boundaries

- `shell=True` — appropriate for local dev tool where user is the operator
- Blocked patterns are substring-matched defense-in-depth, not a security boundary
- `permissive` policy allows any command not in the blocked list
- No network or filesystem sandboxing — relies on user trust

### Files Created

- `apps/local/forgemind_local/local_exec.py`

### Acceptance Criteria

- [x] Always-blocked patterns rejected regardless of policy
- [x] Safe policy only allows allowlisted command prefixes
- [x] Locked policy blocks everything
- [x] Execution results logged to JSON

---

## FM-095 — Patch Generation & Management

- **Priority:** P1
- **Depends on:** FM-091

### Scope

- `generate_patch()` — `git diff` to `.patch` file with JSON metadata
- `list_patches()` — enumerate all patches with metadata
- `preview_patch()` — read raw diff
- `apply_patch()` — `git apply --check` then `git apply`
- `reject_patch()` — set status="rejected" in metadata
- CLI group: `forgemind patch generate/list/preview/apply/reject`

### Files Created

- `apps/local/forgemind_local/local_patch.py`

### Acceptance Criteria

- [x] Generates .patch + .json metadata pair
- [x] Apply runs safety check before applying
- [x] Reject updates metadata status

---

## FM-096 — PR Preparation

- **Priority:** P1
- **Depends on:** FM-092, FM-095

### Scope

- `prepare_pr()` — reads `git diff --stat` and `git diff --name-only`
- Classifies files into 11 subsystems (api, frontend, tests, config, etc.)
- Detects risk patterns (security, db migration, env vars, auth changes)
- Generates dynamic test checklist
- Produces markdown with title, branch, files, risks, checklist, subsystems
- CLI command: `forgemind pr prepare`

### Files Created

- `apps/local/forgemind_local/local_pr.py`

### Acceptance Criteria

- [x] Returns dict with markdown, title, branch, files, risks, checklist, subsystems
- [x] Risk detection identifies security-sensitive changes
- [x] Subsystem classification covers 11 categories

---

## FM-097 — IDE Integration

- **Priority:** P2
- **Depends on:** FM-091

### Scope

- `setup_editor()` — generates `.vscode/tasks.json` with 10 ForgeMind tasks + 2 input prompts
- Idempotent merge with existing tasks.json (removes old ForgeMind tasks, appends new)
- Tasks: init, attach, status, ask, exec, patch generate/apply, pr prepare, snapshot export/import
- CLI command: `forgemind ide setup`

### Files Created

- `apps/local/forgemind_local/ide_integration.py`

### Acceptance Criteria

- [x] Creates tasks.json with all ForgeMind tasks
- [x] Idempotent — running twice doesn't duplicate tasks
- [x] Preserves existing non-ForgeMind tasks

---

## FM-098 — State Management & Sync Queue

- **Priority:** P1
- **Depends on:** FM-091

### Scope

- Cache: `cache_put/get/clear` with TTL-based expiry
- Sync queue: `queue_event/list_queue/mark_synced/clear_synced`
- Mode management: `get_mode/set_mode/is_online` — 3 modes: offline, hybrid, remote
- All JSON-file-backed in `.forgemind/state/` and `.forgemind/cache/`

> **Note:** The sync queue stores events for future offline→online handoff but no sync consumer is implemented yet. This is infrastructure-ready for a future FM task.

### Files Created

- `apps/local/forgemind_local/local_state.py`

### Acceptance Criteria

- [x] Cache entries expire after TTL
- [x] Queue events persist and can be marked synced
- [x] Mode validation rejects invalid modes
- [x] `is_online` reflects current mode

---

## FM-099 — Handoff Snapshots

- **Priority:** P1
- **Depends on:** FM-098

### Scope

- `export_snapshot()` — bundles config, manifest, patches metadata, sync queue (last 50), run logs (last 20), PR summary into timestamped zip with `manifest.json`
- `import_snapshot()` — unpacks bundle into `.forgemind/` non-destructively (won't overwrite existing config)
- `inspect_bundle()` — reads manifest without importing
- CLI commands: `forgemind snapshot export`, `forgemind snapshot import`

### Files Created

- `apps/local/forgemind_local/local_handoff.py`

### Acceptance Criteria

- [x] Export creates valid zip with manifest
- [x] Import is non-destructive
- [x] Inspect reads metadata without importing
- [x] Round-trip export→import preserves data

---

## FM-100 — Hardening, Tests & Documentation

- **Priority:** P0
- **Depends on:** FM-091–FM-099

### Scope

- 53 tests across 9 test classes covering all modules
- Documentation updates across all tracking files
- Response files for each FM task

### Files Created

- `apps/local/tests/test_local.py`

### Tests

| Test Class         | Count | Module Covered     |
| ------------------ | ----- | ------------------ |
| TestConfig         | 7     | config.py          |
| TestRepoIndex      | 7     | repo_index.py      |
| TestLocalChat      | 8     | local_chat.py      |
| TestLocalExec      | 7     | local_exec.py      |
| TestLocalPatch     | 4     | local_patch.py     |
| TestLocalPR        | 7     | local_pr.py        |
| TestIDEIntegration | 2     | ide_integration.py |
| TestLocalState     | 9     | local_state.py     |
| TestLocalHandoff   | 5     | local_handoff.py   |

### Acceptance Criteria

- [x] All 53 tests passing
- [x] Ruff lint + format clean
- [x] Documentation updated across all tracking files
- [x] Response files created for FM-091 through FM-100

---

### ForgeMind Local (FM-091–FM-100)

| FM     | Title                            | Status      |
| ------ | -------------------------------- | ----------- |
| FM-091 | Local Foundation & Config        | ✅ Complete |
| FM-092 | Repo Indexing & Manifest         | ✅ Complete |
| FM-093 | Local Chat Over Codebase         | ✅ Complete |
| FM-094 | Local Execution Sandbox          | ✅ Complete |
| FM-095 | Patch Generation & Management    | ✅ Complete |
| FM-096 | PR Preparation                   | ✅ Complete |
| FM-097 | IDE Integration                  | ✅ Complete |
| FM-098 | State Management & Sync Queue    | ✅ Complete |
| FM-099 | Handoff Snapshots                | ✅ Complete |
| FM-100 | Hardening, Tests & Documentation | ✅ Complete |

---

## Cross-Milestone Dependencies

```
FM-071/072/073 (frontend pages) — independent, parallelizable
        ↓
FM-074 (real auth) — can start in parallel but must gate page access
FM-075 (RBAC) — depends on FM-074 for real identities
FM-076 (CI/CD) — independent, start anytime
        ↓
FM-077 (SSE) — depends on FM-071–073 pages existing
FM-078 (observability) — independent
FM-079 (packages) — independent refactoring
FM-080 (production) — benefits from FM-076 + FM-078
        ↓
FM-081–090 (architecture intelligence) — depends on backend models/services
        ↓
FM-091–100 (local CLI) — standalone package, no backend dependency
```

---

## Success Condition

By the end of FM-100, ForgeMind is a fully navigable, production-hardened AI execution platform with:

- Complete frontend parity across all backend subsystems
- Real authentication and enforced RBAC
- CI/CD and automated quality gates
- Runtime observability with metrics and tracing
- Shared monorepo packages with real code
- Production deployment foundation
- **Architecture intelligence** — graph-based structural analysis, drift detection, rule enforcement, impact analysis, refactor recommendations, and a composite structural health score
- **ForgeMind Local** — standalone developer workstation CLI for offline repo intelligence, bounded execution, patch management, PR preparation, IDE integration, and team handoff snapshots

**All 100 tasks across 22 milestones are complete. 535 tests passing.**

---

## Wave 6 — SPEC-Driven Lifecycle (FM-101–FM-110)

### Overview

Wave 6 transforms ForgeMind into a **truly SPEC-driven platform** where every run begins with a formal specification, flows through a validated plan, and is gated at every lifecycle transition. This wave introduces project constitutions, slash commands, ADR-aware planning, spec-to-plan validation, and approval integration.

### Status Tracker

| FM     | Title                              | Status      |
| ------ | ---------------------------------- | ----------- |
| FM-101 | SPEC Artifact & SPECIFYING Status  | ✅ Complete |
| FM-102 | Project Constitution Model         | ✅ Complete |
| FM-103 | Constitution UI & Governance Hooks | ✅ Complete |
| FM-104 | Slash Command Parsing              | ✅ Complete |
| FM-105 | Structured SPEC Generation         | ✅ Complete |
| FM-106 | PLAN Artifact Export & Linking     | ✅ Complete |
| FM-107 | ADR-Aware Planning                 | ✅ Complete |
| FM-108 | Spec-to-Plan Validation            | ✅ Complete |
| FM-109 | Approval Integration               | ✅ Complete |
| FM-110 | Tests & Hardening                  | ✅ Complete |

### Milestone 23 — SPEC-Driven Lifecycle (FM-101 to FM-110)

---

## FM-101 — SPEC Artifact & SPECIFYING Status

**Goal:** Introduce `SPEC` as a first-class artifact type and `SPECIFYING` as a run lifecycle status.

### What was built:

- Added `SPEC = "spec"` and `PLAN = "plan"` to `ArtifactType` enum
- Added `SPECIFYING = "specifying"` to `RunStatus` enum
- Added `spec_artifact_id` FK on Artifact model (self-referential, nullable) to link PLAN → SPEC
- Lifecycle gating: `SPECIFYING → PLANNING` requires a SPEC artifact; `PLANNING → RUNNING` requires a PLAN artifact
- Updated frontend TypeScript types for new artifact/run status values

### Files changed:

- `app/models/artifact.py` — ArtifactType enum, spec_artifact_id column
- `app/models/run.py` — RunStatus enum
- `app/schemas/artifact.py` — spec_artifact_id in read/create schemas
- `app/services/run_lifecycle_service.py` — transition validation
- `packages/schemas/src/artifact.ts` — TypeScript types
- `packages/schemas/src/run.ts` — TypeScript types

---

## FM-102 — Project Constitution Model

**Goal:** Allow projects to define a governing constitution that shapes all AI behavior.

### What was built:

- `ProjectConstitution` model with id, project_id (unique), title, content, summary, version, timestamps
- `ConstitutionRead`, `ConstitutionCreate`, `ConstitutionUpdate` Pydantic schemas with content validation (1–50,000 chars)
- `constitution_service` with get/create_or_update/delete + governance event emission (CONSTITUTION_UPDATED)
- `build_constitution_prompt_section()` for injecting constitution into LLM prompts
- REST routes: GET/PUT/PATCH/DELETE `/projects/{project_id}/constitution`

### Files changed:

- `app/models/project_constitution.py` — new model
- `app/models/project.py` — constitution relationship
- `app/schemas/constitution.py` — new schemas
- `app/services/constitution_service.py` — new service
- `app/api/routes/constitution.py` — new routes
- `app/api/router.py` — route registration
- `app/db/base.py` — model registration

---

## FM-103 — Constitution UI & Governance Hooks

**Goal:** Frontend constitution editor and governance audit trail integration.

### What was built:

- `ConstitutionEditor` React component with create/edit/delete UI
- TypeScript types and API client functions for constitution CRUD
- Governance event emission on all constitution mutations (create, update, delete)
- Constitution context injected into chat service prompts

### Files changed:

- `apps/web/components/projects/constitution-editor.tsx` — new component
- `apps/web/types/constitution.ts` — TypeScript re-exports
- `apps/web/lib/constitution.ts` — API client
- `packages/schemas/src/constitution.ts` — shared types
- `packages/schemas/src/index.ts` — barrel export
- `app/services/chat_service.py` — constitution context injection

---

## FM-104 — Slash Command Parsing

**Goal:** Support `/fm.*` slash commands in the chat interface for direct lifecycle actions.

### What was built:

- `SlashCommandService` with regex parsing for `/fm.specify`, `/fm.plan`, `/fm.tasks`, `/fm.implement`
- `ParsedCommand` and `CommandResult` dataclasses
- `execute_command()` routing to appropriate services
- Chat route integration — slash commands intercepted before normal LLM chat
- `GET /chat/commands` autocomplete endpoint
- Frontend slash command suggestions in chat panel

### Files changed:

- `app/services/slash_command_service.py` — new service
- `app/api/routes/chat.py` — slash command detection + commands endpoint
- `apps/web/components/chat/run-chat-panel.tsx` — command suggestions UI

---

## FM-105 — Structured SPEC Generation

**Goal:** LLM-powered SPEC artifact generation with constitution context.

### What was built:

- `spec_service.generate_spec()` — LLM-based structured specification generation with stub fallback
- Constitution context integration via `constitution_service.get_constitution_for_prompt()`
- Governance event emission (SPEC_CREATED)
- Auto-transition from PENDING → SPECIFYING on spec generation
- `get_spec_for_run()` for retrieving latest SPEC artifact

### Files changed:

- `app/services/spec_service.py` — new service

---

## FM-106 — PLAN Artifact Export & Linking

**Goal:** Generate PLAN artifacts linked to their SPEC, with markdown export capability.

### What was built:

- `plan_artifact_service.generate_plan_artifact()` — LLM-based plan generation with SPEC linkage via `spec_artifact_id`
- `export_plan_markdown()` — combined SPEC+PLAN markdown export
- `get_plan_export_data()` — JSON metadata for API export
- Auto-transition SPECIFYING → PLANNING on plan generation
- REST endpoints: `GET /runs/{id}/plan/export` (JSON), `GET /runs/{id}/plan/export/markdown` (plaintext)

### Files changed:

- `app/services/plan_artifact_service.py` — new service
- `app/api/routes/artifacts.py` — export endpoints

---

## FM-107 — ADR-Aware Planning

**Goal:** Enrich plans with architecture context from the FM-081–090 architecture intelligence system.

### What was built:

- `adr_service.build_adr_section()` — ADR-style markdown from architecture graph (nodes, edges, drifts, violations)
- `adr_service.enrich_plan_with_adr()` — appends architecture context to plan content
- `adr_service.get_architecture_context_for_prompt()` — concise summary for LLM prompts
- Integrated into `plan_artifact_service` — architecture context in prompt + ADR section in output

### Files changed:

- `app/services/adr_service.py` — new service
- `app/services/plan_artifact_service.py` — ADR integration

---

## FM-108 — Spec-to-Plan Validation

**Goal:** Validate that plans adequately cover their specification before allowing execution.

### What was built:

- `spec_plan_validation_service.validate_spec_plan()` — returns `SpecPlanValidationResult` with coverage map and issues list
- Validation rules: spec_exists, plan_exists, plan_linked_to_spec, spec/plan section completeness, plan_substance (≥100 chars), acceptance_criteria_coverage (keyword matching), constraints_acknowledged
- Lifecycle gate: PLANNING → RUNNING blocked if validation fails
- REST endpoint: `GET /lifecycle/runs/{id}/spec-plan/validate`

### Files changed:

- `app/services/spec_plan_validation_service.py` — new service
- `app/services/run_lifecycle_service.py` — validation gate integration
- `app/api/routes/run_lifecycle.py` — validation endpoint

---

## FM-109 — Approval Integration

**Goal:** Gate lifecycle transitions on SPEC and PLAN approval status.

### What was built:

- `spec_plan_approval_service` with request_spec_approval(), request_plan_approval(), is_spec_approved(), is_plan_approved()
- Idempotent approval request creation tied to artifact IDs
- Lifecycle gates: SPECIFYING → PLANNING blocked if SPEC has pending/rejected approval; PLANNING → RUNNING blocked if PLAN has pending/rejected approval
- REST endpoints: `POST /lifecycle/runs/{id}/spec/approve`, `POST /lifecycle/runs/{id}/plan/approve`, `GET /lifecycle/runs/{id}/artifact-approvals`

### Files changed:

- `app/services/spec_plan_approval_service.py` — new service
- `app/services/run_lifecycle_service.py` — approval gate integration
- `app/api/routes/run_lifecycle.py` — approval endpoints

---

## FM-110 — Tests & Hardening

**Goal:** Comprehensive test coverage for FM-101–109.

### What was built:

- 60 tests across 12 test classes covering all milestones
- Test classes: TestFM101_ArtifactTypes, TestFM101_LifecycleGating, TestFM102_Constitution, TestFM103_GovernanceEvents, TestFM104_SlashCommands, TestFM105_SpecGeneration, TestFM106_PlanArtifact, TestFM107_ADREnrichment, TestFM108_SpecPlanValidation, TestFM109_SpecPlanApproval, TestFM110_E2E, TestFM_Routes
- E2E lifecycle tests validating the full PENDING → SPECIFYING → PLANNING → RUNNING flow
- Route integration tests for chat, slash commands, constitution CRUD, and validation endpoints
- Governance event emission tests for constitution mutations
- ADR-aware enrichment tests for architecture context injection

### Files changed:

- `tests/test_fm101_110_spec_lifecycle.py` — 60 tests

### Test Results:

- **60/60 new tests passing**
- **542 total tests passing (no regressions)**

---

## Success Condition (Updated)

By the end of FM-110, ForgeMind is a fully SPEC-driven AI execution platform with:

- Formal SPEC → PLAN → EXECUTE lifecycle with gating at every transition
- Project constitutions that govern all AI behavior
- Slash commands for direct lifecycle control from chat
- LLM-powered SPEC and PLAN generation with constitution context
- Architecture-aware planning via ADR enrichment
- Spec-to-plan validation ensuring plan coverage before execution
- Approval gates on SPEC and PLAN artifacts
- **542 tests across 23 milestones, all passing.**

---

# Future Roadmap — FM-111 to FM-140 (Planned)

> The following milestones are **planned** and have **not yet been implemented**. They represent the next three waves of ForgeMind development, organized into coherent themes aligned with the platform's current architecture through FM-110.

---

## Wave 7 — Phase Routing, Templates, and Project Bootstrapping (FM-111–FM-120)

### Overview

Wave 7 introduces **phase-aware agent routing** and **project templates** — enabling ForgeMind to recommend specialized agent compositions per lifecycle phase and bootstrap new projects from proven templates that include constitutions, policies, and spec/plan scaffolding.

### Status Tracker

| FM     | Title                                          | Status       |
| ------ | ---------------------------------------------- | ------------ |
| FM-111 | Phase Agent Profile Data Model                 | 🔲 Planned  |
| FM-112 | Composition Engine Phase-Aware Routing         | 🔲 Planned  |
| FM-113 | Phase Agent Profile UI                         | 🔲 Planned  |
| FM-114 | Project Template Model and Seeding             | 🔲 Planned  |
| FM-115 | Template-Based Project Creation Flow           | 🔲 Planned  |
| FM-116 | Template Inheritance for Constitution & Policies | 🔲 Planned |
| FM-117 | Knowledge-Driven Constitution Suggestions      | 🔲 Planned  |
| FM-118 | Spec/Plan Bootstrap from Project Templates     | 🔲 Planned  |
| FM-119 | Local Mode Support for Templates & Phase Profiles | 🔲 Planned |
| FM-120 | Project Intelligence Bootstrapping Hardening   | 🔲 Planned  |

### Milestone 24 — Phase Routing, Templates & Bootstrapping (FM-111 to FM-120)

#### FM-111 — Phase Agent Profile Data Model

**Goal:** Define data models for mapping lifecycle phases (SPECIFYING, PLANNING, RUNNING) to recommended agent profiles with capability metadata.

**Planned scope:**
- `PhaseAgentProfile` ORM model — phase, agent_slug, priority, capability_tags
- Per-project and global profiles
- CRUD service and schemas

#### FM-112 — Composition Engine Phase-Aware Routing

**Goal:** Extend the composition engine to select and prioritize agents based on the current run lifecycle phase.

**Planned scope:**
- Query phase profiles when composing agent teams
- Priority-weighted agent selection per phase
- Fallback to default composition if no phase profiles exist

#### FM-113 — Phase Agent Profile UI

**Goal:** Frontend for viewing and editing phase-to-agent mappings per project.

**Planned scope:**
- Phase profile editor component
- Drag-and-drop agent ordering per phase
- Default profile inheritance display

#### FM-114 — Project Template Model and Seeding

**Goal:** Create a template system that captures proven project configurations for reuse.

**Planned scope:**
- `ProjectTemplate` ORM model — name, description, category, config_snapshot
- Template seeding from existing successful projects
- System-provided default templates (API, CLI, Full-Stack, Library)

#### FM-115 — Template-Based Project Creation Flow

**Goal:** Allow users to create new projects from templates instead of from scratch.

**Planned scope:**
- Template picker in project creation UI
- Auto-populate project config, agent profiles, and governance settings from template
- Preview of template contents before creation

#### FM-116 — Template Inheritance for Constitution & Policies

**Goal:** Templates carry constitution content and approval policies that seed new projects.

**Planned scope:**
- Constitution content snapshot in templates
- Approval policy settings in templates
- Merge/override logic when user customizes inherited settings

#### FM-117 — Knowledge-Driven Constitution Suggestions

**Goal:** Use project knowledge base to suggest constitution improvements based on past run outcomes.

**Planned scope:**
- Analyze failed/successful runs to identify governance patterns
- Suggest constitution additions (e.g., "add constraint: always include error handling")
- User accept/reject flow for suggestions

#### FM-118 — Spec/Plan Bootstrap from Project Templates

**Goal:** Auto-generate initial SPEC and PLAN scaffolding from project template metadata.

**Planned scope:**
- Template-aware spec_service that generates SPEC with template context
- Template-aware plan_artifact_service that generates PLAN with template phases
- Integrate with existing slash commands (`/fm.specify` with template context)

#### FM-119 — Local Mode Support for Templates & Phase Profiles

**Goal:** Extend ForgeMind Local to support template-based project creation and phase profile awareness.

**Planned scope:**
- Template import/export in local handoff bundles
- Phase profile export for offline use
- CLI commands for template-based local project creation

#### FM-120 — Project Intelligence Bootstrapping Hardening

**Goal:** Test coverage and hardening for FM-111–119.

**Planned scope:**
- Comprehensive tests for phase profiles, templates, constitution suggestions
- E2E tests for template-based project creation flow
- Documentation and response files

---

## Wave 8 — Execution Memory, Checkpoints, and Delivery Artifacts (FM-121–FM-130)

### Overview

Wave 8 adds **checkpoint-based execution control** and **delivery artifact synthesis** — enabling mid-run snapshots, replay-aware rollback, auto-generated changelogs, and traceability from SPEC through PLAN to implementation artifacts.

### Status Tracker

| FM     | Title                                          | Status       |
| ------ | ---------------------------------------------- | ------------ |
| FM-121 | Checkpoint Task Type and Run Integration       | 🔲 Planned  |
| FM-122 | Replay-Aware Checkpoint Rollback               | 🔲 Planned  |
| FM-123 | Adaptive Checkpoint Injection Logic            | 🔲 Planned  |
| FM-124 | Mid-Run Branch / WIP Snapshot Support          | 🔲 Planned  |
| FM-125 | Auto-Generated CHANGELOG Artifacts             | 🔲 Planned  |
| FM-126 | Run Completion Narrative and Release Notes     | 🔲 Planned  |
| FM-127 | Implementation Artifact Bundle Synthesis       | 🔲 Planned  |
| FM-128 | Spec/Plan/Implementation Traceability Graph    | 🔲 Planned  |
| FM-129 | Architecture-Aware Release Risk Summary        | 🔲 Planned  |
| FM-130 | Delivery Artifact Hardening                    | 🔲 Planned  |

### Milestone 25 — Execution Memory, Checkpoints & Delivery (FM-121 to FM-130)

#### FM-121 — Checkpoint Task Type and Run Integration

**Goal:** Introduce checkpoint tasks that capture execution state at defined points during a run.

**Planned scope:**
- `TaskType.CHECKPOINT` enum value
- Checkpoint task creation with state snapshot (completed tasks, artifacts, events)
- Integration with run timeline for checkpoint visibility

#### FM-122 — Replay-Aware Checkpoint Rollback

**Goal:** Enable rolling back a run to a previous checkpoint state for replay.

**Planned scope:**
- Checkpoint selection UI
- State restoration to checkpoint (task statuses, artifact visibility)
- Integration with existing replay service (FM-046)

#### FM-123 — Adaptive Checkpoint Injection Logic

**Goal:** Automatically inject checkpoint tasks at strategic points in execution plans.

**Planned scope:**
- Heuristic rules: after each phase, before destructive operations, after approval gates
- Configurable checkpoint frequency via project settings
- Integration with plan_artifact_service

#### FM-124 — Mid-Run Branch / WIP Snapshot Support

**Goal:** Allow creating work-in-progress snapshots during active runs for safe experimentation.

**Planned scope:**
- WIP snapshot creation from active run state
- Branch/fork run from snapshot
- Merge or discard WIP branches

#### FM-125 — Auto-Generated CHANGELOG Artifacts

**Goal:** Automatically generate CHANGELOG entries from completed run artifacts and events.

**Planned scope:**
- `ArtifactType.CHANGELOG` type
- Aggregate task completions, artifact creations, and key events into structured changelog
- Markdown and JSON export

#### FM-126 — Run Completion Narrative and Release Notes

**Goal:** Generate human-readable release notes from a completed run's full history.

**Planned scope:**
- LLM-powered narrative generation from run timeline, artifacts, and events
- Customizable tone and detail level via constitution settings
- Export as markdown artifact

#### FM-127 — Implementation Artifact Bundle Synthesis

**Goal:** Package all implementation artifacts from a run into a coherent delivery bundle.

**Planned scope:**
- Bundle creation service collecting code, tests, docs, patches from a run
- Dependency ordering and conflict detection between artifacts
- Export as zip or structured directory

#### FM-128 — Spec/Plan/Implementation Traceability Graph

**Goal:** Build a traceability graph linking SPEC requirements → PLAN phases → implementation artifacts.

**Planned scope:**
- Traceability link model (requirement_id → plan_section → artifact_id)
- Coverage visualization: which spec requirements have corresponding implementations
- Gap detection: unimplemented requirements, untracted artifacts

#### FM-129 — Architecture-Aware Release Risk Summary

**Goal:** Generate risk assessments for planned releases using architecture graph context.

**Planned scope:**
- Analyze implementation artifacts against architecture drift/violations
- Risk scoring: structural risk, dependency risk, untested risk
- Integration with ADR service for architecture-aware risk context

#### FM-130 — Delivery Artifact Hardening

**Goal:** Test coverage and hardening for FM-121–129.

**Planned scope:**
- Comprehensive tests for checkpoints, changelogs, traceability, risk summaries
- E2E tests for checkpoint-rollback-replay flow
- Documentation and response files

---

## Wave 9 — Connector Ecosystem, Extensions, and Enterprise Pluginability (FM-131–FM-140)

### Overview

Wave 9 transforms ForgeMind's hardcoded connector system into a **registry-based extension ecosystem** — enabling discovery, installation, marketplace UI, credential management, and community-contributed extension packs.

### Status Tracker

| FM     | Title                                          | Status       |
| ------ | ---------------------------------------------- | ------------ |
| FM-131 | Connector Registry Data Model                  | 🔲 Planned  |
| FM-132 | Registry-Backed Connector Discovery API        | 🔲 Planned  |
| FM-133 | Connector Install / Activation Workflow        | 🔲 Planned  |
| FM-134 | Connector Marketplace UI                       | 🔲 Planned  |
| FM-135 | Connector Capability and Credential Metadata   | 🔲 Planned  |
| FM-136 | Hardcoded Connector Migration to Registry Model | 🔲 Planned |
| FM-137 | Project/Workspace Extension Permissions        | 🔲 Planned  |
| FM-138 | Local Mode Connector Awareness                 | 🔲 Planned  |
| FM-139 | Community / Custom Extension Pack Framework    | 🔲 Planned  |
| FM-140 | Extension Ecosystem Hardening                  | 🔲 Planned  |

### Milestone 26 — Connector Ecosystem & Extensions (FM-131 to FM-140)

#### FM-131 — Connector Registry Data Model

**Goal:** Replace the current hardcoded connector list with a registry-backed data model.

**Planned scope:**
- `ConnectorDefinition` ORM model — name, type, version, capability_tags, config_schema
- `ConnectorInstance` ORM model — per-workspace/project connector installations
- Migration from existing `RepoConnection` / `ConnectorConfig` models

#### FM-132 — Registry-Backed Connector Discovery API

**Goal:** Provide an API for discovering available connectors from the registry.

**Planned scope:**
- `GET /connectors/registry` — list available connectors with filtering
- `GET /connectors/registry/{id}` — connector detail with config schema
- Search by type, capability, compatibility

#### FM-133 — Connector Install / Activation Workflow

**Goal:** Enable installing and activating connectors from the registry into a project or workspace.

**Planned scope:**
- Install endpoint: `POST /connectors/install`
- Activation/deactivation toggle
- Config validation against connector's config_schema
- Dependency resolution between connectors

#### FM-134 — Connector Marketplace UI

**Goal:** Frontend marketplace for browsing, installing, and managing connectors.

**Planned scope:**
- Marketplace browse page with category filtering
- Connector detail cards with capability descriptions
- Install/remove actions with confirmation
- Installed connectors management panel

#### FM-135 — Connector Capability and Credential Metadata

**Goal:** Formalize connector capabilities and credential requirements in the registry.

**Planned scope:**
- Capability schema: read, write, execute, notify, sync
- Credential requirement declarations per connector
- Integration with existing credential vault (FM-041–045)
- Validation that required credentials exist before activation

#### FM-136 — Hardcoded Connector Migration to Registry Model

**Goal:** Migrate existing built-in connectors (GitHub, GitLab, local repo) to the registry model.

**Planned scope:**
- Create registry entries for all existing connector types
- Backward-compatible migration path
- Preserve existing connector configurations

#### FM-137 — Project/Workspace Extension Permissions

**Goal:** RBAC controls for connector installation and usage at project and workspace levels.

**Planned scope:**
- Permission: `CONNECTOR_INSTALL`, `CONNECTOR_CONFIGURE`, `CONNECTOR_USE`
- Workspace-level connector allowlists
- Project-level connector overrides

#### FM-138 — Local Mode Connector Awareness

**Goal:** Extend ForgeMind Local to understand and interact with registry connectors.

**Planned scope:**
- Local connector config in `.forgemind/connectors.yaml`
- Offline connector capability checking
- Sync connector state in handoff bundles

#### FM-139 — Community / Custom Extension Pack Framework

**Goal:** Enable community-contributed extension packs that bundle connectors, templates, and phase profiles.

**Planned scope:**
- Extension pack manifest format
- Pack validation and safety scanning
- Import/export extension packs
- Community contribution guidelines

#### FM-140 — Extension Ecosystem Hardening

**Goal:** Test coverage and hardening for FM-131–139.

**Planned scope:**
- Comprehensive tests for registry, installation, marketplace, permissions
- E2E tests for connector lifecycle: discover → install → configure → activate → use → remove
- Documentation and response files

---

## Roadmap Summary

| Wave | Milestones | Tasks        | Theme                                              | Status       |
| ---- | ---------- | ------------ | -------------------------------------------------- | ------------ |
| 1    | 1–9        | FM-001–045   | Platform foundation through pre-release             | ✅ Complete  |
| 2    | 10–13      | FM-046–070   | Intelligence, collaboration, code ops               | ✅ Complete  |
| 3    | 14–20      | FM-071–080   | Frontend parity, RBAC, CI/CD, observability         | ✅ Complete  |
| 4    | 21         | FM-081–090   | Architecture intelligence                           | ✅ Complete  |
| 5    | 22         | FM-091–100   | Developer workstation (ForgeMind Local)             | ✅ Complete  |
| 6    | 23         | FM-101–110   | SPEC-driven lifecycle                               | ✅ Complete  |
| 7    | 24         | FM-111–120   | Phase routing, templates, project bootstrapping     | 🔲 Planned  |
| 8    | 25         | FM-121–130   | Execution memory, checkpoints, delivery artifacts   | 🔲 Planned  |
| 9    | 26         | FM-131–140   | Connector ecosystem, extensions, enterprise plugins | 🔲 Planned  |
