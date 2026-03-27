# ForgeMind — Complete Project Roadmap v2

> **A Secure Autonomous Engineering Platform that turns high-level goals into complete, connected, verifiable software systems — with architecture generation, connector intelligence, local workspace access, approval-based execution, and long-term project drift awareness.**

ForgeMind is **not** just another multi-agent coding tool. It is a **goal-to-system synthesis platform** — it understands what to build, what to connect, how to secure it, how to verify it, and how to keep it aligned over time.

---

## Table of Contents

1. [Product Philosophy & Positioning](#1-product-philosophy--positioning)
2. [Six Core Differentiators](#2-six-core-differentiators)
3. [What Users Get](#3-what-users-get)
4. [Core Concepts](#4-core-concepts)
5. [Updated Tech Stack](#5-updated-tech-stack)
6. [System Architecture](#6-system-architecture)
7. [Feature List (Complete)](#7-feature-list-complete)
8. [Database Schema](#8-database-schema)
9. [Agent Definitions & Dynamic Composition](#9-agent-definitions--dynamic-composition)
10. [Phase-Wise Implementation](#10-phase-wise-implementation)
11. [API Design](#11-api-design)
12. [Security Model](#12-security-model)
13. [Testing Strategy](#13-testing-strategy)
14. [Deployment Strategy](#14-deployment-strategy)
15. [Monitoring & Observability](#15-monitoring--observability)
16. [Competitive Positioning](#16-competitive-positioning)

---

## 1. Product Philosophy & Positioning

### What ForgeMind Is NOT

- Not just an AI coding agent
- Not just a multi-agent task executor
- Not just a code generation tool
- Not another OpenClaw/NemoClaw-style autonomous agent builder

### What ForgeMind IS

> **An AI software systems orchestration and delivery platform.**

| Aspect             | Typical Agent Systems        | ForgeMind                                     |
| ------------------ | ---------------------------- | --------------------------------------------- |
| Main focus         | Autonomous code execution    | **Goal-to-system synthesis**                  |
| Planning depth     | Task execution oriented      | **Architecture + roadmap + task graph**       |
| Connector handling | User-heavy manual setup      | **Connector intelligence + setup wizard**     |
| Secrets/tokens     | Basic config, burden on user | **Token vault + permission-aware setup**      |
| Local machine      | Limited or none              | **ForgeMind Local companion**                 |
| Trust/audit        | May vary                     | **Replay, risk scoring, evidence, approvals** |
| Long-term health   | Limited                      | **Drift detection + scorecards**              |
| Agent composition  | Fixed prebuilt agent teams   | **Dynamic agent team generation per project** |
| Self-improvement   | Raw autonomy                 | **Governed self-improving workflows**         |
| Enterprise appeal  | Autonomy                     | **Autonomy + governance + traceability**      |
| Product scope      | Coding agent system          | **Autonomous engineering platform**           |

### The One-Line Pitch

> **ForgeMind dynamically assembles the optimal AI engineering team to turn your idea into a secure, connected, verifiable software system — and keeps it healthy over time.**

---

## 2. Six Core Differentiators

These are the features that make ForgeMind fundamentally different from any existing agent platform:

### D1. Goal-to-System Synthesis

User says _"Build a YouTube automation pipeline"_ → ForgeMind infers system type, chooses stack, selects connectors, generates architecture, creates roadmap, scaffolds the project, and monitors it. It's an **autonomous systems architect + builder**, not just a code agent.

### D2. Connector Intelligence + Token Vaulting

Most systems leave users stuck with client IDs, OAuth scopes, token refresh headaches, and env var chaos. ForgeMind provides a connector registry, setup wizard, callback URI generation, scope guidance, encrypted token vault, connection testing, expiry/rotation alerts, and full audit trail.

### D3. ForgeMind Local (OS/Workspace Companion)

A lightweight local agent that provides scoped folder access, local command execution with approvals, repo inspection, file import, environment analysis, local build/test execution, and hybrid local-cloud workflows. Makes the platform feel real and usable.

### D4. Trust Layer (Approval + Replay + Audit)

Every agent action has: a decision explanation, evidence view, risk score, confidence score, replayable run, audit log, and approval gate. Users can always answer: _Why did it do this? Can I trust it? What changed? How do I reproduce it?_

### D5. Architecture Compliance + Drift Detection

ForgeMind tracks intended architecture vs. actual codebase vs. actual deployment vs. docs/runbooks. It detects drift, inconsistencies, missing security controls, and missing backup implementations. It's a **guardian of project health**, not just a generator.

### D6. Dynamic Agent Composition

Instead of running every project through the same fixed agent pipeline, ForgeMind analyzes the task, identifies required capabilities, and dynamically assembles the optimal agent team. A RAG app gets different agents than a CI/CD pipeline. The system creates the right team for every job.

---

## 3. What Users Get

### Core Platform Features

| Feature                      | Description                                                                      |
| ---------------------------- | -------------------------------------------------------------------------------- |
| **Goal-to-System Builder**   | Describe your idea → get architecture, connectors, code, tests, docs, deployment |
| **Dynamic Agent Teams**      | ForgeMind builds the right AI workforce per project (not fixed pipelines)        |
| **Connector Vault**          | OAuth setup wizard, token vault, rotation alerts, connection testing             |
| **ForgeMind Local**          | Local repo inspection, file import, build/test execution, environment analysis   |
| **Architecture Engine**      | Auto-generated architecture docs with Mermaid diagrams + drift detection         |
| **Project Planner**          | Natural language → full PRD, task breakdown, DAG visualization                   |
| **Auto-Coder**               | Agents write code following your style guide, patterns, and conventions          |
| **Code Reviewer**            | Every piece of code is reviewed by an AI reviewer before merge                   |
| **Test Generator**           | Automatic unit/integration/e2e test generation + sandboxed execution             |
| **Doc Writer**               | API docs, README, architecture docs auto-generated and kept in sync              |
| **Deploy Manager**           | One-click CI/CD pipeline generation and deployment configs                       |
| **Bug Fixer**                | Paste an error → agent diagnoses, fixes, tests, and creates a PR                 |
| **Refactor Agent**           | Highlight code → agent refactors with safety checks and tests                    |
| **Security Scanner**         | Continuous OWASP-aware security scanning + secrets detection                     |
| **Trust Dashboard**          | Risk scores, confidence scores, decision explanations, evidence views            |
| **Replay System**            | Replay any agent run with the same inputs to verify output                       |
| **Approval Gates**           | Nothing ships without your approval. Full control at every step                  |
| **Audit Trail**              | Every agent action logged — who, what, when, why, and which prompt               |
| **Drift Scorecards**         | Architecture compliance scores, codebase health, deployment state                |
| **Multi-LLM Support**        | OpenAI, Anthropic, Google, Ollama, or any OpenAI-compatible provider             |
| **Real-Time Dashboard**      | Watch agents work in real-time with live logs and progress                       |
| **Cost Tracking**            | Per-agent, per-task, per-project token usage and cost breakdown                  |
| **Team Collaboration**       | Invite team members, assign roles, share projects                                |
| **Self-Improving Workflows** | Templates, decomposition, and recommendations improve over time (governed)       |

---

## 4. Core Concepts

### Agent

A specialized autonomous worker with a defined role, tools, and boundaries. Each agent has a **contract** specifying capabilities, restrictions, tools, input/output schema, retry policy, and timeout.

### Agent Composition Engine

The intelligence layer that inspects project intent, classifies project type, identifies required capabilities, instantiates the right agents from templates, and decides parallel vs sequential execution — all within budget and policy bounds.

### Orchestrator

The brain that receives a user request, delegates to the Agent Composition Engine for team assembly, manages the task DAG, handles agent-to-agent handoffs, manages failures/retries, and enforces governance.

### Connector

An external service integration (API, OAuth provider, database, cloud service). Each connector has a registry entry with: setup instructions, required scopes, token storage, refresh logic, health check, and audit trail.

### Token Vault

Encrypted storage for all external service credentials (API keys, OAuth tokens, secrets). Supports rotation alerts, expiry tracking, scoped access (which agents can use which tokens), and never exposes raw secrets in logs or UI.

### Governance

Human-defined rules controlling agent behavior:

- Approval gates (which actions need human sign-off)
- Budget limits (max tokens/cost per task)
- Tool restrictions (which agents can access which tools)
- Rate limits (max actions per time window)
- Policy boundaries for self-improvement (what can/cannot change automatically)

### Artifact

Any output an agent produces: code files, docs, test files, configs, PRDs, diagrams, architecture docs. All artifacts are **versioned** with full diff history.

### Drift

The delta between intended state (architecture doc, deployment plan) and actual state (codebase, running infra, documentation). ForgeMind tracks drift continuously and alerts when it exceeds thresholds.

### Trust Score

A per-action metric combining: confidence level (how sure the agent is), risk level (potential impact), evidence quality (what data informed the decision), and historical accuracy (past performance on similar tasks).

### Session

A workspace context persisting across agent interactions. Contains project state, conversation history, file tree, active tasks, and connector states.

---

## 5. Updated Tech Stack

### Frontend

| Technology                          | Purpose           | Why                                                  |
| ----------------------------------- | ----------------- | ---------------------------------------------------- |
| **Next.js 15** (App Router)         | Web framework     | Server components, streaming, API routes             |
| **TypeScript 5.x**                  | Type safety       | Catch errors at compile time                         |
| **Tailwind CSS 4**                  | Styling           | Utility-first, fast iteration                        |
| **shadcn/ui**                       | Component library | Accessible, customizable, no lock-in                 |
| **Zustand**                         | State management  | Simple, fast, no boilerplate                         |
| **React Query (TanStack Query v5)** | Server state      | Caching, background refetch, optimistic updates      |
| **Socket.IO Client**                | Real-time updates | Live agent progress, logs streaming                  |
| **Monaco Editor**                   | Code editor       | VS Code-quality code editing in browser              |
| **Mermaid.js**                      | Diagrams          | Render architecture/flow diagrams from agent output  |
| **React Flow**                      | DAG visualization | Visualize task dependency graphs + agent composition |
| **Recharts**                        | Analytics charts  | Cost tracking, drift scores, performance dashboards  |

### Backend

| Technology                       | Purpose           | Why                                         |
| -------------------------------- | ----------------- | ------------------------------------------- |
| **FastAPI** (Python 3.12)        | API framework     | Async, fast, auto-docs, type-safe           |
| **Pydantic v2**                  | Data validation   | Schema validation, serialization            |
| **SQLAlchemy 2.0** + **Alembic** | ORM + Migrations  | Async ORM, reliable schema migrations       |
| **Celery 5** + **Redis**         | Task queue        | Distributed async task execution            |
| **Socket.IO (python-socketio)**  | WebSocket server  | Real-time agent status broadcasting         |
| **LiteLLM**                      | LLM gateway       | Unified API for 100+ LLM providers          |
| **LangChain / LangGraph**        | Agent framework   | Agent orchestration, tool calling, chains   |
| **Jinja2**                       | Prompt templates  | Version-controlled prompt rendering         |
| **cryptography (Fernet)**        | Secret encryption | Encrypt connector tokens + API keys at rest |
| **httpx**                        | HTTP client       | Async connector health checks + OAuth flows |

### ForgeMind Local (Desktop Companion)

| Technology                   | Purpose              | Why                                               |
| ---------------------------- | -------------------- | ------------------------------------------------- |
| **Python CLI** (Click/Typer) | Local agent          | Lightweight, cross-platform                       |
| **WebSocket client**         | Cloud sync           | Real-time communication with ForgeMind cloud      |
| **watchdog**                 | File watcher         | Detect local file changes                         |
| **subprocess**               | Command runner       | Execute local build/test commands (with approval) |
| **Docker SDK**               | Container management | Run sandboxed local tasks                         |

### Database & Storage

| Technology           | Purpose               | Why                                         |
| -------------------- | --------------------- | ------------------------------------------- |
| **PostgreSQL 16**    | Primary database      | JSONB for flexible data, robust, mature     |
| **Redis 7**          | Cache + Queue broker  | Session cache, Celery broker, rate limiting |
| **MinIO** (or S3/R2) | File/artifact storage | Store generated code, docs, artifacts       |
| **Alembic**          | DB migrations         | Version-controlled schema changes           |

### Auth & Security

| Technology                  | Purpose           | Why                                           |
| --------------------------- | ----------------- | --------------------------------------------- |
| **Clerk**                   | Authentication    | Social login, MFA, user management, free tier |
| **CASL / custom RBAC**      | Authorization     | Fine-grained permission control               |
| **python-jose**             | JWT handling      | Verify Clerk JWTs on backend                  |
| **bcrypt**                  | Secret hashing    | Hash API keys at rest                         |
| **cryptography**            | Token vault       | AES-256-GCM encryption for connector secrets  |
| **Vault** (optional, later) | Secret management | Rotate and manage secrets centrally           |

### DevOps & Infrastructure

| Technology                      | Purpose          | Why                                    |
| ------------------------------- | ---------------- | -------------------------------------- |
| **Docker** + **Docker Compose** | Containerization | Consistent local + prod environments   |
| **GitHub Actions**              | CI/CD            | Automated testing, linting, deployment |
| **Nginx** (or Caddy)            | Reverse proxy    | SSL termination, routing               |
| **Railway / Fly.io / AWS ECS**  | Hosting          | Easy deployment with scaling           |

### Monitoring & Observability

| Technology                         | Purpose              | Why                                            |
| ---------------------------------- | -------------------- | ---------------------------------------------- |
| **Prometheus** + **Grafana**       | Metrics & dashboards | Agent performance, system health, drift scores |
| **Structured logging** (structlog) | Logging              | JSON logs, correlation IDs                     |
| **Sentry**                         | Error tracking       | Catch and alert on exceptions                  |
| **OpenTelemetry**                  | Distributed tracing  | Trace requests across services                 |

### Testing

| Technology                       | Purpose           | Why                            |
| -------------------------------- | ----------------- | ------------------------------ |
| **pytest** + **pytest-asyncio**  | Backend tests     | Async test support             |
| **Vitest** + **Testing Library** | Frontend tests    | Fast, modern, React-friendly   |
| **Playwright**                   | E2E tests         | Cross-browser, reliable        |
| **Factory Boy**                  | Test fixtures     | Generate test data easily      |
| **Testcontainers**               | Integration tests | Spin up real DB/Redis in tests |

---

## 6. System Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                           FRONTEND (Next.js)                              │
│  Dashboard │ Project View │ Agent Monitor │ Code Editor │ Connector UI    │
│  Trust Dashboard │ Drift Scorecards │ Replay Viewer │ Analytics          │
└──────────────────────────────┬───────────────────────────────────────────┘
                               │ REST + WebSocket (Socket.IO)
                               ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                        API GATEWAY (FastAPI)                               │
│  Auth Middleware │ Rate Limiter │ Request Router │ WS Manager │ RBAC      │
└────────┬───────────────┬──────────────┬──────────────┬──────────────────┘
         │               │              │              │
   ┌─────▼─────┐  ┌─────▼──────┐ ┌────▼─────┐ ┌─────▼──────────┐
   │  Auth      │  │ Project    │ │Governance│ │  Connector     │
   │  Service   │  │ Service    │ │ Service  │ │  Service       │
   └───────────┘  └─────┬──────┘ └────┬─────┘ └─────┬──────────┘
                        │              │              │
                  ┌─────▼──────────────▼──────────────▼──────┐
                  │           ORCHESTRATOR ENGINE              │
                  │  ┌────────────────────────────────────┐   │
                  │  │   Agent Composition Engine          │   │
                  │  │  Project Classifier │ Team Builder  │   │
                  │  │  Capability Registry │ Templates    │   │
                  │  └────────────────────────────────────┘   │
                  │  DAG Scheduler │ Task Router │ Retry Mgr  │
                  │  Timeout Mgr │ Heartbeat Monitor           │
                  └──────────────────┬───────────────────────┘
                                     │
                  ┌──────────────────▼───────────────────────┐
                  │           CELERY TASK QUEUE                │
                  │         (Redis as Broker)                   │
                  └──┬───┬───┬───┬───┬───┬───┬───┬───┬──────┘
                     │   │   │   │   │   │   │   │   │
                     ▼   ▼   ▼   ▼   ▼   ▼   ▼   ▼   ▼
              ┌──────────────────────────────────────────────┐
              │         DYNAMIC AGENT POOL                    │
              │  Agents created per-project by Composition    │
              │  Engine based on project type + capabilities  │
              │                                               │
              │  [Planner] [Architect] [Backend] [Frontend]   │
              │  [Connector] [Security] [DevOps] [Tester]     │
              │  [Reviewer] [Documenter] [Debugger] [...]     │
              └──────────────────┬───────────────────────────┘
                                 │
              ┌──────────────────▼───────────────────────────┐
              │            CORE SERVICES LAYER                │
              │                                               │
              │  ┌─────────────┐ ┌─────────────────────────┐ │
              │  │ LiteLLM     │ │  Connector Intelligence  │ │
              │  │ Gateway     │ │  Registry │ Setup Wizard │ │
              │  │ OpenAI │    │ │  OAuth Flow │ Token Vault│ │
              │  │ Anthropic │ │ │  Health Check │ Rotation │ │
              │  │ Ollama │...│ │                           │ │
              │  └─────────────┘ └─────────────────────────┘ │
              │                                               │
              │  ┌─────────────┐ ┌─────────────────────────┐ │
              │  │ Trust       │ │  Architecture Engine     │ │
              │  │ Engine      │ │  Drift Detector          │ │
              │  │ Risk Score  │ │  Compliance Checker      │ │
              │  │ Confidence  │ │  Health Scorecards       │ │
              │  │ Replay Mgr  │ │  Intended vs Actual      │ │
              │  └─────────────┘ └─────────────────────────┘ │
              │                                               │
              │  ┌─────────────┐ ┌─────────────────────────┐ │
              │  │ Verification│ │  Self-Improvement        │ │
              │  │ Pipeline    │ │  Engine                  │ │
              │  │ Tests│Lint  │ │  Template Optimizer      │ │
              │  │ Types│Scan  │ │  Decomposition Learner   │ │
              │  │ Policy Check│ │  Policy Bounded          │ │
              │  └─────────────┘ └─────────────────────────┘ │
              └──────────────────┬───────────────────────────┘
                                 │
          ┌──────────────────────┼──────────────────────┐
          │                      │                       │
    ┌─────▼──────┐      ┌──────▼───────┐       ┌──────▼───────┐
    │ PostgreSQL  │      │   Redis      │       │ MinIO / S3   │
    │  (Data +    │      │ (Cache/Q/    │       │ (Artifacts + │
    │   Audit)    │      │  Rate Limit) │       │  Tokens)     │
    └────────────┘      └──────────────┘       └──────────────┘

         ┌──────────────────────────────────────────────┐
         │            FORGEMIND LOCAL                     │
         │  (Desktop Companion — connects via WebSocket) │
         │                                               │
         │  Scoped Folder Access │ Local Build/Test      │
         │  Environment Analysis │ File Import           │
         │  Command Execution (with approval)            │
         │  Hybrid Local/Cloud Workflow                  │
         └──────────────────────────────────────────────┘
```

---

## 7. Feature List (Complete)

### 7.1 Goal-to-System Synthesis

- [ ] Natural language project description → full system plan
- [ ] Auto-infer system type (web app, RAG app, pipeline, SaaS, CLI, etc.)
- [ ] Auto-select tech stack based on requirements
- [ ] Auto-identify required connectors/integrations
- [ ] Generate architecture document with Mermaid diagrams
- [ ] Generate PRD (Product Requirements Document)
- [ ] Generate task breakdown as DAG
- [ ] Scaffold entire project structure
- [ ] Project templates for common types (web app, API, CLI, RAG, SaaS, etc.)
- [ ] Import existing codebase for analysis + improvement

### 7.2 Dynamic Agent Composition

- [ ] **Project Classifier** — classify project type from user intent
- [ ] **Capability Registry** — what each agent type can do
- [ ] **Agent Template Registry** — templates with prompts, tools, models, limits
- [ ] **Agent Composition Engine** — assemble optimal team per project
- [ ] **Team Builder** — map classification + requirements → agent team
- [ ] Parallel execution planning (which agents can run concurrently)
- [ ] Orchestrator-approved subagent spawning (agents can request more agents)
- [ ] Per-team performance analytics
- [ ] Custom agent creation (user-defined agents with prompts + tools)
- [ ] Agent marketplace (community-shared agent templates)

### 7.3 Connector Intelligence + Token Vault

- [ ] **Connector Registry** — catalog of supported integrations (GitHub, Google, Stripe, etc.)
- [ ] **Setup Wizard** — step-by-step guided connector setup
- [ ] **Callback URI Generator** — auto-generate OAuth redirect URIs
- [ ] **Scope Guidance** — explain what each OAuth scope does and recommend minimal set
- [ ] **Token Vault** — encrypted storage (AES-256-GCM) for all external credentials
- [ ] **Connection Test** — verify connector works before using
- [ ] **Token Refresh** — automatic OAuth token refresh before expiry
- [ ] **Rotation Alerts** — notify when tokens/keys approaching expiry
- [ ] **Scoped Access** — which agents can use which connectors
- [ ] **Connector Health Dashboard** — status of all connections (green/yellow/red)
- [ ] **Audit Trail** — log every connector usage (who, when, which agent)

### 7.4 ForgeMind Local (Desktop Companion)

- [ ] Lightweight CLI agent (Python/Click)
- [ ] Scoped folder access (user grants access to specific directories)
- [ ] Local file import to cloud projects
- [ ] Local command execution with approval gates
- [ ] Environment analysis (detect installed languages, frameworks, versions)
- [ ] Local repo inspection (git status, branch, recent commits)
- [ ] Local build/test execution (run tests locally, report results)
- [ ] Hybrid local/cloud workflow (start locally, scale to cloud)
- [ ] WebSocket sync with ForgeMind cloud
- [ ] Sandboxed execution via local Docker

### 7.5 Trust Layer

- [ ] **Decision Explanation** — why the agent made each choice
- [ ] **Evidence View** — what data/context informed the decision
- [ ] **Risk Score** — per-action impact assessment (low/medium/high/critical)
- [ ] **Confidence Score** — how sure the agent is about its output (0–100%)
- [ ] **Replayable Runs** — replay any agent run with identical inputs + prompt
- [ ] **Approval Gates** — configurable per action type (code, deploy, connect, etc.)
- [ ] **Auto-approve Rules** — auto-approve low-risk, low-cost actions
- [ ] **Audit Logs** — every action with timestamp, agent, input, output, prompt version
- [ ] **Change Impact Analysis** — what this change affects across the codebase
- [ ] **Rollback Support** — revert any agent action to previous state

### 7.6 Architecture Compliance + Drift Detection

- [ ] **Intended Architecture Tracker** — store the planned architecture (from Planner)
- [ ] **Codebase Analyzer** — extract actual architecture from code
- [ ] **Deployment State Tracker** — what's actually deployed where
- [ ] **Docs/Runbooks Tracker** — are docs in sync with code
- [ ] **Drift Detector** — compare intended vs actual, flag differences
- [ ] **Health Scorecards** — per-project compliance scores
- [ ] **Missing Controls Alert** — detect missing security, backup, monitoring
- [ ] **Architecture Diff View** — visual comparison (intended vs actual)
- [ ] **Scheduled Drift Scans** — periodic automated checks
- [ ] **Drift Resolution Agent** — suggest fixes when drift detected

### 7.7 Verification-First Execution

- [ ] Every code change triggers: tests, linting, type checks
- [ ] Security scans on every generated code (OWASP Top 10)
- [ ] Secrets detection (API keys, passwords in code)
- [ ] Dependency vulnerability checking
- [ ] Policy checks (does this comply with project rules?)
- [ ] Approval steps before merge/deploy
- [ ] Sandboxed test execution (Docker containers)
- [ ] Coverage tracking and enforcement
- [ ] Test result visualization with pass/fail breakdown

### 7.8 Governed Self-Improvement

- [ ] Template optimization — improve agent templates based on success rates
- [ ] Task decomposition learning — better breakdowns over time
- [ ] Retry logic improvement — learn which retry strategies work
- [ ] Connector recommendations — suggest connectors based on project type
- [ ] Stack defaults — improve default tech choices from outcomes
- [ ] **Policy Boundaries** — self-improvement CANNOT:
  - Change core governance policies
  - Escalate agent privileges
  - Run destructive actions autonomously
  - Bypass approval gates
  - Modify security configurations

### 7.9 Core Agent Features

- [ ] Planner Agent — PRD, architecture, task decomposition
- [ ] Architect Agent — system design, component diagrams, tech selection
- [ ] Coder Agent (Backend) — server-side code generation
- [ ] Coder Agent (Frontend) — UI code generation
- [ ] Connector Agent — integration setup, OAuth flows, API wiring
- [ ] Reviewer Agent — code review with actionable feedback
- [ ] Tester Agent — test generation and execution
- [ ] Documenter Agent — docs, README, API docs, architecture docs
- [ ] Debugger Agent — diagnose and fix errors
- [ ] Refactor Agent — improve code quality
- [ ] Security Agent — OWASP scanning, vulnerability detection
- [ ] DevOps Agent — CI/CD, Docker, deployment configs
- [ ] Researcher Agent — find solutions, reference code, docs search
- [ ] Monitoring Agent — health checks, alerting config, dashboard generation

### 7.10 Orchestration & Governance

- [ ] DAG-based task scheduling with dependency resolution
- [ ] Human approval gates (configurable per action type)
- [ ] Budget limits per agent, per task, per project
- [ ] Rate limiting (max N actions per minute/hour)
- [ ] Agent timeout policies (per-agent configurable)
- [ ] Cancellation support (cancel running tasks/agents)
- [ ] Retry policies with exponential backoff
- [ ] Idempotency keys for all agent actions
- [ ] Agent heartbeat monitoring (detect stuck agents)
- [ ] Error taxonomy (transient vs permanent failures)
- [ ] Circuit breaker pattern for failing agents
- [ ] Dead letter queue for permanently failed tasks

### 7.11 Real-Time Features

- [ ] Live agent activity stream (Socket.IO)
- [ ] Real-time log viewer per agent
- [ ] Task progress indicators
- [ ] Notification system (in-app + email)
- [ ] Collaborative cursors (team members see each other's focus)
- [ ] Live drift score updates

### 7.12 Code & Artifact Management

- [ ] In-browser code editor (Monaco)
- [ ] Artifact versioning (every generated file has history)
- [ ] Diff viewer (compare artifact versions)
- [ ] Git-like branching for agent experiments
- [ ] File tree browser with search
- [ ] Prompt versioning (track which prompt version produced which output)

### 7.13 LLM & Cost Management

- [ ] Multi-provider support via LiteLLM
- [ ] Per-request cost tracking
- [ ] Per-agent cost breakdown
- [ ] Per-project budget with alerts
- [ ] Smart model routing (cheap models for simple tasks, powerful for complex)
- [ ] Prompt caching for repeated operations
- [ ] Token usage analytics dashboard
- [ ] Model comparison (cost vs quality metrics)

### 7.14 User & Team

- [ ] User registration/login (Clerk)
- [ ] Social login (Google, GitHub)
- [ ] Team workspaces
- [ ] Role-based access control (Owner, Admin, Member, Viewer)
- [ ] Invite system
- [ ] Activity feed per team
- [ ] API key management (encrypted at rest)

### 7.15 Audit & Compliance

- [ ] Full audit log (every agent action with timestamp, input, output, prompt)
- [ ] Prompt audit trail (which prompt version was used)
- [ ] Connector usage audit (which agent used which secret, when)
- [ ] Export audit logs (CSV, JSON)
- [ ] Data retention policies
- [ ] GDPR-friendly data deletion

### 7.16 Integrations (Later Phases)

- [ ] GitHub / GitLab integration
- [ ] Slack notifications
- [ ] VS Code extension
- [ ] CLI tool
- [ ] Webhook system (notify external services)
- [ ] REST API for third-party integrations

---

## 8. Database Schema

### Core Tables (from v1 — unchanged)

```
users
├── id (UUID, PK)
├── clerk_id (VARCHAR, UNIQUE)
├── email (VARCHAR, UNIQUE)
├── name (VARCHAR)
├── avatar_url (VARCHAR)
├── role (ENUM: admin, user)
├── created_at, updated_at

teams
├── id (UUID, PK)
├── name (VARCHAR)
├── owner_id (FK → users)
├── settings (JSONB)
├── created_at, updated_at

team_members
├── team_id (FK → teams)
├── user_id (FK → users)
├── role (ENUM: owner, admin, member, viewer)

projects
├── id (UUID, PK)
├── team_id (FK → teams)
├── name (VARCHAR)
├── description (TEXT)
├── project_type (VARCHAR)  -- NEW: web_app, rag_app, pipeline, saas, cli, etc.
├── status (ENUM: planning, active, paused, completed, archived)
├── settings (JSONB)  -- approval gates, budget, model prefs
├── intended_architecture (JSONB)  -- NEW: planned architecture snapshot
├── drift_score (FLOAT, DEFAULT 100.0)  -- NEW: 100 = perfect alignment
├── last_drift_scan (TIMESTAMP)  -- NEW
├── created_at, updated_at

tasks
├── id (UUID, PK)
├── project_id (FK → projects)
├── parent_task_id (FK → tasks, nullable)
├── title (VARCHAR)
├── description (TEXT)
├── status (ENUM: pending, queued, running, awaiting_approval, completed, failed, cancelled)
├── assigned_agent (VARCHAR)
├── priority (INT)
├── depends_on (UUID[])
├── idempotency_key (VARCHAR, UNIQUE)
├── retry_count (INT, DEFAULT 0)
├── max_retries (INT, DEFAULT 3)
├── timeout_seconds (INT)
├── started_at, completed_at, created_at

task_results
├── id (UUID, PK)
├── task_id (FK → tasks)
├── output (JSONB)
├── error (TEXT, nullable)
├── error_type (ENUM: transient, permanent, timeout, nullable)
├── tokens_used (INT)
├── cost_usd (DECIMAL)
├── model_used (VARCHAR)
├── prompt_version (VARCHAR)
├── duration_ms (INT)
├── risk_score (FLOAT)         -- NEW: trust layer
├── confidence_score (FLOAT)   -- NEW: trust layer
├── evidence (JSONB)           -- NEW: what data informed the decision
├── replay_hash (VARCHAR)      -- NEW: deterministic hash for replay
├── created_at
```

### New Tables (v2)

```
connectors
├── id (UUID, PK)
├── team_id (FK → teams)
├── name (VARCHAR)  -- e.g., "GitHub", "Google Sheets", "Stripe"
├── connector_type (VARCHAR)  -- oauth2, api_key, webhook
├── provider (VARCHAR)  -- github, google, stripe, etc.
├── status (ENUM: active, expired, error, disconnected)
├── config (JSONB)  -- provider-specific settings (scopes, endpoints)
├── last_health_check (TIMESTAMP)
├── last_used_at (TIMESTAMP)
├── created_at, updated_at

connector_tokens
├── id (UUID, PK)
├── connector_id (FK → connectors)
├── token_encrypted (BYTEA)   -- AES-256-GCM encrypted
├── refresh_token_encrypted (BYTEA, nullable)
├── token_type (VARCHAR)  -- access_token, api_key, client_secret
├── scopes (VARCHAR[])
├── expires_at (TIMESTAMP, nullable)
├── rotated_at (TIMESTAMP, nullable)
├── created_at

connector_usage_log
├── id (UUID, PK)
├── connector_id (FK → connectors)
├── task_id (FK → tasks, nullable)
├── agent_type (VARCHAR)
├── action (VARCHAR)  -- "api_call", "token_refresh", "health_check"
├── status (ENUM: success, failure)
├── error_message (TEXT, nullable)
├── created_at

connector_registry
├── id (UUID, PK)
├── provider (VARCHAR, UNIQUE)  -- github, google, stripe, etc.
├── display_name (VARCHAR)
├── auth_type (VARCHAR)  -- oauth2, api_key, basic
├── setup_instructions (JSONB)  -- step-by-step setup guide
├── required_scopes (VARCHAR[])
├── recommended_scopes (VARCHAR[])
├── callback_uri_template (VARCHAR)
├── docs_url (VARCHAR)
├── icon_url (VARCHAR)
├── is_active (BOOLEAN)
├── created_at

agent_templates
├── id (UUID, PK)
├── agent_type (VARCHAR)  -- e.g., "planner", "backend_coder", "connector"
├── display_name (VARCHAR)
├── description (TEXT)
├── capabilities (VARCHAR[])  -- e.g., ["planning", "architecture", "decomposition"]
├── restrictions (VARCHAR[])
├── system_prompt (TEXT)
├── prompt_version (VARCHAR)
├── model_preference (VARCHAR)
├── fallback_model (VARCHAR)
├── tools_allowed (VARCHAR[])
├── max_tokens (INT)
├── temperature (FLOAT)
├── timeout_seconds (INT)
├── rate_limit_per_minute (INT)
├── retry_policy (JSONB)  -- { max_retries, backoff, retry_on }
├── is_builtin (BOOLEAN)  -- system-provided vs user-created
├── created_by (FK → users, nullable)
├── created_at, updated_at

capability_registry
├── id (UUID, PK)
├── capability (VARCHAR, UNIQUE)  -- e.g., "backend_coding", "oauth_setup"
├── description (TEXT)
├── agent_types (VARCHAR[])  -- which agent templates have this capability
├── created_at

project_agent_teams
├── id (UUID, PK)
├── project_id (FK → projects)
├── agent_template_id (FK → agent_templates)
├── instantiated_at (TIMESTAMP)
├── config_overrides (JSONB)  -- project-specific overrides
├── status (ENUM: active, completed, failed)
├── tasks_completed (INT, DEFAULT 0)
├── tokens_used (INT, DEFAULT 0)
├── cost_usd (DECIMAL, DEFAULT 0)

architecture_snapshots
├── id (UUID, PK)
├── project_id (FK → projects)
├── snapshot_type (ENUM: intended, actual_code, actual_deploy, actual_docs)
├── snapshot_data (JSONB)  -- parsed architecture representation
├── created_by (VARCHAR)  -- "planner_agent", "drift_scan", "user"
├── created_at

drift_reports
├── id (UUID, PK)
├── project_id (FK → projects)
├── intended_snapshot_id (FK → architecture_snapshots)
├── actual_snapshot_id (FK → architecture_snapshots)
├── drift_score (FLOAT)  -- 0-100, 100 = perfect
├── findings (JSONB)  -- array of { category, severity, description, suggestion }
├── created_at

trust_scores
├── id (UUID, PK)
├── task_id (FK → tasks)
├── risk_level (ENUM: low, medium, high, critical)
├── confidence_percent (FLOAT)  -- 0-100
├── evidence_summary (TEXT)
├── decision_explanation (TEXT)
├── created_at

replay_snapshots
├── id (UUID, PK)
├── task_id (FK → tasks)
├── input_snapshot (JSONB)  -- exact inputs used
├── prompt_snapshot (TEXT)  -- exact prompt sent
├── model_used (VARCHAR)
├── temperature (FLOAT)
├── output_snapshot (JSONB)  -- exact output received
├── replay_hash (VARCHAR)  -- for deduplication
├── created_at

self_improvement_log
├── id (UUID, PK)
├── improvement_type (VARCHAR)  -- template, decomposition, retry, connector_rec
├── before_state (JSONB)
├── after_state (JSONB)
├── reason (TEXT)  -- why the improvement was made
├── performance_delta (FLOAT)  -- measured improvement
├── approved_by (FK → users, nullable)  -- null if auto-approved within policy
├── policy_check_passed (BOOLEAN)
├── created_at

-- Tables from v1 (unchanged)
artifacts              -- (same as v1)
artifact_versions      -- (same as v1)
agent_configs          -- (same as v1, kept for backward compat)
audit_logs             -- (same as v1)
approval_gates         -- (same as v1)
api_keys               -- (same as v1)
llm_provider_configs   -- (same as v1)
```

---

## 9. Agent Definitions & Dynamic Composition

### How Dynamic Agent Composition Works

```
User: "Build a RAPTOR RAG app with secure file upload and source citations"
                    │
                    ▼
        ┌───────────────────────┐
        │   PROJECT CLASSIFIER   │
        │                        │
        │  Input: user prompt    │
        │  Output:               │
        │   type: rag_app        │
        │   needs: retrieval,    │
        │     storage, citation, │
        │     security, upload   │
        └───────────┬───────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │  CAPABILITY RESOLVER   │
        │                        │
        │  Required:             │
        │  - planning            │
        │  - architecture        │
        │  - backend_api         │
        │  - retrieval_pipeline  │
        │  - vector_db           │
        │  - file_storage        │
        │  - frontend_chat       │
        │  - security_review     │
        │  - testing             │
        │  - documentation       │
        └───────────┬───────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │     TEAM BUILDER       │
        │                        │
        │  Maps capabilities →   │
        │  agent templates:      │
        │                        │
        │  1. Architect Agent    │
        │  2. Retrieval Agent    │
        │  3. Backend Agent      │
        │  4. Frontend Agent     │
        │  5. Storage Agent      │
        │  6. Security Agent     │
        │  7. Test Agent         │
        │  8. Docs Agent         │
        └───────────┬───────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │   DAG SCHEDULER        │
        │                        │
        │  Phase 1: Architect    │
        │  Phase 2: Backend,     │
        │    Frontend, Storage,  │
        │    Retrieval (parallel)│
        │  Phase 3: Security,    │
        │    Tests (parallel)    │
        │  Phase 4: Docs         │
        │  Phase 5: Verify all   │
        └───────────────────────┘
```

### Agent Template Contract

```yaml
agent_type: "backend_coder"
display_name: "Backend Coder Agent"
description: "Generates server-side code (APIs, services, DB models)"
capabilities:
  - backend_api
  - database_models
  - server_logic
  - authentication
restrictions:
  - cannot_deploy
  - cannot_delete_files
  - cannot_access_other_project_data
  - cannot_modify_governance
input_schema:
  task_description: string
  file_context: string[]
  architecture_ref: string
  style_guide: string (optional)
output_schema:
  files_created: FileChange[]
  files_modified: FileChange[]
  explanation: string
  risk_assessment: { level: string, reason: string }
  confidence: float
tools:
  - file_read
  - file_write
  - search_codebase
  - run_linter
  - run_type_check
retry_policy:
  max_retries: 3
  backoff: exponential
  retry_on: [transient_error, timeout, rate_limit]
timeout: 300s
rate_limit: 20/minute
model_preference: "claude-sonnet-4-20250514"
fallback_model: "gpt-4o"
```

### Dynamic Agent Examples by Project Type

| Project Type                    | Agents Assembled                                                                                                                              |
| ------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| **YouTube Automation Pipeline** | Planner, Workflow Architect, Connector Agent, Scheduler Agent, Media Pipeline Agent, Upload Agent, Monitoring Agent, Docs Agent               |
| **RAPTOR RAG System**           | Planner, AI Architect, Retrieval Agent, Vector DB Agent, Data Pipeline Agent, Backend Agent, Frontend Agent, Security Agent, Evaluation Agent |
| **SaaS with Auth + Billing**    | Planner, Architect, Backend Agent, Frontend Agent, Auth Agent, Billing/Connector Agent, DevOps Agent, Tester, Security Agent, Docs Agent      |
| **CI/CD + Infra Automation**    | Planner, DevOps Agent, Cloud Agent, Security Agent, Secrets Agent, Monitoring Agent, Cost Agent                                               |
| **Bug Fix Request**             | Debugger Agent, Tester Agent, Reviewer Agent                                                                                                  |
| **Code Refactor**               | Refactor Agent, Tester Agent, Reviewer Agent, Docs Agent                                                                                      |

### Hierarchical Agent Spawning (Advanced)

Agents can **request** additional sub-agents, but only the orchestrator can approve/instantiate them:

```
Main Architect Agent
├── requests → Backend Specialist (approved by orchestrator)
│   ├── requests → Auth Subagent (approved)
│   ├── requests → DB Subagent (approved)
│   └── requests → API Subagent (denied — budget limit)
├── requests → Frontend Specialist (approved)
└── requests → Infra Specialist (approved)
```

**Rule**: Agents can _request_ more agents. The orchestrator decides whether to create them based on budget, policy, and necessity. No infinite self-spawn.

### Full Agent Roster (Templates)

| Agent              | Role                                      | Model Tier                  | Tools                                       | Approval               |
| ------------------ | ----------------------------------------- | --------------------------- | ------------------------------------------- | ---------------------- |
| **Planner**        | PRD, goals, requirements                  | High (Claude Sonnet/GPT-4o) | web_search, file_read                       | Yes — for plan         |
| **Architect**      | System design, component diagrams         | High                        | file_read, diagram_gen                      | Yes — for architecture |
| **Backend Coder**  | Server code, APIs, DB models              | High                        | file_read, file_write, lint, typecheck      | Yes — for merge        |
| **Frontend Coder** | UI code, components, styling              | High                        | file_read, file_write, lint                 | Yes — for merge        |
| **Connector**      | OAuth setup, API wiring, token management | High                        | connector_registry, token_vault, http_call  | Yes — always           |
| **Reviewer**       | Code review, quality checks               | High                        | file_read, search, run_tests                | No — advisory          |
| **Tester**         | Generate & run tests                      | Medium (GPT-4o-mini)        | file_read, file_write, run_tests            | No                     |
| **Documenter**     | Docs, README, API docs                    | Medium                      | file_read, file_write                       | No                     |
| **Debugger**       | Error diagnosis, bug fixes                | High                        | file_read, file_write, run_tests, read_logs | Yes — for fix          |
| **Refactor**       | Code improvement, optimization            | High                        | file_read, file_write, run_tests, lint      | Yes — for changes      |
| **Security**       | Vulnerability scanning, secrets detection | High                        | file_read, search, security_scan            | No — advisory          |
| **DevOps**         | CI/CD, Docker, deployment configs         | Medium                      | file_read, file_write, run_commands         | Yes — always           |
| **Researcher**     | Find solutions, reference code            | Low (GPT-4o-mini)           | web_search, read_docs                       | No                     |
| **Monitoring**     | Health checks, alerting, dashboards       | Medium                      | file_read, file_write                       | No                     |
| **Drift Detector** | Architecture compliance checking          | Medium                      | file_read, search, compare                  | No — advisory          |

---

## 10. Phase-Wise Implementation

---

### Phase 0: Foundation & Project Setup (Week 1–2)

**Goal**: Monorepo, dev environment, CI pipeline, base configs.

#### Tasks

- [ ] Initialize monorepo structure
  ```
  forgemind/
  ├── apps/
  │   ├── web/              # Next.js frontend
  │   ├── api/              # FastAPI backend
  │   └── local/            # ForgeMind Local CLI
  ├── packages/
  │   └── shared/           # Shared types, constants
  ├── docker/
  │   ├── Dockerfile.web
  │   ├── Dockerfile.api
  │   └── docker-compose.yml
  ├── .github/
  │   └── workflows/
  │       ├── ci.yml
  │       └── lint.yml
  ├── .env.example
  ├── Makefile
  └── README.md
  ```
- [ ] Set up **Docker Compose** (PostgreSQL, Redis, MinIO, API, Web)
- [ ] Set up **FastAPI** skeleton with health check endpoint
- [ ] Set up **Next.js 15** with TypeScript, Tailwind, shadcn/ui
- [ ] Configure **Alembic** for database migrations
- [ ] Configure **GitHub Actions** CI (lint + test on PR)
- [ ] Create **Makefile** (`make dev`, `make test`, `make migrate`)
- [ ] Set up **structlog** for JSON logging with correlation IDs
- [ ] Set up **pre-commit hooks** (ruff, black, eslint, prettier)

#### Deliverables

- `docker compose up` starts everything
- API at `/health` → `{ "status": "ok" }`
- Frontend at `localhost:3000`
- CI runs on every PR

---

### Phase 1: Auth, Users & Database (Week 3–4)

**Goal**: Users can sign up, log in, RBAC works. All DB tables created.

#### Tasks

- [ ] Integrate **Clerk** (frontend + backend JWT verification)
- [ ] Create ALL database tables (core + v2 tables from Schema section)
- [ ] Write Alembic migrations
- [ ] Implement user sync webhook (Clerk → PostgreSQL)
- [ ] Build API endpoints:
  - `POST /v1/auth/webhook` — Clerk webhook
  - `GET /v1/users/me` — Current user
  - `PATCH /v1/users/me` — Update profile
- [ ] Build frontend pages:
  - Sign in / Sign up (Clerk)
  - User settings
  - Dashboard layout (sidebar + main)
- [ ] Set up **RBAC middleware** in FastAPI
- [ ] Implement **API key management** (create, list, revoke, hashed)
- [ ] Seed database with Factory Boy

#### Deliverables

- Users sign up with Google/GitHub/email
- JWT auth on all protected routes
- Dashboard layout with user info
- API keys work for authentication

---

### Phase 2: Projects, Task Engine & Orchestrator Core (Week 5–7)

**Goal**: Users create projects, DAG engine schedules work, orchestrator core runs.

#### Tasks

- [ ] Build **Project CRUD** API (create, list, get, update, archive)
- [ ] Build **Task Engine**:
  - Task CRUD with DAG structure
  - DAG dependency resolver (topological sort)
  - Task state machine (pending → queued → running → completed/failed)
- [ ] Set up **Celery** with Redis broker:
  - Worker config, task routing, retry with backoff
  - Timeout enforcement, cancellation (revoke)
- [ ] Build **Orchestrator** core:
  - Accept high-level goal → break into tasks (stub planner)
  - Schedule tasks respecting dependencies
  - Task completion → trigger dependents
  - Task failure → retry or escalate
- [ ] Build frontend:
  - Project creation wizard
  - Project list/grid view
  - Project detail page
  - Task DAG visualization (React Flow)
  - Task status indicators

#### Deliverables

- User creates project → sees it on dashboard
- Tasks with dependencies work
- Celery processes tasks
- DAG visualizer shows task flow

---

### Phase 3: LLM Integration + Planner Agent + Project Classifier (Week 8–11)

**Goal**: First working agent. User describes idea → gets PRD + architecture + task breakdown. Project type is auto-classified.

#### Tasks

- [ ] Integrate **LiteLLM** as LLM gateway:
  - Configure providers (OpenAI, Anthropic, Ollama)
  - Model routing per agent, token counting, cost calc
  - Streaming support
- [ ] Build **Agent Base Class**:

  ```python
  class BaseAgent:
      agent_type: str
      model: str
      system_prompt: str
      tools: list[Tool]
      rate_limiter: RateLimiter
      timeout: int

      async def execute(self, task: Task) -> AgentResult
      async def stream(self, task: Task) -> AsyncIterator[str]
      def validate_input(self, input: dict) -> bool
      def validate_output(self, output: dict) -> bool
      def explain_decision(self) -> str           # NEW: trust layer
      def assess_risk(self) -> RiskScore           # NEW: trust layer
      def assess_confidence(self) -> float         # NEW: trust layer
  ```

- [ ] Build **Project Classifier**:
  - Input: user prompt (natural language)
  - Output: project_type, required_capabilities, suggested_stack
  - Uses LLM to classify (web_app, rag_app, pipeline, saas, cli, etc.)
- [ ] Build **Planner Agent**:
  - Input: project description + classified type
  - Output: PRD, architecture doc (Mermaid), task list with dependencies
  - Output includes risk assessment + confidence score
- [ ] Build **Prompt Management System**:
  - Versioned Jinja2 templates
  - `prompt_versions` table
- [ ] Build **LLM Provider Settings** page:
  - Add API keys (encrypted), select default model, test connection
- [ ] Implement **Socket.IO** for real-time agent updates
- [ ] Build frontend:
  - "New Project" flow: describe idea → see classification → watch Planner work → review PRD
  - PRD viewer/editor, task list from plan
  - Real-time progress indicator

#### Deliverables

- "Build a RAPTOR RAG app" → classified as `rag_app`
- Planner generates full PRD + architecture + DAG
- Streaming output to UI
- Project type and required capabilities stored

---

### Phase 4: Dynamic Agent Composition Engine (Week 12–14)

**Goal**: The system dynamically assembles the right agent team per project.

This is ForgeMind's **core innovation**.

#### Tasks

- [ ] Build **Capability Registry**:
  - Seed with capabilities: planning, architecture, backend_api, frontend_ui, retrieval_pipeline, oauth_setup, security_review, testing, documentation, devops, monitoring, etc.
  - CRUD API for capabilities
- [ ] Build **Agent Template Registry**:
  - Seed with 15 built-in agent templates (see Agent Roster)
  - Each template: type, prompt, tools, model, timeout, rate limit, retry
  - CRUD API for templates
  - Custom template creation by users
- [ ] Build **Agent Composition Engine**:
  - Input: project classification + required capabilities
  - Maps capabilities → agent templates
  - Decides parallel vs sequential execution plan
  - Respects budget + policy limits
  - Returns: agent team + execution DAG
- [ ] Build **Team Builder** service:
  - Instantiate agents for a project
  - Store in `project_agent_teams` table
  - Track per-agent metrics (tasks, tokens, cost)
- [ ] Build **Orchestrator-Approved Subagent Spawning**:
  - Agent can request additional subagents
  - Orchestrator approves/denies based on budget + need
  - No infinite self-spawn
- [ ] Build frontend:
  - Agent team visualization per project
  - Capability graph view
  - Agent performance per project
  - "Why these agents?" explanation

#### Deliverables

- "Build a SaaS with auth and billing" → system creates: Planner, Architect, Backend Coder, Frontend Coder, Auth Agent, Billing Connector Agent, DevOps, Tester, Security, Docs
- Different projects get different agent teams
- User sees which agents were assembled and why
- Budget-aware team sizing

---

### Phase 5: Connector Intelligence + Token Vault (Week 15–18)

**Goal**: ForgeMind's strongest practical differentiator — make integrations painless.

#### Tasks

- [ ] Build **Connector Registry** (seed with 20+ common connectors):
  - GitHub, GitLab, Google (Sheets, Drive, Gmail, Calendar)
  - Stripe, Slack, Discord, Twitter/X, YouTube
  - AWS, GCP, Azure, Vercel, Railway
  - PostgreSQL, MongoDB, Redis, Pinecone, Weaviate
  - SendGrid, Twilio, OpenAI, Anthropic
- [ ] Build **Connector Setup Wizard**:
  - Step-by-step guided flow per connector
  - Auto-generate callback URIs
  - Scope selector with plain-English explanations
  - "What does each scope do?" tooltips
- [ ] Build **Token Vault**:
  - AES-256-GCM encryption for all stored credentials
  - Scoped access (which agents can use which tokens)
  - Never log or return raw secrets
  - Encrypted at rest in PostgreSQL (BYTEA column)
- [ ] Build **OAuth2 Flow Handler**:
  - Authorization code flow
  - Token exchange
  - Automatic refresh before expiry
  - PKCE support for public clients
- [ ] Build **Connection Test** system:
  - Each connector has a health check definition
  - Test button in UI → verify connector works
  - Periodic automated health checks
  - Status indicators (green/yellow/red)
- [ ] Build **Rotation & Expiry Alerts**:
  - Track token expiry dates
  - Alert 7 days, 3 days, 1 day before expiry
  - Suggest rotation for long-lived tokens
- [ ] Build **Connector Agent**:
  - Reads from connector registry
  - Helps users set up new connections
  - Wires connectors into generated code
  - Handles OAuth flows on behalf of the project
- [ ] Build **Connector Dashboard** (frontend):
  - All connections with status
  - Setup wizard UI
  - Token expiry timeline
  - Usage logs per connector
  - "Add Connection" button → guided flow
- [ ] Build **Connector Usage Audit**:
  - Log every connector use (which agent, which task, when)
  - Export audit data

#### Deliverables

- User clicks "Add GitHub" → gets guided setup → connection verified in 60 seconds
- Connector Agent wires GitHub into generated CI/CD pipeline
- Token vault encrypted, audited, with rotation alerts
- Dashboard shows all connector health at a glance

---

### Phase 6: Coder Agents + Artifact System + Verification Pipeline (Week 19–22)

**Goal**: Code generation with verification-first execution. Every code change is tested, linted, type-checked, and security-scanned.

#### Tasks

- [ ] Build **Backend Coder Agent**:
  - Generates server code, APIs, DB models
  - Uses architecture ref from Planner/Architect
  - Context window management (relevant file selection)
- [ ] Build **Frontend Coder Agent**:
  - Generates UI components, pages, styling
  - Follows design system / component library conventions
- [ ] Build **Artifact System**:
  - Store files in MinIO/S3, version every change
  - Diffs, checksums, metadata
  - Artifact API (get, list versions, compare)
- [ ] Build **Verification Pipeline** (runs on EVERY code change):
  - **Step 1**: Lint (ruff/eslint)
  - **Step 2**: Type check (mypy/tsc)
  - **Step 3**: Tests (pytest/vitest) in sandboxed Docker
  - **Step 4**: Security scan (OWASP patterns, secrets detection)
  - **Step 5**: Policy check (project-specific rules)
  - **Step 6**: Approval gate (if configured)
  - All results stored and shown in UI
- [ ] Build **Reviewer Agent**:
  - Code review with line-specific comments
  - Checks: bugs, style, performance, security, best practices
  - Auto-triggered after Coder completes
- [ ] Build **Code Editor** (frontend):
  - Monaco Editor, file tree, syntax highlighting
  - Diff viewer (side-by-side)
  - Verification results panel
  - "Accept / Reject changes" UI
- [ ] Build **Agent Pipeline**:
  - Coder → Verification → Reviewer → Approval → merge
  - If verification fails → Coder fixes → re-verify

#### Deliverables

- Tasks → code generated → automatically verified (lint + types + tests + security)
- Reviewer comments on code
- User approves/rejects with full evidence
- Version history for every file

---

### Phase 7: Trust Layer + Replay System (Week 23–25)

**Goal**: Full trust infrastructure. Every decision is explainable, scoreable, and replayable.

#### Tasks

- [ ] Build **Trust Engine**:
  - Risk score calculation per action (based on action type, scope, cost)
  - Confidence score per agent output (from LLM's self-assessment + heuristics)
  - Evidence collection (what context/data informed the decision)
  - Decision explanation generation
- [ ] Build **Replay System**:
  - Snapshot every agent run (input, prompt, model, temp, output)
  - Replay button → re-run with identical inputs
  - Compare original vs replay output
  - Hash-based deduplication
- [ ] Build **Change Impact Analysis**:
  - When an agent modifies code → show what else it affects
  - Dependency graph analysis
  - "Blast radius" visualization
- [ ] Build **Rollback Support**:
  - Revert any agent action to previous artifact version
  - Rollback with reason logged in audit
- [ ] Build **Trust Dashboard** (frontend):
  - Per-task: risk score, confidence, evidence, explanation
  - Per-project: aggregate trust metrics
  - Replay viewer (original vs replay side-by-side)
  - Change impact visualization
  - Rollback button with confirmation
- [ ] Enhance **Approval Gates** with trust data:
  - Show risk + confidence when requesting approval
  - Auto-approve if risk=low AND confidence>90% AND cost<threshold

#### Deliverables

- Every agent action shows: "Why did it do this?" + risk + confidence
- User can replay any action to verify
- Rollback any change with audit trail
- Trust-aware approval gates

---

### Phase 8: Architecture Engine + Drift Detection (Week 26–28)

**Goal**: ForgeMind becomes a guardian of project health, not just a generator.

#### Tasks

- [ ] Build **Architecture Snapshot Service**:
  - Store intended architecture (from Planner/Architect Agent)
  - Extract actual architecture from codebase (static analysis)
  - Extract deployment state (from DevOps configs)
  - Extract docs state (from generated docs)
- [ ] Build **Drift Detector**:
  - Compare intended vs actual (code, deploy, docs)
  - Flag differences: missing components, extra components, wrong patterns
  - Detect: missing security controls, missing backup configs, missing monitoring
  - Categorize by severity (info, warning, critical)
- [ ] Build **Health Scorecards**:
  - Architecture compliance score (0–100)
  - Security completeness score
  - Test coverage score
  - Documentation freshness score
  - Connector health score
  - Overall project health = weighted average
- [ ] Build **Scheduled Drift Scans**:
  - Configurable schedule (daily/weekly)
  - Auto-run after major changes
  - Notify on score drops
- [ ] Build **Drift Resolution Agent**:
  - Suggests fixes when drift detected
  - Can auto-fix simple drift (with approval)
  - Prioritized fix suggestions
- [ ] Build frontend:
  - Architecture diff view (Mermaid: intended vs actual side-by-side)
  - Health scorecard dashboard
  - Drift findings list with severity
  - "Fix Drift" actions (approval-gated)
  - Score trend charts over time

#### Deliverables

- Project dashboard shows architecture compliance score
- Drift alert when code doesn't match intended architecture
- "Your docs are 3 weeks behind code" warning
- One-click drift fix suggestions

---

### Phase 9: ForgeMind Local (Desktop Companion) (Week 29–31)

**Goal**: Lightweight local agent for real-world developer workflow integration.

#### Tasks

- [ ] Build **ForgeMind Local CLI** (Python + Click/Typer):
  - `forgemind-local init` — connect to ForgeMind cloud project
  - `forgemind-local scan` — analyze local environment
  - `forgemind-local import <path>` — import local files to cloud project
  - `forgemind-local exec <command>` — run command with approval
  - `forgemind-local watch` — watch local folder for changes
  - `forgemind-local test` — run tests locally, report to cloud
  - `forgemind-local status` — show project status
- [ ] **Scoped Folder Access**:
  - User grants access to specific directories only
  - ForgeMind Local cannot access anything outside granted paths
  - Displayed clearly: "ForgeMind has access to: /project/src, /project/tests"
- [ ] **Environment Analysis**:
  - Detect: Python version, Node version, installed packages
  - Detect: Git status, branch, recent commits
  - Detect: Docker availability, running containers
  - Report to cloud for Planner/Architect context
- [ ] **Local Command Execution**:
  - All commands require user approval before execution
  - Sandboxed execution option (Docker container)
  - Output streaming to cloud dashboard
  - Command history + audit log
- [ ] **Hybrid Local/Cloud Workflow**:
  - Code generated in cloud → synced to local via CLI
  - Local edits → synced back to cloud
  - Local test results → reported in cloud dashboard
  - Conflict resolution for bidirectional sync
- [ ] **WebSocket Connection**:
  - Persistent connection to ForgeMind cloud
  - Receive agent instructions
  - Stream local results back
  - Auto-reconnect with backoff
- [ ] Build frontend integration:
  - "ForgeMind Local" status indicator in dashboard
  - Local environment info panel
  - Local command approval UI
  - Sync status indicators

#### Deliverables

- `pip install forgemind-local` → connect to cloud project
- `forgemind-local scan` → shows Python 3.12, Node 20, Docker available
- `forgemind-local exec "pytest"` → prompts user approval → runs → reports
- Local file changes sync to cloud project

---

### Phase 10: Testing Agents + Debugging (Week 32–33)

**Goal**: Auto-generated tests, sandboxed execution, intelligent debugging.

#### Tasks

- [ ] Build **Tester Agent** (enhanced):
  - Generate unit, integration, e2e tests
  - Analyze code paths and edge cases
  - Language-aware (pytest for Python, vitest for JS/TS)
  - Uses Architect output for integration test scoping
- [ ] Build **Test Runner Service**:
  - Execute tests in sandboxed Docker containers
  - Parse results (pass/fail/error)
  - Coverage report generation
  - Store results in database
- [ ] Build **Debugger Agent**:
  - Input: error + stack trace + code context
  - Root cause analysis with evidence
  - Auto-fix with test verification
  - Risk + confidence scores on proposed fixes
- [ ] Build frontend:
  - Test results dashboard, coverage visualization
  - Error log viewer
  - "Fix this error" one-click action
- [ ] Wire up: Coder → Verification → Tester → (if fail) → Debugger → re-test

#### Deliverables

- Every code change gets auto-generated tests
- Tests run in sandboxed containers
- Debugger Agent fixes failures with evidence
- Full test/coverage dashboard

---

### Phase 11: Docs, Security Agents + Cost Analytics (Week 34–36)

**Goal**: Auto-docs, security scanning, and full cost visibility.

#### Tasks

- [ ] Build **Documenter Agent** (enhanced):
  - Auto-generate README, API docs, architecture docs
  - Mermaid diagrams from code analysis
  - Inline comments for complex logic
  - Keep docs in sync when code changes (drift-aware)
- [ ] Build **Security Agent** (enhanced):
  - OWASP Top 10 scanning
  - Dependency vulnerability check
  - Secrets detection
  - SQL injection / XSS pattern detection
  - Security report + score
  - Critical findings block approval
- [ ] Build **Cost Tracking Service**:
  - Tokens per request (input + output)
  - Cost by provider pricing
  - Per-agent, per-task, per-project aggregation
  - Budget enforcement (stop agents if exceeded)
- [ ] Build **Analytics Dashboard**:
  - Spend: daily/weekly/monthly, per agent, per project
  - Token usage trends
  - Agent success/failure rates
  - Average task completion time
  - Model comparison (cost vs quality)
- [ ] Implement **Smart Model Routing**:
  - Cheap models for simple tasks
  - Powerful models for complex tasks

#### Deliverables

- Auto-docs kept in sync with code
- Security scan on every change
- Full cost visibility and budget enforcement

---

### Phase 12: Governed Self-Improvement Engine (Week 37–38)

**Goal**: ForgeMind gets smarter over time — but safely.

#### Tasks

- [ ] Build **Template Optimizer**:
  - Track agent success rates per template
  - Suggest prompt improvements based on outcomes
  - A/B test template variations
  - Human approval required for template changes
- [ ] Build **Decomposition Learner**:
  - Analyze which task breakdowns led to success
  - Improve future DAG generation
  - Learn from failed decompositions
- [ ] Build **Retry Strategy Optimizer**:
  - Track which retry patterns work for which error types
  - Adjust backoff/limits per agent type
- [ ] Build **Connector Recommender**:
  - Suggest connectors based on project type + history
  - "Projects like yours usually connect to GitHub + Vercel + PostgreSQL"
- [ ] Build **Policy Boundary Enforcement**:
  - Self-improvement CANNOT change: governance rules, security configs, approval gates, user permissions
  - All improvements logged in `self_improvement_log`
  - Human can review + revert any improvement
- [ ] Build frontend:
  - Self-improvement log viewer
  - Before/after comparison for each improvement
  - Approval/revert controls
  - Performance delta charts

#### Deliverables

- Agent templates improve based on success data
- Task decomposition gets better project by project
- "ForgeMind learned that X works better for RAG projects"
- All improvements auditable + revertible

---

### Phase 13: Teams & Collaboration (Week 39–40)

**Goal**: Multi-user workspaces, roles, notifications, audit UI.

#### Tasks

- [ ] Build **Team System**: create, invite, roles (Owner, Admin, Member, Viewer)
- [ ] Build **Activity Feed**: real-time team actions, filter, comment
- [ ] Build **Notification System**: in-app + email (approvals, failures, budget, drift)
- [ ] Build **Audit Log Viewer**: searchable, filterable, exportable (CSV/JSON)

#### Deliverables

- Teams collaborate on projects
- Real-time activity feed
- Full audit trail in UI

---

### Phase 14: DevOps Agent + Git Integration (Week 41–43)

**Goal**: CI/CD pipeline generation, deployment configs, Git workflow.

#### Tasks

- [ ] Build **DevOps Agent**: Dockerfile, docker-compose, GitHub Actions, Nginx/Caddy, Railway/Fly.io configs, K8s manifests
- [ ] Build **Git Integration**: connect repos, create branches/commits/PRs, webhook listener, PR auto-description
- [ ] Build frontend: Git settings, deployment config UI, pipeline viz, deploy with approval

#### Deliverables

- Agent generates deployment configs
- One-click PR creation
- Pipeline visualization

---

### Phase 15: Advanced Features + Polish (Week 44–48)

**Goal**: Custom agents, CLI, VS Code extension, webhooks, UX polish.

#### Tasks

- [ ] **Custom Agent Builder** UI — create, save, share agent templates
- [ ] **Agent Marketplace** — community-shared agent templates
- [ ] **CLI Tool** (`forgemind-cli`) — init, plan, run, status, logs
- [ ] **Webhook System** — configurable event webhooks + management UI
- [ ] **VS Code Extension** (stretch) — sidebar, fix errors, generate tests
- [ ] **Performance Optimization** — caching, query optimization, pagination, lazy loading
- [ ] **UX Polish** — onboarding tour, empty states, error boundaries, loading skeletons, dark/light theme, responsive

#### Deliverables

- Custom agent creation + marketplace
- CLI for terminal-first workflow
- Polished, production-ready UI

---

### Phase 16: Production Hardening + Launch (Week 49–52)

**Goal**: Production-ready. Secure. Monitored. Documented. Launched.

#### Tasks

- [ ] **Monitoring**: Prometheus + Grafana, Sentry, OpenTelemetry, health checks
- [ ] **Security Hardening**: audit all endpoints, CORS, rate limiting, input sanitization, CSP headers, API key rotation
- [ ] **Reliability**: database backups, Redis persistence, graceful Celery shutdown, dead letter queue, connection pooling
- [ ] **Load Testing**: 100 concurrent users, identify bottlenecks, optimize
- [ ] **Documentation**: API docs, user guide, admin guide, contributing guide
- [ ] **Landing Page**: positioning statement, feature overview, demo video
- [ ] **Beta Launch**: invite 50 beta users, collect feedback

#### Deliverables

- Production infrastructure live
- Monitoring dashboards
- Security audit passed
- Beta users onboarded

---

## Summary Timeline

| Phase                                    | Duration   | Key Milestone                                      |
| ---------------------------------------- | ---------- | -------------------------------------------------- |
| **Phase 0** — Foundation                 | Week 1–2   | Dev environment running                            |
| **Phase 1** — Auth & Users               | Week 3–4   | Users can sign up and log in                       |
| **Phase 2** — Projects & Tasks           | Week 5–7   | Task DAG engine working                            |
| **Phase 3** — LLM + Planner + Classifier | Week 8–11  | First agent + project classification               |
| **Phase 4** — Dynamic Agent Composition  | Week 12–14 | **Core innovation: dynamic teams**                 |
| **Phase 5** — Connector Intelligence     | Week 15–18 | **Key differentiator: token vault + setup wizard** |
| **Phase 6** — Coder + Verification       | Week 19–22 | Code gen + verification-first pipeline             |
| **Phase 7** — Trust Layer + Replay       | Week 23–25 | **Differentiator: explainable AI trust**           |
| **Phase 8** — Architecture + Drift       | Week 26–28 | **Differentiator: project health guardian**        |
| **Phase 9** — ForgeMind Local            | Week 29–31 | **Differentiator: desktop companion**              |
| **Phase 10** — Testing + Debug           | Week 32–33 | Auto-testing + debugging                           |
| **Phase 11** — Docs + Security + Cost    | Week 34–36 | Full cost visibility + scanning                    |
| **Phase 12** — Self-Improvement          | Week 37–38 | **Governed self-evolving workflows**               |
| **Phase 13** — Teams                     | Week 39–40 | Multi-user collaboration                           |
| **Phase 14** — DevOps + Git              | Week 41–43 | CI/CD + deployment                                 |
| **Phase 15** — Advanced + Polish         | Week 44–48 | Custom agents, CLI, marketplace, UX                |
| **Phase 16** — Production + Launch       | Week 49–52 | Security, monitoring, beta launch                  |

### Milestones

| Milestone                | Phase                    | What You Can Demo                               |
| ------------------------ | ------------------------ | ----------------------------------------------- |
| **Internal Alpha**       | After Phase 3 (Week 11)  | "Describe project → get PRD + architecture"     |
| **Core Innovation Demo** | After Phase 4 (Week 14)  | "Dynamic agent teams assembled per project"     |
| **Connector Demo**       | After Phase 5 (Week 18)  | "Add GitHub in 60 seconds, fully wired"         |
| **End-to-End Demo**      | After Phase 6 (Week 22)  | "Idea → code → verified → reviewed → approved"  |
| **Trust Demo**           | After Phase 7 (Week 25)  | "Explain, replay, rollback any AI action"       |
| **MVP Launch**           | After Phase 8 (Week 28)  | Full platform with 6 differentiators working    |
| **Beta Launch**          | After Phase 16 (Week 52) | Production-ready with teams, polish, monitoring |

> **MVP (Phases 0–8): ~28 weeks (7 months)** — all 6 core differentiators working.
>
> **Full Production (Phases 0–16): ~52 weeks (12 months)** — teams, marketplace, CLI, VS Code, production-hardened.

---

## 11. API Design

### Authentication

All endpoints require `Authorization: Bearer <jwt>` or `X-API-Key: <key>`.

### Base URL

```
Production:  https://api.forgemind.dev/v1
Development: http://localhost:8000/v1
```

### Key Endpoints

```
# Auth
POST   /v1/auth/webhook                     # Clerk webhook
GET    /v1/users/me                          # Current user

# Projects
POST   /v1/projects                          # Create project (goal-to-system)
GET    /v1/projects                          # List projects
GET    /v1/projects/:id                      # Get project (includes health score)
PATCH  /v1/projects/:id                      # Update project
DELETE /v1/projects/:id                      # Archive project
GET    /v1/projects/:id/classification       # Get project type + capabilities

# Tasks
POST   /v1/projects/:id/tasks               # Create task
GET    /v1/projects/:id/tasks               # List tasks (DAG)
GET    /v1/tasks/:id                         # Get task (includes trust score)
PATCH  /v1/tasks/:id                         # Update task
POST   /v1/tasks/:id/cancel                 # Cancel task
POST   /v1/tasks/:id/retry                  # Retry task
POST   /v1/tasks/:id/replay                 # Replay task (trust layer)
GET    /v1/tasks/:id/trust                   # Get trust details (risk, confidence, evidence)
GET    /v1/tasks/:id/impact                  # Get change impact analysis

# Agents (Dynamic Composition)
GET    /v1/agents/templates                  # List agent templates
POST   /v1/agents/templates                  # Create custom template
GET    /v1/agents/capabilities               # List capabilities
POST   /v1/projects/:id/compose              # Compose agent team for project
GET    /v1/projects/:id/team                 # Get assembled agent team
POST   /v1/tasks/:id/execute                # Execute task with assigned agent
POST   /v1/agents/spawn                      # Request subagent spawn (orchestrator approves)

# Connectors
GET    /v1/connectors/registry               # List available connectors
POST   /v1/connectors                        # Add connector to team
GET    /v1/connectors                        # List team connectors
GET    /v1/connectors/:id                    # Get connector details
DELETE /v1/connectors/:id                    # Remove connector
POST   /v1/connectors/:id/test              # Test connection
POST   /v1/connectors/:id/refresh           # Force token refresh
GET    /v1/connectors/:id/usage             # Connector usage log
POST   /v1/connectors/oauth/start           # Start OAuth flow
POST   /v1/connectors/oauth/callback        # Handle OAuth callback

# Artifacts
GET    /v1/projects/:id/artifacts            # List artifacts
GET    /v1/artifacts/:id                     # Get artifact
GET    /v1/artifacts/:id/versions            # List versions
GET    /v1/artifacts/:id/diff                # Compare versions
POST   /v1/artifacts/:id/rollback           # Rollback to version

# Architecture & Drift
GET    /v1/projects/:id/architecture         # Get architecture (intended + actual)
GET    /v1/projects/:id/drift                # Get drift report
GET    /v1/projects/:id/health               # Get health scorecards
POST   /v1/projects/:id/drift/scan          # Trigger drift scan
GET    /v1/projects/:id/drift/history        # Drift score over time

# Approvals
GET    /v1/approvals/pending                 # List pending approvals
POST   /v1/approvals/:id/approve             # Approve (with trust data shown)
POST   /v1/approvals/:id/reject              # Reject

# Analytics
GET    /v1/analytics/costs                   # Cost breakdown
GET    /v1/analytics/usage                   # Token usage
GET    /v1/analytics/agents                  # Agent performance
GET    /v1/analytics/health                  # Project health trends
GET    /v1/analytics/self-improvement        # Self-improvement metrics

# Teams
POST   /v1/teams                             # Create team
GET    /v1/teams/:id                         # Get team
POST   /v1/teams/:id/invite                 # Invite member
DELETE /v1/teams/:id/members/:uid            # Remove member

# Audit
GET    /v1/audit-logs                        # Search audit logs
GET    /v1/audit-logs/export                 # Export logs

# ForgeMind Local
POST   /v1/local/connect                     # Register local client
POST   /v1/local/environment                 # Report local environment
POST   /v1/local/command/request             # Request command approval
POST   /v1/local/sync                        # Sync files
GET    /v1/local/status                      # Local connection status

# Self-Improvement
GET    /v1/improvements                      # List improvements made
POST   /v1/improvements/:id/revert           # Revert an improvement
GET    /v1/improvements/:id/details          # Before/after comparison

# WebSocket
WS     /ws/projects/:id                      # Real-time project updates
WS     /ws/tasks/:id                         # Real-time task/agent stream
WS     /ws/local/:client_id                  # ForgeMind Local connection
```

### Standard Response Format

```json
{
  "data": { ... },
  "meta": {
    "request_id": "uuid",
    "timestamp": "ISO8601"
  }
}
```

### Error Format

```json
{
  "error": {
    "code": "CONNECTOR_AUTH_FAILED",
    "message": "GitHub OAuth token has expired",
    "details": { "connector_id": "uuid", "expired_at": "ISO8601" }
  },
  "meta": {
    "request_id": "uuid",
    "timestamp": "ISO8601"
  }
}
```

---

## 12. Security Model

### Authentication Flow

```
User → Clerk (login) → JWT → Frontend stores token
Frontend → API request with JWT → FastAPI middleware verifies → Route handler
```

### API Key Flow

```
User creates key → Backend generates random key → Hash with bcrypt → Store hash
User sends X-API-Key → Backend hashes → Compare with stored → Authorize
```

### Token Vault Security

```
Connector token → Encrypt with AES-256-GCM → Store encrypted BYTEA in PostgreSQL
Agent needs token → Orchestrator verifies scope → Decrypt in memory → Pass to agent
Token NEVER: logged, returned in API response, stored in plaintext, visible in UI
```

### ForgeMind Local Security

```
Local CLI → Authenticates with API key → Scoped to user's projects
Folder access → User explicitly grants per-directory
Command execution → Always requires user approval (no silent execution)
Data transfer → TLS encrypted WebSocket
```

### Encryption

- **At rest**: API keys hashed (bcrypt), connector tokens encrypted (AES-256-GCM), LLM keys encrypted
- **In transit**: TLS 1.3 everywhere
- **Secrets**: Never logged, never returned in API responses (only key prefix)

### RBAC Matrix

| Action                  | Owner | Admin | Member | Viewer |
| ----------------------- | ----- | ----- | ------ | ------ |
| Create project          | ✅    | ✅    | ✅     | ❌     |
| Delete project          | ✅    | ✅    | ❌     | ❌     |
| Run agents              | ✅    | ✅    | ✅     | ❌     |
| Approve changes         | ✅    | ✅    | ❌     | ❌     |
| Manage connectors       | ✅    | ✅    | ❌     | ❌     |
| View projects           | ✅    | ✅    | ✅     | ✅     |
| Manage team             | ✅    | ✅    | ❌     | ❌     |
| Manage billing          | ✅    | ❌    | ❌     | ❌     |
| View audit logs         | ✅    | ✅    | ✅     | ✅     |
| Export data             | ✅    | ✅    | ❌     | ❌     |
| ForgeMind Local         | ✅    | ✅    | ✅     | ❌     |
| Self-improvement revert | ✅    | ✅    | ❌     | ❌     |

### Rate Limiting

- Per-user: 100 requests/min (API), 20 requests/min (LLM calls)
- Per-agent: Configurable per agent template
- Per-connector: Respects external API rate limits
- Global: Circuit breaker at 50% error rate

---

## 13. Testing Strategy

### Test Pyramid

```
         ╱╲
        ╱ E2E ╲           ~15 tests  (Playwright)
       ╱────────╲
      ╱Integration╲       ~80 tests  (Testcontainers + real DB)
     ╱──────────────╲
    ╱   Unit Tests    ╲    ~300 tests (pytest + vitest)
   ╱────────────────────╲
```

### Backend Testing

- **Unit**: Every service, every agent's I/O validation, every connector handler
- **Integration**: API endpoints with real PostgreSQL/Redis (Testcontainers)
- **Agent tests**: Mock LLM responses, verify prompt construction + output parsing
- **Connector tests**: Mocked OAuth flows, token refresh, health checks
- **Celery tests**: Task routing, retry, timeout, cancellation
- **Trust tests**: Risk score calculation, replay determinism

### Frontend Testing

- **Unit**: Components, state management, connector wizard steps
- **Integration**: Page-level with mocked API
- **E2E**: Sign up → create project → add connector → run agents → approve → view drifts

### CI Pipeline

```yaml
on: pull_request
jobs:
  lint: ruff + eslint + prettier
  type-check: mypy + tsc
  test-backend: pytest --cov (Testcontainers)
  test-frontend: vitest --coverage
  e2e: playwright (on merge to main)
  security: pip-audit + npm audit + secrets scan
```

---

## 14. Deployment Strategy

### Local Dev

```bash
docker compose up -d     # Start everything
make dev                 # Or use Makefile
make test                # Run all tests
make migrate             # Run DB migrations
make seed                # Seed test data
```

### Recommended Hosting (Budget Start)

| Service       | Provider                     | Cost           |
| ------------- | ---------------------------- | -------------- |
| API + Workers | Railway or Fly.io            | ~$10-20/mo     |
| Frontend      | Vercel (free tier)           | $0             |
| PostgreSQL    | Neon or Supabase (free tier) | $0-10/mo       |
| Redis         | Upstash (free tier)          | $0             |
| File Storage  | Cloudflare R2 (free tier)    | $0             |
| Auth          | Clerk (free, 10k MAU)        | $0             |
| Monitoring    | Grafana Cloud (free tier)    | $0             |
| **Total**     |                              | **~$10-30/mo** |

---

## 15. Monitoring & Observability

### Key Metrics

- **API**: Request rate, latency (p50/p95/p99), error rate
- **Agents**: Execution time, success rate, tokens used, cost, trust scores
- **Connectors**: Health status, token expiry countdown, usage frequency
- **Queue**: Depth, processing time, failed task rate
- **Drift**: Per-project compliance score, drift velocity (how fast things diverge)
- **System**: CPU, memory, disk, DB connections

### Alerting

| Alert             | Condition               | Severity |
| ----------------- | ----------------------- | -------- |
| High error rate   | > 5% 5xx in 5min        | Critical |
| Agent stuck       | No heartbeat for 5min   | Warning  |
| Queue depth       | > 100 pending           | Warning  |
| Budget exceeded   | Project spend > limit   | Critical |
| Connector expired | Token expires in < 24hr | Warning  |
| Drift threshold   | Score drops below 70    | Warning  |
| DB connections    | > 80% pool used         | Warning  |

---

## 16. Competitive Positioning

### The One-Liner

> **ForgeMind is a secure autonomous engineering platform that turns high-level goals into complete working systems with connectors, architecture, verification, deployment, and monitoring.**

### Top 10 Differentiators (for README / Landing Page)

1. **Goal-to-System** — Describe your idea. Get architecture, code, connectors, tests, docs, deployment.
2. **Dynamic Agent Teams** — The right AI workforce assembled for each project. Not one-size-fits-all.
3. **Connector Vault** — OAuth, API keys, tokens — set up in 60 seconds with a guided wizard.
4. **ForgeMind Local** — Your desktop companion. Inspect repos, run tests, execute commands locally.
5. **Trust Dashboard** — Risk scores, confidence, evidence, explanations. Know why every decision was made.
6. **Replay Any Action** — Replay any AI action with identical inputs. Full reproducibility.
7. **Architecture Guardian** — Drift detection between what you planned and what actually exists.
8. **Verification-First** — Every code change: linted, type-checked, tested, security-scanned, then approved.
9. **Governed Self-Improvement** — ForgeMind gets smarter over time, but never breaks your rules.
10. **Full Audit Trail** — Every agent action logged. Who, what, when, why, which prompt. Exportable.

### How to Explain ForgeMind

**To developers:**

> "It's like having a full engineering team of AI agents that plans your project, writes code, sets up integrations, tests everything, and keeps your architecture healthy — all with your approval at every step."

**To investors:**

> "ForgeMind is an autonomous engineering platform. Users describe what they want to build, and ForgeMind creates the architecture, assembles a custom AI team, generates verified code, sets up all integrations, and monitors project health over time. Think GitHub Copilot meets Terraform meets a project manager."

**To enterprises:**

> "ForgeMind provides governed, auditable, AI-powered software delivery with full traceability, approval gates, encrypted secret management, and architecture compliance monitoring."

---

## Quick Start Commands (Phase 0)

```bash
# Create the monorepo
mkdir forgemind && cd forgemind
mkdir -p apps/web apps/api apps/local packages/shared docker .github/workflows

# Initialize backend
cd apps/api
python -m venv .venv
.venv\Scripts\activate
pip install fastapi uvicorn sqlalchemy alembic celery redis pydantic litellm python-socketio structlog sentry-sdk cryptography httpx python-jose bcrypt

# Initialize frontend
cd ../web
npx create-next-app@latest . --typescript --tailwind --app --eslint
npm install @clerk/nextjs zustand @tanstack/react-query socket.io-client @monaco-editor/react recharts reactflow

# Initialize ForgeMind Local
cd ../local
python -m venv .venv
.venv\Scripts\activate
pip install click httpx websockets watchdog docker

# Initialize Docker
cd ../../docker
# Create docker-compose.yml with PostgreSQL, Redis, MinIO
```

---

_This document is the single source of truth for ForgeMind v2. Update as you complete phases and make decisions._

_Last updated: 2026-03-26_

---

## Implementation Milestones — Detailed Task Tracker

### Completed Milestones (FM-001 to FM-045)

| ID               | Title                                                             | Status      |
| ---------------- | ----------------------------------------------------------------- | ----------- |
| FM-001 to FM-008 | Foundation, Project CRUD, Task DAG, Run System                    | ✅ Complete |
| FM-009 to FM-016 | Planner, Agents, Approvals, Events, Artifacts                     | ✅ Complete |
| FM-017 to FM-024 | Execution Service, Chat, Composition, Connectors                  | ✅ Complete |
| FM-025 to FM-032 | Memory, Schemas, Health, Full Test Suite (105 tests)              | ✅ Complete |
| FM-033 to FM-040 | Mermaid Diagrams, Documentation, Integration Tests                | ✅ Complete |
| FM-041           | Connector Readiness States                                        | ✅ Complete |
| FM-042           | Credential Vault Abstraction                                      | ✅ Complete |
| FM-043           | Adaptive Retry / Revision Loop v2                                 | ✅ Complete |
| FM-044           | Execution Chatbot v2 (topic detection, connector/retry awareness) | ✅ Complete |
| FM-045           | Execution Quality Eval Suite (23 benchmark evals)                 | ✅ Complete |

### Pre-release Infrastructure (Implemented ahead of roadmap)

Features built as foundational infrastructure before the updated FM-046–FM-050 scope was defined:

| Feature                         | Description                                                     | Status      |
| ------------------------------- | --------------------------------------------------------------- | ----------- |
| Run Lifecycle Manager           | Health checks, auto-complete, auto-fail, stuck detection        | ✅ Complete |
| Cost & Token Tracking           | Per-call LLM cost recording, model breakdown, budget visibility | ✅ Complete |
| Governance Policy Engine        | Configurable approval policies replacing hardcoded gates        | ✅ Complete |
| Audit Trail Export              | JSON/CSV event export with compliance metadata                  | ✅ Complete |
| Trust Scoring & Risk Assessment | Heuristic trust/risk scoring for tasks and runs                 | ✅ Complete |

**Current test suite: 174 tests (all passing)**

### Updated FM-046 to FM-050 Roadmap (Active)

| ID      | Title                                            | Status         |
| ------- | ------------------------------------------------ | -------------- |
| FM-046  | Run Replay and Execution Trace Inspection        | 🔲 Not started |
| FM-047A | Multi-Agent Council Decision Engine              | 🔲 Not started |
| FM-047  | Policy-Based Approval Rules                      | 🔲 Not started |
| FM-048  | Multi-Run Memory and Project Knowledge Base      | 🔲 Not started |
| FM-049  | External Repo / Workspace Execution Integration  | 🔲 Not started |
| FM-050  | Production Readiness and Platform Hardening Pass | 🔲 Not started |

#### Recommended sequence

1. **FM-046** — Run Replay and Execution Trace Inspection
2. **FM-047A** — Multi-Agent Council Decision Engine
3. **FM-047** — Policy-Based Approval Rules
4. **FM-048** — Multi-Run Memory and Project Knowledge Base
5. **FM-049** — External Repo / Workspace Execution Integration
6. **FM-050** — Production Readiness and Platform Hardening Pass

#### Why this order

- **FM-046 first**: Council decisions, policy approvals, and replay all benefit from stronger trace visibility.
- **FM-047A next**: The council engine depends on events, chat context, retry context, and execution visibility — all now available.
- **FM-047 after**: Once councils exist, approval policy can become smarter (auto-approve, require approval, require council + approval).
- **FM-048 next**: Project-level memory becomes much more useful after councils and policy logic exist.
- **FM-049 then**: External repo/workspace execution should happen only after internal decision/control systems are stronger.
- **FM-050 last**: Production hardening pass consolidates everything.
