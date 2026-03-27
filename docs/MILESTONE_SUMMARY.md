# ForgeMind — Milestone Summary

> Last updated: 2026-03-26 (after FM-045 + pre-release infrastructure completion)

---

## Current State

**ForgeMind is an operator-centered AI execution platform with adaptive multi-agent orchestration, governance, cost tracking, and trust scoring.**

It can plan software projects, execute tasks via specialized agents with capability-based composition, surface execution artifacts, require human approval for critical steps, and adapt execution based on failures and feedback. The system has an execution memory layer for rich contextual reasoning, auto-retry with agent re-routing, connector-aware orchestration, credential vault management, configurable governance policies, LLM cost tracking, audit export, and heuristic trust/risk scoring.

---

## What ForgeMind Can Do Now

### Platform Foundation

- Monorepo structure (`apps/api`, `apps/web`, `docs`)
- FastAPI backend + Next.js 15 frontend
- Docker Compose local stack (PostgreSQL 16, Redis 7, MinIO)
- SQLAlchemy 2.0 async + Alembic migrations

### Backend Core

- Project / Run / Task / PlannerResult models
- Project CRUD API
- Prompt intake → structured planner flow
- Task dependency graph (linear chains)
- Ready-task resolution logic
- Planner result persistence (JSON columns)

### Frontend Core

- Dashboard shell with sidebar navigation
- Project list + project creation
- Prompt intake UI (textarea + optional project name)
- Task display with 7-status color badges
- Project detail page with breadcrumb nav
- Planner artifact rendering (overview, architecture, stack, assumptions, next steps)

### AI Planning Capability

- LiteLLM integration (supports OpenAI, Anthropic, Google, etc.)
- Prompt → structured JSON plan generation
- Architecture summary + tech stack recommendation
- Assumptions + next steps generation
- **Normalized/sanitized planner output** (FM-020A)
- **Fallback-safe planner behavior** (stub plan when no LLM configured)
- **Multi-layer defense** against malformed LLM output

### Execution & Agent System

- Background worker loop with configurable polling
- 5 fixed agents: planner, architect, coder, reviewer, tester
- Task claiming, completion, and failure tracking
- Execution artifacts (architecture docs, implementations, reviews, test reports)
- Agent registry with capability-based task routing

### Human-in-the-Loop & Observability

- **Approval request model** — auto-created for architecture/review tasks (FM-026)
- **Execution event log** — full timeline of task/artifact/approval events (FM-027)
- **Run detail page** — unified view of tasks, artifacts, approvals, events (FM-028)
- **Approval inbox** — filter/decide pending approvals with comments (FM-029)
- **Dashboard integration** — pending approval stats, quick navigation (FM-030)
- **Active sidebar navigation** with pathname-based highlighting

### Operator Control & Interaction

- **Artifact detail view** — dedicated page with breadcrumb, metadata cards, content rendering, cross-links to project/run/task (FM-031)
- **Execution control actions** — retry failed tasks (→READY) and cancel running/ready tasks (→SKIPPED) with event logging (FM-032)
- **Execution chatbot** — AI-powered Q&A about any run (context assembly from tasks/artifacts/approvals/events, LLM summarization with stub fallback) (FM-033)
- **Planner-to-execution handoff** — enriched planner output with agent_hint and requires_approval flags, 7 task types with agent mapping (FM-034)
- **Operator UX polish** — clickable dashboard stat cards, consistent breadcrumbs on all pages, section count labels, sidebar active-state fix for child routes, cross-links on project detail page (FM-035)

### Adaptive Multi-Agent Foundations

- **Dynamic agent composition** — capability taxonomy (8 groups, 25+ skills), scoring-based agent selection, team composition analysis, resolve_agent_for_task with hint priority and fallback (FM-036)
- **Agent handoff & collaboration** — upstream artifact context injection, build_handoff_context queries completed upstream tasks and artifacts, all 4 agents receive prior work context in system prompts (FM-037)
- **Connector intelligence** — connector registry model (7 default connectors), keyword-based recommendation engine, project stack → connector requirement mapping, REST API for listing and run-scoped recommendations (FM-038)
- **Execution memory & context** — unified run_memory_service with cached summaries (tasks/artifacts/approvals/events), failure analysis with blocking detection and suggested actions, chat service refactored to use memory layer, REST API for summaries/failures/context (FM-039)
- **Adaptive execution loop** — adaptive_orchestrator with smarter task selection (critical-path priority), auto-retry with agent re-routing (max 2 retries), approval rejection handling (auto-requeue for rework), worker loop integrated with adaptive cycle (FM-040)

---

## Completed Milestones

| Milestone                                    | Tasks                       | Focus                                                                   |
| -------------------------------------------- | --------------------------- | ----------------------------------------------------------------------- |
| **1 — Platform Foundation**                  | FM-001 to FM-005            | Monorepo, FastAPI, Next.js, Docker, DB setup                            |
| **2 — Backend Core**                         | FM-006 to FM-011 (+FM-010A) | Models, migrations, CRUD, task DAG, orchestration                       |
| **3 — Frontend MVP**                         | FM-012 to FM-015A           | Dashboard, forms, task display, validation                              |
| **4 — AI Planning Intelligence**             | FM-016 to FM-020A           | Detail page, planner persistence, LiteLLM, real planning, quality gate  |
| **5 — Execution Foundations**                | FM-021 to FM-025            | Artifacts, agent registry, execution service, worker, fixed agents      |
| **6 — Controlled Execution & Observability** | FM-026 to FM-030            | Approval workflow, event log, run view, approval inbox, UX polish       |
| **7 — Operator Control & Interaction**       | FM-031 to FM-035            | Artifact detail, retry/cancel, chatbot, handoff refinement, UX polish   |
| **8 — Adaptive Multi-Agent Foundations**     | FM-036 to FM-040            | Composition, handoff, connectors, execution memory, adaptive loop       |
| **9 — Connector & Retry Intelligence**       | FM-041 to FM-045            | Connector readiness, credential vault, retry v2, chatbot v2, eval suite |
| **Pre-release Infrastructure**               | (5 features)                | Run lifecycle, cost tracking, governance, audit export, trust scoring   |

**Total tasks completed: 47** (FM-001 through FM-045 including FM-010A, FM-015A, FM-020A, plus 5 pre-release infrastructure features)

---

## Planner Maturity (post FM-020A)

> **Structurally robust enough to continue.**
> **Quality-calibrated enough for MVP planning.**
> **Still needs real provider/output evaluation in practice.**

The FM-020A quality gate fixed 10 issues (3 critical, 4 medium, 3 low) and added 3 technical debt items (TD-007, TD-008, TD-009).

---

## Execution Foundations (post FM-025)

ForgeMind can now:

1. Store execution artifacts (plan summaries, architecture docs, implementations, reviews, test reports)
2. Know which agents exist and what each handles (planner, architect, coder, reviewer, tester)
3. Claim, run, complete, or fail tasks with agent tracking
4. Run a background worker loop that auto-discovers and dispatches ready tasks
5. Execute tasks via 4 fixed agents that produce LLM-powered (or stub) artifacts

---

## Controlled Execution & Observability (post FM-030)

ForgeMind now adds:

1. **Approval workflow** — architecture and review tasks auto-create approval requests; humans approve/reject with comments
2. **Execution event log** — every task claim, completion, failure, artifact creation, and approval decision is recorded as a timestamped event
3. **Run detail page** — unified view showing tasks, artifacts, approvals, and event timeline for any run
4. **Approval inbox** — dedicated page with filter tabs (all/pending/resolved), inline approve/reject with comment fields
5. **Dashboard polish** — pending approval count in stats row, "View Approvals" quick action with badge
6. **Active navigation** — sidebar highlights current page using `usePathname()`

> **ForgeMind is now an auditable AI execution platform with human oversight.**

---

## Operator Control & Interaction (post FM-035)

ForgeMind now adds:

1. **Artifact detail view** — dedicated page for each artifact with breadcrumb navigation, metadata cards, content rendering, and cross-links to project/run/task
2. **Execution control actions** — operators can retry failed tasks (resets to READY) and cancel running/ready tasks (sets to SKIPPED), with event logging for audit
3. **Execution chatbot** — AI-powered run assistant that assembles context from tasks, artifacts, approvals, and events; answers operator questions via LLM with stub fallback
4. **Planner-to-execution handoff** — enriched task metadata with agent_hint (maps task_type → preferred agent slug) and requires_approval flags; 7 task types (planning, architecture, codegen, review, verification, testing, deployment)
5. **Operator UX polish** — clickable stat cards, consistent breadcrumbs on all pages, section count labels on run/project detail, sidebar active-state for nested routes, artifacts and approvals on project detail page, version bump to v0.3.0

> **ForgeMind is now an operator-centered AI execution platform with interactive control and a chat-powered assistant.**

---

## Connector & Retry Intelligence (post FM-045)

ForgeMind now adds:

1. **Connector readiness states (FM-041)** — ProjectConnectorLink model with 4 readiness states (MISSING, CONFIGURED, BLOCKED, READY); per-project connector tracking with priority levels and blocker reasons
2. **Credential vault abstraction (FM-042)** — CredentialVault model storing secret metadata via env-key references (no plaintext secrets in DB); status tracking (ACTIVE, EXPIRED, MISSING, REVOKED); scopes and expiry management
3. **Adaptive retry/revision loop v2 (FM-043)** — retry_count and max_retries columns on Task model; adaptive_retry_service with delay calculation and agent re-routing; retry policy API
4. **Execution chatbot v2 (FM-044)** — topic detection (connector, retry, next-step awareness); enhanced context builders for connector status and retry history; multi-topic support in chat responses
5. **Execution quality eval suite (FM-045)** — 23 benchmark evaluations across 4 categories (planner output quality, task orchestration correctness, agent assignment accuracy, schema validation); eval_benchmarks.json with test data

> **ForgeMind now has intelligent connector management, secure credential handling, and a quality evaluation framework.**

---

## Pre-release Infrastructure

Features built as foundational infrastructure before the updated FM-046–FM-050 scope was defined:

1. **Run Lifecycle Manager** — health checks (HEALTHY, DEGRADED, STUCK, CRITICAL), auto-complete when all tasks terminal, auto-fail on unrecoverable failures, bulk run health scanning; `/lifecycle` API endpoints
2. **Cost & Token Tracking** — per-call LLM cost recording with model-specific rates, run/project cost summaries, model breakdown aggregation; CostRecord model; `/costs` API endpoints
3. **Governance Policy Engine** — configurable approval policies replacing hardcoded gates; 5 trigger types (TASK_TYPE, COST_THRESHOLD, ARTIFACT_TYPE, AGENT_ACTION, CUSTOM); 4 action types (REQUIRE_APPROVAL, AUTO_APPROVE, BLOCK, NOTIFY); GovernancePolicy model; `/governance` API endpoints
4. **Audit Trail Export** — JSON and CSV event export with compliance metadata; configurable filters (project, run, event_type, date range); audit summary with event type breakdown; `/audit` API endpoints
5. **Trust Scoring & Risk Assessment** — heuristic trust/risk scoring for tasks and runs; weighted factor analysis (status, retry burden, agent assignment, errors); 4 risk levels (LOW, MEDIUM, HIGH, CRITICAL); TrustScore model; `/trust` API endpoints

**Database additions:** 3 new migrations (0012–0014), 3 new models (CostRecord, GovernancePolicy, TrustScore)
**Test additions:** 46 new tests in `test_fm046_050.py`
**Total test suite: 174 tests (all passing)**

> **ForgeMind now has production-grade observability with cost tracking, governance, compliance auditing, and risk assessment.**

---

## Next Up: FM-046 to FM-050 (Active Roadmap)

| ID      | Feature                                          | Status      |
| ------- | ------------------------------------------------ | ----------- |
| FM-046  | Run Replay and Execution Trace Inspection        | Not started |
| FM-047A | Multi-Agent Council Decision Engine              | Not started |
| FM-047  | Policy-Based Approval Rules                      | Not started |
| FM-048  | Multi-Run Memory and Project Knowledge Base      | Not started |
| FM-049  | External Repo / Workspace Execution Integration  | Not started |
| FM-050  | Production Readiness and Platform Hardening Pass | Not started |

---

## Technical Debt (active)

See [docs/TECHNICAL_DEBT.md](TECHNICAL_DEBT.md) for full details (18 items). Key new items:

- **TD-013**: Approval required only for fixed task types (no policy engine)
- **TD-014**: No real-time event streaming (polling only)
- **TD-015**: Approval decision has no authorization check
- **TD-016**: Retry/cancel event types reuse existing enum values
- **TD-017**: Chat service has no conversation memory
- **TD-018**: Agent hint from planner not validated against registered agents
