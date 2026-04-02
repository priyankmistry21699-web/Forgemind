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

## Backlog

### Milestone 14 — Advanced Frontend Parity I (FM-071)

- FM-071 Frontend pages for Trust, Replay, Council, Governance (dashboard pages + lib + types + sidebar)

### Milestone 15 — Advanced Frontend Parity II (FM-072)

- FM-072 Frontend pages for Costs, Audit, Knowledge, Credential Vault (dashboard pages + lib + types + sidebar)

### Milestone 16 — Platform Admin Frontend Parity (FM-073)

- FM-073 Frontend pages for Connectors, Agents, Settings (dashboard pages + lib + types + enable sidebar links)

### Milestone 17 — Auth & RBAC Hardening (FM-074 to FM-075)

- FM-074 Real authentication integration (replace stub auth, real login flow, token verification)
- FM-075 Route-level RBAC enforcement hardening (audit all routes, consistent 401/403)

### Milestone 18 — CI/CD & Automation (FM-076)

- FM-076 CI/CD pipeline and quality gates (GitHub Actions: lint, test, typecheck, build)

### Milestone 19 — Real-Time & Observability (FM-077 to FM-078)

- FM-077 Real-time UX integration (SSE consumption, live updates, reconnect handling)
- FM-078 Observability and runtime instrumentation (metrics endpoint, tracing, request IDs)

### Milestone 20 — Platform Maturity (FM-079 to FM-080)

- FM-079 Monorepo package extraction (turn packages/ stubs into real shared packages)
- FM-080 Production deployment foundation (prod compose, env docs, health endpoints, deployment README)

## Blocked

- (none)
