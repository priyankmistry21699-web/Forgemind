# ForgeMind — System Architecture

> Last updated: 2026-03-26 (after FM-045 + pre-release infrastructure completion)

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

| Component         | Technology                    | Purpose                         |
| ----------------- | ----------------------------- | ------------------------------- |
| Framework         | FastAPI (Python 3.12+, async) | REST API server                 |
| ORM               | SQLAlchemy 2.0 (async)        | Database abstraction            |
| DB Driver         | asyncpg                       | Async PostgreSQL driver         |
| Migrations        | Alembic                       | Schema versioning               |
| Validation        | Pydantic v2                   | Request/response DTOs           |
| LLM Gateway       | LiteLLM (>=1.50.0)           | Multi-provider LLM abstraction  |
| Encryption        | cryptography (Fernet)         | Credential vault                |
| HTTP Client       | httpx (async)                 | Connector operations            |

### Frontend

| Component         | Technology                    | Purpose                         |
| ----------------- | ----------------------------- | ------------------------------- |
| Framework         | Next.js 15 (App Router)       | Server-side rendering + routing |
| UI Library        | React 19                      | Component framework             |
| Styling           | Tailwind CSS 4                | Utility-first CSS               |
| Components        | shadcn/ui                     | Accessible UI components        |
| State             | Zustand, TanStack Query v5    | Client + server state           |
| Real-time         | Socket.IO Client              | Live updates                    |
| Code Editor       | Monaco Editor                 | In-browser editing              |
| Visualization     | Mermaid.js, React Flow        | Diagrams + DAG rendering        |
| Charts            | Recharts                      | Analytics dashboards            |

### Infrastructure

| Component         | Technology                    | Purpose                         |
| ----------------- | ----------------------------- | ------------------------------- |
| Database          | PostgreSQL 16                 | Primary data store              |
| Cache/Queue       | Redis 7                       | Caching + Celery broker         |
| Object Storage    | MinIO                         | File/artifact storage           |
| Containerization  | Docker + Docker Compose       | Local development environment   |
| CI/CD             | GitHub Actions                | Automated testing + deployment  |

### Testing

| Component         | Technology                    | Purpose                         |
| ----------------- | ----------------------------- | ------------------------------- |
| Framework         | pytest (>=8.0.0)              | Test runner                     |
| Async             | pytest-asyncio                | Async test support              |
| HTTP Client       | httpx (AsyncClient)           | API integration tests           |
| Test DB           | aiosqlite (in-memory SQLite)  | Fast isolated test database     |
| Total Tests       | **174** (all passing)         | 105 core + 23 evals + 46 infra |

---

## Database Models (15 Total)

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
```

### Model Details

| # | Model | Table | Key Columns | Relationships |
|---|-------|-------|-------------|---------------|
| 1 | **User** | `users` | id(UUID), email(unique), display_name, clerk_id, is_active | 1:N → Projects |
| 2 | **Project** | `projects` | id(UUID), name, description, status(6 states), owner_id(FK) | N:1 → User, 1:N → Runs/Artifacts/ConnectorLinks |
| 3 | **Run** | `runs` | id(UUID), run_number, status(6 states), trigger, project_id(FK) | N:1 → Project, 1:N → Tasks, 1:1 → PlannerResult |
| 4 | **Task** | `tasks` | id(UUID), title, task_type, status(7 states), depends_on(UUID[]), run_id(FK), assigned_agent_slug, max_retries, retry_count | N:1 → Run, self-ref parent/children |
| 5 | **PlannerResult** | `planner_results` | id(UUID), run_id(FK, unique), overview, architecture_summary, recommended_stack(JSON), assumptions(JSON), next_steps(JSON) | N:1 → Run |
| 6 | **Artifact** | `artifacts` | id(UUID), title, artifact_type(7 types), content, meta(JSON), version, project_id(FK), run_id(FK), task_id(FK) | N:1 → Project/Run/Task |
| 7 | **Agent** | `agents` | id(UUID), name, slug(unique), status(3 states), capabilities(JSON), supported_task_types(JSON) | — |
| 8 | **ApprovalRequest** | `approval_requests` | id(UUID), status(3 states), title, project_id(FK), run_id(FK), task_id(FK), decided_by, decision_comment | N:1 → Project/Run/Task/Artifact |
| 9 | **ExecutionEvent** | `execution_events` | id(UUID), event_type(10 types), summary, metadata\_(JSON), agent_slug | N:1 → Project/Run/Task/Artifact |
| 10 | **Connector** | `connectors` | id(UUID), name, slug(unique), connector_type, status(3 states), capabilities(JSON), config(JSON) | — |
| 11 | **ProjectConnectorLink** | `project_connector_links` | id(UUID), project_id(FK), connector_id(FK), priority(3 levels), readiness(4 states), blocker_reason | N:1 → Project/Connector |
| 12 | **CredentialVault** | `credential_vault` | id(UUID), name, env_key(unique), connector_id(FK), status(4 states), secret_type, scopes(JSON), expires_at | N:1 → Connector/Project |
| 13 | **CostRecord** | `cost_records` | id(UUID), model_name, prompt_tokens, completion_tokens, total_tokens, cost_usd, caller | N:1 → Project/Run/Task |
| 14 | **GovernancePolicy** | `governance_policies` | id(UUID), name, trigger(5 types), action(4 types), rules(JSON), project_id(FK), enabled, priority | — |
| 15 | **TrustScore** | `trust_scores` | id(UUID), entity_type(3 types), entity_id, trust_score(0-1), confidence, risk_level(4 levels), factors(JSON) | — |

### Status Enums

| Model | States |
|-------|--------|
| Project | DRAFT, PLANNING, ACTIVE, PAUSED, COMPLETED, FAILED |
| Run | PENDING, PLANNING, RUNNING, PAUSED, COMPLETED, FAILED |
| Task | PENDING, BLOCKED, READY, RUNNING, COMPLETED, FAILED, SKIPPED |
| Agent | ACTIVE, INACTIVE, DEPRECATED |
| Approval | PENDING, APPROVED, REJECTED |
| Connector | AVAILABLE, CONFIGURED, UNAVAILABLE |
| ConnectorLink readiness | MISSING, CONFIGURED, BLOCKED, READY |
| CredentialVault | ACTIVE, EXPIRED, MISSING, REVOKED |
| GovernancePolicy trigger | TASK_TYPE, COST_THRESHOLD, ARTIFACT_TYPE, AGENT_ACTION, CUSTOM |
| GovernancePolicy action | REQUIRE_APPROVAL, AUTO_APPROVE, BLOCK, NOTIFY |
| TrustScore risk_level | LOW, MEDIUM, HIGH, CRITICAL |

---

## API Routes (22 Routers)

All routers registered in `apps/api/app/api/router.py` and mounted via `app.include_router(api_router)` in `main.py`.

### Route Map

| # | Route File | Prefix | Key Endpoints | Tags |
|---|-----------|--------|---------------|------|
| 1 | `health.py` | `/` | `GET /health`, `GET /health/ready` | health |
| 2 | `projects.py` | `/` | `POST /projects`, `GET /projects`, `GET /projects/{id}`, `PATCH /projects/{id}` | projects |
| 3 | `planner.py` | `/planner` | `POST /planner/intake` | planner |
| 4 | `planner_results.py` | `/planner` | Planner result queries | planner |
| 5 | `tasks.py` | `/` | `GET /runs/{id}/tasks`, `GET /runs/{id}/tasks/ready`, `GET /tasks/{id}`, `PATCH /tasks/{id}/status`, `POST /tasks/{id}/claim`, `POST /tasks/{id}/complete`, `POST /tasks/{id}/fail` | tasks |
| 6 | `runs.py` | `/` | `GET /projects/{id}/runs`, `GET /projects/{id}/runs/latest`, `GET /runs/{id}` | runs |
| 7 | `artifacts.py` | `/` | `POST /projects/{id}/artifacts`, `GET /projects/{id}/artifacts`, `GET /artifacts/{id}`, `PATCH /artifacts/{id}`, `DELETE /artifacts/{id}` | artifacts |
| 8 | `agents.py` | `/` | `GET /agents`, `GET /agents/{id}` | agents |
| 9 | `approvals.py` | `/approvals` | `GET /approvals`, `GET /approvals/{id}`, `POST /approvals/{id}/decide` | approvals |
| 10 | `events.py` | `/events` | `GET /events` | events |
| 11 | `chat.py` | `/` | `POST /runs/{id}/chat` | chat |
| 12 | `composition.py` | `/` | `GET /composition/capabilities`, `GET /runs/{id}/composition` | composition |
| 13 | `connectors.py` | `/` | `GET /connectors`, `GET /runs/{id}/connectors/requirements` | connectors |
| 14 | `memory.py` | `/runs/{id}/memory` | `GET .../summary`, `GET .../failures`, `GET .../context` | memory |
| 15 | `credential_vault.py` | `/vault` | Credential CRUD | vault |
| 16 | `retry.py` | `/retry` | Retry policy endpoints | retry |
| 17 | `run_lifecycle.py` | `/lifecycle` | `GET /lifecycle/runs/{id}/health`, `POST .../auto-complete`, `POST .../auto-fail`, `GET /lifecycle/runs/health/scan` | lifecycle |
| 18 | `costs.py` | `/costs` | `GET /costs/runs/{id}/summary`, `GET /costs/projects/{id}/summary`, `GET /costs/breakdown`, `GET /costs` | costs |
| 19 | `governance.py` | `/governance` | `POST /governance/policies`, `GET /governance/policies`, `GET /governance/policies/{id}`, `PATCH ...`, `DELETE ...` | governance |
| 20 | `audit.py` | `/audit` | `GET /audit/export/json`, `GET /audit/export/csv`, `GET /audit/summary` | audit |
| 21 | `trust.py` | `/trust` | `POST /trust/tasks/{id}/assess`, `POST /trust/runs/{id}/assess`, `GET /trust/runs/{id}/risk-summary`, `GET /trust/scores`, `GET /trust/{type}/{id}` | trust |

---

## Services Layer

All business logic lives in `apps/api/app/services/`. Routes are thin — they delegate to services.

### Core Services

| Service | Key Functions | Purpose |
|---------|---------------|---------|
| `project_service.py` | create, get, list, update | Project CRUD |
| `planner_service.py` | plan_from_prompt, normalize_plan | NL → structured plan via LiteLLM |
| `task_service.py` | get, list, update_status, get_ready, promote_ready | DAG-aware task state machine |
| `execution_service.py` | claim_task, complete_task, fail_task | Task lifecycle orchestration |
| `artifact_service.py` | create, get, list, update (bumps version), delete | Versioned artifact storage |
| `agent_service.py` | seed_default_agents, list, get, get_by_slug | Agent registry (5 core agents) |
| `approval_service.py` | create, get, list, resolve | Human-in-the-loop approvals |
| `event_service.py` | emit_event, list_events | Append-only execution log |
| `chat_service.py` | detect_topics, build_context, chat_about_run | AI-powered execution Q&A |
| `composition_service.py` | derive_capabilities, score_agent, compose_team | Dynamic agent team assembly |
| `connector_service.py` | seed_connectors, list, get_requirements | Connector registry + recommendations |
| `run_memory_service.py` | get_summary, get_failures, build_context | Cached run context for chat/agents |
| `adaptive_orchestrator.py` | — | DAG scheduling + failure handling |

### Advanced Services (FM-041–050 Infrastructure)

| Service | Key Functions | Purpose |
|---------|---------------|---------|
| `credential_vault_service.py` | Vault CRUD, rotation, expiry | Encrypted secret metadata |
| `adaptive_retry_service.py` | should_retry, get_delay, plan_reroute | Smart retry with agent re-routing |
| `run_lifecycle_service.py` | get_health, auto_complete, auto_fail, scan | Run health + stuck detection |
| `cost_tracking_service.py` | record_usage, estimate_cost, summaries, breakdown | Per-call LLM cost tracking |
| `governance_service.py` | CRUD policies, evaluate_policies | Configurable approval rules |
| `audit_export_service.py` | export_json, export_csv, summary | Compliance-ready audit export |
| `trust_scoring_service.py` | assess_task, assess_run, risk_summary | Heuristic trust/risk scoring |

---

## Pydantic Schemas

All request/response models in `apps/api/app/schemas/`.

| Schema File | Models | Purpose |
|-------------|--------|---------|
| `project.py` | ProjectCreate, ProjectUpdate, ProjectRead, ProjectList | Project DTOs |
| `task.py` | TaskRead, TaskList, TaskStatusUpdate, ReadyTasksResponse, TaskClaimRequest, TaskCompleteRequest, TaskFailRequest | Task DTOs |
| `run.py` | RunRead, RunList | Run DTOs |
| `artifact.py` | ArtifactRead, ArtifactList, ArtifactCreate, ArtifactUpdate | Artifact DTOs |
| `agent.py` | AgentRead, AgentList | Agent DTOs |
| `approval.py` | ApprovalRead, ApprovalList, ApprovalCreate, ApprovalDecision | Approval DTOs |
| `connector.py` | ConnectorRead, ConnectorList, ConnectorRecommendation, ProjectConnectorLinkCreate/Read, ProjectReadinessSummary | Connector + readiness DTOs |
| `execution_event.py` | ExecutionEventRead, ExecutionEventList | Event DTOs |
| `planner_result.py` | PlannerResultRead, PlannerResponse | Planner output DTOs |
| `prompt_intake.py` | PromptIntakeRequest, PromptIntakeResponse | NL prompt intake DTOs |
| `cost.py` | CostRecordRead, CostRecordList | Cost tracking DTOs |
| `governance.py` | GovernancePolicyRead/List/Create/Update | Governance DTOs |
| `trust.py` | TrustScoreRead, TrustScoreList | Trust score DTOs |

---

## Database Migrations (14 Total)

All migrations in `apps/api/alembic/versions/` using Alembic.

| # | Revision | Description | Tables Added/Changed |
|---|----------|-------------|----------------------|
| 1 | 0001 | Initial schema | users, projects, runs, tasks, agents, artifacts, planner_results |
| 2 | 0002 | Planner results | planner_results table |
| 3 | 0003 | Artifact storage | artifacts table with versioning |
| 4 | 0004 | Agent registry | agents table with capabilities |
| 5 | 0005 | Task execution columns | +assigned_agent_slug, +error_message on tasks |
| 6 | 0006 | Approval requests | approval_requests table |
| 7 | 0007 | Execution events | execution_events table (append-only) |
| 8 | 0008 | Connector registry | connectors table |
| 9 | 0009 | Connector readiness (FM-041) | project_connector_links table |
| 10 | 0010 | Credential vault (FM-042) | credential_vault table |
| 11 | 0011 | Retry columns (FM-043) | +max_retries, +retry_count on tasks |
| 12 | 0012 | Cost tracking | cost_records table |
| 13 | 0013 | Governance policies | governance_policies table |
| 14 | 0014 | Trust scores | trust_scores table |

---

## Application Lifecycle

### Startup Sequence

```
FastAPI app created
  → CORS middleware added (allow_origins from settings)
  → All 22 routers mounted via api_router
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

| Service | Image | Port | Purpose | Health Check |
|---------|-------|------|---------|--------------|
| **postgres** | postgres:16-alpine | 5432 | Primary database | pg_isready |
| **redis** | redis:7-alpine | 6379 | Cache + Celery broker | redis-cli ping |
| **minio** | minio/minio:latest | 9000 (API), 9001 (Console) | Object storage | — |
| **api** | ./apps/api (Dockerfile) | 8000 | FastAPI backend | depends_on postgres+redis |
| **web** | ./apps/web (Dockerfile) | 3000 | Next.js frontend | depends_on api |

### Service Dependencies

```
web → api → postgres (healthy)
              → redis (healthy)
         → minio (optional)
```

---

## Configuration

Settings defined in `apps/api/app/core/config.py` via Pydantic `BaseSettings`:

| Setting | Default | ENV Variable | Purpose |
|---------|---------|--------------|---------|
| app_env | "development" | APP_ENV | Environment mode |
| debug | true | DEBUG | Debug mode |
| secret_key | — | SECRET_KEY | App secret (required) |
| api_host | "0.0.0.0" | API_HOST | Bind address |
| api_port | 8000 | API_PORT | Bind port |
| cors_origins | "http://localhost:3000" | CORS_ORIGINS | Allowed origins (comma-separated) |
| postgres_host | "localhost" | POSTGRES_HOST | DB host |
| postgres_port | 5432 | POSTGRES_PORT | DB port |
| postgres_db | "forgemind" | POSTGRES_DB | DB name |
| postgres_user | "forgemind" | POSTGRES_USER | DB user |
| postgres_password | — | POSTGRES_PASSWORD | DB password (required) |
| database_url | (auto-built) | DATABASE_URL | Full async DB URL |
| redis_host | "localhost" | REDIS_HOST | Redis host |
| redis_port | 6379 | REDIS_PORT | Redis port |
| redis_url | (auto-built) | REDIS_URL | Full Redis URL |
| planner_model | "gpt-4o" | PLANNER_MODEL | LLM model for planning |
| planner_temperature | 0.4 | PLANNER_TEMPERATURE | LLM temperature |
| planner_max_tokens | 4096 | PLANNER_MAX_TOKENS | LLM max output tokens |
| openai_api_key | "" | OPENAI_API_KEY | OpenAI key |
| anthropic_api_key | "" | ANTHROPIC_API_KEY | Anthropic key |
| google_api_key | "" | GOOGLE_API_KEY | Google key |

---

## Test Structure

### Backend Tests (`apps/api/tests/`)

| Test File | Focus | Coverage |
|-----------|-------|----------|
| `test_health.py` | Health endpoints | Liveness + readiness |
| `test_projects.py` | Project CRUD | Create, list, get, update |
| `test_planner.py` | Planner service | NL prompt → plan, fallback stub |
| `test_tasks.py` | Task DAG | State transitions, ready-task, DAG |
| `test_runs.py` | Run management | Creation, listing, status |
| `test_agents.py` | Agent registry | Seed, list, get |
| `test_artifacts.py` | Artifact storage | Versioning, CRUD, filtering |
| `test_approvals.py` | Approval workflow | Create, list, approve/reject |
| `test_events.py` | Event logging | Emit, list, filter |
| `test_chat.py` | Execution chatbot | Topic detection, context, fallback |
| `test_composition.py` | Agent composition | Team assembly, scoring |
| `test_connectors.py` | Connector registry | List, recommendations, readiness |
| `test_memory.py` | Execution memory | Summaries, failure analysis |
| `test_schemas.py` | Pydantic schemas | Validation |
| `test_fm046_050.py` | Infrastructure features | Lifecycle, cost, governance, audit, trust (46 tests) |

### Evaluation Tests (`apps/api/evals/`)

| Test File | Focus |
|-----------|-------|
| `test_quality_evals.py` | 23 benchmark quality evaluations |
| `eval_benchmarks.json` | Benchmark data |

### Test Counts

| Category | Tests |
|----------|-------|
| Core tests (FM-001–040) | 105 |
| Quality evals (FM-045) | 23 |
| Infrastructure tests (FM-046–050) | 46 |
| **Total** | **174** |

---

## Project Structure

```
forgemind/
├── apps/
│   ├── api/                          # FastAPI backend
│   │   ├── app/
│   │   │   ├── api/
│   │   │   │   ├── router.py         # Main router (22 routers)
│   │   │   │   └── routes/           # Route handlers (22 files)
│   │   │   ├── core/
│   │   │   │   └── config.py         # Settings (Pydantic BaseSettings)
│   │   │   ├── db/
│   │   │   │   ├── base.py           # Model registry (15 models)
│   │   │   │   └── session.py        # Async engine + session factory
│   │   │   ├── models/               # SQLAlchemy models (15 files)
│   │   │   ├── schemas/              # Pydantic schemas (13 files)
│   │   │   ├── services/             # Business logic (20+ files)
│   │   │   └── main.py              # FastAPI app factory
│   │   ├── alembic/
│   │   │   └── versions/             # 14 migrations
│   │   ├── tests/                    # 128 tests (15 files)
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
├── FORGEMIND_ROADMAP.md              # Original roadmap
├── FORGEMIND_ROADMAP_V2.md           # Current roadmap (v2)
└── README.md                         # Project overview + Mermaid diagrams
```

---

## Security Architecture

| Area | Implementation |
|------|---------------|
| Authentication | Clerk (JWT via `get_current_user_id()` dependency) |
| Authorization | Owner-based (extensible to RBAC) |
| Secret Storage | Env-key references (no plaintext secrets in DB) |
| CORS | Configurable allowed origins |
| Input Validation | Pydantic model validation on all inputs |
| State Machine | Task transitions validated in service layer |
| Audit | Append-only ExecutionEvent table |
| Governance | Configurable policies (approve/block/notify) |
| Trust | Heuristic scoring per task/run/artifact |

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

## Upcoming (FM-046 to FM-050)

| ID | Feature | Description |
|----|---------|-------------|
| FM-046 | Run Replay & Trace Inspection | Step-by-step execution replay with trace visualization |
| FM-047A | Multi-Agent Council Engine | Collaborative agent decision-making for complex tasks |
| FM-047 | Policy-Based Approval Rules | Smart approval routing with council integration |
| FM-048 | Multi-Run Memory & Knowledge Base | Cross-run learning and project-level knowledge |
| FM-049 | External Repo/Workspace Integration | Local file system and Git repository access |
| FM-050 | Production Hardening Pass | Rate limiting, error recovery, monitoring, deployment |

---

_This document reflects the architecture as of commit `5977b93` on `main`._
