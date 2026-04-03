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

## Success Condition

By the end of FM-090, ForgeMind is a fully navigable, production-hardened AI execution platform with:

- Complete frontend parity across all backend subsystems
- Real authentication and enforced RBAC
- CI/CD and automated quality gates
- Runtime observability with metrics and tracing
- Shared monorepo packages with real code
- Production deployment foundation
- **Architecture intelligence** — graph-based structural analysis, drift detection, rule enforcement, impact analysis, refactor recommendations, and a composite structural health score

**All 90 tasks are complete. 482 tests passing.**
