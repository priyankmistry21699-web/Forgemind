# ForgeMind Task Board

## Backlog

- (none)

## In Progress

- (none)

## Done

### Milestone 1 — Platform Foundation (FM-001 to FM-005)

- FM-001 Initialize monorepo structure
- FM-002 Create FastAPI app skeleton
- FM-003 Create Next.js app shell
- FM-004 Add Docker Compose with Postgres and Redis
- FM-005 SQLAlchemy base/session config

### Milestone 2 — Backend Core (FM-006 to FM-011)

- FM-006 Alembic migration setup
- FM-007 Core domain models (users/projects/runs/tasks)
- FM-008 Project CRUD API
- FM-009 Prompt intake + planner stub flow
- FM-010 Task DAG service + orchestration foundations
- FM-010A Task service + orchestration fixes
- FM-011 Add task CRUD API

### Milestone 3 — Frontend MVP (FM-012 to FM-015A)

- FM-012 Add basic dashboard UI
- FM-013 Add prompt intake page
- FM-014 Add simple planner service stub
- FM-015 MVP polish + frontend validation pass
- FM-015A Frontend validation fixes

### Milestone 4 — AI Planning Intelligence (FM-016 to FM-020A)

- FM-016 Project detail page
- FM-017 Planner result persistence model + API
- FM-018 Frontend planner result view
- FM-019 LiteLLM integration
- FM-020 Real planner generation
- FM-020A Planner quality + robustness gate _(9.5/10)_

### Milestone 5 — Execution Foundations (FM-021 to FM-025)

- FM-021 Execution artifact model and persistence
- FM-022 Agent registry and capability model
- FM-023 Execution service for task claiming and completion
- FM-024 Worker/orchestrator foundation
- FM-025 First fixed execution agents (architect, coder, reviewer, tester)

### Milestone 6 — Controlled Execution & Observability (FM-026 to FM-030)

- FM-026 Approval request model and workflow
- FM-027 Run timeline / execution event log
- FM-028 Frontend execution run view
- FM-029 Frontend approval inbox and decision flow
- FM-030 End-to-end execution UX polish

### Milestone 7 — Operator Control & Interaction (FM-031 to FM-035)

- FM-031 Artifact detail view and navigation
- FM-032 Execution control actions (retry / cancel)
- FM-033 Execution chatbot foundation
- FM-034 Planner-to-execution handoff refinement
- FM-035 End-to-end operator UX polish

### Milestone 8 — Adaptive Multi-Agent Foundations (FM-036 to FM-040)

- FM-036 Dynamic agent composition foundations
- FM-037 Agent handoff and collaboration model
- FM-038 Connector intelligence foundation
- FM-039 Execution memory and contextual reasoning
- FM-040 Adaptive execution loop v1

### Milestone 9 — Connector & Retry Intelligence (FM-041 to FM-045)

- FM-041 Connector readiness states (ProjectConnectorLink model, 4 readiness states)
- FM-042 Credential vault abstraction (CredentialVault model, env-key secrets)
- FM-043 Adaptive retry / revision loop v2 (retry_count/max_retries on Task)
- FM-044 Execution chatbot v2 (topic detection, connector/retry awareness)
- FM-045 Execution quality eval suite (23 benchmark evals)

### Pre-release Infrastructure

- Run lifecycle manager (health checks, auto-complete, auto-fail, stuck detection)
- Cost & token tracking (CostRecord model, per-call usage, model breakdown)
- Governance policy engine (GovernancePolicy model, configurable approval rules)
- Audit trail export (JSON/CSV export with compliance metadata)
- Trust scoring & risk assessment (TrustScore model, heuristic scoring)

### Milestone 10 — Platform Intelligence & Hardening (FM-046 to FM-050)

- FM-046 Run Replay and Execution Trace Inspection (ReplaySnapshot model, SHA-256 hashing, replay comparison)
- FM-047A Multi-Agent Council Decision Engine (CouncilSession/CouncilVote models, 4 decision methods)
- FM-047 Policy-Based Approval Rules (GovernancePolicy model, multi-trigger evaluation)
- FM-048 Multi-Run Memory and Project Knowledge Base (ProjectKnowledge model, auto-extraction, context injection)
- FM-049 External Repo / Workspace Execution Integration (RepoConnection model, GitHub/GitLab/Bitbucket/local)
- FM-050 Production Readiness and Platform Hardening Pass (JWT auth, rate limiting, request logging, error handlers)

### Milestone 11 — Team Collaboration & Real-Time (FM-051 to FM-059)

- FM-051 Workspace model and multi-tenant shell
- FM-052 Workspace member roles (5 roles: owner, admin, manager, member, viewer)
- FM-053 Project-level member and permissions
- FM-054 SSE streaming foundation (asyncio.Queue pub/sub, run-scoped + global streams)
- FM-055 In-app notification engine (12 types, 4 priorities, read/unread tracking)
- FM-056 Notification delivery config (webhook/slack/email channels)
- FM-057 Escalation rule engine (6 triggers, 5 actions, cooldown support)
- FM-058 Activity feed and audit extension (15 activity types, project/workspace filtering)
- FM-059 User presence tracking (heartbeat, assignment context, last-seen)

### Milestone 12 — Collaboration Hardening & Code Foundations (FM-060 to FM-069)

- FM-060 Collaboration hardening pass (presence heartbeat, notification batching, escalation dedup, pagination)
- FM-061 Code mapping model (file-to-artifact mapping with language metadata)
- FM-062 Patch proposal model (structured diff proposals with line-level targeting)
- FM-063 Change review workflow (annotation-based code review with resolution tracking)
- FM-064 Branch strategy configuration (per-project branch naming and protection rules)
- FM-065 PR draft composer (auto-generated PR descriptions from patches)
- FM-066 Repo action approval gate (5 action types: push/merge/pr_create/branch_create/patch_apply)
- FM-067 Sandbox execution engine (async subprocess runner with timeout, stdout/stderr capture)
- FM-068 Code ops REST API (8 route groups, 30+ endpoints)
- FM-069 Code ops integration tests (47 tests across test_code_ops.py + test_code_ops_enhanced.py)

### Milestone 13 — Code Ops Enhancements (FM-070 + FM-061–069 enhanced)

- FM-061 enhanced: Sync status tracking (repo connection health, last-sync timestamps, provider metadata)
- FM-062 enhanced: Branch mode configuration (direct/feature_branch/review_branch)
- FM-063 enhanced: Annotation-based reviews (inline file/line/suggestion annotations)
- FM-064 enhanced: Enhanced patch proposals (target_files, readiness_state, patch_format, proposed_by_agent)
- FM-065 enhanced: PR generation metadata (auto-title, body sections, checklist generation)
- FM-066 enhanced: Approval gate check endpoint (auto-query most recent approval per action type)
- FM-067 enhanced: Sandbox runner safety (command allowlist, dangerous pattern detection, 300s max timeout)
- FM-068 enhanced: Enhanced API layer (file explorer, sync refresh, auto-generate, auto-check endpoints)
- FM-069 enhanced: Extended test coverage (303 total tests, migration verification, enum validation)
- FM-070 Database migration (0020 workspace FK + 0021 code ops enhancements, 5 new enum types)

### Milestone 14 — Advanced Frontend Parity I (FM-071)

- FM-071 Frontend pages for Trust, Replay, Council, Governance (4 dashboard pages, 4 lib clients, 4 type files, sidebar update)

### Milestone 15 — Advanced Frontend Parity II (FM-072)

- FM-072 Frontend pages for Costs, Audit, Knowledge, Credential Vault (4 dashboard pages, 4 lib clients, 4 type files, sidebar update)

### Milestone 16 — Platform Admin Frontend Parity (FM-073)

- FM-073 Frontend pages for Connectors, Agents, Settings (3 dashboard pages, 2 lib clients, 2 type files, sidebar links enabled)

### Milestone 17 — Auth & RBAC Hardening (FM-074 to FM-075)

- ✅ FM-074 Real authentication integration (replace stub auth, real login flow, token verification)
- ✅ FM-075 Route-level RBAC enforcement hardening (auth on all 164 non-public endpoints, permission matrix, RBAC checks)

### Milestone 18 — CI/CD & Automation (FM-076)

- ✅ FM-076 CI/CD pipeline and quality gates (GitHub Actions: lint, test, typecheck, build)

### Milestone 19 — Real-Time & Observability (FM-077 to FM-078)

- ✅ FM-077 Real-time UX integration (SSE consumption, live updates, reconnect handling)
- ✅ FM-078 Observability and runtime instrumentation (metrics endpoint, tracing, request IDs)

### Milestone 20 — Platform Maturity (FM-079 to FM-080)

- ✅ FM-079 Monorepo package extraction (4 real packages: @forgemind/types, forgemind-utils, forgemind-security, forgemind-core)
- ✅ FM-080 Production deployment foundation (prod Dockerfiles, prod compose, nginx, deployment README, env docs)

### Milestone 21 — Architecture Intelligence (FM-081 to FM-090)

- ✅ FM-081 Architecture graph foundation (ArchitectureNode/Edge/Snapshot models, CRUD service + 12 endpoints, migration 0022)
- ✅ FM-082 Topology mapping service (filesystem scanner, Python/TS import parsing, layer classification, topology summary)
- ✅ FM-083 Drift detection engine (snapshot comparison, convention drift, drift resolve/ignore, 4 endpoints)
- ✅ FM-084 Architecture rule engine (5 rule categories, evaluators, rule results, 4 endpoints)
- ✅ FM-085 Architecture dashboard frontend (page, 12-function API client, TypeScript types, sidebar nav link)
- ✅ FM-086 Design doc synthesis (Markdown generation from graph/drift/rules, 1 endpoint)
- ✅ FM-087 Change impact analysis (BFS reverse traversal, blast radius, severity scoring, ChangeImpactAssessment model)
- ✅ FM-088 Refactor recommendations (god-module, circular dep, isolated node, drift/violation backlog detection)
- ✅ FM-089 Architecture approval workflow (auto-approval for HIGH/CRITICAL impacts, architecture approval listing)
- ✅ FM-090 Structural health score (composite 0–100 score, coverage/drift/compliance/isolation breakdown)

### Milestone 22 — ForgeMind Local: Developer Workstation Mode (FM-091 to FM-100)

- ✅ FM-091 Local foundation & config (LocalConfig dataclass, YAML I/O, detect_repo_root, ensure_directories, CLI init/status)
- ✅ FM-092 Repo indexing & manifest (file tree walk, 30+ language extensions, entrypoint/build-file detection, cached JSON manifest)
- ✅ FM-093 Local chat over codebase (keyword search, file snippet reading, optional LiteLLM, offline rule-based fallback)
- ✅ FM-094 Local execution sandbox (16 blocked patterns, 35 safe prefixes, 3 policies, subprocess timeout, JSON run logging)
- ✅ FM-095 Patch generation & management (git diff patches, metadata tracking, apply with --check, reject workflow)
- ✅ FM-096 PR preparation (git diff analysis, 11 subsystem categories, risk detection, dynamic checklist, markdown output)
- ✅ FM-097 IDE integration (VS Code tasks.json generation, 10 tasks + 2 input prompts, idempotent merge)
- ✅ FM-098 State management & sync queue (TTL cache, offline event queue, mode management: offline/hybrid/remote)
- ✅ FM-099 Handoff snapshots (export/import zip bundles, non-destructive import, bundle inspection)
- ✅ FM-100 Hardening, tests & documentation (53 tests, 9 test classes, response files, tracking doc updates)

### Milestone 23 — SPEC-Driven Lifecycle (FM-101 to FM-110)

- ✅ FM-101 SPEC artifact type + SPECIFYING status + lifecycle gating (ArtifactType.SPEC/PLAN, RunStatus.SPECIFYING, spec_artifact_id FK, transition validation gates)
- ✅ FM-102 Project constitution model (ProjectConstitution ORM, schemas, service with upsert/delete, REST routes, prompt injection into spec/plan/chat)
- ✅ FM-103 Constitution UI & governance hooks (ConstitutionEditor component, API client, TypeScript types, CONSTITUTION_UPDATED events, mounted on project detail page)
- ✅ FM-104 Slash command parsing (/fm.specify, /fm.plan, /fm.tasks, /fm.implement — regex parser, execute routing, chat integration, frontend suggestions)
- ✅ FM-105 Structured SPEC generation (LLM-powered with constitution context, stub fallback, SPEC_CREATED event, auto-transition PENDING→SPECIFYING)
- ✅ FM-106 PLAN artifact export & linking (PLAN→SPEC FK linkage, markdown export, JSON export endpoints, auto-transition SPECIFYING→PLANNING)
- ✅ FM-107 ADR-aware planning (architecture graph queries, ADR-001/002/003 sections, plan enrichment, prompt context injection)
- ✅ FM-108 Spec-to-plan validation (8 rules: 4 ERROR + 4 WARNING, lifecycle gate PLANNING→RUNNING, REST endpoint, SpecPlanValidationResult)
- ✅ FM-109 Approval integration (SPEC/PLAN approval requests, idempotent, opt-in gating, lifecycle gate enforcement)
- ✅ FM-110 Tests & hardening (60 tests, 12 test classes, 542 total passing, docs/tracking closure)

### Milestone 24 — Phase Routing, Templates & Project Bootstrapping (FM-111 to FM-120)

- ✅ FM-111 Phase agent profile data model (PhaseAgentProfile ORM, WorkflowPhase enum, CRUD service, schemas, routes, unique project/phase constraint)
- ✅ FM-112 Composition engine phase-aware routing (resolve_agent_for_phase in composition_service, wired into worker task loop + adaptive orchestrator auto-retry)
- ✅ FM-113 Phase agent profile UI (PhaseProfileEditor component, per-phase agent dropdowns, mounted on project detail page, API client)
- ✅ FM-114 Project template model and seeding (ProjectTemplate ORM, 4 built-in templates with real constitutions/governance/spec/plan defaults, idempotent seeding)
- ✅ FM-115 Template-based project creation flow (project_service accepts template_id, seeds constitution + phase profiles, frontend template selector)
- ✅ FM-116 Template inheritance for constitution & policies (3-tier resolution: system → template → project, resolve_governance_config)
- ✅ FM-117 Knowledge-driven constitution suggestions (ConstitutionSuggestion ORM, 5 signal-driven rules, generate/accept/reject, never auto-applied)
- ✅ FM-118 Spec/plan bootstrap from project templates (template spec_defaults/plan_defaults injected into LLM prompts as guidance sections)
- ✅ FM-119 Local mode support for templates & phase profiles (CLI status display, exec context logging, handoff bundle metadata)
- ✅ FM-120 Hardening, tests & documentation (38 tests, 580 total passing, full doc closure)

### Milestone 25 — Execution Memory, Checkpoints & Delivery (FM-121 to FM-130)

- ✅ FM-121 Execution checkpoint model & CRUD (ExecutionCheckpoint ORM, CheckpointType enum, schemas, service, REST router, Alembic migration 0024)
- ✅ FM-122 Auto-checkpoint on phase transitions (AUTO_PHASE on transition_run, PRE_APPROVAL on complete_task, PRE_DELIVERY on try_auto_complete_run)
- ✅ FM-123 Resume-from-checkpoint with real restart (reset FAILED/BLOCKED tasks to READY, set run to RUNNING, emit resume event)
- ✅ FM-124 Mid-run branch / WIP snapshot support (manual checkpoint creation, sequence numbering, live state capture)
- ✅ FM-125 Auto-generated CHANGELOG artifacts (changelog_service, structured output from events/tasks/artifacts)
- ✅ FM-126 Run completion narrative and release notes (narrative_service, timeline/decisions/outcomes)
- ✅ FM-127 Implementation artifact bundle synthesis (bundle_service, collect specs/plans/code/patches into bundle)
- ✅ FM-128 Spec/plan/implementation traceability graph (traceability_service, directed graph, coverage analysis)
- ✅ FM-129 Architecture-aware release risk summary (release_risk_service, local CLI confidence/review/checkpoint save strengthened, handoff import checkpoint restore)
- ✅ FM-130 Delivery artifact hardening (delivery_hardening_service, quality gates, validation pipeline)

## Blocked

- (none)
