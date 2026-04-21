# ForgeMind — Milestone Summary

> **Last updated:** 2026-04-20. V4 feature-complete. **FM-181 → FM-210: 30 COMPLETE / 0 PARTIAL / 0 NOT STARTED.** Program total: FM-001 → FM-210 delivered across 16 waves.

---

## Current state

ForgeMind is a governed, multi-agent AI execution platform. It plans software work from natural language, runs it through specialized agents with adaptive orchestration, records every step as auditable artifacts and events, and surfaces the result in an operator-centered dashboard — with approval gates, cost tracking, trust scoring, execution replay, council deliberation, workspace collaboration, GitHub integration, search & memory, enterprise governance, code intelligence, analytics, a public API, webhooks, and a standalone local CLI.

**Validated at HEAD `2a4e8fc`:** backend **1559 / 1559** pytest passing · frontend **231 / 231** Vitest passing across 37 files · local CLI **61 / 61** passing · lint/format/typecheck/build clean on every surface · CI green on `main` (3 jobs).

---

## QA hardening closeout — 2026-04-20 (commit `7fc9ad5`)

Four concentrated QA passes landed on top of the feature-complete FM-001 → FM-210 tree, followed by a housekeeping batch.

| Pass                           | Commit    | Focus                                                                                                                                                                                                             |
| ------------------------------ | --------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| High-priority behavioural gaps | `a84f793` | Dashboard, forms, operator polish                                                                                                                                                                                 |
| Residual branches              | `01bf361` | Dashboard home, FM-035 polish, prompt intake / project create edge cases                                                                                                                                          |
| Medium-priority                | `b274442` | FE API-client tests (api / projects / approvals / planner / tasks / templates / dashboards / architecture); BE milestone-coded smoke (FM-001-010 / 011-020 / 021-030 / 031-045); Vitest v8 coverage wired into CI |
| Low-priority cleanup           | `7fc9ad5` | 15 `lib/*` API-client test files (+59 tests); FM-070 / 190 / 200 / 209 / 210 aggregate smoke (+16); ESLint flat-config migration; architecture page testability refactor                                          |
| Housekeeping (post-closeout)   | `8aae400` | Repo-wide `ruff check` cleanup (E402 / F811 / F841)                                                                                                                                                               |
| Housekeeping                   | `5783be1` | TS narrow-cast fix in `fm035-operator-polish.test.tsx`                                                                                                                                                            |
| Housekeeping                   | `55ef880` | `ruff format` sweep across 84 files of pre-existing drift                                                                                                                                                         |
| Housekeeping                   | `2a4e8fc` | Alembic migration chain fix (`fm161_170_search_knowledge` was `down_revision=None`)                                                                                                                               |

**Honest residual gaps** (maturity work, not regressions):

- Playwright / browser E2E still deferred.
- axe-based a11y + stable visual snapshots still deferred.
- Several lower-traffic `apps/web/lib/*` modules remain at 0% direct coverage (`auth-context.tsx`, `constitution`, `constitution-suggestions`, `council`, `escalations`, `governance`, `phase-profiles`, `project-members`, `stream`, `vault`, `hooks/use-stream`).
- End-to-end smoke beyond the in-process `scripts/operator_exercise.py` needs real Postgres + Redis + MinIO + an `OPENAI_API_KEY`.

---

## Program totals

| Band   | Range               | Theme                                                       | Status      |
| ------ | ------------------- | ----------------------------------------------------------- | ----------- |
| V1     | FM-001 → FM-050     | Foundation, planning, execution, governance, hardening      | Complete    |
| V2     | FM-051 → FM-100     | Collaboration, code ops, frontend parity, local CLI         | Complete    |
| V3     | FM-101 → FM-140     | SPEC lifecycle, templates, checkpoints, release operations  | Complete    |
| **V4** | **FM-141 → FM-210** | **Ecosystem: integration, intelligence, enterprise, scale** | **30 / 30** |

Detailed V1-V3 history is preserved in [../FORGEMIND_ROADMAP.md](../FORGEMIND_ROADMAP.md) and the per-milestone logs under [agent-handoffs/](agent-handoffs/). The remainder of this document focuses on V4.

---

## V4 wave-by-wave summary (FM-141 → FM-210)

### Wave 10 — Collaboration, UX & team coordination (FM-141 → FM-150)

Threaded comments with mentions, task assignment, saved views, annotations, a unified activity feed, operator presence, dashboard-wide real-time SSE updates, slash commands, an approval delegation model, and UX polish across every existing dashboard.

**Key additions:** `comment_service`, `mention_service`, `saved_view_service`, `task_assignment_service`, `unified_activity_service`, `slash_command_service`; `comment`, `saved_view`, `run_annotation`, `approval_delegation` models; `comments`, `saved_views`, `annotations`, `collaboration` routers; dashboard UX polish across all surfaces.

### Wave 11 — GitHub, CI/CD & developer tooling (FM-151 → FM-160)

GitHub App installation flow, a rate-limited API client, issue sync, PR status pipeline, merge-readiness evaluation, diff intelligence, CI pipeline view, deployment-readiness and rollback-readiness integration with GitHub signals, and post-release checks that consume GitHub data.

**Key additions:** `github_client`, `github_installation_service`, `github_rate_limiter`, `issue_sync_service`, `ci_pipeline_service`, `diff_intelligence_service`, `merge_readiness_service`; `github_integration` model + router.

### Wave 12 — Search, knowledge & organizational memory (FM-161 → FM-170)

Cross-project search backed by embeddings, convention extraction from completed runs, a recommendation engine, ADR tracking, enriched run memory with structured extraction, and integration of the knowledge base into agent prompts for cross-run learning.

**Key additions:** `search_service`, `embedding_service`, `convention_service`, `recommendation_service`, `adr_service`, `run_memory_enrichment_service`; `search_knowledge` model family; `search_knowledge` router; migration head `fm161_170_search_knowledge` (re-chained in `2a4e8fc`).

### Wave 13 — Enterprise governance, permissions & compliance (FM-171 → FM-180)

SSO configuration, IP allowlists, a governance engine on top of FM-048 policies, spec + plan approval flow, approval delegation chains, retention policies, compliance reports, release gates, and enterprise-grade audit logging.

**Key additions:** `governance_engine_service`, `sso_configuration_service`, `ip_allowlist_service`, `retention_policy_service`, `compliance_report_service`, `release_gate_service`, `spec_plan_approval_service`, `spec_plan_validation_service`, `approval_enhanced_service`, `audit_log_service`, `environment_service`; `enterprise_governance`, `sso_configuration`, `approval_delegation` models; `enterprise_governance` router.

### Wave 14 — Code intelligence, change awareness & test intelligence (FM-181 → FM-190)

Project-scoped dependency graphs parsed from source (Python AST + TS regex), impact analysis via BFS, coverage maps with gap detection, configurable pattern rules with automatic knowledge-base promotion of critical/warning hits, technical-debt scoring, flakiness tracker, complexity metrics (cyclomatic + maintainability index), and a quarantine monitor.

**Key additions:** `code_graph_service`, `pattern_debt_service`, `flakiness_complexity_service`; `code_intelligence` model family (ModuleDependency, ImpactAnalysisRun, CoverageMap, PatternRule, PatternOccurrence, TechnicalDebtScore, FlakinessRecord, ComplexityMetric, QuarantineEntry); `code_intelligence` router at `/api/v1/code-intelligence/`. Authoritative doc: [code-intelligence.md](code-intelligence.md).

### Wave 15 — Analytics, metrics & portfolio operations (FM-191 → FM-200)

Execution metrics auto-captured via lifecycle hooks (no manual instrumentation), composite health score (A-F), cost budgets with threshold alerts, velocity metrics, quality metrics, a multi-project portfolio summary (<1s for 50 projects, benchmarked), custom dashboards with six chart types rendered as dependency-free pure-SVG components and a CRUD UI at `/dashboard/analytics`, cron-scheduled reports via the background scheduler, metric alerts, and an executive summary with a natural-language narrative.

**Key additions:** `execution_health_service`, `velocity_quality_service`, `dashboard_alert_service`, `project_overview_service`, `operational_timeline_service`; `analytics_metrics` model family; `analytics` router at `/api/v1/analytics/`; frontend widget + chart renderer under `apps/web/components/dashboard/`. Authoritative doc: [analytics-portfolio.md](analytics-portfolio.md).

### Wave 16 — API, webhooks & ecosystem integrations (FM-201 → FM-210)

Versioned `/api/v1/` public surface, JWT + API-key auth (SHA-256 hashed, `read`/`write`/`admin` scopes), sliding-window rate limiter with `X-RateLimit-*` response headers, OpenAPI 3 completeness validation, Python + TypeScript SDK clients, outbound webhooks with delivery tracking, Slack / email / PagerDuty / generic HTTP connectors, and integration bindings.

**Key additions:** `api_key_service`, `webhook_service`, `webhook_connector_service`, `integration_service`; `api_ecosystem` model family (ApiKey, WebhookEndpoint, WebhookDelivery, RateLimitTier, IntegrationBinding); `api_ecosystem` router; SDK under [`apps/api/app/sdk/`](../apps/api/app/sdk/) (`python_client.py`, `typescript_client.ts`, `openapi-generator-config.yaml`, `pyproject.toml`, `package.json`). Authoritative doc: [api-ecosystem.md](api-ecosystem.md).

---

## V1-V3 highlights (FM-001 → FM-140)

Compact view — full detail is preserved under [agent-handoffs/](agent-handoffs/).

| Wave                                   | Range            | Summary                                                                                                                                                                                               |
| -------------------------------------- | ---------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1 — Platform foundation                | FM-001 → FM-005  | Monorepo, FastAPI, Next.js, Docker, initial DB.                                                                                                                                                       |
| 2 — Backend core                       | FM-006 → FM-011  | Project/Run/Task/PlannerResult models, CRUD, task DAG, orchestration skeleton.                                                                                                                        |
| 3 — Frontend MVP                       | FM-012 → FM-015A | Dashboard shell, prompt intake, task display, validation.                                                                                                                                             |
| 4 — AI planning                        | FM-016 → FM-020A | LiteLLM integration, structured planner output with normalization, quality gate.                                                                                                                      |
| 5 — Execution foundations              | FM-021 → FM-025  | Artifacts, agent registry, worker loop, fixed agents.                                                                                                                                                 |
| 6 — Controlled execution               | FM-026 → FM-030  | Approval workflow, event log, run detail view, approval inbox.                                                                                                                                        |
| 7 — Operator control                   | FM-031 → FM-035  | Artifact detail, retry/cancel, execution chatbot, handoff refinement.                                                                                                                                 |
| 8 — Adaptive multi-agent               | FM-036 → FM-040  | Composition, handoff context, connectors, run memory, adaptive loop.                                                                                                                                  |
| 9 — Connector & retry intelligence     | FM-041 → FM-045  | Connector readiness, credential vault, retry v2, chatbot v2, eval suite.                                                                                                                              |
| Pre-release infra                      | (5 features)     | Run lifecycle health, cost tracking, governance policies, audit export, trust scoring.                                                                                                                |
| 10 — Platform intelligence & hardening | FM-046 → FM-050  | Replay snapshots, council decision engine, knowledge base, external repo integration, production hardening (JWT + rate limit + logging + error handlers).                                             |
| 11 — Team collaboration                | FM-051 → FM-060  | Workspaces, RBAC memberships, notifications + delivery channels, escalation, activity feed, presence, SSE, FM-060 hardening pass.                                                                     |
| 12 — Repo & code execution             | FM-061 → FM-070  | Repo sync metadata, file tree, code mapping, patch proposals, change reviews with annotations, branch strategy, PR drafts, approval gates, sandbox execution, frontend pages.                         |
| 13 — Advanced frontend parity          | FM-071 → FM-073  | Dashboard pages for trust / replay / council / governance / costs / audit / knowledge / vault / connectors / agents / settings.                                                                       |
| 14 — Auth & RBAC hardening             | FM-074 → FM-075  | Real JWT authentication, route-level RBAC across all non-public endpoints.                                                                                                                            |
| 15 — CI/CD, real-time, observability   | FM-076 → FM-078  | GitHub Actions pipeline, SSE consumption in frontend, Prometheus metrics.                                                                                                                             |
| 16 — Platform maturity                 | FM-079 → FM-080  | Shared monorepo packages, production Docker images + reverse proxy config.                                                                                                                            |
| 17 — Architecture intelligence         | FM-081 → FM-090  | Graph foundation, topology mapper, drift detection, rule engine, dashboard, design doc synthesis, impact analysis, refactor recommendations, architecture approvals, structural health score.         |
| 18 — Local developer mode              | FM-091 → FM-100  | `forgemind` CLI: config, repo indexing, local chat, sandbox, patches, PR prep, IDE integration, offline state, handoff snapshots, hardening.                                                          |
| 19 — SPEC lifecycle                    | FM-101 → FM-110  | Spec-driven planning, spec + plan approval, spec validation, project constitution.                                                                                                                    |
| 20 — Phase routing + templates         | FM-111 → FM-120  | Phase agent profiles, phase-aware composition, project templates with inheritance, knowledge-driven constitution suggestions, spec/plan bootstrap.                                                    |
| 21 — Checkpoints + delivery            | FM-121 → FM-130  | Execution checkpoints with auto/manual modes, resume semantics, delivery artifacts, review packages, lifecycle traceability, run memory enrichment, release confidence scoring.                       |
| 22 — Release operations                | FM-131 → FM-140  | Release packages, deployment environments, tiered readiness, release gates, rollback readiness, post-release reporting, operational timeline, frontend release surface, local-mode release awareness. |

---

## Testing & CI history

| Milestone                     | Test count snapshot                                                              |
| ----------------------------- | -------------------------------------------------------------------------------- |
| FM-045                        | 117                                                                              |
| FM-050                        | 185                                                                              |
| FM-060                        | 279                                                                              |
| FM-070                        | 303                                                                              |
| FM-080                        | 413                                                                              |
| FM-090                        | 482                                                                              |
| FM-100                        | 535 (incl. 53 local CLI)                                                         |
| FM-140                        | 746 (685 backend + 61 local)                                                     |
| FM-180                        | 1157                                                                             |
| FM-210                        | 1551 BE + 231 FE + 61 local                                                      |
| Post-QA (`7fc9ad5`)           | 1551 BE + 231 FE + 61 local, coverage artifact uploaded                          |
| Post-housekeeping (`2a4e8fc`) | **1559 BE + 231 FE + 61 local** (F811 renames un-shadowed previously-dead tests) |

CI workflow ([`.github/workflows/ci.yml`](../.github/workflows/ci.yml)) runs three jobs: **backend** (ruff check + ruff format --check + pytest), **frontend** (tsc + ESLint + Vitest with v8 coverage + next build, coverage artifact uploaded), **local-cli** (pytest against `apps/local`).

---

## Deferred / residual

These are explicitly tracked as maturity work, not product gaps:

- Playwright browser E2E tests.
- axe-based a11y tests + stable visual snapshots.
- Direct `lib/*` test coverage for the low-traffic modules listed above.
- A full operator exercise against a live stack with real LLM credentials. The in-process scripted smoke ([`scripts/operator_exercise.py`](../scripts/operator_exercise.py)) validates `/health`, project creation, and `/planner/intake` acceptance against aiosqlite, but LLM-backed plan bodies and authz-gated reads require the full runtime.

---

## References

- Product overview: [../README.md](../README.md)
- System architecture: [ARCHITECTURE.md](ARCHITECTURE.md)
- Developer workflow (local boot + tests + migrations + CI): [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md)
- Repository navigation map: [REPOSITORY_GUIDE.md](REPOSITORY_GUIDE.md)
- Code intelligence guide (Wave 14): [code-intelligence.md](code-intelligence.md)
- Analytics & portfolio guide (Wave 15): [analytics-portfolio.md](analytics-portfolio.md)
- API, webhooks & ecosystem guide (Wave 16): [api-ecosystem.md](api-ecosystem.md)
- Deployment notes: [DEPLOYMENT.md](DEPLOYMENT.md)
- Technical debt tracker: [TECHNICAL_DEBT.md](TECHNICAL_DEBT.md)
- Per-milestone implementation logs: [agent-handoffs/](agent-handoffs/)
- V4 product plan: [../FORGEMIND_V4_ROADMAP.md](../FORGEMIND_V4_ROADMAP.md)
- V1-V3 product plan: [../FORGEMIND_ROADMAP.md](../FORGEMIND_ROADMAP.md)

