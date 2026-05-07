# ForgeMind — System Architecture

> **Last updated:** 2026-05-07 (V5 closure — FM-211 → FM-250 delivered; Waves 17–20 complete).
> **Scope:** this document is the authoritative architectural reference for the ForgeMind platform. It complements the product-framing in [../README.md](../README.md) and the wave-by-wave delivery log in [MILESTONE_SUMMARY.md](MILESTONE_SUMMARY.md).

---

## 1. System overview

ForgeMind is a multi-agent AI execution platform organized as a monorepo with four independent-but-cooperating process types:

| Process       | Path           | Role                                                                                                                                 |
| ------------- | -------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| **API**       | `apps/api/`    | FastAPI + SQLAlchemy 2 async. Owns all business logic. Every external surface (frontend, SDK, webhooks, local CLI sync) enters here. |
| **Web**       | `apps/web/`    | Next.js 15 App Router dashboard. Pure view layer; calls the API over HTTP/SSE.                                                       |
| **Worker**    | `apps/worker/` | Long-running polling loop. Claims ready tasks, dispatches agents, persists artifacts.                                                |
| **Local CLI** | `apps/local/`  | Standalone `forgemind` Python CLI for developer workstations. Offline-first, optional server sync.                                   |

Plus shared code under [`packages/`](../packages/) (`agents`, `connectors`, `core`, `orchestrator`, `schemas`, `security`, `utils`, `verification`) and a background scheduler that lives inside the API's FastAPI lifespan.

```
┌────────────────────────┐   HTTP / SSE   ┌──────────────────────────────────┐
│   Next.js 15 Dashboard │◄──────────────►│   FastAPI Backend (apps/api)     │
│   25 dashboard routes  │                │   65 routers · 123 services      │
│   34 lib modules       │                │   48 SQLAlchemy 2 model files    │
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

Confirmed working local model: Ollama/Mistral-7B (port 11435, PLANNER_MODEL=ollama/mistral).
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

### 2.2 Route organization (65 routers)

All routers are registered in [apps/api/app/api/router.py](../apps/api/app/api/router.py) and mounted as a single `api_router` in `main.py`.

| Group                         | Routers                                                                                                                     |
| ----------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| Platform core                 | `health`, `projects`, `planner`, `planner_results`, `tasks`, `runs`, `artifacts`, `agents`, `events`                        |
| Execution intelligence        | `chat`, `composition`, `memory`, `retry`, `run_lifecycle`                                                                   |
| Governance                    | `approvals`, `governance`, `audit`, `trust`, `costs`, `council`, `enterprise_governance`                                    |
| Collaboration (Wave 10)       | `workspaces`, `members`, `streaming`, `notifications`, `escalation`, `activity`, `comments`, `saved_views`, `collaboration` |
| Code ops                      | `repos`, `code_ops`, `annotations`                                                                                          |
| Security                      | `auth`, `credential_vault`, `metrics`                                                                                       |
| Architecture intelligence     | `architecture`                                                                                                              |
| Constitution / templates      | `constitution`, `constitution_suggestions`, `phase_agent_profiles`, `project_templates`                                     |
| Lifecycle                     | `checkpoints`, `delivery`, `release_ops`, `replay`                                                                          |
| GitHub (Wave 11)              | `github_integration`                                                                                                        |
| Search / knowledge (Wave 12)  | `search_knowledge`, `knowledge`, `connectors`                                                                               |
| Code intelligence (Wave 14)   | `code_intelligence`                                                                                                         |
| Analytics (Wave 15)           | `analytics`                                                                                                                 |
| Public ecosystem (Wave 16)    | `api_ecosystem`                                                                                                             |
| Observability (Wave 17–18)    | `telemetry`, `slow_query`, `cache_admin`, `model_router`, `agent_memory`, `llm_cost`, `stream_output`, `tool_registry`      |
| Platform intelligence (W19–20)| `slo_targets`, `anomaly_events`, `agent_performance`, `model_experiments`, `budget_forecasts`, `cron_triggers`              |
| Platform ops (Wave 19–20)     | `resource_quotas`, `digest_schedules`, `pii_patterns`                                                                       |

Health is mounted at the root (`/health`, `/health/ready`, `/health/live`, `/health/dependencies`). Everything else is either mounted at the module's own prefix or under `/api/v1/` for the Wave 16+ public surface. The OpenAPI spec is validated for completeness in `TestOpenAPISpecCompleteness` (schemas populated, every path has an operation, `api-v1` tag present on versioned routes, spec fully JSON-serializable).

### 2.3 Service layer (123 services)

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

**Observability (Wave 17–18)** — `telemetry_service` (OpenTelemetry tracing, X-Trace-ID middleware), `slow_query_service` (slow-query ring-buffer logger), `cache_service` (Redis hot-path caching layer), `model_router` (multi-model LLM routing with fallback chain), `agent_memory_service` (AgentMemoryEntry long-term memory), `llm_cost_service` (per-run LLM call cost summary), `stream_output_service` (SSE Redis pub/sub agent output), `tool_registry` (WebSearch / ReadFile / WriteFile / RunCommand tools).

**Platform intelligence (Wave 19–20)** — `slo_service` (SLOTarget + SLOPeriodResult — track compliance windows), `anomaly_service` (AnomalyEvent detection with severity/type enums), `agent_performance_service` (AgentPerformanceSnapshot — period-based agent stats), `model_experiment_service` (ModelExperiment — A/B cost and quality scoring), `budget_forecast_service` (BudgetForecast — burn-rate projection and confidence), `cron_trigger_service` (CronTrigger + CronTriggerLog — scheduled pipeline execution).

**Platform ops (Wave 19–20)** — `resource_quota_service` (ResourceQuota — per-workspace limits: runs, projects, cost, API calls, storage), `digest_schedule_service` (DigestSchedule — user daily/weekly summary config), `pii_detection_service` (PIIPattern — regex/keyword/ML artifact scanning).

### 2.4 Data / persistence model (48 model files)

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

**Agent intelligence (Wave 17–18)** — `agent_intelligence` (AgentMemoryEntry for long-term cross-run memory; LLMCallLog for per-call cost tracking; PlanRevision for autonomous re-plan history; ReviewComment for inline PR review annotations; SecurityFinding for agent-detected security issues).

**Scheduling (Wave 19–20)** — `scheduling` (CronTrigger — workspace-scoped scheduled pipelines with cron expressions; CronTriggerLog — per-execution log with status, run linkage, error capture).

**Platform intelligence (Wave 19–20)** — `platform_intelligence` (SLOTarget — per-metric SLO with threshold/window/enabled; SLOPeriodResult — computed compliance over a window; AnomalyEvent — typed/severity anomaly records with raw_data JSON; AgentPerformanceSnapshot — period-based agent stats including tasks_completed, p95_latency, success_rate; ModelExperiment — A/B experiment with cost_a/b, latency_a/b, quality scores, winner; BudgetForecast — burn-rate projection with days_remaining and confidence).

**Platform ops (Wave 19–20)** — `platform_ops` (ResourceQuota — per-workspace limits for concurrent runs, projects, monthly cost, API rate, storage; DigestSchedule — per-user daily/weekly digest with include flags for costs/approvals/security; PIIPattern — regex/keyword/ML scan rules with category, severity, enabled).

### 2.5 Migrations

Alembic chain lives in [`apps/api/alembic/versions/`](../apps/api/alembic/versions/). The current head is `wave19_20_platform_intelligence` (chained from `wave17_18_agent_intelligence` → `fm161_170_search_knowledge`).

**Critical migration notes:**
- All UUID primary keys and foreign keys must use `postgresql.UUID(as_uuid=True)` — not `sa.String(36)`. Mixing types causes `DatatypeMismatchError` on FK creation.
- SQLAlchemy Enum types must be declared explicitly in migrations as `sa.Enum("val1","val2", name="type_name")` — not the Python Enum class directly.
- The Wave 19–20 migration (`2026_05_07_0031`) was a full rewrite to fix 12+ column/type mismatches between the original migration and the authoritative models. Models are always the source of truth.

Tests **do not** run migrations. `tests/conftest.py` calls `Base.metadata.create_all()` against an in-memory SQLite, which is why CI stays green through migration issues. See [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md#migrations) for the local-runtime bootstrap workaround.

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

| Integration          | Service                                                                                                            | Notes                                                                                      |
| -------------------- | ------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------ |
| LLM providers        | `core/llm.py` (LiteLLM)                                                                                            | Any OpenAI / Anthropic / Google / Ollama / Azure-compatible model. Cost recorded per call. Set `PLANNER_MODEL=ollama/mistral` + `OLLAMA_API_BASE=http://127.0.0.1:11435` for local Mistral. |
| GitHub               | `github_client`, `github_installation_service`, `github_rate_limiter`, `issue_sync_service`, `ci_pipeline_service` | GitHub App installs, rate-limited client, issue sync, PR status pipeline.                  |
| Slack                | `integration_service` + webhook connectors                                                                         | Outbound notifications via `notification_delivery_service`.                                |
| Email                | `email_service`                                                                                                    | Digest delivery + escalation notifications.                                                |
| PagerDuty            | `integration_service` via webhook                                                                                  | High-severity escalations.                                                                 |
| External repos       | `repo_service`                                                                                                     | GitHub, GitLab, Bitbucket, local.                                                          |
| S3 / MinIO           | via `boto3`-compatible client                                                                                      | Artifact bodies, release packages.                                                         |
| Webhooks (outbound)  | `webhook_service`, `webhook_connector_service`                                                                     | Configurable endpoints with delivery tracking.                                             |
| SSO                  | `sso_configuration_service`                                                                                        | Wave 13 enterprise governance.                                                             |
| Public API consumers | `api_key_service` + `/api/v1/`                                                                                     | SHA-256 hashed keys, tier-based rate limits.                                               |

---

## 8. SDK — `apps/api/app/sdk/`

Ships generated clients for third-party developers.

| File                            | Purpose                                                     |
| ------------------------------- | ----------------------------------------------------------- |
| `python_client.py`              | Synchronous + async Python client.                          |
| `typescript_client.ts`          | TypeScript client with fetch-based transport.               |
| `openapi-generator-config.yaml` | Config for regenerating clients from the live OpenAPI spec. |
| `pyproject.toml`                | Packaging metadata for the Python client.                   |
| `package.json`                  | Packaging metadata for the TS client.                       |

The OpenAPI spec itself is auto-generated by FastAPI and validated by `TestOpenAPISpecCompleteness` (see [code-intelligence.md](code-intelligence.md) and [api-ecosystem.md](api-ecosystem.md)).

---

## 9. Analytics, code intelligence, and ecosystem separation

These three surfaces live behind three distinct API prefixes and three distinct doc files, and share no tables:

| Surface                             | Router                       | Primary models         | Primary services                                                                                                                              | Doc                                              |
| ----------------------------------- | ---------------------------- | ---------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------ |
| **Code intelligence** (Wave 14)     | `/api/v1/code-intelligence/` | `code_intelligence.py` | `code_graph_service`, `pattern_debt_service`, `flakiness_complexity_service`                                                                  | [code-intelligence.md](code-intelligence.md)     |
| **Analytics & portfolio** (Wave 15) | `/api/v1/analytics/`         | `analytics_metrics.py` | `execution_health_service`, `velocity_quality_service`, `dashboard_alert_service`, `project_overview_service`, `operational_timeline_service` | [analytics-portfolio.md](analytics-portfolio.md) |
| **API ecosystem** (Wave 16)         | `/api/v1/` (public surface)  | `api_ecosystem.py`     | `api_key_service`, `webhook_service`, `webhook_connector_service`, `integration_service`                                                      | [api-ecosystem.md](api-ecosystem.md)             |

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

### 10.4 Scheduled analytics report

```
background_scheduler (FastAPI lifespan, tick every 60s):
  └─ For each ScheduledReport whose cron matches now():
       ├─ execution_health_service.generate_report(...)
       ├─ notification_delivery_service.send(...)  (email / webhook / Slack)
       └─ Mark last_run_at
```

### 10.5 Cron-triggered pipeline (Wave 19–20)

```
CronTrigger fires (background_scheduler tick every 60s, matches cron_expression):
  └─ cron_trigger_service.fire(db, trigger)
       ├─ Resolve project_id + prompt from trigger config
       ├─ planner_service.plan_from_prompt(db, prompt, owner_id)
       │    ├─ _generate_plan() → LLM or stub
       │    ├─ Create Project + ProjectMember(LEAD) + Run + Tasks
       │    └─ Create PlannerResult
       └─ CronTriggerLog(status="success", run_id=run.id)
```

> **Note (2026-05-07 fix):** `plan_from_prompt` previously skipped the `ProjectMember` enrollment step, causing every downstream run/task lookup to return "Not a member of this project". Fixed in `apps/api/app/services/planner_service.py` — the `ProjectMember(role=LEAD)` row is now inserted immediately after the project flush, mirroring `project_service.create_project()`.

### 10.7 Architecture impact analysis

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

| Layer                       | Tool                                        | Count                      | Notes                                                                    |
| --------------------------- | ------------------------------------------- | -------------------------- | ------------------------------------------------------------------------ |
| Backend unit + integration  | pytest + pytest-asyncio + httpx.AsyncClient | **1,691 passing**          | aiosqlite in-memory DB per test via `conftest.py`; no migrations run.    |
| Frontend unit + integration | Vitest + Testing Library + jsdom            | **254 passing / 37 files** | v8 coverage provider; thresholds soft; coverage artifact uploaded by CI. |
| Local CLI                   | pytest                                      | **61 passing**             | Standalone; validates `forgemind` commands end to end.                   |
| Lint                        | ruff (BE) / ESLint flat config (FE)         | clean                      | `ruff check .` + `ruff format --check .` on every PR.                    |
| Type check                  | `tsc --noEmit` (FE)                         | clean                      | TS strict.                                                               |
| Build                       | `next build` (FE)                           | clean                      | —                                                                        |

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

