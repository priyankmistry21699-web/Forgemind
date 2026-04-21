# 1 · Project Overview

## What ForgeMind is

An **operator-centered, AI-native engineering platform** that turns natural-language goals into a governed, auditable, multi-agent execution plan — and runs that plan end-to-end with human approvals, cost tracking, code-change proposals, architecture intelligence, analytics, and a public API.

Not a chat window. A **governed execution runtime**.

## Product goals (what must always be true)

1. **Every agent action is reviewable** — typed artifact + execution event + optional replay snapshot.
2. **Governance is first-class** — approvals, constitution, trust scoring, council, architecture approvals, enterprise governance (SSO / IP allowlist / compliance / retention).
3. **Costs are visible** — per-call cost tracking, per-project budgets, threshold alerts.
4. **Code changes are bounded** — patch proposals → annotation reviews → PR drafts → sandbox execution.
5. **Architecture drift is detectable** — topology graph, rule engine, impact analysis.
6. **Integration surface is versioned** — `/api/v1/`, JWT + API keys, OpenAPI 3, Python + TS SDKs, webhooks.

## Subsystem map

| Subsystem | Role | Primary location |
| :-- | :-- | :-- |
| 🧠 **Planning & Execution** | Prompt → plan → agent run → artifacts / events / snapshots | [apps/api/app/services/planner_service.py](../../apps/api/app/services/planner_service.py) · [apps/worker/worker/](../../apps/worker/worker/) · [apps/api/app/services/adaptive_orchestrator.py](../../apps/api/app/services/adaptive_orchestrator.py) |
| 🛡️ **Governance** | Approvals, constitution, trust, council, architecture approvals, enterprise | `approval_*`, `constitution_*`, `trust_scoring_service`, `council_service`, `architecture_approval_service`, `governance_*` services |
| 🏛️ **Code & Architecture Intelligence** | Repo sync, patch/PR flow, sandbox, topology, drift, rules, impact, refactor, coverage, debt | `code_ops_service`, `code_graph_service`, `drift_detection_service`, `architecture_rule_service`, `impact_analysis_service`, `refactor_recommendation_service`, `pattern_debt_service`, `flakiness_complexity_service` |
| 📊 **Analytics & Portfolio** | Composite health, budgets + alerts, velocity + quality, portfolio, scheduled reports | `execution_health_service`, `structural_health_service`, `cost_tracking_service`, `dashboard_alert_service`, `velocity_quality_service`, `project_overview_service`, `background_scheduler` |
| 🤝 **Collaboration** | Workspaces, RBAC, comments, mentions, saved views, activity, presence, SSE | `workspace_service`, `membership_service`, `comment_service`, `mention_service`, `saved_view_service`, `activity_service`, `stream_service` |
| 🔗 **Integrations** | GitHub App · webhooks · Slack / email / PagerDuty | `github_*` services · `webhook_service` · `webhook_connector_service` · `connector_service` |
| 🌐 **Public API & SDKs** | `/api/v1/`, JWT + API keys, rate limit, OpenAPI 3, Python + TS clients | [apps/api/app/api/routes/](../../apps/api/app/api/routes/) · [apps/api/app/core/](../../apps/api/app/core/) · [apps/api/app/sdk/](../../apps/api/app/sdk/) |
| 💻 **Local CLI** | `forgemind` — attach, index, Q&A, bounded exec, patches, PR prep, IDE integration | [apps/local/forgemind_local/](../../apps/local/forgemind_local/) |

## Tech at a glance

- **Backend** — FastAPI · SQLAlchemy 2 async · asyncpg · Pydantic v2 · Alembic · LiteLLM.
- **Frontend** — Next.js 15 App Router · React 19 · strict TS · Tailwind 4 · shadcn/ui · Vitest + v8.
- **Infra** — PostgreSQL 16 · Redis 7 · MinIO/S3 · Docker Compose.
- **Scheduler** — single 60-second tick inside API's FastAPI lifespan ([background_scheduler.py](../../apps/api/app/services/background_scheduler.py)).

## Counts at HEAD

| Surface | Count |
| :-- | --: |
| Backend route modules (`apps/api/app/api/routes/*.py`) | **53** |
| Backend services (`apps/api/app/services/*.py`) | **109** |
| Backend models (`apps/api/app/models/*.py`) | **42** |
| Backend Pydantic schema modules (`apps/api/app/schemas/*.py`) | **38** |
| Frontend dashboard route folders (`apps/web/app/dashboard/*/`) | **25** |
| Frontend `lib/` modules (typed API clients + helpers) | **33** |
| Backend tests | **1559** |
| Frontend Vitest tests | **231** (37 files) |
| Local CLI tests | **61** |
| V4 milestones | **FM-001 → FM-210** · **30 / 0 / 0** across Waves 10–16 |

> Count discrepancies from older docs: re-ran scan against HEAD and updated. If memory says "51 routers / 103 services / 44 models" elsewhere, trust the live directory count.

## Status

- V4 feature-complete. Backend / frontend / CLI tests all green.
- CI: 3-job pipeline green on `main`.
- Docker + hybrid local stacks both boot. Known quirk: migration `0022` duplicate-enum on fresh Postgres (workaround in [DEVELOPMENT_WORKFLOW §5.2](../DEVELOPMENT_WORKFLOW.md)).
- Deferred: Playwright browser E2E, axe a11y, visual snapshots.
