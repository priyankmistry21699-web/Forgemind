# ForgeMind — Milestone Summary

> Last updated: 2026-04-15 (post-V4 pass 5 — 13 milestones advanced, 1052 tests passing)

---

## Current State

**ForgeMind is an operator-centered AI execution platform with adaptive multi-agent orchestration, governance, cost tracking, trust scoring, execution replay, council decision-making, cross-run knowledge, external repo integration, production hardening, team collaboration, real-time streaming, code operations, a repo-aware code-change-capable execution engine, full frontend parity, real authentication with RBAC enforcement, CI/CD pipeline, observability, production deployment foundation, shared monorepo packages, an architecture intelligence subsystem with graph-based structural analysis, topology mapping, drift detection, rule enforcement, design doc synthesis, change impact analysis, refactor recommendations, architecture approval workflow, and structural health scoring, and an execution memory layer with persistent checkpoints, auto-checkpointing, resume semantics, delivery artifact generation, review packages, lifecycle traceability graphs, run memory enrichment, and explainable release confidence scoring.**

It can plan software projects, execute tasks via specialized agents with capability-based composition, surface execution artifacts, require human approval for critical steps, and adapt execution based on failures and feedback. The system has an execution memory layer for rich contextual reasoning, auto-retry with agent re-routing, connector-aware orchestration, credential vault management, configurable governance policies, LLM cost tracking, audit export, heuristic trust/risk scoring, deterministic execution replay, multi-agent council decisions, project-level knowledge bases, external repository connections, production-grade security middleware, workspace-based multi-tenancy with RBAC memberships, notification engine with delivery configs, escalation rules, activity feeds with user presence, a full code operations pipeline (patch proposals, change reviews, branch strategies, PR drafts, repo action approvals, and sandbox execution), full frontend parity across all backend subsystems, real JWT authentication with RBAC enforcement, CI/CD with GitHub Actions, observability with metrics and tracing, shared monorepo packages, a production deployment foundation, and an architecture intelligence layer that models codebases as directed graphs, detects architectural drift, enforces rules, analyzes change impact, generates design docs and refactor recommendations, and computes structural health scores.

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

| Milestone                                    | Tasks                       | Focus                                                                                                                                                          |
| -------------------------------------------- | --------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **1 — Platform Foundation**                  | FM-001 to FM-005            | Monorepo, FastAPI, Next.js, Docker, DB setup                                                                                                                   |
| **2 — Backend Core**                         | FM-006 to FM-011 (+FM-010A) | Models, migrations, CRUD, task DAG, orchestration                                                                                                              |
| **3 — Frontend MVP**                         | FM-012 to FM-015A           | Dashboard, forms, task display, validation                                                                                                                     |
| **4 — AI Planning Intelligence**             | FM-016 to FM-020A           | Detail page, planner persistence, LiteLLM, real planning, quality gate                                                                                         |
| **5 — Execution Foundations**                | FM-021 to FM-025            | Artifacts, agent registry, execution service, worker, fixed agents                                                                                             |
| **6 — Controlled Execution & Observability** | FM-026 to FM-030            | Approval workflow, event log, run view, approval inbox, UX polish                                                                                              |
| **7 — Operator Control & Interaction**       | FM-031 to FM-035            | Artifact detail, retry/cancel, chatbot, handoff refinement, UX polish                                                                                          |
| **8 — Adaptive Multi-Agent Foundations**     | FM-036 to FM-040            | Composition, handoff, connectors, execution memory, adaptive loop                                                                                              |
| **9 — Connector & Retry Intelligence**       | FM-041 to FM-045            | Connector readiness, credential vault, retry v2, chatbot v2, eval suite                                                                                        |
| **Pre-release Infrastructure**               | (5 features)                | Run lifecycle, cost tracking, governance, audit export, trust scoring                                                                                          |
| **10 — Platform Intelligence & Hardening**   | FM-046 to FM-050            | Replay, council, knowledge, repos, production hardening                                                                                                        |
| **11 — Team Collaboration & Real-Time**      | FM-051 to FM-060            | Workspaces, RBAC, notifications, streaming, escalation, activity, hardening                                                                                    |
| **12 — Repository & Code Execution**         | FM-061 to FM-069            | Code mapping, patches, reviews, branches, PRs, sandbox execution                                                                                               |
| **13 — Code Ops Enhancements**               | FM-061 to FM-070 (enhanced) | Sync metadata, file explorer, artifact mapping, enhanced patches/reviews, branch strategy, PR draft gen, approval gates, sandbox runner, frontend pages        |
| **14 — Advanced Frontend Parity I**          | FM-071                      | Frontend pages for Trust, Replay, Council, Governance                                                                                                          |
| **15 — Advanced Frontend Parity II**         | FM-072                      | Frontend pages for Costs, Audit, Knowledge, Credential Vault                                                                                                   |
| **16 — Platform Admin Frontend Parity**      | FM-073                      | Frontend pages for Connectors, Agents, Settings                                                                                                                |
| **17 — Auth & RBAC Hardening**               | FM-074 to FM-075            | Real authentication, route-level RBAC enforcement                                                                                                              |
| **18 — CI/CD & Automation**                  | FM-076                      | GitHub Actions CI pipeline with lint, test, typecheck, build                                                                                                   |
| **19 — Real-Time & Observability**           | FM-077 to FM-078            | SSE consumption, live updates, metrics endpoint, tracing                                                                                                       |
| **20 — Platform Maturity**                   | FM-079 to FM-080            | Monorepo package extraction, production deployment foundation                                                                                                  |
| **21 — Architecture Intelligence**           | FM-081 to FM-090            | Architecture graph, topology mapping, drift detection, rule engine, dashboard, design docs, impact analysis, refactor recommendations, approvals, health score |

**Total tasks completed: 90** (FM-001 through FM-090 including FM-010A, FM-015A, FM-020A, plus 5 pre-release infrastructure features)

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

## Platform Intelligence & Hardening (post FM-050)

ForgeMind now adds:

1. **Run Replay & Execution Trace (FM-046)** — ReplaySnapshot model capturing every agent execution step with deterministic SHA-256 hashing; replay past executions and compare original vs. replay outputs side-by-side; full execution trace retrieval per run
2. **Multi-Agent Council Decision Engine (FM-047A)** — CouncilSession/CouncilVote models; 4 decision methods (consensus, majority, supermajority, weighted voting); automatic deadlock detection and human escalation; collaborative agent decision-making for complex architectural choices
3. **Policy-Based Approval Rules (FM-047)** — Enhanced governance with 5 policy trigger types (TASK_TYPE, COST_THRESHOLD, ARTIFACT_TYPE, AGENT_ACTION, CUSTOM); custom JSON rules engine with and/or logic and comparison operators; council integration via `evaluate_approval_with_council()`
4. **Multi-Run Memory & Project Knowledge Base (FM-048)** — ProjectKnowledge model with 7 knowledge types (pattern, decision, lesson_learned, dependency, best_practice, architecture, constraint); auto-extraction from completed/failed tasks and planner results; knowledge context injection into agent prompts for smarter cross-run decisions
5. **External Repo Integration (FM-049)** — RepoConnection model supporting GitHub, GitLab, Bitbucket, and local providers; health checking and sync operations per connection; multi-repo support per project
6. **Production Hardening (FM-050)** — JWT authentication via python-jose with dev-mode stub fallback; per-IP token bucket rate limiting (100 req/60s); request logging middleware with timing and unique X-Request-ID headers; global error handlers for consistent JSON error responses

**Database additions:** 4 new migrations (0015–0018), 5 new models (ReplaySnapshot, CouncilSession, CouncilVote, ProjectKnowledge, RepoConnection)
**Test additions:** 34 new tests in `test_fm046_050_v2.py`
**Total test suite: 185 tests (all passing)**

> **ForgeMind is now a complete, production-hardened AI execution platform with 50 features across 10 milestones.**

---

## Team Collaboration & Real-Time (post FM-060)

ForgeMind now adds:

1. **Workspace model & multi-tenant shell (FM-051)** — Workspace entity with name, slug (unique), description, status (active/suspended/archived), owner, settings JSON; full CRUD API
2. **Workspace member roles (FM-052)** — WorkspaceMember with 5 roles (owner/admin/operator/reviewer/viewer); unique constraint per workspace+user
3. **Project-level member & permissions (FM-053)** — ProjectMember with 4 roles (lead/operator/reviewer/viewer) + is_approver/is_reviewer flags; per-project RBAC
4. **SSE streaming foundation (FM-054)** — Server-Sent Events heartbeat endpoint at /stream/events for real-time update infrastructure
5. **In-app notification engine (FM-055)** — Notification model with 12 notification types, 4 priority levels (low/normal/high/urgent); mark individual or all notifications as read; unread count
6. **Notification delivery config (FM-056)** — Per-user delivery channel configuration (slack/email/webhook) with active/paused/disabled status management
7. **Escalation rule engine (FM-057)** — EscalationRule with 6 trigger types, 5 action types, cooldown_minutes, JSON rules; EscalationEvent logging for audit
8. **Activity feed & audit extension (FM-058)** — ActivityFeedEntry with 15 activity types, project/workspace scoping, actor tracking, resource linking, metadata JSON
9. **User presence tracking (FM-059)** — UserPresence with status, current resource type/id, last_seen_at; upsert semantics for efficient updates

**Database additions:** 1 new migration (0019), 9 new models (Workspace, WorkspaceMember, ProjectMember, Notification, NotificationDeliveryConfig, EscalationRule, EscalationEvent, ActivityFeedEntry, UserPresence)
**Test additions:** 50 new tests across 6 test files (workspaces, members, streaming, notifications, escalation, activity)
**Total test suite: 252 tests (all passing)**

> **ForgeMind now has workspace-based multi-tenancy, real-time streaming, notifications, escalation, and activity tracking.**

---

## FM-060 Collaboration Phase Hardening

The FM-060 hardening pass adds structural depth and integration to the basic CRUD built in FM-051–059:

### Backend Structural Enhancements

1. **workspace_id on Project (FM-051)** — Added nullable FK `workspace_id` to the Project model with `SET NULL` on delete; migration 0020 adds the column and index
2. **Authorization service (FM-052)** — `authz_service.py` with Action enum (15 actions), permission matrices for workspace (8 actions) and project (7 actions), check functions that raise 403/404
3. **Workspace membership validation (FM-053)** — `add_project_member()` now validates workspace membership before allowing project assignment
4. **Run-scoped SSE streaming (FM-054)** — `stream_service.py` with in-memory asyncio.Queue-based pub/sub; `GET /runs/{run_id}/stream` endpoint for per-run SSE; global subscriber support
5. **Cross-service notification hooks (FM-055)** — Approval and event services now auto-create notifications on approval_created, approval_resolved, and all emitted events
6. **Multi-channel delivery service (FM-056)** — `notification_delivery_service.py` with webhook (httpx), Slack (incoming webhook), and email (stub) delivery channels
7. **Escalation integration (FM-057)** — `run_lifecycle_service.py` now triggers escalation for STUCK/CRITICAL runs during health scans
8. **Workspace activity endpoint (FM-058)** — `GET /workspaces/{workspace_id}/activity` for workspace-scoped activity feeds
9. **User activity service (FM-059)** — `user_activity_service.py` with presence tracking, active user queries, and assignment context; `GET /users/{user_id}/context` endpoint

### Frontend

10. **Type definitions** — workspace.ts, notification.ts, activity.ts, escalation.ts, project-member.ts
11. **API clients** — workspaces.ts, notifications.ts, escalations.ts, activity.ts, project-members.ts, stream.ts (SSE)
12. **Dashboard pages** — Workspaces, Notifications, Activity Feed, Escalations pages
13. **Components** — ProjectMembersPanel reusable component
14. **Navigation** — Sidebar updated with Workspaces, Notifications, Activity, Escalations nav items; top-nav bell linked to /dashboard/notifications
15. **Project type** — workspace_id field added to Project interface

### Testing

16. **27 FM-060 hardening tests** in `test_collaboration_phase.py` covering:
    - Workspace-scoped projects (workspace_id field, creation with workspace)
    - Authorization permission matrices (workspace + project, role checks, 403/404)
    - Stream service pub/sub (subscribe, publish, global, run-scoped generator)
    - Notification delivery (no configs, email stub, webhook no-URL)
    - Workspace activity endpoint (empty, with entries)
    - User activity service (touch, update, assignment context, endpoint)
    - End-to-end integration flows (full workspace→project flow, notification lifecycle, escalation, presence, delivery config)

**Database additions:** Migration 0020 (workspace_id FK on projects)
**New services:** authz_service.py, notification_delivery_service.py, stream_service.py, user_activity_service.py
**Frontend additions:** 5 type files, 6 lib files, 4 pages, 1 component, sidebar + top-nav updates
**Test additions:** 27 new tests in test_collaboration_phase.py
**Total test suite: 279 tests (all passing)**

> **ForgeMind now has deep team collaboration with RBAC authorization, real-time streaming, cross-service hooks, and workspace-scoped operations.**

---

## Repository & Code Execution (post FM-069)

ForgeMind now adds:

1. **Code mapping model (FM-061)** — CodeMapping linking project artifacts to file paths with language detection and metadata JSON
2. **Patch proposal model (FM-062)** — PatchProposal with diff_content, target_branch, 6 statuses (draft/pending_review/approved/rejected/merged/abandoned), rationale tracking
3. **Change review workflow (FM-063)** — ChangeReview with 3 decisions (approved/changes_requested/commented) linked to patches; reviewer tracking with comments
4. **Branch strategy configuration (FM-064)** — BranchStrategy with base_branch, branch_pattern, pr_target_branch, auto_create_branch flag, config JSON per project
5. **PR draft composer (FM-065)** — PRDraft with 5 statuses (draft/ready/submitted/merged/closed), reviewers/checklist/linked_artifacts JSON, source/target branch tracking
6. **Repo action approval gate (FM-066)** — RepoActionApproval with 5 action types (push/merge/deploy/release/delete_branch), decision workflow with context tracking
7. **Sandbox execution engine (FM-067)** — SandboxExecution with command, environment JSON, timeout_seconds, 5 statuses (pending/running/completed/failed/timed_out), stdout/stderr/exit_code/duration_ms capture
8. **Code ops REST API (FM-068)** — Full REST endpoints for all 7 code operations models (~20 endpoints)
9. **Code ops integration tests (FM-069)** — Comprehensive test coverage for all code operations (17 tests)

**Database additions:** Migration 0019 (shared with Milestone 11), 7 new models (CodeMapping, PatchProposal, ChangeReview, BranchStrategy, PRDraft, RepoActionApproval, SandboxExecution)
**Test additions:** 17 new tests in test_code_ops.py
**Total test suite: 279 tests (all passing)**

> **ForgeMind now has a complete code operations pipeline from mapping to sandbox execution with 69 features across 12 milestones.**

---

## Code Ops Enhancements (FM-061–FM-070)

ForgeMind transforms from a collaborative AI operations platform into a **repo-aware, code-change-capable execution platform**:

### FM-061: Repo Sync Metadata

- SyncStatus enum (IDLE, SYNCING, SUCCESS, FAILED) + 10 new columns on RepoConnection
- `refresh_sync_metadata()` and `get_sync_status()` service methods
- `GET /repos/{id}/sync-status` and `POST /repos/{id}/refresh-sync` endpoints

### FM-062: File Tree Explorer

- `get_file_tree()` with directory browsing, `get_file_content()` with size limits (1MB), `get_file_metadata()`, `build_context_snippet()`
- Path traversal protection, MAX_TREE_ENTRIES (500), language detection via \_LANG_MAP
- `GET /repos/{id}/tree`, `GET /repos/{id}/file`, `GET /repos/{id}/file-meta` endpoints
- Frontend: Code Explorer page with split-panel tree browser and file viewer

### FM-063: Code Artifact Mapping

- ChangeType enum (CREATE, MODIFY, DELETE, CONCEPTUAL)
- 5 new columns on Artifact: repo_connection_id (FK), target_path, target_module, change_type, target_metadata

### FM-064: Patch Proposal Engine

- PatchFormat enum (UNIFIED, SIDE_BY_SIDE, RAW), ReadinessState enum (INCOMPLETE, NEEDS_REVIEW, READY, BLOCKED)
- 5 new columns on PatchProposal: target_files, patch_format, proposed_by_agent, readiness_state, linked_artifact_ids

### FM-065: Change Review Workspace

- 4 new columns on ChangeReview: file_path, line_start, line_end, suggestion
- Inline code annotation support for file-level review comments
- Frontend: Review workspace page with diff viewer, file annotations, and suggestion rendering

### FM-066: Branch Strategy Manager

- BranchMode enum (DIRECT, FEATURE_BRANCH, REVIEW_BRANCH)
- branch_mode, target_branch_template, last_generated_branch on RepoConnection

### FM-067: PR Draft Generation

- `generate_pr_draft()` service auto-builds PR title/body/checklist from patch proposals
- `POST /projects/{id}/pr-drafts/generate` endpoint with PRDraftGenerateRequest schema

### FM-068: Repo Action Approval Gates

- `check_approval_gate()` service queries latest approval status per action type
- `GET /projects/{id}/repo-approvals/check` endpoint

### FM-069: Code Execution Sandbox

- Command allowlist (python, pip, pytest, echo, cat, ls, etc.) with shell injection prevention
- `_validate_command()` blocks dangerous patterns (&&, ||, ;, |, `, $()
- `run_sandbox_execution()` with asyncio subprocess, timeout enforcement, output capture
- `POST /sandbox/run` endpoint with SandboxRunRequest schema
- Frontend: Sandbox page with command runner, execution list, and output viewer

### FM-070: Code Ops Consolidation

- Frontend pages: Code Explorer, Review Workspace, Sandbox Viewer
- Documentation updates: ARCHITECTURE.md, MILESTONE_SUMMARY.md, TECHNICAL_DEBT.md
- Handoff response documents for FM-061–FM-070
- Migration 0021 covering all schema enhancements

**Database additions:** Migration 0021 (+10 cols on repo_connections, +5 on artifacts, +5 on patch_proposals, +4 on change_reviews, +4 on sandbox_executions; 5 new enum types)
**Frontend additions:** 3 new dashboard pages (Code Explorer, Review Workspace, Sandbox)
**Test additions:** 24 new tests in test_code_ops_enhanced.py
**Total test suite: 303 tests (all passing)**

> **ForgeMind is now a repo-aware, code-change-capable AI execution platform with 70 features across 13 milestones.**

---

## Productization & Frontend Parity (post FM-073)

ForgeMind now adds:

1. **Advanced Frontend Parity I (FM-071)** — Dashboard pages for Trust (risk level badges, factor display), Replay (snapshot list, trace explorer, comparison view), Council (session list, vote breakdown, decision method display), and Governance (policy list, trigger/action filtering, enable/disable toggle)
2. **Advanced Frontend Parity II (FM-072)** — Dashboard pages for Costs (run/project summaries, token breakdowns), Audit (summary view, JSON/CSV export, action filtering), Knowledge (project knowledge list, type filtering, relevance metadata), and Credential Vault (metadata-only display, connector binding, expiry/scope visibility)
3. **Platform Admin Frontend Parity (FM-073)** — Dashboard pages for Connectors (catalog, readiness states, project linkage), Agents (registry, capabilities, status), and Settings (user preferences, notification config); all sidebar links enabled

> **ForgeMind now has complete frontend parity — every backend subsystem is surfaced in the dashboard.**

---

## Auth & RBAC Hardening (post FM-075)

ForgeMind now adds:

1. **Real Authentication (FM-074)** — Production-grade JWT authentication replacing the dev stub; real login/logout flow; token verification against identity provider; user identity binding to backend user model; dev fallback only in explicit dev mode
2. **Route-Level RBAC (FM-075)** — Auth required on all 164 non-public endpoints; workspace/project membership checks; admin-only action protection; consistent 401/403/404 error semantics; permission matrix tests

> **ForgeMind now has production-grade authentication with enforced role-based access control.**

---

## CI/CD, Real-Time & Observability (post FM-078)

ForgeMind now adds:

1. **CI/CD Pipeline (FM-076)** — GitHub Actions workflow with Python lint (ruff), pytest, TypeScript typecheck, ESLint, and build verification; pushes and PRs trigger CI
2. **Real-Time UX (FM-077)** — Frontend SSE consumption for live run updates, notification streaming, activity feed, and escalation alerts; reconnect and heartbeat handling
3. **Observability (FM-078)** — Prometheus metrics endpoint, request latency/error counters, worker task execution metrics, sandbox telemetry, consistent request IDs

> **ForgeMind now has automated quality gates, live frontend updates, and runtime observability.**

---

## Platform Maturity (post FM-080)

ForgeMind now adds:

1. **Monorepo Packages (FM-079)** — 4 real shared packages: @forgemind/types, forgemind-utils, forgemind-security, forgemind-core; extracted from app code for cleaner imports and reduced duplication
2. **Production Deployment (FM-080)** — Multi-stage Docker builds, production Docker Compose with 6 services, nginx reverse proxy with TLS, deployment README, environment variable documentation, health endpoint guidance

**Total test suite: 413 tests (all passing)**

> **ForgeMind is now a production-deployable, CI-protected, observable AI execution platform with 80 features across 20 milestones.**

---

## Architecture Intelligence (post FM-090)

ForgeMind now adds:

1. **Architecture Graph Foundation (FM-081)** — ArchitectureNode (12 types), ArchitectureEdge (10 types), ArchitectureSnapshot models; full CRUD with graph queries, neighbor traversal; migration 0022 with 7 tables and 11 DB enum types
2. **Topology Mapping Service (FM-082)** — Filesystem scanner that infers nodes/edges from Python/TypeScript source; import parsing, layer classification (route/service/model/schema/middleware/utility/config/test/migration/component/page), topology summary
3. **Drift Detection Engine (FM-083)** — Compare current graph against snapshots or conventions; detect cross-layer imports, undocumented components, new/removed nodes; ArchitectureDrift model with severity (info/warning/error/critical) and resolve/ignore workflow
4. **Architecture Rule Engine (FM-084)** — Define rules across 5 categories (import/layer/dependency/ownership/boundary); evaluate against graph; ArchitectureRule and ArchitectureRuleResult models with pass/fail tracking
5. **Architecture Dashboard Frontend (FM-085)** — Full dashboard page at `/dashboard/architecture` with stat cards, drift summary, rule results, health score donut; 12-function API client; TypeScript types in packages/schemas; sidebar navigation link
6. **Design Doc Synthesis (FM-086)** — Generate Markdown architecture summary from graph data, drift records, and rule violations; node inventory, layer breakdown, edge statistics
7. **Change Impact Analysis (FM-087)** — BFS reverse traversal to compute blast radius; ChangeImpactAssessment model with severity escalation (≥10 deps → HIGH, ≥20 → CRITICAL); impacted nodes/services lists
8. **Refactor Recommendations (FM-088)** — Detect god-modules (high fan-in), circular dependencies, isolated nodes, drift backlogs, rule violation backlogs; actionable recommendation list with severity
9. **Architecture Approval Workflow (FM-089)** — Auto-create ApprovalRequest when impact severity is HIGH or CRITICAL; list architecture-related approvals; integrates with existing approval workflow
10. **Structural Health Score (FM-090)** — Composite 0–100 score from coverage, drift penalty, rule compliance, and isolation ratio; letter grade; detailed breakdown via HealthScoreDetails

**Database additions:** Migration 0022 (7 tables, 11 enum types)
**New services:** architecture_service, topology_mapper_service, drift_detection_service, architecture_rule_service, design_doc_service, impact_analysis_service, refactor_recommendation_service, architecture_approval_service, structural_health_service
**New route file:** architecture.py with 27 endpoints
**Frontend additions:** 1 dashboard page, 1 API client (12 functions), TypeScript types (19 interfaces + 8 type unions)
**Test additions:** ~69 architecture-specific tests
**Total test suite: 482 tests (all passing)**

> **All 90 tasks across 21 milestones are complete. 482 tests passing.**

---

## Milestone 22 — ForgeMind Local: Developer Workstation Mode (FM-091–FM-100)

ForgeMind Local is a standalone CLI companion that provides offline repo intelligence, bounded execution, patching, PR preparation, IDE integration, and team handoff — all without requiring the full backend stack.

### Key Capabilities

- **Local foundation** — YAML-based per-repo config in `.forgemind/`, auto-detection of git repos, workspace initialisation via `forgemind init`
- **Repo indexing** — Full file tree walk with language classification (30+ extensions), entrypoint/build-file detection, cached JSON manifest
- **Local chat** — Keyword search over indexed files with file snippet reading; optional LiteLLM integration; works fully offline with rule-based fallback
- **Execution sandbox** — Bounded local command execution with 3 policies (safe/permissive/locked), 16 blocked patterns, 35 safe prefixes, subprocess timeout, JSON run logging
- **Patch workflow** — Generate patches from `git diff`, list/preview/apply/reject with metadata tracking; `git apply --check` safety validation
- **PR preparation** — Generate PR description, risk analysis, test checklist from git diff; 11 subsystem categories; security/migration/auth risk detection
- **IDE integration** — Generate VS Code `tasks.json` with 10 ForgeMind tasks; idempotent merge with existing editor config
- **State management** — TTL-based cache, offline sync queue (infrastructure-ready, no consumer yet), mode management (offline/hybrid/remote)
- **Handoff snapshots** — Export/import zip bundles with config, manifest, patches, sync queue, run logs for team handoff
- **Hardening** — 53 tests across 9 test classes, ruff-clean, documentation across all tracking files

### Architecture

- **Package:** `apps/local/` — standalone Python package (`forgemind-local`)
- **Entry point:** `forgemind` CLI via Click
- **Dependencies:** click, rich, pyyaml, gitpython, watchdog; optional litellm
- **Data directory:** `.forgemind/` per repo (config, state, cache, index, patches, snapshots)
- **No backend dependency** — operates entirely offline

### Safety Boundaries

- Execution sandbox uses `shell=True` — appropriate for local dev tool where user is the operator
- 16 blocked patterns are substring-matched defense-in-depth, not a security boundary
- `permissive` policy allows any command not in blocked list — wide scope by design
- Sync queue stores events but no consumer transmits them yet

## FM-091 to FM-100 — ✅ COMPLETE

| ID     | Feature                          | Status      |
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

> **ForgeMind now spans 140 features across 26 milestones — a structurally self-aware, SPEC-driven AI execution platform with lifecycle gating, project constitutions, phase-aware agent routing, reusable project templates, persistent execution checkpoints, delivery artifact generation, lifecycle traceability, explainable release confidence scoring, versioned release packages, deployment environments, configurable release gates, rollback readiness analysis, post-release reporting, and unified operational timelines. 746 tests passing (685 backend + 61 local).**

## FM-131 to FM-140 — ✅ COMPLETE

| ID     | Feature                                           | Status      |
| ------ | ------------------------------------------------- | ----------- |
| FM-131 | Release Package Model & Generation                | ✅ Complete |
| FM-132 | Deployment Environment Model & Targets            | ✅ Complete |
| FM-133 | Environment-Aware Deployment Readiness Evaluation | ✅ Complete |
| FM-134 | Release Gates & Operational Policy Checks         | ✅ Complete |
| FM-135 | Rollback Readiness & Recovery Metadata            | ✅ Complete |
| FM-136 | Post-Release Report & Outcome Tracking            | ✅ Complete |
| FM-137 | Operational Timeline View                         | ✅ Complete |
| FM-138 | Frontend Release Operations Surface               | ✅ Complete |
| FM-139 | Local Mode Release Awareness                      | ✅ Complete |
| FM-140 | Tests, Docs & Hardening                           | ✅ Complete |

### Key Capabilities (Milestone 26)

- **Release packages**: Versioned bundles auto-generated from run state with artifact manifests, changelogs, confidence snapshots, and rollback metadata
- **Deployment environments**: Tiered targets (dev/staging/canary/production) with configurable required gates and promotion chains
- **Deployment readiness**: 7-check evaluator with tier-aware confidence thresholds (dev=30, staging=50, canary=65, prod=80)
- **Release gates**: 9 built-in policy gates evaluated against real run signals; per-gate pass/fail persistence with auto package status transitions
- **Rollback readiness**: Recovery point enumeration from checkpoints and previous releases; strategy recommendations with risk assessment
- **Post-release reports**: Aggregated task outcomes, gate results, approval summaries, artifact inventories, checkpoint coverage
- **Outcome tracking**: Record deployment outcomes (deployed/rolled_back/failed) with notes
- **Operational timeline**: Unified chronological view merging run lifecycle events, checkpoints, approvals, releases, gates, and tasks
- **Frontend surface**: Release dashboard with gate evaluation panels, rollback readiness views, and status badges
- **Local CLI**: Release list, status (7 local readiness checks), and environment listing commands

## FM-121 to FM-130 — ✅ COMPLETE

| ID     | Feature                                      | Status      |
| ------ | -------------------------------------------- | ----------- |
| FM-121 | Execution Checkpoint Model & CRUD            | ✅ Complete |
| FM-122 | Auto-Checkpoint on Phase Transitions         | ✅ Complete |
| FM-123 | Resume-from-Checkpoint Semantics             | ✅ Complete |
| FM-124 | Delivery Artifact Generation                 | ✅ Complete |
| FM-125 | Review Package Assembly                      | ✅ Complete |
| FM-126 | Lifecycle Traceability Graph                 | ✅ Complete |
| FM-127 | Run Memory Enrichment                        | ✅ Complete |
| FM-128 | Release Confidence Scoring                   | ✅ Complete |
| FM-129 | Local CLI Checkpoint & Delivery Commands     | ✅ Complete |
| FM-130 | Integration Hardening, Tests & Documentation | ✅ Complete |

### Key Capabilities (Milestone 25)

- **Execution checkpoints**: Persistent snapshots of run state (status, artifacts, approvals, architecture) with 5 checkpoint types (manual, auto_phase, pre_approval, pre_delivery, post_validation)
- **Auto-checkpointing**: Automatic checkpoint creation capturing run state with computed snapshots
- **Resume semantics**: Resume execution from any checkpoint with ownership validation, continuation context, and event logging
- **Delivery artifacts**: Generate implementation summaries, changelog drafts, release notes, and completion bundles from run state
- **Review packages**: Assemble reviewer-ready packages with spec, plan, tasks, approvals, risks, and recommendations
- **Lifecycle traceability**: Directed graph (nodes + edges) linking runs → prompts → artifacts → tasks → checkpoints with typed relationships
- **Run memory enrichment**: Structured memory extraction (objectives, blockers, confidence factors, validation outcomes, delivery notes)
- **Release confidence scoring**: Explainable 0–100 score with 8 weighted signals, band classification (high/medium/low), blocking factors, and suggested actions
- **Local CLI integration**: Checkpoint list/save, confidence scoring, and review summary commands for offline workflows
- **REST API**: Full CRUD for checkpoints plus endpoints for delivery artifacts, review packages, traceability, memory, and confidence

## FM-111 to FM-120 — ✅ COMPLETE

| ID     | Feature                                          | Status      |
| ------ | ------------------------------------------------ | ----------- |
| FM-111 | Phase Agent Profile Data Model                   | ✅ Complete |
| FM-112 | Composition Engine Phase-Aware Routing           | ✅ Complete |
| FM-113 | Phase Agent Profile UI                           | ✅ Complete |
| FM-114 | Project Template Model and Seeding               | ✅ Complete |
| FM-115 | Template-Based Project Creation Flow             | ✅ Complete |
| FM-116 | Template Inheritance for Constitution & Policies | ✅ Complete |
| FM-117 | Knowledge-Driven Constitution Suggestions        | ✅ Complete |
| FM-118 | Spec/Plan Bootstrap from Project Templates       | ✅ Complete |
| FM-119 | Local Mode Support for Templates & Profiles      | ✅ Complete |
| FM-120 | Hardening, Tests & Documentation                 | ✅ Complete |

### Key Capabilities (Milestone 24)

- **Phase-agent profiles**: Per-project agent-to-phase assignments (specify, plan, tasks, implement, review, validate)
- **Phase-aware routing**: Worker and adaptive orchestrator consult phase profiles before capability-based fallback
- **Reusable project templates**: 4 built-in templates (rest-api, frontend-app, data-pipeline, cli-tool) with real constitutions, governance config, phase profiles, and spec/plan defaults
- **Template-based creation**: Project creation applies template defaults (constitution, phase profiles)
- **3-tier governance inheritance**: system defaults → template → project overrides
- **Constitution suggestions**: 5 rules evaluate run/task signals to propose constitution improvements (never auto-applied)
- **Template-influenced SPEC/PLAN**: Template spec_defaults and plan_defaults injected into LLM prompts
- **Local mode awareness**: Local CLI displays template/phase config, execution logs include context, handoff bundles carry template metadata

## FM-101 to FM-110 — ✅ COMPLETE

| ID     | Feature                            | Status      |
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

### Key Capabilities (Milestone 23)

- **SPEC-driven lifecycle**: Runs follow PENDING → SPECIFYING → PLANNING → RUNNING with gating at each transition
- **Project constitutions**: Persistent AI behavior rulebooks injected into SPEC generation, PLAN generation, and chat
- **Slash commands**: `/fm.specify`, `/fm.plan`, `/fm.tasks`, `/fm.implement` for direct lifecycle control from chat
- **Formal PLAN→SPEC linking**: PLAN artifacts reference their SPEC via FK, with markdown export
- **ADR-aware planning**: Architecture graph context (nodes, drifts, rule violations) enriches generated plans
- **Spec-to-plan validation**: 8 rules (4 ERROR, 4 WARNING) enforce plan quality before execution
- **Approval gates**: SPEC and PLAN artifacts can require approval before lifecycle transitions proceed

## FM-071 to FM-080 — ✅ COMPLETE

| ID     | Feature                                   | Status      |
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

## FM-081 to FM-090 — ✅ COMPLETE

| ID     | Feature                         | Status      |
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

## FM-046 to FM-050 — ✅ COMPLETE

| ID      | Feature                                          | Status      |
| ------- | ------------------------------------------------ | ----------- |
| FM-046  | Run Replay and Execution Trace Inspection        | ✅ Complete |
| FM-047A | Multi-Agent Council Decision Engine              | ✅ Complete |
| FM-047  | Policy-Based Approval Rules                      | ✅ Complete |
| FM-048  | Multi-Run Memory and Project Knowledge Base      | ✅ Complete |
| FM-049  | External Repo / Workspace Execution Integration  | ✅ Complete |
| FM-050  | Production Readiness and Platform Hardening Pass | ✅ Complete |

## FM-051 to FM-059 — ✅ COMPLETE

| ID     | Feature                              | Status      |
| ------ | ------------------------------------ | ----------- |
| FM-051 | Workspace Model & Multi-Tenant Shell | ✅ Complete |
| FM-052 | Workspace Member Roles               | ✅ Complete |
| FM-053 | Project-Level Member & Permissions   | ✅ Complete |
| FM-054 | SSE Streaming Foundation             | ✅ Complete |
| FM-055 | In-App Notification Engine           | ✅ Complete |
| FM-056 | Notification Delivery Config         | ✅ Complete |
| FM-057 | Escalation Rule Engine               | ✅ Complete |
| FM-058 | Activity Feed & Audit Extension      | ✅ Complete |
| FM-059 | User Presence Tracking               | ✅ Complete |

## FM-061 to FM-069 — ✅ COMPLETE

| ID     | Feature                       | Status      |
| ------ | ----------------------------- | ----------- |
| FM-061 | Code Mapping Model            | ✅ Complete |
| FM-062 | Patch Proposal Model          | ✅ Complete |
| FM-063 | Change Review Workflow        | ✅ Complete |
| FM-064 | Branch Strategy Configuration | ✅ Complete |
| FM-065 | PR Draft Composer             | ✅ Complete |
| FM-066 | Repo Action Approval Gate     | ✅ Complete |
| FM-067 | Sandbox Execution Engine      | ✅ Complete |
| FM-068 | Code Ops REST API             | ✅ Complete |
| FM-069 | Code Ops Integration Tests    | ✅ Complete |

---

## FM-141 to FM-150 — ✅ COMPLETE (Wave 10: Collaboration & UX)

| ID     | Feature                          | Status                                                                                                                                                                                                                                                                                                                                                |
| ------ | -------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| FM-141 | Threaded Comments                | ✅ Complete                                                                                                                                                                                                                                                                                                                                           |
| FM-142 | @Mentions & Notification Routing | ✅ Complete — `NotificationPreference` model, `upsert_preference`/`get_preferences`/`is_notification_allowed` service functions, per-category mute-until with timezone-safe comparison, GET/PUT `/notifications/preferences` routes                                                                                                                   |
| FM-143 | Unified Activity Feed            | ✅ Complete — cursor-based pagination on project/run activity routes; `next_cursor` in response                                                                                                                                                                                                                                                       |
| FM-144 | Saved Views & Filters            | ✅ Complete — default views (My tasks, Pending approvals, Failed runs) seeded on project creation                                                                                                                                                                                                                                                     |
| FM-145 | User Presence & Online Status    | ✅ Complete                                                                                                                                                                                                                                                                                                                                           |
| FM-146 | Collaborative Run Annotations    | ✅ Complete                                                                                                                                                                                                                                                                                                                                           |
| FM-147 | Task Assignment & Workload       | ✅ Complete — assign/unassign/reassign emit `TASK_ASSIGNED`/`TASK_UNASSIGNED`/`TASK_REASSIGNED` execution events with metadata (assignee_id, previous_assignee_id)                                                                                                                                                                                    |
| FM-148 | Approval Delegation & Batch      | ✅ Complete — delegation CRUD + revoke, batch-decide (two-pass atomic: validate-all-then-mutate), pending, expired routes, delegation-aware escalation, background scheduler. Cross-project dashboard (`GET /dashboard`) with per-project health grades (A-F), success rates, pending approval details (top 10 per project), and cross-project totals |
| FM-149 | Notification Digest & Center     | ✅ Complete — dismiss, grouped notifications, and digest preview routes; grouping by `group_key`                                                                                                                                                                                                                                                      |
| FM-150 | Project Overview Dashboard       | ✅ Complete — HTTP route + composite metrics (runs, tasks, approvals, health grade, team)                                                                                                                                                                                                                                                             |

**Wave 10 summary:** 10/10 milestones fully complete. Pass 6 closed FM-148: batch_decide now uses two-pass atomic approach (validate all → mutate all), dashboard enriched with health grades and pending approval details.

## FM-151 to FM-160 — ⚙️ PARTIAL (Wave 11: GitHub & CI Integration)

> **Note:** Wave 11 now has outbound GitHub API capability (PR comments, commit statuses)
> via `github_client.py` using `GITHUB_API_TOKEN`. Webhook signature verification is
> enforced when `GITHUB_WEBHOOK_SECRET` is configured.

| ID     | Feature                                | Status                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| ------ | -------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| FM-151 | GitHub App Installation & Linking      | ✅ Complete (Pass 7) — Full token lifecycle: AES-256-GCM encryption, store/get/refresh, `validate_installation()` health check, `get_or_refresh_token()` chained refresh, `list_installations_needing_refresh()` proactive monitoring, `deactivate_installation()` soft-deactivate, 3 management routes (`token-status`, `refresh-token`, `deactivate`), OAuth callback. **Remaining caveat:** no live GitHub App JWT signing (requires GitHub App private key) |
| FM-152 | Webhook Ingestion & Events             | ✅ Complete — signature verification enforced; 6/6 event types processed (pull_request, issue, check_run, push, release, check_run via new processors)                                                                                                                                                                                                                                                                                                          |
| FM-153 | PR Auto-Creation & Tracking            | ✅ Complete — CRUD, webhook-driven state sync, outbound PR creation via GitHub API, local DB recording                                                                                                                                                                                                                                                                                                                                                          |
| FM-154 | CI Pipeline Status Integration         | ✅ Complete — inbound ingestion, outbound commit status posting, CI pass-rate calculation, CI readiness gate (threshold-based pass-rate check integrated into merge readiness + standalone route)                                                                                                                                                                                                                                                               |
| FM-155 | Issue Sync                             | ✅ Complete (Pass 7) — Bidirectional sync: ForgeMind→GitHub via `sync_status_to_github()`, GitHub→ForgeMind via `handle_issue_webhook()`, batch export `process_pending_exports()`, bulk import `bulk_import_issues()`, loop prevention (5s debounce + sync_direction tracking), `sync_direction`/`last_synced_at` tracking columns, 2 sync routes. **Remaining caveat:** no automatic background sync scheduler                                                |
| FM-156 | Branch Strategy & Merge Readiness      | ✅ Complete — merge readiness + auto-create branch: `create_branch()` in github_client (resolves base SHA, creates git ref), `slugify_branch_name()` generates `task/{slug}-{short_id}`, `POST /github/branches/auto-create` route                                                                                                                                                                                                                              |
| FM-157 | Code Review Routing                    | ✅ Complete — glob ownership matching, outbound PR comments, GitHub reviewer requests, reviewer suggestion/scoring ranked by coverage breadth + specificity                                                                                                                                                                                                                                                                                                     |
| FM-158 | Commit & Diff Intelligence             | ✅ Complete — diff parsing + 8 risk rules (LARGE_FILE_CHANGE, MIGRATION_DETECTED, SECRET_PATTERN, CI_CONFIG_CHANGE, DEPENDENCY_CHANGE, DOCKERFILE_CHANGE, SECURITY_FILE, TEST_DELETION), `evaluate_risk_rules()` with severity-weighted scoring, `get_risk_rules()`, `POST /github/diffs/risk` and `GET /github/diffs/rules` routes                                                                                                                             |
| FM-159 | VS Code Extension Foundation           | ⏸️ DEFERRED (separate repo)                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| FM-160 | Hardening: Rate Limiter, Retry, Replay | ✅ Complete                                                                                                                                                                                                                                                                                                                                                                                                                                                     |

**Wave 11 summary:** 9/10 fully complete (Pass 7 upgraded FM-151 + FM-155), 1 deferred. Pass 7 added installation health monitoring, bidirectional issue sync with loop prevention, batch export/import. Remaining caveats: live App JWT signing (FM-151, requires GitHub App key), background sync scheduler (FM-155).

---

## Technical Debt (active)

See [docs/TECHNICAL_DEBT.md](TECHNICAL_DEBT.md) for full details (18 items). Key new items:

- **TD-013**: Approval required only for fixed task types (no policy engine)
- **TD-014**: No real-time event streaming (polling only)
- **TD-015**: Approval decision has no authorization check
- **TD-016**: Retry/cancel event types reuse existing enum values
- **TD-017**: Chat service has no conversation memory
- **TD-018**: Agent hint from planner not validated against registered agents

---

_Wave 10: 10/10 complete. Wave 11: 9/10 complete, 1 deferred. Wave 12: 10/10 complete. Wave 13: 10/10 complete. FM-159 (VS Code extension) is explicitly deferred — requires a separate TypeScript/VS Code extension project. **39 COMPLETE, 0 PARTIAL, 1 DEFERRED** across FM-141→180. Pass 8 closed FM-162 (Semantic Search with Embeddings) — real embedding vectors via litellm, cosine similarity, hybrid ranking, 25 new tests, 1157 total._

---

## FM-161 to FM-170 — ✅ 10/10 COMPLETE (Wave 12: Search, Knowledge & Organizational Memory)

| ID     | Feature                                     | Status                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| ------ | ------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| FM-161 | Full-Text Search Index                      | ✅ Complete (LIKE-based keyword search; tsvector deferred)                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| FM-162 | Semantic Search with Embeddings             | ✅ **COMPLETE** — Real embedding vectors via litellm (pluggable provider), `SearchEmbedding` model with JSON-stored vectors, cosine similarity for vector search, `hybrid_search()` with configurable alpha blending (text + semantic), `semantic_search()` for pure vector search, `find_similar()` upgraded to use embeddings with TF-IDF fallback, `GET /search/semantic` and `POST /projects/{id}/generate-embeddings` routes. 25 tests covering cosine math, storage, semantic search, hybrid ranking, fallback. |
| FM-163 | Knowledge Base — Decision & Pattern Library | ✅ Complete — knowledge-type search filter + `suggest_knowledge_for_task()` multi-strategy engine (tag matching, title overlap, word overlap, LIKE fallback), `GET /projects/{project_id}/knowledge/suggest` route                                                                                                                                                                                                                                                                                                    |
| FM-164 | Project Templates V2 — Knowledge-Enriched   | ✅ Complete — marketplace browse + deep clone (`clone_template`) + versioning (`create_template_version`), `version` and `parent_template_id` columns on ProjectTemplate, `POST /templates/{id}/clone` and `POST /templates/{id}/version` routes                                                                                                                                                                                                                                                                      |
| FM-165 | Cross-Project Search & Discovery            | ✅ Complete — RBAC-filtered cross-project search + project directory (`get_project_directory` with health grades A-F, `GET /project-directory`) + related project suggestions (`get_related_projects` via knowledge tag + search index overlap, `GET /projects/{id}/related`)                                                                                                                                                                                                                                         |
| FM-166 | Execution Replay & Comparison               | ✅ Complete — comparison + replay mode: `replay_run()` iterates original snapshots, creates replay snapshots, detects output divergence, returns summary with divergent_count/all_match. `POST /runs/{run_id}/replay` route                                                                                                                                                                                                                                                                                           |
| FM-167 | Organizational Context & Conventions Engine | ✅ Complete                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| FM-168 | Artifact Versioning & History               | ✅ Complete                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| FM-169 | Smart Recommendations Engine                | ✅ Complete (7 rules)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| FM-170 | Knowledge & Search Tests, Docs & Hardening  | ✅ Complete (45 tests, index integrity checker; perf benchmarks deferred)                                                                                                                                                                                                                                                                                                                                                                                                                                             |

**Wave 12 summary:** 10/10 milestones complete. FM-162 upgraded with real embedding vectors (litellm), cosine similarity, hybrid ranking — all 5/5 ACs met. FM-163 gained auto-suggestion engine. FM-164 gained deep clone + versioning. FM-165 gained project directory + related suggestions. FM-166 gained replay mode.

---

## Wave 13 — Enterprise Governance, Permissions & Compliance (FM-171 → FM-180)

> Audit trails, policy evaluation engine, compliance reports, IP allowlisting, retention policies,
> governance settings, role introspection, SSO configuration, secret resolution.
> 8/10 milestones at PARTIAL or above; 2/10 have remaining work deferred.

| FM     | Feature                                       | Status                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| ------ | --------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| FM-171 | Organization / Governance Metadata            | ✅ Complete — `governance_settings` JSON column on Workspace (plan_tier, compliance_level, sso/ip enforcement, data_region, audit_retention_days). Validated CRUD via `GET/PUT /workspaces/{id}/governance` with Pydantic schema, tier/compliance/retention validation, defaults for unset workspaces                                                                                                                                                             |
| FM-172 | RBAC V2 — Fine-Grained Permissions            | ✅ Complete — 25-action enforcement matrix, role introspection endpoints, `CustomRole` model (workspace-scoped, JSON permissions list), `create_custom_role`/`list_custom_roles`/`update_custom_role` service functions with Action enum validation, `POST/GET /workspaces/{id}/custom-roles` and `PATCH /custom-roles/{id}` routes                                                                                                                               |
| FM-173 | Comprehensive Audit Log                       | ✅ Complete — Immutable AuditLog model, 8-filter query, CSV export, stats endpoint                                                                                                                                                                                                                                                                                                                                                                                |
| FM-174 | Policy Engine — Automated Rule Enforcement    | ✅ Complete — GovernancePolicyEvaluation with 5 trigger types, enforcement recording, evaluation history                                                                                                                                                                                                                                                                                                                                                          |
| FM-175 | SSO Configuration Model                       | ✅ Complete (Pass 7) — SSOConfiguration model, CRUD routes, `validate_sso_config()` per-provider validation, `build_oidc_authorize_url()` standard OAuth2 URL construction, `get_active_sso_for_workspace()`, `check_sso_enforcement()` workspace-level enforcement, `check_jit_provisioning_ready()`, 3 new routes (`validate`, `sso-enforcement`, `sso-login-url`). **Remaining caveat:** live SAML assertion/OIDC token exchange requires python3-saml/authlib |
| FM-176 | Data Retention & Lifecycle Policies           | ✅ Complete — RetentionPolicy model, CRUD, dry-run + execution mode, 4 entity types (run, audit_log, artifact, notification), background scheduler. ARCHIVE action now stamps `archived_at` on Run/Artifact models + creates audit trail. `archived_at` column added to Run and Artifact models                                                                                                                                                                   |
| FM-177 | Compliance Reporting & Export                 | ✅ Complete — 5 report types (access review, change mgmt, approval audit, policy compliance, full governance). JSON/CSV export. PDF deferred.                                                                                                                                                                                                                                                                                                                     |
| FM-178 | IP Allowlisting & Access Controls             | ✅ Complete — CIDR-based allowlist with IPv4/IPv6, `IPAllowlistMiddleware` wired in FastAPI app, workspace governance flag controls enforcement                                                                                                                                                                                                                                                                                                                   |
| FM-179 | Secrets Management — Resolution & Lifecycle   | ✅ Complete — `resolve_secret()` with scope enforcement (encrypted → env var fallback), `rotate_credential()` lifecycle tracking. AES-256-GCM encryption via `encryption_service.py` (FORGEMIND_ENCRYPTION_KEY, 12-byte random nonce + GCM tag). `encrypted_value` column on CredentialVault. `create_credential(secret_value=)` encrypts at creation, `store_encrypted_secret()` for updates. `build_credential_read()` masks encrypted values                   |
| FM-180 | Enterprise Governance Tests, Docs & Hardening | ✅ Complete — 70+ tests covering all services, IPv6 CIDR fix, doc overclaims corrected                                                                                                                                                                                                                                                                                                                                                                            |

**Wave 13 summary:** 10/10 fully complete. Pass 7 upgraded FM-175: SSO validation, OIDC URL builder, enforcement checks, JIT provisioning readiness, 3 new routes. Live SAML/OIDC flows remain a caveat (requires python3-saml/authlib).

---

## Wave 14 — Code Intelligence, Change Awareness & Test Intelligence (FM-181 → FM-190)

> AST-based dependency parsing, impact analysis, coverage mapping, pattern detection,
> technical debt tracking, flakiness detection, complexity metrics.
> 0/10 COMPLETE — all PARTIAL or DEFERRED. 35 tests.

| FM     | Feature                                   | Status                                                                                                               |
| ------ | ----------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| FM-181 | Codebase Graph — Dependency Mapping       | 🔶 Partial — Python AST parsing works; no TypeScript parser; no incremental scan                                     |
| FM-182 | Change Impact Analysis                    | 🔶 Partial — BFS traversal works; no explicit risk scoring; no test/source file separation                           |
| FM-183 | Test Coverage Mapping                     | 🔶 Partial — Static mapping + upsert; no coverage report parser (pytest-cov/istanbul/LCOV)                           |
| FM-184 | Intelligent Test Selection                | ⏳ Deferred — requires FM-182 + FM-183 composition                                                                   |
| FM-185 | Code Pattern Detection                    | 🔶 Partial — Regex scan engine; zero built-in rules shipped; no KB integration                                       |
| FM-186 | Technical Debt Tracking                   | 🔶 Partial — All 4 debt sources (comment/pattern/age/complexity) detected and scored; budget warning not implemented |
| FM-187 | Test Flakiness Detection                  | 🔶 Partial — Flakiness scoring works; quarantine flag exists but no gate enforcement                                 |
| FM-188 | Code Complexity Metrics                   | 🔶 Partial — Cyclomatic + cognitive complexity computed; no trend tracking across snapshots                          |
| FM-189 | Code Intelligence Agent Integration       | ⏳ Deferred — requires agent runtime pipeline                                                                        |
| FM-190 | Code Intelligence Tests, Docs & Hardening | 🔶 Partial — 35 tests (target 40+); no perf benchmarks; no docs                                                      |

**Wave 14 summary:** 0 COMPLETE / 8 PARTIAL / 2 DEFERRED. Foundation laid for all services; key gaps are cognitive complexity, multi-debt-source scanning, and coverage report ingestion.

---

## Wave 15 — Analytics, Metrics & Portfolio Operations (FM-191 → FM-200)

> Execution metrics, health scoring, cost budgets, velocity, quality snapshots,
> portfolio aggregation, dashboards, alerts, executive summaries.
> 0/10 COMPLETE — all PARTIAL. 32 tests.

| FM     | Feature                                      | Status                                                                                                                                         |
| ------ | -------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| FM-191 | Run Execution Metrics & Time Tracking        | 🔶 Partial — Manual recording + aggregation; no auto-capture from status transitions                                                           |
| FM-192 | Project Health Scoring                       | 🔶 Partial — auto_compute_health_dimensions() computes all 6 dims from real Run/Cost/Quality/Complexity data; weighted composite + grades work |
| FM-193 | Cost Tracking & Budget Management            | 🔶 Partial — check_budget() enforces BLOCK (403)/WARN/LOG per BudgetConfig threshold; no LLM call auto-recording                               |
| FM-194 | Team Velocity & Throughput Metrics           | 🔶 Partial — compute_approval_velocity() + compute_velocity_comparison() with % change; throughput works                                       |
| FM-195 | Quality Metrics Dashboard                    | 🔶 Partial — evaluate_quality_gates() with configurable thresholds + violations/warnings; snapshot + trend work                                |
| FM-196 | Portfolio Overview — Multi-Project Dashboard | 🔶 Partial — Service-layer sort/filter for 4 dims added but route does not forward params; N+1 not yet optimized                                 |
| FM-197 | Custom Dashboards & Widgets                  | 🔶 Partial — Dashboard CRUD complete; no widget rendering or data source resolution                                                            |
| FM-198 | Scheduled Reports & Alerts                   | 🔶 Partial — Alerts with cooldown enforcement + trigger history; no scheduled report execution engine                                          |
| FM-199 | Executive Summary Generator                  | 🔶 Partial — Aggregates health/velocity/quality/execution; no NLP generation; no artifact storage                                              |
| FM-200 | Analytics Tests, Docs & Hardening            | 🔶 Partial — 32 tests (target 40+); no perf benchmarks; no docs                                                                                |

**Wave 15 summary:** 0 COMPLETE / 10 PARTIAL / 0 DEFERRED. Service-layer analytics working: auto-computed health dimensions, budget enforcement, approval velocity, quality gates, portfolio sort/filter. Route integration pending for most new functions. Remaining gaps: auto-capture timings, LLM call recording, widget rendering, report execution engine.

---

## Wave 16 — API, Webhooks & Ecosystem Integrations (FM-201 → FM-210)

> API key management, rate limiting, webhooks, external integrations, connector registry.
> 0/10 COMPLETE — 5 PARTIAL / 5 DEFERRED. 26 tests.

| FM     | Feature                                       | Status                                                                                                |
| ------ | --------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| FM-201 | Public API v1 — Core Endpoints                | 🔶 Partial — API key gen/validate/revoke + scope enforcement; no /api/v1/ routing; no OpenAPI spec    |
| FM-202 | API Rate Limiting & Throttling                | 🔶 Partial — require_rate_limit() dependency exists but not applied to any route; no per-tier limits  |
| FM-203 | Webhook Subscription System                   | 🔶 Partial — HTTP dispatch via httpx + HMAC signing + delivery tracking + fire_event; retry works     |
| FM-204 | Slack Integration                             | ⏳ Deferred — external integration                                                                    |
| FM-205 | Jira Integration                              | ⏳ Deferred — external integration                                                                    |
| FM-206 | PagerDuty & Incident Integration              | ⏳ Deferred — external integration                                                                    |
| FM-207 | Email Notification Channel                    | ⏳ Deferred — external integration                                                                    |
| FM-208 | Integration Marketplace & Custom Connectors   | 🔶 Partial — Registry CRUD works; no abstract Connector interface/ABC                                 |
| FM-209 | API SDK & Client Libraries                    | ⏳ Deferred — requires stable API surface                                                             |
| FM-210 | Ecosystem Integration Tests, Docs & Hardening | 🔶 Partial — 26 tests (target 45+); no e2e scenario; no docs                                          |

**Wave 16 summary:** 0 COMPLETE / 5 PARTIAL / 5 DEFERRED. Key infrastructure (keys, rate limiter, webhook records) built; require_rate_limit() exists but is not applied to any route yet. Remaining gaps: route integration for rate-limit headers, per-tier limits, /api/v1/ routing, connector ABC.

---

## ForgeMind V5 — FUTURE (FM-211 → FM-250)

> **Status:** Not yet implemented. Architecture direction planned for after FM-210 is complete.
> **Full roadmap:** See [FORGEMIND_V5_ROADMAP.md](../FORGEMIND_V5_ROADMAP.md)

V5 transforms ForgeMind into a **dynamic multi-agent orchestration platform** with persistent graph-based reasoning, council-style deliberation, and explainable workflow selection.

| Wave    | Range           | Theme                                       | Status    |
| ------- | --------------- | ------------------------------------------- | --------- |
| Wave 17 | FM-211 → FM-220 | Dynamic Multi-Agent Runtime Foundations     | 🔮 Future |
| Wave 18 | FM-221 → FM-230 | Council Collaboration & Deliberation Engine | 🔮 Future |
| Wave 19 | FM-231 → FM-240 | Graph Memory & Persistent Reasoning         | 🔮 Future |
| Wave 20 | FM-241 → FM-250 | Adaptive Workflow Selection & FAIR Engine   | 🔮 Future |

### Version Boundary Summary

| Version | Milestones     | Focus            | Status         |
| ------- | -------------- | ---------------- | -------------- |
| V1      | FM-001–050     | Foundation       | ✅ Complete    |
| V2      | FM-051–100     | Breadth          | ✅ Complete    |
| V3      | FM-101–140     | Depth            | ✅ Complete    |
| V4      | FM-141–210     | Ecosystem        | 🔧 In Progress |
| **V5**  | **FM-211–250** | **Intelligence** | **🔮 Future**  |
