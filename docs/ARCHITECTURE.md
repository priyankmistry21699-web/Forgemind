# ForgeMind — System Architecture

> **Last updated:** 2026-04-20 (V4 closure — FM-181 → FM-210 delivered; V4 total 30 / 0 / 0).
> **Scope:** this document is the authoritative architectural reference for the ForgeMind platform. It complements the product-framing in [../README.md](../README.md) and the wave-by-wave delivery log in [MILESTONE_SUMMARY.md](MILESTONE_SUMMARY.md).

---

## 1. System overview

ForgeMind is a multi-agent AI execution platform organized as a monorepo with four independent-but-cooperating process types:

| Process | Path | Role |
| ------- | ---- | ---- |
| **API** | `apps/api/` | FastAPI + SQLAlchemy 2 async. Owns all business logic. Every external surface (frontend, SDK, webhooks, local CLI sync) enters here. |
| **Web** | `apps/web/` | Next.js 15 App Router dashboard. Pure view layer; calls the API over HTTP/SSE. |
| **Worker** | `apps/worker/` | Long-running polling loop. Claims ready tasks, dispatches agents, persists artifacts. |
| **Local CLI** | `apps/local/` | Standalone `forgemind` Python CLI for developer workstations. Offline-first, optional server sync. |

Plus shared code under [`packages/`](../packages/) (`agents`, `connectors`, `core`, `orchestrator`, `schemas`, `security`, `utils`, `verification`) and a background scheduler that lives inside the API's FastAPI lifespan.

```
┌────────────────────────┐   HTTP / SSE   ┌──────────────────────────────────┐
│   Next.js 15 Dashboard │◄──────────────►│   FastAPI Backend (apps/api)     │
│   25 dashboard routes  │                │   51 routers · 103 services      │
│   34 lib modules       │                │   44 SQLAlchemy 2 models         │
└────────────────────────┘                │   JWT + API keys + rate limit    │
                                          │   Background scheduler (cron 60s)│
┌────────────────────────┐   /api/v1      └──────────────┬───────────────────┘
│  SDK: Python + TS      │──────────────►                │
│  apps/api/app/sdk      │                               │
└────────────────────────┘                               ▼
                                          ┌──────────────────────────────────┐
┌────────────────────────┐   polling      │   Worker (apps/worker)           │
│  forgemind CLI (local) │◄──────────────►│   Adaptive orchestrator          │
│  61 pytest tests       │                │   4 agents: architect, coder,    │
└────────────────────────┘                │   reviewer, tester               │
                                          └──────────────┬───────────────────┘
                                                         │
                    ┌────────────┬────────────┬──────────┴────────┐
                    ▼            ▼            ▼                   ▼
               ┌─────────┐ ┌──────────┐ ┌──────────┐     ┌─────────────────┐
               │Postgres │ │ Redis 7  │ │  MinIO   │     │ LiteLLM gateway │
               │   16    │ │ cache /  │ │ S3 files │     │ OpenAI · Claude │
               │         │ │ queues   │ │          │     │ Gemini · Ollama │
               └─────────┘ └──────────┘ └──────────┘     └─────────────────┘
```

Boundaries to keep in mind:

- **Routes never contain business logic.** They validate, authorize, delegate to services, shape responses. Cross-cutting (auth, rate limiting, logging, metrics, error handling) lives in middleware.
- **Services own all DB, LLM, and external I/O.** This keeps tests fast (services are called directly) and lets the worker reuse the same code paths as the API.
- **Models are the only source of schema truth.** Everything else — Pydantic DTOs, SDK types, dashboard types — flows from them.
- **Migrations are append-only** and must chain to the current `alembic heads`. See [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md#migrations).

---

## 2. Backend — `apps/api/`

### 2.1 Process layout

```
apps/api/app/
├── main.py              FastAPI app, middleware stack, lifespan (scheduler start/stop)
├── api/
│   ├── router.py        51 routers mounted here
│   └── routes/          51 route files, one per domain
├── services/            103 service modules — the real business logic
├── models/              44 SQLAlchemy 2 models
├── schemas/             Pydantic v2 request/response DTOs
├── core/
│   ├── config.py        Env-based settings (Pydantic BaseSettings)
│   ├── auth.py          JWT auth + dev stub fallback
│   ├── authz_deps.py    RBAC dependency injection
│   ├── rate_limit.py    Per-IP token bucket + per-API-key sliding window
│   ├── logging_middleware.py  Request IDs, timing
│   ├── error_handlers.py      Uniform JSON errors
│   ├── metrics.py       Prometheus metrics endpoint
│   └── llm.py           LiteLLM wrapper (cost tracking integrated)
├── db/
│   ├── base.py          Imports every model (migration + create_all discovery)
│   ├── base_class.py    Declarative base
│   └── session.py       Async engine + session factory
├── sdk/
│   ├── python_client.py
│   ├── typescript_client.ts
│   ├── openapi-generator-config.yaml
│   ├── pyproject.toml
│   └── package.json
└── alembic/versions/    Append-only migration chain
```

### 2.2 Route organization (51 routers)

All routers are registered in [apps/api/app/api/router.py](../apps/api/app/api/router.py) and mounted as a single `api_router` in `main.py`.

| Group | Routers |
| ----- | ------- |
| Platform core | `health`, `projects`, `planner`, `planner_results`, `tasks`, `runs`, `artifacts`, `agents`, `events` |
| Execution intelligence | `chat`, `composition`, `memory`, `retry`, `run_lifecycle` |
| Governance | `approvals`, `governance`, `audit`, `trust`, `costs`, `council`, `enterprise_governance` |
| Collaboration (Wave 10) | `workspaces`, `members`, `streaming`, `notifications`, `escalation`, `activity`, `comments`, `saved_views`, `collaboration` |
| Code ops | `repos`, `code_ops`, `annotations` |
| Security | `auth`, `credential_vault`, `metrics` |
| Architecture intelligence | `architecture` |
| Constitution / templates | `constitution`, `constitution_suggestions`, `phase_agent_profiles`, `project_templates` |
| Lifecycle | `checkpoints`, `delivery`, `release_ops`, `replay` |
| GitHub (Wave 11) | `github_integration` |
| Search / knowledge (Wave 12) | `search_knowledge`, `knowledge`, `connectors` |
| Code intelligence (Wave 14) | `code_intelligence` |
| Analytics (Wave 15) | `analytics` |
| Public ecosystem (Wave 16) | `api_ecosystem` |

Health is mounted at the root (`/health`, `/health/ready`). Everything else is either mounted at the module's own prefix or under `/api/v1/` for the Wave 16 public surface. The OpenAPI spec is validated for completeness in `TestOpenAPISpecCompleteness` (schemas populated, every path has an operation, `api-v1` tag present on versioned routes, spec fully JSON-serializable).

### 2.3 Service layer (103 services)

Services are the real business-logic core. They are pure Python classes/functions that take an `AsyncSession` and return domain objects or DTOs. Grouped by theme:

**Core delivery** — `project_service`, `planner_service`, `task_service`, `execution_service`, `artifact_service`, `artifact_version_service`, `agent_service`, `event_service`, `plan_artifact_service`, `spec_service`, `spec_plan_validation_service`, `spec_plan_approval_service`.

**Intelligence & composition** — `chat_service`, `composition_service`, `run_memory_service`, `run_memory_enrichment_service`, `adaptive_retry_service`, `adaptive_orchestrator`.

**Code ops** — `code_ops_service`, `repo_service`, `pr_service`, `code_review_service`, `diff_intelligence_service`, `merge_readiness_service`.

**Architecture intelligence** — `architecture_service`, `topology_mapper_service`, `drift_detection_service`, `architecture_rule_service`, `impact_analysis_service`, `refactor_recommendation_service`, `design_doc_service`, `structural_health_service`, `architecture_approval_service`, `convention_service`.

**Code intelligence (Wave 14)** — `code_graph_service` (dependency graph + BFS impact analysis), `pattern_debt_service` (regex anti-pattern detection + debt scoring), `flakiness_complexity_service` (flakiness tracker, cyclomatic complexity, maintainability index, quarantine).

**Analytics (Wave 15)** — `execution_health_service`, `velocity_quality_service`, `dashboard_alert_service`, `project_overview_service`, `operational_timeline_service`.

**Governance & compliance** — `governance_service`, `governance_engine_service`, `trust_scoring_service`, `cost_tracking_service`, `audit_export_service`, `audit_log_service`, `compliance_report_service`, `sso_configuration_service`, `ip_allowlist_service`, `retention_policy_service`, `release_gate_service`, `approval_service`, `approval_enhanced_service`, `environment_service`.

**Release lifecycle** — `release_confidence_service`, `release_package_service`, `post_release_service`, `deployment_readiness_service`, `rollback_readiness_service`, `run_annotation_service`, `run_comparison_service`, `execution_checkpoint_service`, `delivery_artifact_service`, `traceability_service`, `adr_service`.

**Search & memory** — `search_service`, `embedding_service`, `knowledge_service`, `recommendation_service`.

**Integrations** — `github_client`, `github_installation_service`, `github_rate_limiter`, `webhook_service`, `webhook_connector_service`, `email_service`, `slash_command_service`, `issue_sync_service`, `integration_service`, `ci_pipeline_service`.

**Collaboration (Wave 10)** — `workspace_service`, `membership_service`, `authz_service`, `stream_service`, `notification_service`, `notification_delivery_service`, `notification_digest_service`, `escalation_service`, `activity_service`, `unified_activity_service`, `user_activity_service`, `comment_service`, `mention_service`, `saved_view_service`, `task_assignment_service`.

**Security** — `api_key_service`, `encryption_service`, `credential_vault_service`.

**Infrastructure** — `background_scheduler` (cron runner inside FastAPI lifespan), `connector_service`, `phase_agent_profile_service`, `project_template_service`, `template_inheritance_service`, `constitution_service`, `constitution_suggestion_service`.

### 2.4 Data / persistence model (44 models)

Models live in [`apps/api/app/models/`](../apps/api/app/models/). Every model must be imported in [`apps/api/app/db/base.py`](../apps/api/app/db/base.py) so `Base.metadata` sees it (both Alembic autogenerate and the test-suite `create_all()` depend on this).

**Core domain** — `user`, `project`, `run`, `task`, `planner_result`, `artifact`, `agent`, `approval_request`, `execution_event`, `workspace`, `membership`.

**Governance** — `governance_policy`, `trust_score`, `cost_record`, `council`, `project_constitution`, `constitution_suggestion`, `approval_delegation`, `enterprise_governance` (SSO, IP allowlists, retention policies), `project_knowledge`.

**Repo / code ops** — `repo_connection`, `code_ops` (CodeMapping, PatchProposal, ChangeReview, BranchStrategy, PRDraft, RepoActionApproval, SandboxExecution), `annotations` (module `run_annotation`), `saved_view`.

**Architecture intelligence** — `architecture` (ArchitectureNode, ArchitectureEdge, ArchitectureSnapshot, ArchitectureDrift, ArchitectureRule, ArchitectureRuleResult, ChangeImpactAssessment).

**Code intelligence (Wave 14)** — `code_intelligence` (ModuleDependency, ImpactAnalysisRun, CoverageMap, PatternRule, PatternOccurrence, TechnicalDebtScore, FlakinessRecord, ComplexityMetric, QuarantineEntry).

**Analytics (Wave 15)** — `analytics_metrics` (ExecutionMetric, HealthScore, Budget, VelocityMetric, QualityMetric, Dashboard, DashboardWidget, ScheduledReport, MetricAlert).

**API ecosystem (Wave 16)** — `api_ecosystem` (ApiKey, WebhookEndpoint, WebhookDelivery, RateLimitTier, IntegrationBinding).

**Integrations** — `connector`, `project_connector_link`, `credential_vault`, `github_integration` (installations, PRs, status checks, issue syncs).

**Collaboration** — `notification`, `escalation`, `activity`, `comment`.

**Lifecycle** — `execution_checkpoint`, `release_ops` (ReleasePackage, ReleaseGate, DeploymentReadiness, RollbackReadiness, PostReleaseCheck, ReleaseConfidenceScore, RunAnnotation, RunComparison), `search_knowledge` (SearchIndexEntry, Convention, Recommendation, ADR).

**Phase config** — `phase_agent_profile`, `project_template`, `sso_configuration`.

**Replay** — `replay_snapshot`.

### 2.5 Migrations

Alembic chain lives in [`apps/api/alembic/versions/`](../apps/api/alembic/versions/). The current head is `fm161_170_search_knowledge` (chained from `0026_add_collaboration_github_tables`; the `down_revision=None` bug that broke `alembic upgrade heads` was fixed in commit `2a4e8fc`).

Tests **do not** run migrations. `tests/conftest.py` calls `Base.metadata.create_all()` against an in-memory SQLite, which is why the CI stayed green through the multi-head break. See [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md#migrations) for the local-runtime bootstrap workaround for migration `0022_add_architecture_tables`'s duplicate-enum quirk.

### 2.6 Middleware stack

In order, inside `apps/api/app/main.py`:

1. **CORS** (`starlette.middleware.cors`)
2. **Request logging** (`core/logging_middleware.py`) — adds `X-Request-ID`, logs method/path/status/duration.
3. **Rate limiting** (`core/rate_limit.py`) — per-IP token bucket for unauthenticated; `api_key_service.require_rate_limit()` for `/api/v1/` routes.
4. **Auth** — JWT verification + API-key verification as route-level dependencies, not middleware, so endpoints can opt in.
5. **Error handlers** (`core/error_handlers.py`) — uniform JSON error shape for `HTTPException`, validation errors, and unhandled exceptions.

---

## 3. Frontend — `apps/web/`

### 3.1 Stack

Next.js 15.5.14 (App Router) · React 19 · TypeScript 5 (strict) · Tailwind CSS 4 · shadcn/ui · TanStack Query v5 · Zustand · Socket.IO client · Mermaid.js · React Flow · Monaco Editor · Recharts. Custom pure-SVG chart components under `apps/web/components/dashboard/` power the FM-197 custom-dashboard feature with zero additional chart-library dependencies.

### 3.2 Route organization (25 dashboard routes)

[`apps/web/app/dashboard/`](../apps/web/app/dashboard/) holds 25 route folders, one per domain:

```
activity/         agents/          analytics/       approvals/
architecture/     artifacts/       audit/           code-explorer/
connectors/       costs/           council/         escalations/
governance/       knowledge/       notifications/   projects/
releases/         replay/          reviews/         runs/
sandbox/          settings/        trust/           vault/
workspaces/
```

Each route has:

- A `page.tsx` (server/client component mix).
- A sibling API-client module under `apps/web/lib/` that wraps the HTTP calls.
- Domain-scoped UI components under `apps/web/components/<domain>/`.
- Tests colocated under `apps/web/app/dashboard/__tests__/` and `apps/web/lib/__tests__/`.

### 3.3 Library (34 API-client modules)

[`apps/web/lib/`](../apps/web/lib/) is the single boundary between the dashboard and the backend. Every module is ~thin: one function per endpoint, typed with a dedicated TS interface, error-normalized via `lib/api.ts`'s shared fetch helper.

Modules: `activity`, `agents`, `api`, `approvals`, `architecture`, `artifacts`, `audit`, `auth-context`, `chat`, `connectors`, `constitution`, `constitution-suggestions`, `costs`, `council`, `dashboards`, `escalations`, `events`, `governance`, `knowledge`, `notifications`, `phase-profiles`, `planner`, `project-members`, `projects`, `release-ops`, `replay`, `runs`, `stream`, `tasks`, `templates`, `trust`, `vault`, `workspaces`, plus `hooks/` (`use-stream.ts`).

### 3.4 Dashboard rendering model

- **Server components** render the page shell and initial data.
- **Client components** handle interactivity (forms, mutations, real-time subscriptions).
- **TanStack Query** handles cache + invalidation. Mutations refresh the relevant query keys.
- **SSE streams** are subscribed via `lib/stream.ts` + `hooks/use-stream.ts` for live run/event updates.
- **FM-197 custom dashboards** render widgets through a per-widget-type data adapter that fetches via the appropriate `lib/*` module, then dispatches to one of six pure-SVG chart renderers (line, bar, pie, table, number, gauge). Layouts persist as `layout_json` on the `Dashboard` model. CRUD UI lives at `/dashboard/analytics`.

### 3.5 Testing

Vitest + Testing Library + @testing-library/jest-dom. v8 coverage provider. 231 tests across 37 files. Coverage thresholds are soft; the `npm run test:coverage` job uploads the coverage artifact in CI.

---

## 4. Worker — `apps/worker/`

A single polling loop with pluggable agents.

```
apps/worker/worker/
├── main.py              Poll loop · adaptive orchestrator cycle
└── agents/
    ├── base.py          BaseAgent · build_handoff_context · system prompt assembly
    ├── registry.py      slug → class dispatch
    ├── architect_agent.py
    ├── coder_agent.py
    ├── reviewer_agent.py
    └── tester_agent.py
```

Each cycle of `adaptive_orchestrator.run_cycle(db)`:

1. **Handle rejections** — any approval rejected since last cycle requeues its task with rejection context.
2. **Auto-retry failures** — failed tasks with `retry_count < max_retries` (default 2) are reset to `READY` with a possibly different agent (rerouting).
3. **Select next tasks** — ready tasks are scored by priority (critical-path + task-type weights) and the top N (configurable, default 3) are claimed.
4. **Resolve agent** — `composition_service.resolve_agent_for_task(task)` returns the best agent. If `task.agent_hint` is set, it wins; otherwise capability scoring (60% task-type match, 40% capability overlap) picks the highest-scoring registered agent.
5. **Build handoff context** — the agent's `build_handoff_context(task)` pulls completed upstream tasks and their artifacts into a packet used for the LLM system prompt.
6. **Execute** — the agent calls `core/llm.py` (LiteLLM wrapper) which records a `CostRecord` per call. Output is parsed into typed artifacts.
7. **Persist** — artifacts, events, optional replay snapshots (with SHA-256 hashes).
8. **Gate** — if the task type requires approval (architecture, review), an `ApprovalRequest` is created and the task waits.

---

## 5. Local CLI — `apps/local/`

A standalone Python package (`forgemind_local`) installable via `pip install -e apps/local`. Entry point: the `forgemind` console script.

```
apps/local/forgemind_local/
├── config.py            LocalConfig dataclass, YAML I/O, .forgemind/ dir management
├── cli.py               Click CLI — 10 command groups
├── repo_index.py        File tree scanner, language detection, manifest builder
├── local_chat.py        Keyword search + snippets + optional LLM Q&A
├── local_exec.py        Bounded subprocess with safe / permissive / locked policy
├── local_patch.py       Generate / preview / apply / reject unified diffs
├── local_pr.py          PR markdown from git diff (subsystems, risk, test checklist)
├── ide_integration.py   VS Code tasks.json / settings.json generator
├── local_state.py       Cache (TTL) + sync queue + mode (offline / hybrid / remote)
└── local_handoff.py     Export / import zip bundles
```

Modes (`offline` / `hybrid` / `remote`) and execution policies (`safe` / `permissive` / `locked`) persist in `.forgemind/config.yaml`. 61 pytest tests live under [apps/local/tests/](../apps/local/tests/).

---

## 6. Shared packages — `packages/`

Shared code that is consumed by more than one app:

- `packages/core` — domain-level types and shared constants.
- `packages/schemas` — Pydantic models reusable between API, worker, and local CLI.
- `packages/agents` — agent interface declarations.
- `packages/connectors` — shared connector implementations.
- `packages/orchestrator` — orchestrator primitives.
- `packages/security` — crypto + auth helpers.
- `packages/utils` — `logging_middleware.py` and other cross-cutting utilities.
- `packages/verification` — shared verification/validation logic.

Extracting code into `packages/` is the preferred pattern once a module needs to be reused outside a single app.

---

## 7. Integration architecture

| Integration | Service | Notes |
| ----------- | ------- | ----- |
| LLM providers | `core/llm.py` (LiteLLM) | Any OpenAI / Anthropic / Google / Ollama / Azure-compatible model. Cost recorded per call. |
| GitHub | `github_client`, `github_installation_service`, `github_rate_limiter`, `issue_sync_service`, `ci_pipeline_service` | GitHub App installs, rate-limited client, issue sync, PR status pipeline. |
| Slack | `integration_service` + webhook connectors | Outbound notifications via `notification_delivery_service`. |
| Email | `email_service` | Digest delivery + escalation notifications. |
| PagerDuty | `integration_service` via webhook | High-severity escalations. |
| External repos | `repo_service` | GitHub, GitLab, Bitbucket, local. |
| S3 / MinIO | via `boto3`-compatible client | Artifact bodies, release packages. |
| Webhooks (outbound) | `webhook_service`, `webhook_connector_service` | Configurable endpoints with delivery tracking. |
| SSO | `sso_configuration_service` | Wave 13 enterprise governance. |
| Public API consumers | `api_key_service` + `/api/v1/` | SHA-256 hashed keys, tier-based rate limits. |

---

## 8. SDK — `apps/api/app/sdk/`

Ships generated clients for third-party developers.

| File | Purpose |
| ---- | ------- |
| `python_client.py` | Synchronous + async Python client. |
| `typescript_client.ts` | TypeScript client with fetch-based transport. |
| `openapi-generator-config.yaml` | Config for regenerating clients from the live OpenAPI spec. |
| `pyproject.toml` | Packaging metadata for the Python client. |
| `package.json` | Packaging metadata for the TS client. |

The OpenAPI spec itself is auto-generated by FastAPI and validated by `TestOpenAPISpecCompleteness` (see [code-intelligence.md](code-intelligence.md) and [api-ecosystem.md](api-ecosystem.md)).

---

## 9. Analytics, code intelligence, and ecosystem separation

These three surfaces live behind three distinct API prefixes and three distinct doc files, and share no tables:

| Surface | Router | Primary models | Primary services | Doc |
| ------- | ------ | -------------- | ---------------- | --- |
| **Code intelligence** (Wave 14) | `/api/v1/code-intelligence/` | `code_intelligence.py` | `code_graph_service`, `pattern_debt_service`, `flakiness_complexity_service` | [code-intelligence.md](code-intelligence.md) |
| **Analytics & portfolio** (Wave 15) | `/api/v1/analytics/` | `analytics_metrics.py` | `execution_health_service`, `velocity_quality_service`, `dashboard_alert_service`, `project_overview_service`, `operational_timeline_service` | [analytics-portfolio.md](analytics-portfolio.md) |
| **API ecosystem** (Wave 16) | `/api/v1/` (public surface) | `api_ecosystem.py` | `api_key_service`, `webhook_service`, `webhook_connector_service`, `integration_service` | [api-ecosystem.md](api-ecosystem.md) |

Keeping them isolated lets each evolve without cross-surface regressions.

---

## 10. Request / data flow examples

### 10.1 Prompt → plan → execution

```
Operator POSTs /planner/intake with { prompt, project_id }
  └─ planner_service.intake_prompt(db, prompt, project_id)
       ├─ LLM call via core/llm.py (LiteLLM)
       ├─ Normalize + sanitize JSON plan (FM-020A)
       ├─ Create PlannerResult + Run + Task DAG (typed task_type per step)
       └─ Emit ExecutionEvent("plan.created")

Worker loop (apps/worker/worker/main.py) — every WORKER_POLL_INTERVAL seconds:
  └─ adaptive_orchestrator.run_cycle(db)
       ├─ handle rejections / retries / selection
       ├─ composition_service.resolve_agent_for_task(task)
       ├─ agent.build_handoff_context(task)
       ├─ agent.execute(task, context)  ──► LiteLLM ──► CostRecord
       ├─ artifact_service.create(...)
       ├─ event_service.record(...)
       └─ approval_service.create_if_gated(task, artifact)

Dashboard /dashboard/runs/[id]
  └─ lib/runs.ts GET /runs/{id}
     lib/tasks.ts GET /runs/{id}/tasks
     lib/stream.ts subscribe SSE /runs/{id}/events
```

### 10.2 Operator approves a gated artifact

```
Dashboard POST /approvals/{id}/decide { decision: "approve", comment }
  └─ approval_service.decide(db, approval_id, decision, comment, user_id)
       ├─ Update ApprovalRequest
       ├─ event_service.record("approval.decided")
       └─ unblock downstream tasks (move BLOCKED → READY)

Worker next cycle picks up the newly READY tasks.
```

### 10.3 Code-intelligence scan on push

```
CI → POST /api/v1/code-intelligence/{project_id}/scan { files: [...] }
  └─ code_graph_service.scan_file_dependencies(db, project_id, file_path, source)
       ├─ AST (Python) or regex (TS) parse → edges
       ├─ Upsert ModuleDependency rows
       └─ pattern_debt_service.scan_file_for_patterns(...)
            └─ CRITICAL/WARNING patterns auto-promoted to ProjectKnowledge
```

### 10.4 Scheduled report

```
background_scheduler (FastAPI lifespan, tick every 60s):
  └─ For each ScheduledReport whose cron matches now():
       ├─ execution_health_service.generate_report(...)
       ├─ notification_delivery_service.send(...)  (email / webhook / Slack)
       └─ Mark last_run_at
```

### 10.5 Architecture impact analysis

```
Operator POST /architecture/impact { target_node_id, scope }
  └─ impact_analysis_service.compute(db, project_id, target_node_id)
       ├─ BFS over architecture_edges (limit depth, score severity)
       ├─ Produce ChangeImpactAssessment row
       └─ If severity ∈ {HIGH, CRITICAL}:
           architecture_approval_service.auto_create(...)
```

---

## 11. Observability & operations

- **Metrics:** `core/metrics.py` exposes `/metrics` (Prometheus format). Counters for requests, latencies, LLM calls, cost, approvals.
- **Logging:** structured via `logging_middleware`. Every request has a unique `X-Request-ID`.
- **Audit:** `audit_export_service` produces JSON/CSV exports; `audit_log_service` persists privileged actions.
- **Tracing:** request IDs flow into events; run-level traceability via `traceability_service` and `operational_timeline_service`.
- **Scheduler health:** the cron inside the FastAPI lifespan logs tick times; scheduled reports record `last_run_at`.

---

## 12. Testing topology

| Layer | Tool | Count | Notes |
| ----- | ---- | ----- | ----- |
| Backend unit + integration | pytest + pytest-asyncio + httpx.AsyncClient | **1559 passing** | aiosqlite in-memory DB per test via `conftest.py`; no migrations run. |
| Frontend unit + integration | Vitest + Testing Library + jsdom | **231 passing / 37 files** | v8 coverage provider; thresholds soft; coverage artifact uploaded by CI. |
| Local CLI | pytest | **61 passing** | Standalone; validates `forgemind` commands end to end. |
| Lint | ruff (BE) / ESLint flat config (FE) | clean | `ruff check .` + `ruff format --check .` on every PR. |
| Type check | `tsc --noEmit` (FE) | clean | TS strict. |
| Build | `next build` (FE) | clean | — |

Playwright browser E2E, axe-based a11y, and visual snapshots are deferred maturity work (documented in [MILESTONE_SUMMARY.md](MILESTONE_SUMMARY.md#honest-residual-gaps)).

---

## 13. References

- Product-level framing: [../README.md](../README.md)
- Wave-by-wave delivery: [MILESTONE_SUMMARY.md](MILESTONE_SUMMARY.md)
- Developer workflow (local boot, tests, CI, migrations): [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md)
- Repository navigation map: [REPOSITORY_GUIDE.md](REPOSITORY_GUIDE.md)
- Production deploy: [DEPLOYMENT.md](DEPLOYMENT.md)
- Code intelligence: [code-intelligence.md](code-intelligence.md)
- Analytics & portfolio: [analytics-portfolio.md](analytics-portfolio.md)
- API, webhooks & ecosystem: [api-ecosystem.md](api-ecosystem.md)
- Technical debt tracker: [TECHNICAL_DEBT.md](TECHNICAL_DEBT.md)
- Per-milestone implementation logs: [agent-handoffs/](agent-handoffs/)
- V4 product plan: [../FORGEMIND_V4_ROADMAP.md](../FORGEMIND_V4_ROADMAP.md)
- V1-V3 product plan: [../FORGEMIND_ROADMAP.md](../FORGEMIND_ROADMAP.md)
# ForgeMind — System Architecture

> Last updated: 2026-04-20 (V4 closure — FM-181→210: 30 COMPLETE / 0 PARTIAL / 0 NOT STARTED)

---

## Overview

ForgeMind is an **operator-centered AI execution platform** that dynamically assembles specialized AI agents to plan, build, review, and test software projects — with human approval at every critical step.

```
┌──────────────────────────────────────────────────────────────────┐
│                     OPERATOR (User / API)                        │
│              "Build me a REST API with FastAPI..."                │
└──────────────┬───────────────────────────────────┬───────────────┘
               │                                   │
               ▼                                   ▼
┌──────────────────────────┐       ┌──────────────────────────────┐
│     Next.js 15 Frontend  │       │     FastAPI Backend (API)     │
│  React 19 · Tailwind CSS │◄─────►│  SQLAlchemy 2.0 · LiteLLM    │
│  App Router · shadcn/ui  │       │  Pydantic v2 · Alembic       │
└──────────────────────────┘       └──────────────┬───────────────┘
                                                   │
               ┌───────────────┬───────────────────┼───────────────┐
               ▼               ▼                   ▼               ▼
       ┌──────────┐    ┌──────────┐        ┌──────────┐    ┌──────────┐
       │PostgreSQL│    │  Redis   │        │  MinIO   │    │  LiteLLM │
       │   16     │    │    7     │        │ (Object) │    │ (LLM GW) │
       └──────────┘    └──────────┘        └──────────┘    └──────────┘
        Primary DB      Cache/Queue        File Storage    OpenAI/Anthropic/Google
```

---

## Tech Stack

### Backend

| Component   | Technology                    | Purpose                        |
| ----------- | ----------------------------- | ------------------------------ |
| Framework   | FastAPI (Python 3.12+, async) | REST API server                |
| ORM         | SQLAlchemy 2.0 (async)        | Database abstraction           |
| DB Driver   | asyncpg                       | Async PostgreSQL driver        |
| Migrations  | Alembic                       | Schema versioning              |
| Validation  | Pydantic v2                   | Request/response DTOs          |
| LLM Gateway | LiteLLM (>=1.50.0)            | Multi-provider LLM abstraction |
| Encryption  | cryptography (Fernet)         | Credential vault               |
| HTTP Client | httpx (async)                 | Connector operations           |

### Frontend

| Component     | Technology                 | Purpose                         |
| ------------- | -------------------------- | ------------------------------- |
| Framework     | Next.js 15 (App Router)    | Server-side rendering + routing |
| UI Library    | React 19                   | Component framework             |
| Styling       | Tailwind CSS 4             | Utility-first CSS               |
| Components    | shadcn/ui                  | Accessible UI components        |
| State         | Zustand, TanStack Query v5 | Client + server state           |
| Real-time     | Socket.IO Client           | Live updates                    |
| Code Editor   | Monaco Editor              | In-browser editing              |
| Visualization | Mermaid.js, React Flow     | Diagrams + DAG rendering        |
| Charts        | Recharts                   | Analytics dashboards            |

### Infrastructure

| Component        | Technology              | Purpose                        |
| ---------------- | ----------------------- | ------------------------------ |
| Database         | PostgreSQL 16           | Primary data store             |
| Cache/Queue      | Redis 7                 | Caching + Celery broker        |
| Object Storage   | MinIO                   | File/artifact storage          |
| Containerization | Docker + Docker Compose | Local development environment  |
| CI/CD            | GitHub Actions          | Automated testing + deployment |

### Testing

| Component   | Technology                   | Purpose                          |
| ----------- | ---------------------------- | -------------------------------- |
| Framework   | pytest (>=8.0.0)             | Test runner                      |
| Async       | pytest-asyncio               | Async test support               |
| HTTP Client | httpx (AsyncClient)          | API integration tests            |
| Test DB     | aiosqlite (in-memory SQLite) | Fast isolated test database      |
| Total Tests | **1157** (all passing)       | Backend + Local (through FM-180) |

---

## Database Models (27 Total + 14 New Enums)

All models defined in `apps/api/app/models/` and registered in `apps/api/app/db/base.py`.

```
┌─────────────────────────────────────────────────────────────────┐
│                        CORE ENTITIES                            │
├─────────────┬──────────────┬─────────────┬──────────────────────┤
│    User     │   Project    │     Run     │        Task          │
│  (users)    │  (projects)  │   (runs)    │      (tasks)         │
│             │  owner_id→   │ project_id→ │  run_id→, parent_id→ │
│             │    User      │   Project   │   depends_on[UUID]   │
└─────────────┴──────────────┴─────────────┴──────────────────────┘
┌─────────────────────────────────────────────────────────────────┐
│                   PLANNING & EXECUTION                          │
├──────────────┬──────────────┬──────────────┬────────────────────┤
│PlannerResult │   Artifact   │    Agent     │  ExecutionEvent    │
│(planner_     │ (artifacts)  │  (agents)    │(execution_events)  │
│  results)    │ project_id→  │ slug(unique) │ Append-only audit  │
│ run_id→(1:1) │ run_id→,     │ capabilities │ project/run/task→  │
│              │ task_id→     │ task_types   │                    │
└──────────────┴──────────────┴──────────────┴────────────────────┘
┌─────────────────────────────────────────────────────────────────┐
│                  GOVERNANCE & SECURITY                          │
├─────────────────┬──────────────────┬────────────────────────────┤
│ ApprovalRequest │ GovernancePolicy │       TrustScore           │
│(approval_       │(governance_      │   (trust_scores)           │
│  requests)      │  policies)       │ entity_type + entity_id    │
│ project/run/    │ trigger/action/  │ trust_score, confidence,   │
│ task/artifact→  │ rules(JSON)      │ risk_level, factors(JSON)  │
└─────────────────┴──────────────────┴────────────────────────────┘
┌─────────────────────────────────────────────────────────────────┐
│                 INTEGRATION & TRACKING                          │
├──────────────┬────────────────────┬──────────────┬──────────────┤
│  Connector   │ProjectConnectorLink│CredentialVault│  CostRecord │
│(connectors)  │(project_connector_ │(credential_   │(cost_records)│
│ slug(unique) │  links)            │  vault)       │ model_name,  │
│ capabilities │ readiness(enum)    │ env_key(uniq) │ tokens, USD  │
│ config(JSON) │ project→,connect→  │ connector→    │ project/run→ │
└──────────────┴────────────────────┴──────────────┴──────────────┘
┌─────────────────────────────────────────────────────────────────┐
│              INTELLIGENCE & REPLAY (FM-046–050)                  │
├────────────────┬───────────────┬────────────────┬───────────────┤
│ReplaySnapshot │CouncilSession │CouncilVote     │ProjectKnowl- │
│(replay_       │(council_      │(council_votes) │  edge         │
│ snapshots)    │ sessions)     │ session_id→    │(project_     │
│ task/run/     │ project_id→   │ agent_slug,    │ knowledge)   │
│ agent_slug,   │ topic,method  │ decision,conf  │ type, title, │
│ replay_hash   │ final_decision│ weight         │ relevance    │
└────────────────┴───────────────┴────────────────┴───────────────┘
┌─────────────────────────────────┐
│    EXTERNAL INTEGRATIONS           │
├─────────────────────────────────┤
│  RepoConnection                    │
│  (repo_connections)                │
│  project_id→, provider,            │
│  repo_url, status,                 │
│  default_branch, last_synced_at    │
└─────────────────────────────────┘
```

### Model Details

| #   | Model                      | Table                       | Key Columns                                                                                                                                                                                                                                                                                                                     | Relationships                                   |
| --- | -------------------------- | --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------- |
| 1   | **User**                   | `users`                     | id(UUID), email(unique), display_name, clerk_id, is_active                                                                                                                                                                                                                                                                      | 1:N → Projects                                  |
| 2   | **Project**                | `projects`                  | id(UUID), name, description, status(6 states), owner_id(FK), workspace_id(FK, nullable)                                                                                                                                                                                                                                         | N:1 → User/Workspace, 1:N → Runs/Artifacts      |
| 3   | **Run**                    | `runs`                      | id(UUID), run_number, status(6 states), trigger, project_id(FK)                                                                                                                                                                                                                                                                 | N:1 → Project, 1:N → Tasks, 1:1 → PlannerResult |
| 4   | **Task**                   | `tasks`                     | id(UUID), title, task_type, status(7 states), depends_on(UUID[]), run_id(FK), assigned_agent_slug, max_retries, retry_count                                                                                                                                                                                                     | N:1 → Run, self-ref parent/children             |
| 5   | **PlannerResult**          | `planner_results`           | id(UUID), run_id(FK, unique), overview, architecture_summary, recommended_stack(JSON), assumptions(JSON), next_steps(JSON)                                                                                                                                                                                                      | N:1 → Run                                       |
| 6   | **Artifact**               | `artifacts`                 | id(UUID), title, artifact_type(7 types), content, meta(JSON), version, project_id(FK), run_id(FK), task_id(FK)                                                                                                                                                                                                                  | N:1 → Project/Run/Task                          |
| 7   | **Agent**                  | `agents`                    | id(UUID), name, slug(unique), status(3 states), capabilities(JSON), supported_task_types(JSON)                                                                                                                                                                                                                                  | —                                               |
| 8   | **ApprovalRequest**        | `approval_requests`         | id(UUID), status(3 states), title, project_id(FK), run_id(FK), task_id(FK), decided_by, decision_comment                                                                                                                                                                                                                        | N:1 → Project/Run/Task/Artifact                 |
| 9   | **ExecutionEvent**         | `execution_events`          | id(UUID), event_type(10 types), summary, metadata\_(JSON), agent_slug                                                                                                                                                                                                                                                           | N:1 → Project/Run/Task/Artifact                 |
| 10  | **Connector**              | `connectors`                | id(UUID), name, slug(unique), connector_type, status(3 states), capabilities(JSON), config(JSON)                                                                                                                                                                                                                                | —                                               |
| 11  | **ProjectConnectorLink**   | `project_connector_links`   | id(UUID), project_id(FK), connector_id(FK), priority(3 levels), readiness(4 states), blocker_reason                                                                                                                                                                                                                             | N:1 → Project/Connector                         |
| 12  | **CredentialVault**        | `credential_vault`          | id(UUID), name, env_key(unique), connector_id(FK), status(4 states), secret_type, scopes(JSON), expires_at                                                                                                                                                                                                                      | N:1 → Connector/Project                         |
| 13  | **CostRecord**             | `cost_records`              | id(UUID), model_name, prompt_tokens, completion_tokens, total_tokens, cost_usd, caller                                                                                                                                                                                                                                          | N:1 → Project/Run/Task                          |
| 14  | **GovernancePolicy**       | `governance_policies`       | id(UUID), name, trigger(5 types), action(4 types), rules(JSON), project_id(FK), enabled, priority                                                                                                                                                                                                                               | —                                               |
| 15  | **TrustScore**             | `trust_scores`              | id(UUID), entity_type(3 types), entity_id, trust_score(0-1), confidence, risk_level(4 levels), factors(JSON)                                                                                                                                                                                                                    | —                                               |
| 16  | **ReplaySnapshot**         | `replay_snapshots`          | id(UUID), task_id(FK), run_id(FK), project_id(FK), agent_slug, input/output_snapshot(JSON), replay_hash(SHA256), is_replay                                                                                                                                                                                                      | N:1 → Task/Run/Project, self-ref original       |
| 17  | **CouncilSession**         | `council_sessions`          | id(UUID), project_id(FK), topic, status(5 states), decision_method(4 types), final_decision, decision_metadata(JSON)                                                                                                                                                                                                            | N:1 → Project, 1:N → CouncilVotes               |
| 18  | **CouncilVote**            | `council_votes`             | id(UUID), session_id(FK), agent_slug, decision(4 types), reasoning, confidence(0-1), weight(float)                                                                                                                                                                                                                              | N:1 → CouncilSession                            |
| 19  | **ProjectKnowledge**       | `project_knowledge`         | id(UUID), project_id(FK), knowledge_type(7 types), title, content, tags(JSON), relevance_score, usage_count                                                                                                                                                                                                                     | N:1 → Project                                   |
| 20  | **RepoConnection**         | `repo_connections`          | id(UUID), project_id(FK), provider(4 types), repo_url, repo_name, status(4 states), default_branch, last_synced_at, **+base_branch, target_branch, linked_paths(JSON), last_sync_status(enum), last_sync_error, last_synced_commit, provider_metadata(JSON), branch_mode(enum), target_branch_template, last_generated_branch** | N:1 → Project                                   |
| 21  | **ArchitectureNode**       | `architecture_nodes`        | id(UUID), workspace_id(FK), project_id(FK), repo_id(FK), node_type(12 types), key, name, path, language, metadata\_(JSON), source_type(3 types), status(3 states)                                                                                                                                                               | N:1 → Project/Workspace                         |
| 22  | **ArchitectureEdge**       | `architecture_edges`        | id(UUID), workspace_id(FK), project_id(FK), from_node_id(FK), to_node_id(FK), edge_type(10 types), confidence_score, metadata\_(JSON), source_type                                                                                                                                                                              | N:1 → Project, N:1 → ArchitectureNode×2         |
| 23  | **ArchitectureSnapshot**   | `architecture_snapshots`    | id(UUID), workspace_id(FK), project_id(FK), name, source, summary, node_count, edge_count, snapshot_data(JSON), generated_at                                                                                                                                                                                                    | N:1 → Project                                   |
| 24  | **ArchitectureDrift**      | `architecture_drifts`       | id(UUID), project_id(FK), drift_type, severity(4 levels), title, description, source_snapshot_id(FK), status(3 states), metadata\_(JSON)                                                                                                                                                                                        | N:1 → Project/Snapshot                          |
| 25  | **ArchitectureRule**       | `architecture_rules`        | id(UUID), project_id(FK), name, description, category(5 types), rule_config(JSON), enabled, severity                                                                                                                                                                                                                            | N:1 → Project                                   |
| 26  | **ArchitectureRuleResult** | `architecture_rule_results` | id(UUID), rule_id(FK), project_id(FK), status(pass/fail), message, details(JSON), violating_node_ids, violating_edge_ids                                                                                                                                                                                                        | N:1 → Rule/Project                              |
| 27  | **ChangeImpactAssessment** | `change_impact_assessments` | id(UUID), project_id(FK), target_node_id(FK), target_path, target_key, severity(5 levels), blast_radius, impacted_nodes(JSON), impacted_services(JSON), rationale, confidence_score                                                                                                                                             | N:1 → Project/Node                              |

### Status Enums

| Model                     | States                                                                                                  |
| ------------------------- | ------------------------------------------------------------------------------------------------------- |
| Project                   | DRAFT, PLANNING, ACTIVE, PAUSED, COMPLETED, FAILED                                                      |
| Run                       | PENDING, PLANNING, RUNNING, PAUSED, COMPLETED, FAILED                                                   |
| Task                      | PENDING, BLOCKED, READY, RUNNING, COMPLETED, FAILED, SKIPPED                                            |
| Agent                     | ACTIVE, INACTIVE, DEPRECATED                                                                            |
| Approval                  | PENDING, APPROVED, REJECTED                                                                             |
| Connector                 | AVAILABLE, CONFIGURED, UNAVAILABLE                                                                      |
| ConnectorLink readiness   | MISSING, CONFIGURED, BLOCKED, READY                                                                     |
| CredentialVault           | ACTIVE, EXPIRED, MISSING, REVOKED                                                                       |
| GovernancePolicy trigger  | TASK_TYPE, COST_THRESHOLD, ARTIFACT_TYPE, AGENT_ACTION, CUSTOM                                          |
| GovernancePolicy action   | REQUIRE_APPROVAL, AUTO_APPROVE, BLOCK, NOTIFY                                                           |
| TrustScore risk_level     | LOW, MEDIUM, HIGH, CRITICAL                                                                             |
| CouncilSession status     | CONVENED, DELIBERATING, DECIDED, DEADLOCKED, ESCALATED                                                  |
| CouncilSession method     | CONSENSUS, MAJORITY, SUPERMAJORITY, WEIGHTED                                                            |
| CouncilVote decision      | APPROVE, REJECT, ABSTAIN, MODIFY                                                                        |
| ProjectKnowledge type     | PATTERN, DECISION, LESSON_LEARNED, DEPENDENCY, BEST_PRACTICE, ARCHITECTURE, CONSTRAINT                  |
| RepoConnection provider   | GITHUB, GITLAB, BITBUCKET, LOCAL                                                                        |
| RepoConnection status     | CONNECTED, DISCONNECTED, ERROR, PENDING                                                                 |
| SyncStatus (FM-061)       | IDLE, SYNCING, SUCCESS, FAILED                                                                          |
| BranchMode (FM-066)       | DIRECT, FEATURE_BRANCH, REVIEW_BRANCH                                                                   |
| ChangeType (FM-063)       | CREATE, MODIFY, DELETE, CONCEPTUAL                                                                      |
| PatchFormat (FM-064)      | UNIFIED, SIDE_BY_SIDE, RAW                                                                              |
| ReadinessState (FM-064)   | INCOMPLETE, NEEDS_REVIEW, READY, BLOCKED                                                                |
| NodeType (FM-081)         | SERVICE, MODULE, ROUTE, MODEL, SCHEMA, MIDDLEWARE, UTILITY, CONFIG, TEST, MIGRATION, COMPONENT, PAGE    |
| EdgeType (FM-081)         | IMPORTS, CALLS, DEPENDS_ON, EXTENDS, IMPLEMENTS, COMPOSES, ROUTES_TO, READS_FROM, WRITES_TO, CONFIGURES |
| SourceType (FM-081)       | MANUAL, SCANNED, INFERRED                                                                               |
| NodeStatus (FM-081)       | ACTIVE, DEPRECATED, REMOVED                                                                             |
| DriftSeverity (FM-083)    | INFO, WARNING, ERROR, CRITICAL                                                                          |
| DriftStatus (FM-083)      | OPEN, RESOLVED, IGNORED                                                                                 |
| RuleCategory (FM-084)     | IMPORT_RULE, LAYER_RULE, DEPENDENCY_RULE, OWNERSHIP_RULE, BOUNDARY_RULE                                 |
| RuleResultStatus (FM-084) | PASS, FAIL                                                                                              |
| ImpactSeverity (FM-087)   | NONE, LOW, MEDIUM, HIGH, CRITICAL                                                                       |

---

## API Routes (33 Routers)

All routers registered in `apps/api/app/api/router.py` and mounted via `app.include_router(api_router)` in `main.py`.

### Route Map

| #   | Route File            | Prefix              | Key Endpoints                                                                                                                                                                                                                                                                                                              | Tags          |
| --- | --------------------- | ------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------- |
| 1   | `health.py`           | `/`                 | `GET /health`, `GET /health/ready`                                                                                                                                                                                                                                                                                         | health        |
| 2   | `projects.py`         | `/`                 | `POST /projects`, `GET /projects`, `GET /projects/{id}`, `PATCH /projects/{id}`                                                                                                                                                                                                                                            | projects      |
| 3   | `planner.py`          | `/planner`          | `POST /planner/intake`                                                                                                                                                                                                                                                                                                     | planner       |
| 4   | `planner_results.py`  | `/planner`          | Planner result queries                                                                                                                                                                                                                                                                                                     | planner       |
| 5   | `tasks.py`            | `/`                 | `GET /runs/{id}/tasks`, `GET /runs/{id}/tasks/ready`, `GET /tasks/{id}`, `PATCH /tasks/{id}/status`, `POST /tasks/{id}/claim`, `POST /tasks/{id}/complete`, `POST /tasks/{id}/fail`                                                                                                                                        | tasks         |
| 6   | `runs.py`             | `/`                 | `GET /projects/{id}/runs`, `GET /projects/{id}/runs/latest`, `GET /runs/{id}`                                                                                                                                                                                                                                              | runs          |
| 7   | `artifacts.py`        | `/`                 | `POST /projects/{id}/artifacts`, `GET /projects/{id}/artifacts`, `GET /artifacts/{id}`, `PATCH /artifacts/{id}`, `DELETE /artifacts/{id}`                                                                                                                                                                                  | artifacts     |
| 8   | `agents.py`           | `/`                 | `GET /agents`, `GET /agents/{id}`                                                                                                                                                                                                                                                                                          | agents        |
| 9   | `approvals.py`        | `/approvals`        | `GET /approvals`, `GET /approvals/{id}`, `POST /approvals/{id}/decide`                                                                                                                                                                                                                                                     | approvals     |
| 10  | `events.py`           | `/events`           | `GET /events`                                                                                                                                                                                                                                                                                                              | events        |
| 11  | `chat.py`             | `/`                 | `POST /runs/{id}/chat`                                                                                                                                                                                                                                                                                                     | chat          |
| 12  | `composition.py`      | `/`                 | `GET /composition/capabilities`, `GET /runs/{id}/composition`                                                                                                                                                                                                                                                              | composition   |
| 13  | `connectors.py`       | `/`                 | `GET /connectors`, `GET /runs/{id}/connectors/requirements`                                                                                                                                                                                                                                                                | connectors    |
| 14  | `memory.py`           | `/runs/{id}/memory` | `GET .../summary`, `GET .../failures`, `GET .../context`                                                                                                                                                                                                                                                                   | memory        |
| 15  | `credential_vault.py` | `/vault`            | Credential CRUD                                                                                                                                                                                                                                                                                                            | vault         |
| 16  | `retry.py`            | `/retry`            | Retry policy endpoints                                                                                                                                                                                                                                                                                                     | retry         |
| 17  | `run_lifecycle.py`    | `/lifecycle`        | `GET /lifecycle/runs/{id}/health`, `POST .../auto-complete`, `POST .../auto-fail`, `GET /lifecycle/runs/health/scan`                                                                                                                                                                                                       | lifecycle     |
| 18  | `costs.py`            | `/costs`            | `GET /costs/runs/{id}/summary`, `GET /costs/projects/{id}/summary`, `GET /costs/breakdown`, `GET /costs`                                                                                                                                                                                                                   | costs         |
| 19  | `governance.py`       | `/governance`       | `POST /governance/policies`, `GET /governance/policies`, `GET /governance/policies/{id}`, `PATCH ...`, `DELETE ...`                                                                                                                                                                                                        | governance    |
| 20  | `audit.py`            | `/audit`            | `GET /audit/export/json`, `GET /audit/export/csv`, `GET /audit/summary`                                                                                                                                                                                                                                                    | audit         |
| 21  | `trust.py`            | `/trust`            | `POST /trust/tasks/{id}/assess`, `POST /trust/runs/{id}/assess`, `GET /trust/runs/{id}/risk-summary`, `GET /trust/scores`, `GET /trust/{type}/{id}`                                                                                                                                                                        | trust         |
| 22  | `replay.py`           | `/`                 | `GET /runs/{id}/trace`, `GET /tasks/{id}/snapshots`, `POST /replay/snapshots`, `GET /replay/snapshots/{id}`, `POST /replay/snapshots/{id}/replay`, `GET /replay/compare`                                                                                                                                                   | replay        |
| 23  | `council.py`          | `/council`          | `POST /council/sessions`, `GET /council/sessions`, `GET /council/sessions/{id}`, `POST .../vote`, `POST .../resolve`, `POST .../escalate`                                                                                                                                                                                  | council       |
| 24  | `knowledge.py`        | `/`                 | `POST /projects/{id}/knowledge`, `GET /projects/{id}/knowledge`, `GET /knowledge/{id}`, `DELETE /knowledge/{id}`, `POST /runs/{id}/extract-knowledge`, `GET .../knowledge/context`                                                                                                                                         | knowledge     |
| 25  | `repos.py`            | `/`                 | `POST /projects/{id}/repos`, `GET /projects/{id}/repos`, `GET /repos/{id}`, `PATCH /repos/{id}`, `DELETE /repos/{id}`, `POST /repos/{id}/health`, `POST /repos/{id}/sync`, **`GET /repos/{id}/sync-status`, `POST /repos/{id}/refresh-sync`, `GET /repos/{id}/tree`, `GET /repos/{id}/file`, `GET /repos/{id}/file-meta`** | repos         |
| 26  | `workspaces.py`       | `/`                 | `POST /workspaces`, `GET /workspaces`, `GET /workspaces/{id}`, `PATCH /workspaces/{id}`                                                                                                                                                                                                                                    | workspaces    |
| 27  | `members.py`          | `/`                 | Workspace/project member CRUD                                                                                                                                                                                                                                                                                              | members       |
| 28  | `notifications.py`    | `/`                 | `POST /notifications`, `GET /notifications`, `POST /{id}/read`, `POST /read-all`, delivery config CRUD                                                                                                                                                                                                                     | notifications |
| 29  | `streaming.py`        | `/`                 | `GET /stream/events`, `GET /runs/{id}/stream`                                                                                                                                                                                                                                                                              | streaming     |
| 30  | `escalation.py`       | `/`                 | `POST /projects/{id}/escalation/rules`, `GET .../rules`, `GET .../events`, rule CRUD                                                                                                                                                                                                                                       | escalation    |
| 31  | `activity.py`         | `/`                 | Activity feed CRUD, presence CRUD, `GET /workspaces/{id}/activity`, `GET /users/{id}/context`                                                                                                                                                                                                                              | activity      |
| 32  | `code_ops.py`         | `/`                 | Code mapping, patch proposals, change reviews, branch strategies, PR drafts, repo action approvals, sandbox executions, **+PR draft generation, approval gate check, sandbox run**                                                                                                                                         | code_ops      |
| 33  | `architecture.py`     | `/`                 | Node CRUD (5), edge CRUD (3), graph query, neighbors, snapshots (2), topology map, drift detect/list/resolve/ignore (4), rules CRUD + evaluate (4), design doc, impact analysis, recommendations, approvals (2), health score — **27 endpoints**                                                                           | architecture  |

---

## Services Layer

All business logic lives in `apps/api/app/services/`. Routes are thin — they delegate to services.

### Core Services

| Service                    | Key Functions                                      | Purpose                              |
| -------------------------- | -------------------------------------------------- | ------------------------------------ |
| `project_service.py`       | create, get, list, update                          | Project CRUD                         |
| `planner_service.py`       | plan_from_prompt, normalize_plan                   | NL → structured plan via LiteLLM     |
| `task_service.py`          | get, list, update_status, get_ready, promote_ready | DAG-aware task state machine         |
| `execution_service.py`     | claim_task, complete_task, fail_task               | Task lifecycle orchestration         |
| `artifact_service.py`      | create, get, list, update (bumps version), delete  | Versioned artifact storage           |
| `agent_service.py`         | seed_default_agents, list, get, get_by_slug        | Agent registry (5 core agents)       |
| `approval_service.py`      | create, get, list, resolve                         | Human-in-the-loop approvals          |
| `event_service.py`         | emit_event, list_events                            | Append-only execution log            |
| `chat_service.py`          | detect_topics, build_context, chat_about_run       | AI-powered execution Q&A             |
| `composition_service.py`   | derive_capabilities, score_agent, compose_team     | Dynamic agent team assembly          |
| `connector_service.py`     | seed_connectors, list, get_requirements            | Connector registry + recommendations |
| `run_memory_service.py`    | get_summary, get_failures, build_context           | Cached run context for chat/agents   |
| `adaptive_orchestrator.py` | —                                                  | DAG scheduling + failure handling    |

### Advanced Services (FM-041–045 Infrastructure)

| Service                       | Key Functions                                     | Purpose                           |
| ----------------------------- | ------------------------------------------------- | --------------------------------- |
| `credential_vault_service.py` | Vault CRUD, rotation, expiry                      | Encrypted secret metadata         |
| `adaptive_retry_service.py`   | should_retry, get_delay, plan_reroute             | Smart retry with agent re-routing |
| `run_lifecycle_service.py`    | get_health, auto_complete, auto_fail, scan        | Run health + stuck detection      |
| `cost_tracking_service.py`    | record_usage, estimate_cost, summaries, breakdown | Per-call LLM cost tracking        |
| `governance_service.py`       | CRUD policies, evaluate_policies, custom rules    | Configurable approval rules       |
| `audit_export_service.py`     | export_json, export_csv, summary                  | Compliance-ready audit export     |
| `trust_scoring_service.py`    | assess_task, assess_run, risk_summary             | Heuristic trust/risk scoring      |

### Intelligence & Hardening Services (FM-046–050)

| Service                | Key Functions                                                                                                                                               | Purpose                                   |
| ---------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------- |
| `replay_service.py`    | capture_snapshot, get_execution_trace, replay, compare                                                                                                      | Deterministic execution replay            |
| `council_service.py`   | convene, cast_vote, resolve (4 methods), escalate                                                                                                           | Multi-agent council decisions             |
| `knowledge_service.py` | create, extract_from_run, get_context, list, delete                                                                                                         | Cross-run project knowledge base          |
| `repo_service.py`      | CRUD connections, check_health, sync, **refresh_sync_metadata, get_sync_status, get_file_tree, get_file_content, get_file_metadata, build_context_snippet** | External repo integration + file explorer |

### Collaboration & Real-Time Services (FM-051–060)

| Service                            | Key Functions                                                 | Purpose                             |
| ---------------------------------- | ------------------------------------------------------------- | ----------------------------------- |
| `workspace_service.py`             | create, get, list, update                                     | Workspace CRUD                      |
| `membership_service.py`            | add/remove workspace & project members, workspace validation  | RBAC membership management          |
| `notification_service.py`          | create, list, mark read, mark all read, delivery config CRUD  | In-app notification engine          |
| `notification_delivery_service.py` | deliver_notification, webhook/slack/email channels            | External notification delivery      |
| `escalation_service.py`            | create/list/update rules, trigger/list events                 | Escalation rule engine              |
| `activity_service.py`              | create/list activities, upsert/get/list presence              | Activity feed + user presence       |
| `authz_service.py`                 | check_workspace/project_permission, permission matrices       | RBAC authorization checks           |
| `stream_service.py`                | subscribe/unsubscribe run/global, publish, SSE generators     | In-memory pub/sub for real-time SSE |
| `user_activity_service.py`         | touch_user_activity, get_active_users, get_assignment_context | User presence & assignment tracking |

### Architecture Intelligence Services (FM-081–090)

| Service                              | Key Functions                                                                            | Purpose                              |
| ------------------------------------ | ---------------------------------------------------------------------------------------- | ------------------------------------ |
| `architecture_service.py`            | create/get/list/update/delete node, create/list/delete edge, graph, neighbors, snapshots | Architecture graph CRUD              |
| `topology_mapper_service.py`         | parse_python/typescript_imports, classify_layer, scan_directory, map_topology            | Filesystem → graph inference         |
| `drift_detection_service.py`         | detect_drift, list_drifts, resolve_drift, ignore_drift                                   | Architectural drift detection        |
| `architecture_rule_service.py`       | create_rule, list_rules, evaluate_rule, list_rule_results                                | Rule definition & evaluation         |
| `design_doc_service.py`              | generate_design_doc                                                                      | Markdown doc synthesis from graph    |
| `impact_analysis_service.py`         | analyse_impact                                                                           | BFS blast-radius computation         |
| `refactor_recommendation_service.py` | generate_recommendations                                                                 | Structural issue detection           |
| `architecture_approval_service.py`   | maybe_create_approval, list_architecture_approvals                                       | High-impact change approval workflow |
| `structural_health_service.py`       | compute_health_score                                                                     | Composite 0–100 health scoring       |

---

## Pydantic Schemas

All request/response models in `apps/api/app/schemas/`.

| Schema File          | Models                                                                                                                                                                                                                                                                                                                                                                                                                           | Purpose                        |
| -------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------ |
| `project.py`         | ProjectCreate, ProjectUpdate, ProjectRead, ProjectList                                                                                                                                                                                                                                                                                                                                                                           | Project DTOs                   |
| `task.py`            | TaskRead, TaskList, TaskStatusUpdate, ReadyTasksResponse, TaskClaimRequest, TaskCompleteRequest, TaskFailRequest                                                                                                                                                                                                                                                                                                                 | Task DTOs                      |
| `run.py`             | RunRead, RunList                                                                                                                                                                                                                                                                                                                                                                                                                 | Run DTOs                       |
| `artifact.py`        | ArtifactRead, ArtifactList, ArtifactCreate, ArtifactUpdate                                                                                                                                                                                                                                                                                                                                                                       | Artifact DTOs                  |
| `agent.py`           | AgentRead, AgentList                                                                                                                                                                                                                                                                                                                                                                                                             | Agent DTOs                     |
| `approval.py`        | ApprovalRead, ApprovalList, ApprovalCreate, ApprovalDecision                                                                                                                                                                                                                                                                                                                                                                     | Approval DTOs                  |
| `connector.py`       | ConnectorRead, ConnectorList, ConnectorRecommendation, ProjectConnectorLinkCreate/Read, ProjectReadinessSummary                                                                                                                                                                                                                                                                                                                  | Connector + readiness DTOs     |
| `execution_event.py` | ExecutionEventRead, ExecutionEventList                                                                                                                                                                                                                                                                                                                                                                                           | Event DTOs                     |
| `planner_result.py`  | PlannerResultRead, PlannerResponse                                                                                                                                                                                                                                                                                                                                                                                               | Planner output DTOs            |
| `prompt_intake.py`   | PromptIntakeRequest, PromptIntakeResponse                                                                                                                                                                                                                                                                                                                                                                                        | NL prompt intake DTOs          |
| `cost.py`            | CostRecordRead, CostRecordList                                                                                                                                                                                                                                                                                                                                                                                                   | Cost tracking DTOs             |
| `governance.py`      | GovernancePolicyRead/List/Create/Update                                                                                                                                                                                                                                                                                                                                                                                          | Governance DTOs                |
| `trust.py`           | TrustScoreRead, TrustScoreList                                                                                                                                                                                                                                                                                                                                                                                                   | Trust score DTOs               |
| `replay.py`          | ReplaySnapshotRead/Create/List, ReplayRequest, ReplayCompare, ExecutionTrace                                                                                                                                                                                                                                                                                                                                                     | Replay & trace DTOs            |
| `council.py`         | CouncilSessionRead/List, ConveneCouncilRequest, CastVoteRequest, CouncilVoteRead, CouncilDecisionResult                                                                                                                                                                                                                                                                                                                          | Council decision DTOs          |
| `knowledge.py`       | ProjectKnowledgeRead/Create/List, KnowledgeExtractionResult, KnowledgeContext                                                                                                                                                                                                                                                                                                                                                    | Knowledge base DTOs            |
| `repo.py`            | RepoConnectionRead/Create/Update/List, RepoBranchInfo, RepoSyncResult                                                                                                                                                                                                                                                                                                                                                            | Repo integration DTOs          |
| `workspace.py`       | WorkspaceCreate/Update/Read/List                                                                                                                                                                                                                                                                                                                                                                                                 | Workspace DTOs                 |
| `membership.py`      | WorkspaceMemberCreate/Update/Read/List, ProjectMemberCreate/Update/Read/List                                                                                                                                                                                                                                                                                                                                                     | Membership DTOs                |
| `notification.py`    | NotificationCreate/Read/List, DeliveryConfigCreate/Read/List                                                                                                                                                                                                                                                                                                                                                                     | Notification DTOs              |
| `escalation.py`      | EscalationRuleCreate/Update/Read/List, EscalationEventRead/List                                                                                                                                                                                                                                                                                                                                                                  | Escalation DTOs                |
| `activity.py`        | ActivityFeedEntryCreate/Read, ActivityFeedList, PresenceUpdate/Read/List                                                                                                                                                                                                                                                                                                                                                         | Activity & presence DTOs       |
| `code_ops.py`        | CodeMapping/PatchProposal/ChangeReview/BranchStrategy/PRDraft/RepoActionApproval/SandboxExecution CRUD schemas, **PRDraftGenerateRequest, SandboxRunRequest**                                                                                                                                                                                                                                                                    | Code operations DTOs           |
| `architecture.py`    | ArchitectureNodeCreate/Read/List/Update, ArchitectureEdgeCreate/Read/List, ArchitectureSnapshotRead/List, ArchitectureGraphRead, NeighborRead, TopologyMapRequest, TopologySummary, ArchitectureDriftRead/List, ArchitectureRuleCreate/Read/List, ArchitectureRuleResultRead/List, DesignDocRead/List, ImpactAnalysisRequest, ChangeImpactAssessmentRead, RefactorRecommendation/List, HealthScoreDetails, StructuralHealthScore | Architecture intelligence DTOs |

---

## Database Migrations (22 Total)

All migrations in `apps/api/alembic/versions/` using Alembic.

| #   | Revision | Description                        | Tables Added/Changed                                                                                                                                                                                                                                                                              |
| --- | -------- | ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | 0001     | Initial schema                     | users, projects, runs, tasks, agents, artifacts, planner_results                                                                                                                                                                                                                                  |
| 2   | 0002     | Planner results                    | planner_results table                                                                                                                                                                                                                                                                             |
| 3   | 0003     | Artifact storage                   | artifacts table with versioning                                                                                                                                                                                                                                                                   |
| 4   | 0004     | Agent registry                     | agents table with capabilities                                                                                                                                                                                                                                                                    |
| 5   | 0005     | Task execution columns             | +assigned_agent_slug, +error_message on tasks                                                                                                                                                                                                                                                     |
| 6   | 0006     | Approval requests                  | approval_requests table                                                                                                                                                                                                                                                                           |
| 7   | 0007     | Execution events                   | execution_events table (append-only)                                                                                                                                                                                                                                                              |
| 8   | 0008     | Connector registry                 | connectors table                                                                                                                                                                                                                                                                                  |
| 9   | 0009     | Connector readiness (FM-041)       | project_connector_links table                                                                                                                                                                                                                                                                     |
| 10  | 0010     | Credential vault (FM-042)          | credential_vault table                                                                                                                                                                                                                                                                            |
| 11  | 0011     | Retry columns (FM-043)             | +max_retries, +retry_count on tasks                                                                                                                                                                                                                                                               |
| 12  | 0012     | Cost tracking                      | cost_records table                                                                                                                                                                                                                                                                                |
| 13  | 0013     | Governance policies                | governance_policies table                                                                                                                                                                                                                                                                         |
| 14  | 0014     | Trust scores                       | trust_scores table                                                                                                                                                                                                                                                                                |
| 15  | 0015     | Replay snapshots (FM-046)          | replay_snapshots table                                                                                                                                                                                                                                                                            |
| 16  | 0016     | Council tables (FM-047A)           | council_sessions + council_votes tables                                                                                                                                                                                                                                                           |
| 17  | 0017     | Project knowledge (FM-048)         | project_knowledge table                                                                                                                                                                                                                                                                           |
| 18  | 0018     | Repo connections (FM-049)          | repo_connections table                                                                                                                                                                                                                                                                            |
| 19  | 0019     | Collaboration + code ops           | workspaces, workspace_members, project_members, notifications, notification_delivery_configs, escalation_rules, escalation_events, activity_feed_entries, user_presences, code_mappings, patch_proposals, change_reviews, branch_strategies, pr_drafts, repo_action_approvals, sandbox_executions |
| 20  | 0020     | Project workspace FK (FM-051)      | +workspace_id (nullable FK) on projects table                                                                                                                                                                                                                                                     |
| 21  | 0021     | Code ops enhancements (FM-061–069) | +10 columns on repo_connections, +5 on artifacts, +5 on patch_proposals, +4 on change_reviews, +4 on sandbox_executions; 5 new enum types                                                                                                                                                         |
| 22  | 0022     | Architecture tables (FM-081–090)   | architecture_nodes, architecture_edges, architecture_snapshots, architecture_drifts, architecture_rules, architecture_rule_results, change_impact_assessments; 11 new enum types                                                                                                                  |

---

## Application Lifecycle

### Startup Sequence

```
FastAPI app created
  → register_error_handlers() — global HTTP/validation/unhandled error handlers
  → CORS middleware added (allow_origins from settings)
  → RateLimitMiddleware added (100 req/60s per IP, production only)
  → RequestLoggingMiddleware added (timing + X-Request-ID headers)
  → All 35 routers mounted via api_router
  → Lifespan startup:
      → seed_default_agents() — creates 5 core agents
        (Planner, Architect, Coder, Reviewer, Tester)
  → Server ready on port 8000
```

### Shutdown Sequence

```
Lifespan shutdown:
  → engine.dispose() — close all DB connections
```

### Request Flow

```
Client Request
  → FastAPI routing → Route handler (thin)
    → Service layer (business logic + DB)
      → SQLAlchemy async session
        → PostgreSQL
    → Pydantic schema serialization
  → JSON Response
```

---

## Docker Compose Services

| Service      | Image                   | Port                       | Purpose               | Health Check              |
| ------------ | ----------------------- | -------------------------- | --------------------- | ------------------------- |
| **postgres** | postgres:16-alpine      | 5432                       | Primary database      | pg_isready                |
| **redis**    | redis:7-alpine          | 6379                       | Cache + Celery broker | redis-cli ping            |
| **minio**    | minio/minio:latest      | 9000 (API), 9001 (Console) | Object storage        | —                         |
| **api**      | ./apps/api (Dockerfile) | 8000                       | FastAPI backend       | depends_on postgres+redis |
| **web**      | ./apps/web (Dockerfile) | 3000                       | Next.js frontend      | depends_on api            |

### Service Dependencies

```
web → api → postgres (healthy)
              → redis (healthy)
         → minio (optional)
```

---

## Configuration

Settings defined in `apps/api/app/core/config.py` via Pydantic `BaseSettings`:

| Setting             | Default                 | ENV Variable        | Purpose                           |
| ------------------- | ----------------------- | ------------------- | --------------------------------- |
| app_env             | "development"           | APP_ENV             | Environment mode                  |
| debug               | true                    | DEBUG               | Debug mode                        |
| secret_key          | —                       | SECRET_KEY          | App secret (required)             |
| api_host            | "0.0.0.0"               | API_HOST            | Bind address                      |
| api_port            | 8000                    | API_PORT            | Bind port                         |
| cors_origins        | "http://localhost:3000" | CORS_ORIGINS        | Allowed origins (comma-separated) |
| postgres_host       | "localhost"             | POSTGRES_HOST       | DB host                           |
| postgres_port       | 5432                    | POSTGRES_PORT       | DB port                           |
| postgres_db         | "forgemind"             | POSTGRES_DB         | DB name                           |
| postgres_user       | "forgemind"             | POSTGRES_USER       | DB user                           |
| postgres_password   | —                       | POSTGRES_PASSWORD   | DB password (required)            |
| database_url        | (auto-built)            | DATABASE_URL        | Full async DB URL                 |
| redis_host          | "localhost"             | REDIS_HOST          | Redis host                        |
| redis_port          | 6379                    | REDIS_PORT          | Redis port                        |
| redis_url           | (auto-built)            | REDIS_URL           | Full Redis URL                    |
| planner_model       | "gpt-4o"                | PLANNER_MODEL       | LLM model for planning            |
| planner_temperature | 0.4                     | PLANNER_TEMPERATURE | LLM temperature                   |
| planner_max_tokens  | 4096                    | PLANNER_MAX_TOKENS  | LLM max output tokens             |
| openai_api_key      | ""                      | OPENAI_API_KEY      | OpenAI key                        |
| anthropic_api_key   | ""                      | ANTHROPIC_API_KEY   | Anthropic key                     |
| google_api_key      | ""                      | GOOGLE_API_KEY      | Google key                        |

---

## Test Structure

### Backend Tests (`apps/api/tests/`)

| Test File                            | Focus                                | Coverage                                                                                                                                       |
| ------------------------------------ | ------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| `test_health.py`                     | Health endpoints                     | Liveness + readiness                                                                                                                           |
| `test_projects.py`                   | Project CRUD                         | Create, list, get, update                                                                                                                      |
| `test_planner.py`                    | Planner service                      | NL prompt → plan, fallback stub                                                                                                                |
| `test_tasks.py`                      | Task DAG                             | State transitions, ready-task, DAG                                                                                                             |
| `test_runs.py`                       | Run management                       | Creation, listing, status                                                                                                                      |
| `test_agents.py`                     | Agent registry                       | Seed, list, get                                                                                                                                |
| `test_artifacts.py`                  | Artifact storage                     | Versioning, CRUD, filtering                                                                                                                    |
| `test_approvals.py`                  | Approval workflow                    | Create, list, approve/reject                                                                                                                   |
| `test_events.py`                     | Event logging                        | Emit, list, filter                                                                                                                             |
| `test_chat.py`                       | Execution chatbot                    | Topic detection, context, fallback                                                                                                             |
| `test_composition.py`                | Agent composition                    | Team assembly, scoring                                                                                                                         |
| `test_connectors.py`                 | Connector registry                   | List, recommendations, readiness                                                                                                               |
| `test_memory.py`                     | Execution memory                     | Summaries, failure analysis                                                                                                                    |
| `test_schemas.py`                    | Pydantic schemas                     | Validation                                                                                                                                     |
| `test_fm046_050.py`                  | Infrastructure features              | Lifecycle, cost, governance, audit, trust (46 tests)                                                                                           |
| `test_fm046_050_v2.py`               | FM-046–050 new features              | Replay, council, knowledge, repos, hardening (34 tests)                                                                                        |
| `test_workspaces.py`                 | Workspace CRUD                       | Create, list, get, update, delete workspaces                                                                                                   |
| `test_members.py`                    | Membership management                | Workspace + project member CRUD                                                                                                                |
| `test_streaming.py`                  | SSE streaming                        | Event generator output + route registration                                                                                                    |
| `test_notifications.py`              | Notification system                  | Create, list, mark read, delivery config                                                                                                       |
| `test_escalation.py`                 | Escalation engine                    | Rules CRUD + escalation events                                                                                                                 |
| `test_activity.py`                   | Activity & presence                  | Activity feed + user presence upsert                                                                                                           |
| `test_code_ops.py`                   | Code operations                      | Mappings, patches, reviews, branches, PRs, approvals, sandbox                                                                                  |
| `test_code_ops_enhanced.py`          | FM-061–069 enhancements              | Sync metadata, file tree, artifact mapping, patches, reviews, PR drafts, approval gates, sandbox runner (24 tests)                             |
| `test_fm081_090_architecture.py`     | FM-081–090 architecture intelligence | Graph CRUD, topology mapping, drift detection, rules, design docs, impact analysis, recommendations, approvals, RBAC, health score (~69 tests) |
| `test_fm161_170_knowledge_search.py` | FM-161–170 knowledge & search        | Search indexing, similarity, knowledge CRUD, conventions, versioning, recommendations, comparisons, integrity check (~45 tests)                |

### Evaluation Tests (`apps/api/evals/`)

| Test File               | Focus                            |
| ----------------------- | -------------------------------- |
| `test_quality_evals.py` | 23 benchmark quality evaluations |
| `eval_benchmarks.json`  | Benchmark data                   |

### Test Counts

| Category                           | Tests   |
| ---------------------------------- | ------- |
| Core tests (FM-001–040)            | 105     |
| Quality evals (FM-045)             | 23      |
| Infrastructure tests (pre-release) | 23      |
| FM-046–050 feature tests           | 34      |
| FM-051–069 feature tests           | 67      |
| FM-061–069 enhanced tests          | 24      |
| FM-071–080 feature tests           | 110     |
| FM-081–090 architecture tests      | 69      |
| FM-161–170 knowledge & search      | 45      |
| Quality evals                      | 27      |
| **Total**                          | **527** |

---

## Project Structure

```
forgemind/
├── apps/
│   ├── api/                          # FastAPI backend
│   │   ├── app/
│   │   │   ├── api/
│   │   │   │   ├── router.py         # Main router (35 routers)
│   │   │   │   └── routes/           # Route handlers (33 files)
│   │   │   ├── core/
│   │   │   │   ├── config.py         # Settings (Pydantic BaseSettings)
│   │   │   │   ├── auth.py           # JWT authentication (prod)
│   │   │   │   ├── auth_stub.py      # Auth stub (dev fallback)
│   │   │   │   ├── rate_limit.py     # Token bucket rate limiter
│   │   │   │   ├── logging_middleware.py # Request logging + timing
│   │   │   │   ├── error_handlers.py # Global error handlers
│   │   │   │   └── llm.py            # LiteLLM wrapper
│   │   │   ├── db/
│   │   │   │   ├── base.py           # Model registry (43 models)
│   │   │   │   └── session.py        # Async engine + session factory
│   │   │   ├── models/               # SQLAlchemy models (27 files)
│   │   │   ├── schemas/              # Pydantic schemas (24 files)
│   │   │   ├── services/             # Business logic (40+ services)
│   │   │   └── main.py              # FastAPI app factory
│   │   ├── alembic/
│   │   │   └── versions/             # 22 migrations
│   │   ├── tests/                    # 482 tests (25 files)
│   │   ├── evals/                    # 23 eval tests
│   │   ├── alembic.ini
│   │   └── requirements.txt
│   └── web/                          # Next.js 15 frontend
│       ├── app/                      # App Router pages
│       ├── components/               # React components
│       ├── lib/                      # API clients + utilities
│       └── types/                    # TypeScript types
├── docs/
│   ├── ARCHITECTURE.md               # ← This file
│   ├── MILESTONE_SUMMARY.md          # Milestone completion summary
│   ├── TECHNICAL_DEBT.md             # Known tech debt (TD-001–TD-009)
│   └── agent-handoffs/               # Per-task implementation records
├── docker-compose.yml                # 5 services
├── FORGEMIND_ROADMAP.md              # Original roadmap (legacy)
├── FORGEMIND_ROADMAP_V2.md           # Expanded roadmap (legacy)
├── FORGEMIND_ROADMAP_V3.md           # Current roadmap (FM-071–090)
└── README.md                         # Project overview + Mermaid diagrams
```

---

## Security Architecture

| Area             | Implementation                                                                   |
| ---------------- | -------------------------------------------------------------------------------- |
| Authentication   | JWT via python-jose (`get_current_user_id()` dependency); dev-mode stub fallback |
| Authorization    | Owner-based (extensible to RBAC)                                                 |
| Rate Limiting    | Token bucket per IP (100 req/60s default, production only)                       |
| Request Logging  | Middleware with timing, unique X-Request-ID headers per request                  |
| Error Handling   | Global handlers for HTTP, validation, and unhandled exceptions (consistent JSON) |
| Secret Storage   | Env-key references (no plaintext secrets in DB)                                  |
| CORS             | Configurable allowed origins                                                     |
| Input Validation | Pydantic model validation on all inputs                                          |
| State Machine    | Task transitions validated in service layer                                      |
| Audit            | Append-only ExecutionEvent table                                                 |
| Governance       | Configurable policies with 5 triggers and 4 actions, custom JSON rules engine    |
| Trust            | Heuristic scoring per task/run/artifact                                          |

---

## Key Architectural Patterns

1. **Thin Routes, Fat Services** — Route handlers validate input and delegate to services. Services own all business logic and DB operations.

2. **Async-First** — All DB operations use SQLAlchemy 2.0 async sessions with asyncpg. No blocking I/O in the request path.

3. **DAG-Based Task Orchestration** — Tasks form a dependency graph. Tasks transition PENDING → BLOCKED → READY → RUNNING → COMPLETED/FAILED/SKIPPED. Ready-task promotion runs automatically after status changes.

4. **Capability-Based Agent Composition** — Instead of fixed agent pipelines, the system scores agents against required capabilities and assembles optimal teams per project.

5. **Append-Only Audit** — ExecutionEvents are never modified or deleted. Full replay capability for any run.

6. **Policy-Driven Governance** — Approval gates are configurable via GovernancePolicy, not hardcoded in service logic.

7. **Context-Rich AI** — Chat and agent services receive assembled context from `run_memory_service` (tasks, artifacts, approvals, events, failures) for informed decision-making.

---

## Completed: Platform Intelligence & Hardening (FM-046–050)

| ID      | Feature                             | Description                                                                           | Status      |
| ------- | ----------------------------------- | ------------------------------------------------------------------------------------- | ----------- |
| FM-046  | Run Replay & Trace Inspection       | Snapshot capture, deterministic SHA-256 hashing, replay, side-by-side diff comparison | ✅ Complete |
| FM-047A | Multi-Agent Council Engine          | 4 decision methods (consensus/majority/supermajority/weighted), deadlock escalation   | ✅ Complete |
| FM-047  | Policy-Based Approval Rules         | Multi-trigger evaluation, custom JSON rules engine, council integration               | ✅ Complete |
| FM-048  | Multi-Run Memory & Knowledge Base   | Auto-extraction from runs, 7 knowledge types, relevance scoring, context injection    | ✅ Complete |
| FM-049  | External Repo/Workspace Integration | GitHub/GitLab/Bitbucket/local providers, health checks, sync operations               | ✅ Complete |
| FM-050  | Production Hardening Pass           | JWT auth, token bucket rate limiter, request logging, global error handlers           | ✅ Complete |

> **All 50 tasks across 10 milestones are complete. 185 tests passing.**

---

## Completed: Team Collaboration & Real-Time (FM-051–060)

| ID     | Feature                              | Description                                                                             | Status      |
| ------ | ------------------------------------ | --------------------------------------------------------------------------------------- | ----------- |
| FM-051 | Workspace Model & Multi-Tenant Shell | Workspace entity with slug, status, owner, settings JSON; CRUD API                      | ✅ Complete |
| FM-052 | Workspace Member Roles               | WorkspaceMember with 5 roles (owner/admin/operator/reviewer/viewer); unique constraints | ✅ Complete |
| FM-053 | Project-Level Member & Permissions   | ProjectMember with 4 roles + is_approver/is_reviewer flags; per-project RBAC            | ✅ Complete |
| FM-054 | SSE Streaming Foundation             | Server-Sent Events heartbeat endpoint for real-time updates                             | ✅ Complete |
| FM-055 | In-App Notification Engine           | Notification model with 12 types, 4 priority levels; mark read/read-all                 | ✅ Complete |
| FM-056 | Notification Delivery Config         | Per-user delivery channel config (slack/email/webhook) with status management           | ✅ Complete |
| FM-057 | Escalation Rule Engine               | Configurable escalation rules with 6 triggers, 5 actions, cooldown; event logging       | ✅ Complete |
| FM-058 | Activity Feed & Audit Extension      | ActivityFeedEntry with 15 activity types, project/workspace scoping, resource linking   | ✅ Complete |
| FM-059 | User Presence Tracking               | UserPresence model with status, current resource tracking, last_seen; upsert semantics  | ✅ Complete |

---

## Completed: Repository & Code Execution (FM-061–069)

| ID     | Feature                       | Description                                                                              | Status      |
| ------ | ----------------------------- | ---------------------------------------------------------------------------------------- | ----------- |
| FM-061 | Code Mapping Model            | CodeMapping linking artifacts to file paths with language detection and metadata         | ✅ Complete |
| FM-062 | Patch Proposal Model          | PatchProposal with diff content, target branch, 6 statuses, rationale tracking           | ✅ Complete |
| FM-063 | Change Review Workflow        | ChangeReview with 3 decisions (approved/changes_requested/commented) linked to patches   | ✅ Complete |
| FM-064 | Branch Strategy Configuration | BranchStrategy with base/pattern/PR target, auto-create flag, config JSON per project    | ✅ Complete |
| FM-065 | PR Draft Composer             | PRDraft with 5 statuses, reviewer/checklist/linked artifact JSON, source/target branches | ✅ Complete |
| FM-066 | Repo Action Approval Gate     | RepoActionApproval with 5 action types, decision workflow, context tracking              | ✅ Complete |
| FM-067 | Sandbox Execution Engine      | SandboxExecution with command, environment, timeout, 5 statuses, stdout/stderr/exit_code | ✅ Complete |
| FM-068 | Code Ops REST API             | Full REST API for all code operations models (~20 endpoints)                             | ✅ Complete |
| FM-069 | Code Ops Integration Tests    | Comprehensive test coverage for all code operations (17 tests)                           | ✅ Complete |

> **All 69 tasks across 12 milestones are complete. 252 tests passing.**

---

## Completed: Productization & Frontend Parity (FM-071–080)

| ID     | Feature                                   | Description                                                                            | Status      |
| ------ | ----------------------------------------- | -------------------------------------------------------------------------------------- | ----------- |
| FM-071 | Advanced Frontend Parity I                | Dashboard pages for Trust, Replay, Council, Governance                                 | ✅ Complete |
| FM-072 | Advanced Frontend Parity II               | Dashboard pages for Costs, Audit, Knowledge, Credential Vault                          | ✅ Complete |
| FM-073 | Platform Admin Frontend Parity            | Dashboard pages for Connectors, Agents, Settings; sidebar links enabled                | ✅ Complete |
| FM-074 | Real Authentication Integration           | Production JWT auth replacing dev stub; real login/logout; token verification          | ✅ Complete |
| FM-075 | Route-Level RBAC Enforcement Hardening    | Auth on all 164 non-public endpoints; permission matrix; consistent error semantics    | ✅ Complete |
| FM-076 | CI/CD Pipeline and Quality Gates          | GitHub Actions: Python lint, pytest, TS typecheck, ESLint, build verification          | ✅ Complete |
| FM-077 | Real-Time UX Integration                  | Frontend SSE consumption, live run updates, reconnect handling                         | ✅ Complete |
| FM-078 | Observability and Runtime Instrumentation | Prometheus metrics, request latency/error counters, worker metrics, request IDs        | ✅ Complete |
| FM-079 | Monorepo Package Extraction               | 4 real packages: @forgemind/types, forgemind-utils, forgemind-security, forgemind-core | ✅ Complete |
| FM-080 | Production Deployment Foundation          | Multi-stage Docker builds, prod compose, nginx reverse proxy, deployment docs          | ✅ Complete |

> **All 80 tasks across 20 milestones are complete. 413 tests passing.**

---

## Completed: Architecture Intelligence (FM-081–090)

| ID     | Feature                         | Description                                                                            | Status      |
| ------ | ------------------------------- | -------------------------------------------------------------------------------------- | ----------- |
| FM-081 | Architecture Graph Foundation   | 7 models, 9 enums, 28 schemas, graph CRUD service, 12 endpoints, migration 0022        | ✅ Complete |
| FM-082 | Topology Mapping Service        | Filesystem scanner, Python/TS import parsing, layer classification, topology summary   | ✅ Complete |
| FM-083 | Drift Detection Engine          | Snapshot comparison, convention drift, cross-layer violations, resolve/ignore workflow | ✅ Complete |
| FM-084 | Architecture Rule Engine        | 5 rule categories, evaluators, pass/fail results with violating node/edge tracking     | ✅ Complete |
| FM-085 | Architecture Dashboard Frontend | Dashboard page, 12-function API client, TypeScript types, sidebar nav link             | ✅ Complete |
| FM-086 | Design Doc Synthesis            | Markdown generation from graph, drift records, rule violations                         | ✅ Complete |
| FM-087 | Change Impact Analysis          | BFS reverse traversal, blast radius, severity escalation, ChangeImpactAssessment model | ✅ Complete |
| FM-088 | Refactor Recommendations        | God-module, circular dep, isolated node, drift/violation backlog detection             | ✅ Complete |
| FM-089 | Architecture Approval Workflow  | Auto-approval for HIGH/CRITICAL impacts, architecture approval listing                 | ✅ Complete |
| FM-090 | Structural Health Score         | Composite 0–100 score: coverage, drift penalty, compliance, isolation ratio            | ✅ Complete |

> **All 90 tasks across 21 milestones are complete. 482 tests passing.**

---

## Completed: ForgeMind Local — Developer Workstation Mode (FM-091–100)

ForgeMind Local is a **standalone CLI package** (`apps/local/`) that provides offline developer workstation capabilities without requiring the backend API, database, or any infrastructure.

### Package Structure

```
apps/local/
├── pyproject.toml              # forgemind-local package config
├── forgemind_local/
│   ├── __init__.py             # v0.1.0
│   ├── config.py               # FM-091: LocalConfig, YAML I/O, repo detection
│   ├── cli.py                  # FM-091+: Click CLI (20+ commands)
│   ├── repo_index.py           # FM-092: file tree walk, language classification
│   ├── local_chat.py           # FM-093: keyword search, optional LLM
│   ├── local_exec.py           # FM-094: bounded execution, safety policies
│   ├── local_patch.py          # FM-095: git patch generation & management
│   ├── local_pr.py             # FM-096: PR preparation from git diff
│   ├── ide_integration.py      # FM-097: VS Code tasks.json generation
│   ├── local_state.py          # FM-098: cache, sync queue, mode management
│   └── local_handoff.py        # FM-099: export/import zip snapshots
└── tests/
    └── test_local.py           # FM-100: 53 tests across 9 classes
```

### Key Design Decisions

- **No backend dependency** — operates entirely from `.forgemind/` directory per repo
- **Offline-first** — all features work without network; LLM integration is optional
- **shell=True execution** — appropriate for local dev tool; 16 blocked patterns provide defense-in-depth
- **Sync queue** — stores events for future offline→online bridge (consumer not yet implemented)
- **Non-destructive import** — snapshot import won't overwrite existing config

| ID     | Feature                          | Description                                                                          | Status      |
| ------ | -------------------------------- | ------------------------------------------------------------------------------------ | ----------- |
| FM-091 | Local Foundation & Config        | LocalConfig dataclass, YAML I/O, detect_repo_root, .forgemind/ directory structure   | ✅ Complete |
| FM-092 | Repo Indexing & Manifest         | File tree walk, 30+ language extensions, entrypoint/build-file detection, JSON cache | ✅ Complete |
| FM-093 | Local Chat Over Codebase         | Keyword search over manifest, file snippets, optional LiteLLM, offline fallback      | ✅ Complete |
| FM-094 | Local Execution Sandbox          | 16 blocked patterns, 35 safe prefixes, 3 policies, subprocess timeout, JSON logs     | ✅ Complete |
| FM-095 | Patch Generation & Management    | Git diff patches, metadata tracking, apply with --check, reject workflow             | ✅ Complete |
| FM-096 | PR Preparation                   | Git diff analysis, 11 subsystem categories, risk detection, dynamic checklist        | ✅ Complete |
| FM-097 | IDE Integration                  | VS Code tasks.json with 10 ForgeMind tasks, idempotent merge                         | ✅ Complete |
| FM-098 | State Management & Sync Queue    | TTL cache, offline event queue, mode management (offline/hybrid/remote)              | ✅ Complete |
| FM-099 | Handoff Snapshots                | Export/import zip bundles, non-destructive import, bundle inspection                 | ✅ Complete |
| FM-100 | Hardening, Tests & Documentation | 53 tests, 9 test classes, documentation across all tracking files                    | ✅ Complete |

> **All 100 tasks across 22 milestones are complete. 535 tests passing.**

---

## Future Architecture: V5 (FM-211 → FM-250)

> **Status:** Not yet implemented. See [FORGEMIND_V5_ROADMAP.md](../FORGEMIND_V5_ROADMAP.md) for the full vision.

V5 evolves ForgeMind into a **dynamic multi-agent orchestration platform** adding:

- **Master Orchestration Service** — interprets tasks and deploys specialized sub-agents dynamically
- **Redis Event Bus** — inter-agent communication and messaging layer
- **Council Deliberation** — structured proposal-debate-resolution protocol for complex decisions
- **Graph Memory** — persistent knowledge graph for structured reasoning and relationship storage
- **FAIR Workflow Engine** — explainable scoring with confidence/policy signals for workflow selection

### Milestone 23 — SPEC-Driven Lifecycle (FM-101 → FM-110)

**New Models:**

- `ProjectConstitution` — persistent AI behavior rulebook per project (preamble, constraints, goals, anti-goals)

**New Services:**

- `constitution_service` — upsert/delete/get constitution, prompt injection helpers
- `spec_service` — structured SPEC generation with constitution context, LLM or stub fallback
- `plan_artifact_service` — PLAN creation linked to SPEC, markdown/JSON export
- `slash_command_service` — parse and route `/fm.*` commands from chat
- `spec_plan_validation_service` — 8-rule validation gate (4 ERROR + 4 WARNING) before PLANNING→RUNNING
- `spec_plan_approval_service` — approval requests for SPEC/PLAN artifacts, lifecycle gating
- `adr_service` — architecture graph queries, ADR-001/002/003 section generation for plans

**New Routes:**

- `/api/projects/{id}/constitution` — CRUD for project constitutions
- `/api/runs/{id}/lifecycle/*` — SPEC approval, PLAN approval, validation, PLAN export
- `/api/runs/{id}/chat` — slash command integration

**Lifecycle Flow:**

```
PENDING → SPECIFYING → PLANNING → RUNNING → COMPLETED
         ↑ /fm.specify  ↑ /fm.plan   ↑ validation gate
         └─ SPEC artifact └─ PLAN artifact └─ approval gate
```

| ID     | Feature                        | Description                                                                         | Status          |
| ------ | ------------------------------ | ----------------------------------------------------------------------------------- | --------------- |
| FM-101 | SPEC Artifact & SPECIFYING     | ArtifactType.SPEC/PLAN, RunStatus.SPECIFYING, spec_artifact_id FK, transition gates | ✅ Complete     |
| FM-102 | Project Constitution           | ProjectConstitution ORM, schemas, service, REST routes, prompt injection            | ✅ Complete     |
| FM-103 | Constitution UI & Governance   | ConstitutionEditor component, API client, TypeScript types, audit events            | ✅ Complete     |
| FM-104 | Slash Command Parsing          | /fm.specify, /fm.plan, /fm.tasks, /fm.implement — regex parser, execute routing     | ✅ Complete     |
| FM-105 | Structured SPEC Generation     | LLM-powered with constitution, stub fallback, SPEC_CREATED event                    | ✅ Complete     |
| FM-106 | PLAN Artifact Export & Linking | PLAN→SPEC FK, markdown export, JSON export endpoints                                | ✅ Complete     |
| FM-107 | ADR-Aware Planning             | Architecture graph queries, ADR sections, plan enrichment                           | ✅ Complete     |
| FM-108 | Spec-to-Plan Validation        | 8 rules (4 ERROR + 4 WARNING), lifecycle gate PLANNING→RUNNING                      | ✅ Complete     |
| FM-109 | Approval Integration           | SPEC/PLAN approval requests, idempotent, opt-in gating                              | ✅ Complete     |
| FM-110 | Tests & Hardening              | 60 tests, 12 test classes, 542 total passing, full doc closure                      | \u2705 Complete |

> **All 110 tasks across 23 milestones are complete. 542 tests passing.**

---

### Milestone 24 — Phase Routing, Templates & Project Bootstrapping (FM-111 → FM-120)

**New Models:**

- `PhaseAgentProfile` — per-project phase-to-agent assignment (6 workflow phases, unique per project/phase)
- `ProjectTemplate` — reusable project presets with JSON config (constitution, governance, phase profiles, spec/plan defaults)
- `ConstitutionSuggestion` — knowledge-driven constitution improvement proposals (PENDING/ACCEPTED/REJECTED/EXPIRED)

**New Services:**

- `phase_agent_profile_service` — CRUD for phase-agent assignments, agent validation, bulk set
- `project_template_service` — template CRUD, 4 built-in templates with real content, idempotent seeding
- `template_inheritance_service` — 3-tier governance resolution (system → template → project), template application
- `constitution_suggestion_service` — 5 suggestion rules, signal gathering from runs/tasks/knowledge, generate/resolve

**Modified Services:**

- `composition_service` — added `resolve_agent_for_phase()` for phase-aware agent routing
- `project_service` — template-based project creation with `template_id`
- `spec_service` — template spec_defaults injection into LLM prompts
- `plan_artifact_service` — template plan_defaults injection into LLM prompts
- `adaptive_orchestrator` — phase-aware agent re-routing on auto-retry

**New Routes:**

- `/api/projects/{id}/phase-agent-profiles` — CRUD for phase-agent assignments
- `/api/templates` — list, get, create, update project templates
- `/api/projects/{id}/constitution-suggestions` — generate, list, resolve suggestions

**Worker Integration:**

- Worker task loop uses `resolve_agent_for_phase()` before capability-based fallback
- Adaptive orchestrator uses phase-aware routing for auto-retry agent selection

| ID     | Feature                            | Description                                                                      | Status      |
| ------ | ---------------------------------- | -------------------------------------------------------------------------------- | ----------- |
| FM-111 | Phase Agent Profile Data Model     | PhaseAgentProfile ORM, WorkflowPhase enum, CRUD service, schemas, routes         | ✅ Complete |
| FM-112 | Phase-Aware Routing                | resolve_agent_for_phase in composition_service, wired into worker + orchestrator | ✅ Complete |
| FM-113 | Phase Agent Profile UI             | PhaseProfileEditor component, per-phase dropdowns, project detail integration    | ✅ Complete |
| FM-114 | Project Template Model & Seeding   | 4 built-in templates with real constitutions, governance, spec/plan defaults     | ✅ Complete |
| FM-115 | Template-Based Project Creation    | project_service accepts template_id, seeds constitution + phase profiles         | ✅ Complete |
| FM-116 | Template Inheritance               | 3-tier governance resolution: system → template → project                        | ✅ Complete |
| FM-117 | Constitution Suggestions           | 5 signal-driven rules, generate/accept/reject, never auto-applied                | ✅ Complete |
| FM-118 | Spec/Plan Bootstrap from Templates | Template spec_defaults and plan_defaults injected into LLM prompts               | ✅ Complete |
| FM-119 | Local Mode Template Support        | Local CLI status/exec/handoff consume template_slug and phase_profiles           | ✅ Complete |
| FM-120 | Hardening & Tests                  | 38 tests, 580 total passing, full documentation closure                          | ✅ Complete |

> **All 120 tasks across 24 milestones are complete. 593 tests passing.**

---

## FM-121 to FM-130 — Execution Memory, Checkpoints & Delivery Artifacts — ✅ COMPLETE

Execution checkpoint infrastructure with persistent state snapshots, resume semantics, delivery artifact generation, lifecycle traceability, and release confidence scoring.

### New Models & Services

- **ExecutionCheckpoint** — ORM model with CheckpointType enum (manual, auto_phase, pre_approval, pre_delivery, post_validation), JSON columns for status/artifact/validation/approval/architecture snapshots
- **ExecutionCheckpointService** — CRUD, auto-checkpoint, resume-from-checkpoint with ownership validation
- **DeliveryArtifactService** — Generates implementation summaries, changelogs, release notes, completion bundles, and review packages
- **TraceabilityService** — Computes directed lifecycle graph (run → prompt → artifact → task → checkpoint)
- **RunMemoryEnrichmentService** — Extracts structured memory (objectives, blockers, confidence factors, delivery notes)
- **ReleaseConfidenceService** — Weighted 0–100 scoring with 8 signals, band classification, blocking factors, suggested actions

### Routes

- `POST/GET /runs/{id}/checkpoints` — Create and list checkpoints
- `GET /runs/{id}/checkpoints/latest` — Latest checkpoint
- `GET /checkpoints/{id}` — Get by ID
- `POST /runs/{id}/checkpoints/{id}/resume` — Resume from checkpoint
- `POST /runs/{id}/delivery-artifacts?kind=...` — Generate delivery artifacts
- `POST /runs/{id}/review-package` — Assemble review package
- `GET /runs/{id}/traceability` — Lifecycle traceability graph
- `GET /runs/{id}/memory` — Run memory enrichment
- `GET /runs/{id}/confidence` — Release confidence score

### Local CLI

- `forgemind checkpoint list/save` — Manage local checkpoints
- `forgemind confidence` — Local heuristic confidence scoring
- `forgemind review` — Local review summary

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

> **All 140 tasks across 26 milestones are complete. 730 tests passing.**

---

## Wave 9: FM-131–FM-140 — Release Operations & Deployment Confidence

> Versioned release packages, deployment environments with tiered gates,
> deployment readiness evaluation, release gate orchestration, rollback
> readiness assessment, post-release reporting, and operational timeline.

| Wave | Milestone | Tasks         | Theme                                                             | Status      |
| ---- | --------- | ------------- | ----------------------------------------------------------------- | ----------- |
| 9    | 26        | FM-131–FM-140 | Release operations, deployment confidence, operational governance | ✅ Complete |

---

## Wave 10: FM-141–FM-150 — Collaboration, UX & Team Coordination (✅ COMPLETE)

> Threaded comments, @mentions, activity feed, saved views, user presence,
> run annotations, task assignment, approval delegation, notification center,
> project overview. 10/10 complete (Passes 1–7 closed all gaps).

| ID     | Feature                          | Status      |
| ------ | -------------------------------- | ----------- |
| FM-141 | Threaded Comments                | ✅ Complete |
| FM-142 | @Mentions & Notification Routing | ✅ Complete |
| FM-143 | Unified Activity Feed            | ✅ Complete |
| FM-144 | Saved Views & Filters            | ✅ Complete |
| FM-145 | User Presence & Online Status    | ✅ Complete |
| FM-146 | Collaborative Run Annotations    | ✅ Complete |
| FM-147 | Task Assignment & Workload       | ✅ Complete |
| FM-148 | Approval Delegation & Batch      | ✅ Complete |
| FM-149 | Notification Digest & Center     | ✅ Complete |
| FM-150 | Project Overview Dashboard       | ✅ Complete |

---

## Wave 11: FM-151–FM-160 — GitHub & CI Integration (9/10 COMPLETE, 1 DEFERRED)

> GitHub app installation, webhook ingestion, PR tracking, CI pipeline status,
> issue sync, branch strategy, code review routing, diff intelligence.
> 9/10 complete (Passes 1–7 closed all gaps), 1 deferred. **Zero outbound GitHub API calls.**

| ID     | Feature                                | Status                      |
| ------ | -------------------------------------- | --------------------------- |
| FM-151 | GitHub App Installation & Linking      | ✅ Complete                 |
| FM-152 | Webhook Ingestion & Events             | ✅ Complete                 |
| FM-153 | PR Auto-Creation & Tracking            | ✅ Complete                 |
| FM-154 | CI Pipeline Status Integration         | ✅ Complete                 |
| FM-155 | Issue Sync                             | ✅ Complete                 |
| FM-156 | Branch Strategy & Merge Readiness      | ✅ Complete                 |
| FM-157 | Code Review Routing                    | ✅ Complete                 |
| FM-158 | Commit & Diff Intelligence             | ✅ Complete                 |
| FM-159 | VS Code Extension Foundation           | ⏸️ Deferred (separate repo) |
| FM-160 | Hardening: Rate Limiter, Retry, Replay | ✅ Complete                 |

---

## Wave 12: FM-161–FM-170 — Search, Knowledge & Organizational Memory (10/10 COMPLETE)

> Full-text search, knowledge base, conventions engine, artifact versioning,
> recommendations, run comparison, cross-project discovery. 10/10 complete.
> FM-162 upgraded with real embedding vectors (litellm), cosine similarity, hybrid ranking.

| ID     | Feature                                     | Status                                                              |
| ------ | ------------------------------------------- | ------------------------------------------------------------------- |
| FM-161 | Full-Text Search Index                      | ✅ Complete (LIKE-based)                                            |
| FM-162 | Semantic Search with Embeddings             | ✅ Complete (litellm embeddings, cosine similarity, hybrid ranking) |
| FM-163 | Knowledge Base — Decision & Pattern Library | ✅ Complete                                                         |
| FM-164 | Project Templates V2                        | ✅ Complete                                                         |
| FM-165 | Cross-Project Search & Discovery            | ✅ Complete                                                         |
| FM-166 | Execution Replay & Comparison               | ✅ Complete                                                         |
| FM-167 | Organizational Context & Conventions Engine | ✅ Complete                                                         |
| FM-168 | Artifact Versioning & History               | ✅ Complete                                                         |
| FM-169 | Smart Recommendations Engine                | ✅ Complete                                                         |
| FM-170 | Knowledge & Search Tests & Hardening        | ✅ Complete (45 tests)                                              |

### Wave 13 — Enterprise Governance, Permissions & Compliance (FM-171 → FM-180) (✅ COMPLETE)

> Immutable audit trail, governance policy evaluation engine, compliance report generation,
> IP allowlisting, data retention policies, workspace governance settings, role introspection,
> SSO configuration, secret resolution & rotation lifecycle.
> 10/10 complete (Passes 1–7 closed all gaps).

| ID     | Feature                                    | Status                                    |
| ------ | ------------------------------------------ | ----------------------------------------- |
| FM-171 | Workspace Governance Metadata              | ✅ Complete                               |
| FM-172 | RBAC V2 — Role Introspection               | ✅ Complete                               |
| FM-173 | Comprehensive Audit Log                    | ✅ Complete                               |
| FM-174 | Policy Engine — Automated Rule Enforcement | ✅ Complete                               |
| FM-175 | SSO Configuration Model                    | ✅ Complete                               |
| FM-176 | Data Retention & Lifecycle Policies        | ✅ Complete                               |
| FM-177 | Compliance Reporting & Export              | ✅ Complete (5 report types, JSON/CSV)    |
| FM-178 | IP Allowlisting & Access Controls          | ✅ Complete (middleware wired, IPv4/IPv6) |
| FM-179 | Secrets Resolution & Lifecycle             | ✅ Complete                               |
| FM-180 | Enterprise Governance Tests & Hardening    | ✅ Complete (70+ tests, docs corrected)   |

**New models:** AuditLog, GovernancePolicyEvaluation, ComplianceReport, IpAllowlistEntry, RetentionPolicy, SSOConfiguration
**New services:** audit_log_service, governance_engine_service, compliance_report_service, ip_allowlist_service, retention_policy_service, sso_configuration_service
**New routes:** 25+ endpoints under `/enterprise-governance` (audit log, policy eval, compliance, IP allowlist, retention, governance settings, role introspection, SSO config)
**New middleware:** IPAllowlistMiddleware — enforces workspace-scoped IP restrictions
**Test file:** `test_fm171_180_enterprise_governance.py` (70+ tests)

---

_This document reflects the architecture as of the latest commit on `main`. FM-141–FM-180: 39 COMPLETE, 0 PARTIAL, 1 DEFERRED (FM-159) out of 40 milestones. 1157 tests passing._
