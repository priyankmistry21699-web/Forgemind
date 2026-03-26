# ForgeMind — Complete Project Roadmap (v2)

> **A Secure Autonomous Engineering Platform That Turns High-Level Goals Into Complete Working Systems**
>
> ForgeMind is not just a multi-agent coding system. It is a governed autonomous engineering platform that turns high-level goals into secure, connected, verifiable software systems — with goal-to-system synthesis, dynamic agent composition, connector intelligence, local workspace access, approval-based execution, architecture compliance, and long-term project drift awareness.

---

## Table of Contents

1. [Vision & Positioning](#1-vision--positioning)
2. [What Makes ForgeMind Different](#2-what-makes-forgemind-different)
3. [What Users Get](#3-what-users-get)
4. [Core Concepts](#4-core-concepts)
5. [Updated Tech Stack](#5-updated-tech-stack)
6. [System Architecture](#6-system-architecture)
7. [Feature List (Complete)](#7-feature-list-complete)
8. [Database Schema Overview](#8-database-schema-overview)
9. [Dynamic Agent Composition](#9-dynamic-agent-composition)
10. [Agent Definitions & Contracts](#10-agent-definitions--contracts)
11. [Connector Intelligence & Token Vault](#11-connector-intelligence--token-vault)
12. [ForgeMind Local (OS Companion)](#12-forgemind-local-os-companion)
13. [Architecture Compliance & Drift Engine](#13-architecture-compliance--drift-engine)
14. [Trust Layer (Replay, Risk, Evidence)](#14-trust-layer-replay-risk-evidence)
15. [Phase-Wise Implementation](#15-phase-wise-implementation)
16. [API Design Overview](#16-api-design-overview)
17. [Security Model](#17-security-model)
18. [Testing Strategy](#18-testing-strategy)
19. [Deployment Strategy](#19-deployment-strategy)
20. [Monitoring & Observability](#20-monitoring--observability)

---

## 1. Vision & Positioning

### The Problem (Bigger Than Code)

Building software is not just "writing code." It involves:
- Understanding **what** to build (requirements, architecture)
- Figuring out **how to connect** things (APIs, OAuth, tokens, secrets)
- Setting up **local environments** (repos, dependencies, env vars)
- Writing, reviewing, testing, and securing code
- Deploying, monitoring, and maintaining systems over time
- Keeping architecture **aligned** as code evolves

Developers lose 60%+ of their time on setup, integration, configuration, and maintenance — not actual problem-solving.

Existing AI coding agents solve a narrow slice: they generate code and execute tasks. They don't understand systems, don't set up connectors, don't track architectural drift, and don't run locally on your machine with governance.

### ForgeMind's Position

ForgeMind is **NOT** just another AI coding agent.

**Other tools**: "Agents that do stuff" — autonomous task execution, code generation, multi-agent pipelines.

**ForgeMind**: "A system that understands **what** to build, **what** to connect, **how** to secure it, **how** to verify it, and **how** to keep it aligned over time."

### One-Line Positioning

> **ForgeMind is an AI software systems orchestration and delivery platform — not just a coding agent.**

### Category

| Other Tools (OpenClaw/NemoClaw-style) | ForgeMind |
|---------------------------------------|-----------|
| AI coding agent | AI systems architect + builder + guardian |
| Autonomous execution | Governed autonomous engineering |
| Task completion | Goal-to-system synthesis |
| Code generation | Architecture + connectors + code + verification + deployment + monitoring |
| Fixed agent pipeline | Dynamic agent composition per project |
| User handles OAuth/tokens/env | Connector intelligence + token vault |
| Cloud-only | Local OS companion + cloud hybrid |
| Generate and forget | Long-term drift detection + project health |

---

## 2. What Makes ForgeMind Different

### The 7 Core Differentiators

#### 1. Goal-to-System Synthesis
User says "Build a YouTube automation pipeline" → ForgeMind infers system type, chooses stack, chooses connectors, generates architecture, generates roadmap, scaffolds it, monitors it. Not just code — a complete **system**.

#### 2. Dynamic Agent Composition
ForgeMind doesn't use fixed agent teams. It analyzes the project, identifies required capabilities, and **dynamically assembles the right agent team** per project. A RAG app gets different agents than a CI/CD pipeline.

#### 3. Connector Intelligence + Token Vault
Most tools leave users stuck with client IDs, OAuth scopes, token refresh, and env var chaos. ForgeMind provides a connector registry, setup wizard, callback URI generation, scope guidance, token vault, connection testing, and expiry/rotation — all governed and audited.

#### 4. ForgeMind Local (OS/Workspace Companion)
Local repo inspection, file import, command execution, environment analysis, build/test execution — all with scoped folder access, approval gates, and hybrid local/cloud workflow. It runs **on your machine**, securely.

#### 5. Trust Layer (Replay, Risk, Evidence, Approvals)
Every agent decision has: decision explanation, evidence view, risk score, confidence score, replayable runs, audit logs, and approval gates. Users can always answer: "Why did it do this? Can I trust it? What changed? How do I reproduce it?"

#### 6. Architecture Compliance + Drift Detection
ForgeMind tracks intended architecture vs actual codebase vs deployment state vs docs. It detects drift, inconsistencies, missing security controls, and missing backup implementations. It's a **guardian of project health**, not just a generator.

#### 7. Governed Self-Improvement
ForgeMind improves templates, task decomposition, retry logic, connector recommendations, and stack defaults over time — but **never** changes core policies, escalates privileges, or runs destructive actions autonomously. Improvement within policy boundaries.

---

## 3. What Users Get

| Feature | Description |
|---------|-------------|
| **Goal-to-System** | Describe your idea in plain English → get a complete system: PRD, architecture, connectors, code, tests, deployment |
| **Smart Agent Teams** | ForgeMind builds the right AI team for your project — not a fixed pipeline |
| **Connector Vault** | OAuth, API keys, tokens — set up in a guided wizard with secure storage and auto-rotation |
| **Local Companion** | Inspect local repos, run builds, execute commands — all with approval gates |
| **Auto-Coder** | Agents write code following your style guide, patterns, and conventions |
| **Code Reviewer** | Every piece of code is reviewed by an AI reviewer before merge |
| **Test Generator** | Automatic unit/integration/e2e test generation + sandboxed execution |
| **Security Scanner** | Continuous OWASP scanning + dependency checks + secrets detection |
| **Architecture Guardian** | Drift detection, compliance scoring, architecture-vs-reality checks |
| **Doc Writer** | API docs, README, architecture docs auto-generated and kept in sync |
| **Deploy Manager** | CI/CD pipeline generation + deployment configs + one-click deploy |
| **Bug Fixer** | Paste an error → diagnosis, fix, test verification, PR creation |
| **Trust Dashboard** | Decision explanations, risk scores, confidence levels, replayable runs |
| **Approval Gates** | Nothing ships without your approval. Full control at every step |
| **Full Audit Trail** | Every agent action logged — who, what, when, why, which prompt, what cost |
| **Multi-LLM Support** | OpenAI, Anthropic, Google, Ollama, or any compatible provider |
| **Real-Time Dashboard** | Watch agents work in real-time with live logs and progress |
| **Cost Tracking** | Per-agent, per-task, per-project token usage and cost breakdown |
| **Team Collaboration** | Invite team members, assign roles, share projects |
| **Self-Improving** | Templates, recommendations, and defaults get smarter — within your policies |

---

## 4. Core Concepts

### Agent
A specialized autonomous worker with a defined role, tools, and boundaries. Each agent has a **contract** specifying: capabilities, restrictions, tools, input/output schema, retry/timeout policy, model preference, and rate limits. Agents are NOT fixed — they are **dynamically composed** per project.

### Agent Composition Engine
The system that analyzes project intent, classifies the project type, identifies required capabilities, chooses agent templates, instantiates agents with proper prompts/tools, and decides parallel vs sequential execution. This is ForgeMind's brain for team building.

### Orchestrator
Receives a user request, invokes the Agent Composition Engine to build the right team, breaks work into a **DAG (Directed Acyclic Graph)**, assigns tasks to agents, manages dependencies, handles failures, and enforces governance.

### Connector
An external service integration (API, OAuth provider, database, cloud service). Connectors are managed through the **Connector Registry** with guided setup, token vaulting, rotation, and health monitoring.

### Governance
Human-defined rules that control agent behavior:
- Approval gates (which actions need human sign-off)
- Budget limits (max tokens/cost per task)
- Tool restrictions (which agents can access which tools)
- Rate limits (max actions per time window)
- Self-improvement boundaries (what can/cannot be auto-updated)

### Artifact
Any output an agent produces: code files, docs, test files, configs, PRDs, diagrams, architecture docs. All artifacts are **versioned** with full history, diffs, and checksums.

### Trust Record
Every agent action generates a trust record: input, output, decision reasoning, evidence references, risk score, confidence score, prompt version, cost, and duration. Trust records enable **replay** (re-run any past action with same inputs) and **audit** (trace any decision).

### Architecture Blueprint
A living document describing the intended architecture of a project: components, relationships, data flows, security boundaries, deployment topology. The **Drift Engine** continuously compares this blueprint against actual code, deployment, and docs.

### Session
A workspace context that persists across agent interactions. Contains project state, conversation history, file tree, active tasks, and local environment info (when ForgeMind Local is connected).

---

## 5. Updated Tech Stack

### Frontend
| Technology | Purpose | Why |
|-----------|---------|-----|
| **Next.js 15** (App Router) | Web framework | Server components, streaming, API routes |
| **TypeScript 5.x** | Type safety | Catch errors at compile time |
| **Tailwind CSS 4** | Styling | Utility-first, fast iteration |
| **shadcn/ui** | Component library | Accessible, customizable, no lock-in |
| **Zustand** | State management | Simple, fast, no boilerplate |
| **React Query (TanStack Query v5)** | Server state | Caching, background refetch, optimistic updates |
| **Socket.IO Client** | Real-time updates | Live agent progress, logs streaming |
| **Monaco Editor** | Code editor | VS Code-quality code editing in browser |
| **Mermaid.js** | Diagrams | Render architecture/flow diagrams from agent output |
| **React Flow** | DAG visualization | Visualize task DAGs + architecture graphs |
| **xterm.js** | Terminal emulator | ForgeMind Local terminal in browser |

### Backend — Core API
| Technology | Purpose | Why |
|-----------|---------|-----|
| **FastAPI** (Python 3.12) | API framework | Async, fast, auto-docs, type-safe |
| **Pydantic v2** | Data validation | Schema validation, serialization |
| **SQLAlchemy 2.0** + **Alembic** | ORM + Migrations | Async ORM, reliable schema migrations |
| **Celery 5** + **Redis** | Task queue | Distributed async task execution |
| **Socket.IO (python-socketio)** | WebSocket server | Real-time agent status broadcasting |
| **LiteLLM** | LLM gateway | Unified API for 100+ LLM providers |
| **LangGraph** | Agent orchestration | Stateful agent graphs, tool calling, loops |
| **Jinja2** | Prompt templates | Version-controlled prompt rendering |

### Backend — ForgeMind-Specific Engines
| Technology | Purpose | Why |
|-----------|---------|-----|
| **Agent Composition Engine** (custom) | Dynamic agent assembly | Classify project → build right agent team |
| **Connector Registry** (custom) | Integration management | Store connector metadata, setup flows, health checks |
| **Token Vault** (custom + Fernet/AES) | Secret management | Encrypt, store, rotate tokens securely |
| **Drift Engine** (custom + AST) | Architecture compliance | Compare blueprint vs reality, detect drift |
| **Trust Recorder** (custom) | Decision audit | Log evidence, risk, confidence for every agent action |
| **Project Classifier** (LLM-powered) | Goal analysis | Understand project type and required capabilities |

### Database & Storage
| Technology | Purpose | Why |
|-----------|---------|-----|
| **PostgreSQL 16** | Primary database | JSONB for flexible data, robust, mature |
| **Redis 7** | Cache + Queue broker | Session cache, Celery broker, rate limiting |
| **MinIO** (or S3/R2) | File/artifact storage | Store generated code, docs, artifacts |
| **Alembic** | DB migrations | Version-controlled schema changes |

### Auth & Security
| Technology | Purpose | Why |
|-----------|---------|-----|
| **Clerk** | Authentication | Social login, MFA, user management, free tier |
| **Custom RBAC** | Authorization | Fine-grained permission control |
| **python-jose** | JWT handling | Verify Clerk JWTs on backend |
| **bcrypt** | Secret hashing | Hash API keys at rest |
| **cryptography (Fernet)** | Token encryption | Encrypt connector tokens at rest |

### ForgeMind Local (Desktop Companion)
| Technology | Purpose | Why |
|-----------|---------|-----|
| **Tauri** (or Electron-lite) | Desktop shell | Lightweight, secure, system access |
| **WebSocket bridge** | Local↔Cloud sync | Secure tunnel between local agent and cloud |
| **Chokidar** (Node) / **Watchdog** (Python) | File watcher | Monitor local repo changes |
| **Sandboxed executor** | Local commands | Run builds/tests with approval gates |

### DevOps & Infrastructure
| Technology | Purpose | Why |
|-----------|---------|-----|
| **Docker** + **Docker Compose** | Containerization | Consistent local + prod environments |
| **GitHub Actions** | CI/CD | Automated testing, linting, deployment |
| **Nginx** (or Caddy) | Reverse proxy | SSL termination, routing |
| **Railway / Fly.io / AWS ECS** | Hosting | Easy deployment with scaling |

### Monitoring & Observability
| Technology | Purpose | Why |
|-----------|---------|-----|
| **Prometheus** + **Grafana** | Metrics & dashboards | Agent performance, system health |
| **Structured logging** (structlog) | Logging | JSON logs, correlation IDs |
| **Sentry** | Error tracking | Catch and alert on exceptions |
| **OpenTelemetry** | Distributed tracing | Trace requests across services |

### Testing
| Technology | Purpose | Why |
|-----------|---------|-----|
| **pytest** + **pytest-asyncio** | Backend tests | Async test support |
| **Vitest** + **Testing Library** | Frontend tests | Fast, modern, React-friendly |
| **Playwright** | E2E tests | Cross-browser, reliable |
| **Factory Boy** | Test fixtures | Generate test data easily |
| **Testcontainers** | Integration tests | Spin up real DB/Redis in tests |

---

## 6. System Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                          FRONTEND (Next.js 15)                            │
│  Dashboard │ Project │ Agent Monitor │ Code Editor │ Connector Vault     │
│  Trust View │ Architecture Map │ Drift Dashboard │ Local Terminal        │
└───────────────────────────────┬──────────────────────────────────────────┘
                                │ REST + WebSocket (Socket.IO)
           ┌────────────────────┤
           │                    ▼
┌──────────▼───┐  ┌───────────────────────────────────────────────────────┐
│  FORGEMIND   │  │                 API GATEWAY (FastAPI)                   │
│  LOCAL       │  │  Auth │ Rate Limiter │ Router │ WS Manager │ Trust     │
│  (Tauri)     │  └───┬──────────┬──────────┬──────────┬──────────────────┘
│  File Watch  │      │          │          │          │
│  Local Exec  │  ┌───▼───┐ ┌───▼───┐ ┌───▼────┐ ┌───▼─────────┐
│  Env Scan    │  │ Auth  │ │Project│ │Govern- │ │ Connector   │
└──────┬───────┘  │Service│ │Service│ │ance    │ │ Service +   │
       │          └───────┘ └───┬───┘ │Service │ │ Token Vault │
       │ WS                     │     └───┬────┘ └──────┬──────┘
       │ Bridge           ┌─────▼─────────▼────────────▼──────┐
       └─────────────────►│         ORCHESTRATOR ENGINE         │
                          │  Project Classifier │ Team Builder  │
                          │  DAG Scheduler │ Task Router        │
                          │  Retry Mgr │ Timeout │ Self-Improve │
                          └─────────────┬──────────────────────┘
                                        │
                          ┌─────────────▼──────────────────────┐
                          │     AGENT COMPOSITION ENGINE         │
                          │  Capability Registry │ Templates    │
                          │  Dynamic Team Assembly              │
                          │  Budget/Limit Manager               │
                          └──┬──────┬──────┬──────┬──────┬────┘
                             │      │      │      │      │
                          ┌──▼──┐┌──▼──┐┌──▼──┐┌──▼──┐┌──▼──┐
                          │Arch ││Code ││Test ││Conn ││Sec  │ ..dynamic
                          │Agent││Agent││Agent││Agent││Agent│
                          └──┬──┘└──┬──┘└──┬──┘└──┬──┘└──┬──┘
                             │      │      │      │      │
                          ┌──▼──────▼──────▼──────▼──────▼──┐
                          │   VERIFICATION PIPELINE           │
                          │  Tests │ Lint │ TypeCheck │ Scan  │
                          │  Policy Check │ Approval Gate     │
                          └──────────────┬───────────────────┘
                                         │
                          ┌──────────────▼───────────────────┐
                          │         LiteLLM Gateway           │
                          │  OpenAI │ Anthropic │ Ollama │... │
                          └──────────────────────────────────┘
                                         │
              ┌──────────────────────────┼──────────────────────┐
              │                          │                      │
        ┌─────▼─────┐           ┌───────▼──────┐       ┌──────▼──────┐
        │ PostgreSQL │           │    Redis      │       │ MinIO / S3  │
        │ (Data+Audit│           │ (Cache+Q+     │       │ (Artifacts) │
        │  +Trust)   │           │  Rate Limit)  │       └─────────────┘
        └─────┬──────┘           └──────────────┘
              │
        ┌─────▼──────────┐
        │  DRIFT ENGINE   │
        │  Blueprint vs   │
        │  Reality check  │
        │  Health scores  │
        └────────────────┘
```

---

## 7. Feature List (Complete)

### 7.1 Goal-to-System Synthesis
- [ ] Natural language project description → full system plan
- [ ] Project type classification (web app, RAG app, pipeline, CLI, SaaS, etc.)
- [ ] Automatic stack selection based on project type
- [ ] Automatic connector identification (which APIs/services needed)
- [ ] PRD generation (Product Requirements Document)
- [ ] Architecture document generation with Mermaid diagrams
- [ ] Task breakdown into DAG (dependency graph)
- [ ] Scaffold generation (folder structure, configs, boilerplate)
- [ ] Project templates (web app, API, CLI, library, RAG, pipeline, SaaS)
- [ ] Import existing codebase for analysis and onboarding

### 7.2 Dynamic Agent Composition
- [ ] Project Classifier — analyze goal and determine project type
- [ ] Capability Registry — what each agent type can do
- [ ] Agent Template Registry — reusable agent definitions
- [ ] Agent Composition Engine — assemble right team per project
- [ ] Parallel execution planning (which agents can run simultaneously)
- [ ] Hierarchical agent creation (agents can request sub-agents via orchestrator)
- [ ] Per-team performance analytics
- [ ] Custom Agents — users define their own agents with custom prompts/tools
- [ ] Agent marketplace (community-shared agent templates)

### 7.3 Connector Intelligence & Token Vault
- [ ] Connector Registry (OAuth, API key, webhook, database connectors)
- [ ] Setup Wizard per connector (guided step-by-step)
- [ ] Callback URI generation for OAuth flows
- [ ] Scope guidance (explain what each permission does)
- [ ] Token Vault (encrypted storage with AES-256)
- [ ] Connection testing (verify connector works)
- [ ] Token expiry detection + rotation support
- [ ] Connector health monitoring
- [ ] Audit trail for every token access
- [ ] Environment variable generation from connectors

### 7.4 ForgeMind Local (Desktop Companion)
- [ ] Scoped folder access (user chooses which folders to expose)
- [ ] Local repo inspection (file tree, git status, dependencies)
- [ ] Local file import into ForgeMind projects
- [ ] Local command execution with approval gates
- [ ] Local environment analysis (Python version, Node version, installed packages)
- [ ] Local build/test execution in sandboxed scope
- [ ] Hybrid local/cloud workflow (local files + cloud agents)
- [ ] Secure WebSocket bridge (local ↔ cloud sync)

### 7.5 Core Agent System
- [ ] Architect Agent — system design, component decomposition
- [ ] Coder Agent — write code following conventions
- [ ] Reviewer Agent — code review with actionable feedback
- [ ] Tester Agent — generate and run tests
- [ ] Documenter Agent — write/update documentation
- [ ] Debugger Agent — diagnose and fix errors
- [ ] Refactor Agent — improve code quality
- [ ] Security Agent — OWASP scanning, vulnerability detection
- [ ] Connector Agent — set up and configure integrations
- [ ] DevOps Agent — CI/CD pipeline generation, deployment configs
- [ ] Researcher Agent — search docs, StackOverflow, GitHub for solutions

### 7.6 Orchestration & Governance
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

### 7.7 Trust Layer
- [ ] Decision explanation per agent action
- [ ] Evidence view (what data the agent used)
- [ ] Risk score per action (low/medium/high/critical)
- [ ] Confidence score per action (0–100%)
- [ ] Replayable runs (re-execute any past action with same inputs)
- [ ] Full audit logs (every agent action with timestamp, input, output)
- [ ] Prompt audit trail (which prompt version was used)
- [ ] Diff viewer for any action's before/after state
- [ ] Export audit logs (CSV, JSON)
- [ ] Trust dashboard (project-level trust metrics)

### 7.8 Architecture Compliance & Drift Detection
- [ ] Architecture Blueprint editor (define intended architecture)
- [ ] Auto-generate blueprint from codebase analysis
- [ ] Drift detection (blueprint vs actual code)
- [ ] Deployment state tracking (what's deployed where)
- [ ] Documentation state tracking (are docs in sync with code)
- [ ] Missing security control detection
- [ ] Architecture compliance score
- [ ] Drift alerts (notify when code diverges from blueprint)
- [ ] Architecture visualization (component diagram, live)
- [ ] Runbook consistency checks

### 7.9 Verification-First Execution
- [ ] Auto-test generation for all code changes
- [ ] Sandboxed test execution (Docker containers)
- [ ] Linting on all generated code
- [ ] Type checking (mypy/tsc)
- [ ] Security scanning (OWASP, dependency audit, secrets detection)
- [ ] Policy checks (custom rules per project)
- [ ] Approval gates before merge/deploy
- [ ] Verification report per task

### 7.10 Real-Time Features
- [ ] Live agent activity stream (Socket.IO)
- [ ] Real-time log viewer per agent
- [ ] Task progress indicators
- [ ] Notification system (in-app + email)
- [ ] Collaborative cursors (team members see each other's focus)

### 7.11 Code & Artifact Management
- [ ] In-browser code editor (Monaco)
- [ ] Artifact versioning (every generated file has history)
- [ ] Diff viewer (compare artifact versions)
- [ ] Git-like branching for agent experiments
- [ ] File tree browser with search
- [ ] Prompt versioning (track which prompt version produced which output)

### 7.12 LLM & Cost Management
- [ ] Multi-provider support via LiteLLM
- [ ] Per-request cost tracking
- [ ] Per-agent cost breakdown
- [ ] Per-project budget with alerts
- [ ] Smart model routing (cheap models for simple tasks, expensive for complex)
- [ ] Prompt caching for repeated operations
- [ ] Token usage analytics dashboard

### 7.13 User & Team
- [ ] User registration/login (Clerk)
- [ ] Social login (Google, GitHub)
- [ ] Team workspaces
- [ ] Role-based access control (Owner, Admin, Member, Viewer)
- [ ] Invite system
- [ ] Activity feed per team
- [ ] API key management (encrypted at rest)

### 7.14 Governed Self-Improvement
- [ ] Template quality tracking (which templates produce best results)
- [ ] Task decomposition improvement (learn from past projects)
- [ ] Retry logic optimization (adjust strategies based on failure patterns)
- [ ] Connector recommendation improvement (suggest integrations based on project type)
- [ ] Stack default optimization (learn which stacks work best for which goals)
- [ ] Improvement changelog (log every self-improvement action)
- [ ] Policy boundaries (define what CAN and CANNOT be auto-updated)
- [ ] Human review of self-improvement suggestions

### 7.15 Integrations (Later Phases)
- [ ] GitHub / GitLab integration
- [ ] Slack notifications
- [ ] VS Code extension
- [ ] CLI tool
- [ ] Webhook system (notify external services)
- [ ] REST API for third-party integrations

---

## 8. Database Schema Overview

### Core Tables

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
├── status (ENUM: planning, active, paused, completed, archived)
├── settings (JSONB)  -- approval gates, budget, model prefs
├── created_at, updated_at

tasks
├── id (UUID, PK)
├── project_id (FK → projects)
├── parent_task_id (FK → tasks, nullable)  -- for subtasks
├── title (VARCHAR)
├── description (TEXT)
├── status (ENUM: pending, queued, running, awaiting_approval, completed, failed, cancelled)
├── assigned_agent (VARCHAR)  -- agent type
├── priority (INT)
├── depends_on (UUID[])  -- task IDs this depends on
├── idempotency_key (VARCHAR, UNIQUE)
├── retry_count (INT, DEFAULT 0)
├── max_retries (INT, DEFAULT 3)
├── timeout_seconds (INT)
├── started_at, completed_at, created_at

task_results
├── id (UUID, PK)
├── task_id (FK → tasks)
├── output (JSONB)  -- agent output
├── error (TEXT, nullable)
├── error_type (ENUM: transient, permanent, timeout, nullable)
├── tokens_used (INT)
├── cost_usd (DECIMAL)
├── model_used (VARCHAR)
├── prompt_version (VARCHAR)
├── duration_ms (INT)
├── created_at

artifacts
├── id (UUID, PK)
├── project_id (FK → projects)
├── task_id (FK → tasks)
├── type (ENUM: code, doc, test, config, prd, diagram)
├── file_path (VARCHAR)
├── storage_key (VARCHAR)  -- MinIO/S3 key
├── version (INT)
├── checksum (VARCHAR)
├── metadata (JSONB)
├── created_at

artifact_versions
├── id (UUID, PK)
├── artifact_id (FK → artifacts)
├── version (INT)
├── storage_key (VARCHAR)
├── diff_from_previous (TEXT)
├── created_by_task_id (FK → tasks)
├── created_at

agent_configs
├── id (UUID, PK)
├── project_id (FK → projects, nullable)  -- null = global default
├── agent_type (VARCHAR)
├── system_prompt (TEXT)
├── prompt_version (VARCHAR)
├── model_name (VARCHAR)
├── temperature (FLOAT)
├── max_tokens (INT)
├── tools_allowed (VARCHAR[])
├── rate_limit_per_minute (INT)
├── timeout_seconds (INT)
├── is_active (BOOLEAN)
├── created_at, updated_at

audit_logs
├── id (UUID, PK)
├── project_id (FK → projects)
├── task_id (FK → tasks, nullable)
├── user_id (FK → users, nullable)  -- null if agent-initiated
├── agent_type (VARCHAR, nullable)
├── action (VARCHAR)  -- e.g., "code.generate", "review.approve"
├── input_summary (TEXT)
├── output_summary (TEXT)
├── prompt_version (VARCHAR)
├── tokens_used (INT)
├── cost_usd (DECIMAL)
├── ip_address (VARCHAR, nullable)
├── created_at

approval_gates
├── id (UUID, PK)
├── project_id (FK → projects)
├── action_pattern (VARCHAR)  -- e.g., "deploy.*", "code.merge"
├── requires_approval (BOOLEAN)
├── auto_approve_under_cost (DECIMAL, nullable)
├── approver_role (ENUM: owner, admin, member)
├── created_at

api_keys
├── id (UUID, PK)
├── user_id (FK → users)
├── name (VARCHAR)
├── key_hash (VARCHAR)  -- bcrypt hash, never store raw
├── key_prefix (VARCHAR)  -- first 8 chars for identification
├── scopes (VARCHAR[])
├── expires_at (TIMESTAMP, nullable)
├── last_used_at (TIMESTAMP)
├── created_at

llm_provider_configs
├── id (UUID, PK)
├── team_id (FK → teams)
├── provider (ENUM: openai, anthropic, google, ollama, custom)
├── api_key_encrypted (BYTEA)  -- encrypted at rest
├── base_url (VARCHAR, nullable)
├── is_default (BOOLEAN)
├── created_at, updated_at
```

---

## 7. Agent Definitions

Each agent follows a **contract** pattern:

### Agent Contract Template

```yaml
agent_name: "coder"
description: "Writes production-quality code"
capabilities:
  - generate_code
  - modify_code
  - read_files
restrictions:
  - cannot_delete_files
  - cannot_deploy
  - cannot_access_secrets
input_schema:
  task_description: string
  file_context: string[]
  style_guide: string (optional)
output_schema:
  files_created: FileChange[]
  files_modified: FileChange[]
  explanation: string
tools:
  - file_read
  - file_write
  - search_codebase
  - run_linter
retry_policy:
  max_retries: 3
  backoff: exponential
  retry_on: [transient_error, timeout]
timeout: 300s
rate_limit: 20/minute
model_preference: "claude-sonnet-4-20250514" # complex reasoning
fallback_model: "gpt-4o-mini" # if primary fails
```

### Agent Roster

| Agent          | Role                                  | Model Tier                  | Tools                                              | Approval Needed      |
| -------------- | ------------------------------------- | --------------------------- | -------------------------------------------------- | -------------------- |
| **Planner**    | PRD, architecture, task decomposition | High (Claude Sonnet/GPT-4o) | web_search, file_read                              | Yes — for final plan |
| **Coder**      | Write/modify code                     | High                        | file_read, file_write, search_codebase, run_linter | Yes — for merge      |
| **Reviewer**   | Code review, quality checks           | High                        | file_read, search_codebase, run_tests              | No — advisory        |
| **Tester**     | Generate & run tests                  | Medium (GPT-4o-mini)        | file_read, file_write, run_tests                   | No                   |
| **Documenter** | Write docs, README, API docs          | Medium                      | file_read, file_write                              | No                   |
| **Debugger**   | Diagnose errors, fix bugs             | High                        | file_read, file_write, run_tests, read_logs        | Yes — for fix        |
| **Refactor**   | Code improvement, optimization        | High                        | file_read, file_write, run_tests, run_linter       | Yes — for changes    |
| **Security**   | Vulnerability scanning                | High                        | file_read, search_codebase, run_security_scan      | No — advisory        |
| **DevOps**     | CI/CD, deployment configs             | Medium                      | file_read, file_write, run_commands                | Yes — always         |
| **Researcher** | Find solutions, reference code        | Low (GPT-4o-mini)           | web_search, read_docs                              | No                   |

---

## 8. Phase-Wise Implementation

---

### Phase 0: Foundation & Project Setup (Week 1–2)

**Goal**: Monorepo setup, dev environment, CI pipeline, base configs.

#### Tasks

- [ ] Initialize monorepo structure
  ```
  forgemind/
  ├── apps/
  │   ├── web/          # Next.js frontend
  │   └── api/          # FastAPI backend
  ├── packages/
  │   └── shared/       # Shared types, constants
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
- [ ] Create **Makefile** with common commands (`make dev`, `make test`, `make migrate`)
- [ ] Set up **structlog** for JSON logging with correlation IDs
- [ ] Set up **pre-commit hooks** (ruff, black, eslint, prettier)

#### Deliverables

- Running dev environment with `docker compose up`
- API returns `{ "status": "ok" }` at `/health`
- Frontend loads at `localhost:3000`
- CI runs on every PR

---

### Phase 1: Auth, Users & Database (Week 3–4)

**Goal**: User can sign up, log in, and have a profile. Database schema is live.

#### Tasks

- [ ] Integrate **Clerk** (frontend: `@clerk/nextjs`, backend: JWT verification)
- [ ] Create all core database tables (see Schema section)
- [ ] Write Alembic migrations
- [ ] Implement user sync webhook (Clerk → PostgreSQL)
- [ ] Build API endpoints:
  - `POST /api/auth/webhook` — Clerk webhook handler
  - `GET /api/users/me` — Get current user
  - `PATCH /api/users/me` — Update profile
- [ ] Build frontend pages:
  - Sign in / Sign up (Clerk components)
  - User settings page
  - Dashboard layout (sidebar + main content)
- [ ] Set up **RBAC middleware** in FastAPI
- [ ] Implement **API key management** (create, list, revoke, hashed storage)
- [ ] Seed database with test data using **Factory Boy**

#### Deliverables

- Users can sign up with Google/GitHub/email
- JWT auth works on all protected API routes
- Dashboard layout renders with user info
- API keys can be created and used for authentication

---

### Phase 2: Projects & Task Engine (Week 5–7)

**Goal**: Users can create projects, and the task DAG engine can schedule work.

#### Tasks

- [ ] Build **Project CRUD** API:
  - `POST /api/projects` — Create project
  - `GET /api/projects` — List projects
  - `GET /api/projects/:id` — Get project details
  - `PATCH /api/projects/:id` — Update project
  - `DELETE /api/projects/:id` — Archive project
- [ ] Build **Task Engine**:
  - `POST /api/projects/:id/tasks` — Create task
  - `GET /api/projects/:id/tasks` — List tasks (with DAG structure)
  - `PATCH /api/tasks/:id` — Update task status
  - DAG dependency resolver (topological sort)
  - Task state machine (pending → queued → running → completed/failed)
- [ ] Set up **Celery** with Redis broker
  - Worker configuration
  - Task routing (different queues for different agent types)
  - Task retry with exponential backoff
  - Task timeout enforcement
  - Task cancellation (revoke)
- [ ] Build **Orchestrator** core:
  - Accept a high-level goal
  - Break into tasks (using Planner Agent — stub for now)
  - Schedule tasks respecting dependencies
  - Handle task completion → trigger dependent tasks
  - Handle task failure → retry or escalate
- [ ] Build frontend:
  - Project creation wizard
  - Project list / grid view
  - Project detail page with task list
  - Task DAG visualization (React Flow)
  - Task status indicators

#### Deliverables

- User creates a project → sees it on dashboard
- Tasks can be created with dependencies
- Celery processes tasks from queue
- DAG visualizer shows task flow

---

### Phase 3: First Agent — Planner (Week 8–10)

**Goal**: User describes a project → Planner Agent generates a PRD + task breakdown.

#### Tasks

- [ ] Integrate **LiteLLM** as the LLM gateway
  - Configure providers (OpenAI, Anthropic, Ollama)
  - Implement model routing per agent
  - Token counting and cost calculation
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
  ```
- [ ] Build **Planner Agent**:
  - Input: project description (natural language)
  - Output: PRD (markdown), architecture doc, task list with dependencies
  - Prompt engineering with few-shot examples
  - Output validation (ensure all required sections present)
- [ ] Build **Prompt Management System**:
  - Store prompts as versioned Jinja2 templates
  - `prompt_versions` table tracking which version produced which output
  - A/B testing support (optional)
- [ ] Build **LLM Provider Settings** page:
  - Add API keys (encrypted storage)
  - Select default provider/model
  - Test connection button
- [ ] Implement **Socket.IO** for real-time updates:
  - Agent started, progress, completed, failed events
  - Connect frontend to WebSocket
- [ ] Build frontend:
  - "New Project" flow: describe idea → watch Planner Agent work → review PRD
  - PRD viewer/editor (Markdown)
  - Task list generated from plan
  - Real-time progress indicator

#### Deliverables

- User types "Build a task management app with React" → gets a full PRD
- PRD includes: overview, features, tech stack, architecture, task breakdown
- Tasks auto-created in DAG from the plan
- Real-time streaming of agent output to UI

---

### Phase 4: Coder Agent + Artifact System (Week 11–14)

**Goal**: Coder Agent generates actual code files. Artifacts are versioned and viewable.

#### Tasks

- [ ] Build **Coder Agent**:
  - Input: task description, file context, style guide
  - Output: file changes (create/modify)
  - Tool: file_read, file_write, search_codebase
  - Context window management (select relevant files)
  - Handle large codebases (chunking, summarization)
- [ ] Build **Artifact System**:
  - Store files in MinIO/S3
  - Version every change
  - Compute diffs between versions
  - Checksum verification
  - `GET /api/artifacts/:id` — Get artifact
  - `GET /api/artifacts/:id/versions` — List versions
  - `GET /api/artifacts/:id/diff/:v1/:v2` — Compare versions
- [ ] Build **Code Editor** (frontend):
  - Monaco Editor integration
  - File tree browser
  - Syntax highlighting (auto-detect language)
  - Diff viewer (side-by-side)
  - "Accept / Reject changes" UI
- [ ] Build **Reviewer Agent**:
  - Input: code diff, project context
  - Output: review comments (line-specific)
  - Checks: bugs, style, performance, security, best practices
  - Auto-triggered after Coder Agent completes
- [ ] Implement **Approval Gates**:
  - Configurable per action type (code.generate, code.merge, deploy)
  - Approval UI (approve / request changes / reject)
  - Auto-approve rules (e.g., auto-approve if cost < $0.10)
  - Notification when approval is needed
- [ ] Build **Agent Pipeline**:
  - Coder → Reviewer → (if approved) → merge to project
  - If reviewer finds issues → Coder fixes → re-review

#### Deliverables

- Tasks assigned to Coder Agent → code files generated
- Code appears in browser editor with syntax highlighting
- Reviewer Agent comments on code
- User approves/rejects changes
- Full version history for every file

---

### Phase 5: Testing & Debugging Agents (Week 15–17)

**Goal**: Auto-generated tests, test execution, and intelligent debugging.

#### Tasks

- [ ] Build **Tester Agent**:
  - Input: code files, project context
  - Output: test files (unit, integration)
  - Analyzes code paths and edge cases
  - Generates pytest / vitest tests depending on language
- [ ] Build **Test Runner Service**:
  - Execute tests in sandboxed Docker containers
  - Parse test results (pass/fail/error)
  - Coverage report generation
  - Store results in database
- [ ] Build **Debugger Agent**:
  - Input: error message/stack trace + code context
  - Output: diagnosis + fix
  - Root cause analysis
  - Auto-fix with test verification
- [ ] Build frontend:
  - Test results dashboard (pass/fail breakdown)
  - Coverage visualization
  - Error log viewer
  - "Fix this error" one-click action
- [ ] Wire up pipeline: Coder → Tester → (if tests fail) → Debugger → re-test

#### Deliverables

- Every code change gets auto-generated tests
- Tests run in sandboxed environment
- Failed tests trigger Debugger Agent
- User sees test results and coverage in UI

---

### Phase 6: Documentation & Security Agents (Week 18–19)

**Goal**: Auto-generated docs and continuous security scanning.

#### Tasks

- [ ] Build **Documenter Agent**:
  - Auto-generate README.md from project structure
  - API documentation from endpoint code
  - Architecture docs with Mermaid diagrams
  - Inline code comments for complex logic
  - Keep docs in sync when code changes
- [ ] Build **Security Agent**:
  - OWASP Top 10 scanning
  - Dependency vulnerability check
  - Secrets detection (API keys in code)
  - SQL injection / XSS pattern detection
  - Security report generation
- [ ] Build frontend:
  - Documentation viewer (rendered Markdown)
  - Security dashboard (vulnerabilities list, severity)
  - Security score per project

#### Deliverables

- Every project has auto-generated, up-to-date docs
- Security scan runs on every code change
- Critical vulnerabilities block approval

---

### Phase 7: Cost Tracking & Analytics (Week 20–21)

**Goal**: Full visibility into LLM costs and agent performance.

#### Tasks

- [ ] Build **Cost Tracking Service**:
  - Track tokens per request (input + output)
  - Calculate cost using provider pricing
  - Per-agent, per-task, per-project aggregation
  - Budget alerts (email + in-app)
  - Budget enforcement (stop agents if budget exceeded)
- [ ] Build **Analytics Dashboard**:
  - Total spend (daily/weekly/monthly)
  - Cost per agent type (bar chart)
  - Cost per project (pie chart)
  - Token usage trends (line chart)
  - Agent success/failure rates
  - Average task completion time
  - Model comparison (cost vs quality)
- [ ] Implement **Smart Model Routing**:
  - Use cheap models for simple tasks (classification, formatting)
  - Use expensive models for complex tasks (architecture, debugging)
  - Configurable per agent

#### Deliverables

- User sees exactly how much each agent costs
- Budget alerts prevent unexpected bills
- Analytics help optimize model selection

---

### Phase 8: Teams & Collaboration (Week 22–24)

**Goal**: Multi-user workspaces with role-based access.

#### Tasks

- [ ] Build **Team System**:
  - Create team, invite members (email)
  - Role management (Owner, Admin, Member, Viewer)
  - Team-level settings (default models, budget, approval rules)
  - Switch between personal/team workspace
- [ ] Build **Activity Feed**:
  - Real-time feed of all team actions
  - Filter by project, agent, user
  - Comment on tasks/artifacts
- [ ] Build **Notification System**:
  - In-app notifications (bell icon)
  - Email notifications (approval requests, task failures, budget alerts)
  - Notification preferences page
- [ ] Build **Audit Log Viewer**:
  - Searchable/filterable log of all actions
  - Export to CSV/JSON
  - Retention policy settings

#### Deliverables

- Teams can collaborate on projects
- Members see real-time activity
- Full audit trail accessible in UI

---

### Phase 9: DevOps Agent & Deployment (Week 25–27)

**Goal**: Auto-generate CI/CD pipelines and deployment configs.

#### Tasks

- [ ] Build **DevOps Agent**:
  - Generate Dockerfile from project analysis
  - Generate docker-compose.yml
  - Generate GitHub Actions workflows (CI/CD)
  - Generate Nginx/Caddy configs
  - Generate Kubernetes manifests (optional)
  - Railway/Fly.io deployment configs
- [ ] Build **Git Integration**:
  - Connect GitHub/GitLab repositories
  - Create branches, commits, PRs from agent output
  - Webhook listener for push/PR events
  - PR description auto-generation
- [ ] Build frontend:
  - Git settings page (connect repo)
  - Deployment configuration UI
  - Pipeline visualization
  - Deploy button with approval gate

#### Deliverables

- Agent generates deployment configs from code analysis
- One-click PR creation from agent output
- Deployment pipeline visualization

---

### Phase 10: Advanced Features & Polish (Week 28–32)

**Goal**: Custom agents, CLI, VS Code extension, webhooks.

#### Tasks

- [ ] **Custom Agent Builder**:
  - UI to create custom agents (name, prompt, tools, model)
  - Save as templates, share with team
  - Agent marketplace (community-shared agents)
- [ ] **CLI Tool** (`forgemind-cli`):
  - `forgemind init` — initialize project
  - `forgemind plan "description"` — run planner
  - `forgemind run task-id` — execute a task
  - `forgemind status` — check project status
  - `forgemind logs` — view agent logs
  - Auth via API key
- [ ] **Webhook System**:
  - Configurable webhooks for events (task.completed, review.needed, etc.)
  - Webhook management UI
  - Retry logic for failed deliveries
- [ ] **VS Code Extension** (stretch goal):
  - Sidebar panel showing ForgeMind tasks
  - "Fix with ForgeMind" on error squiggles
  - "Generate tests" right-click menu
  - Real-time agent status in status bar
- [ ] **Performance Optimization**:
  - Redis caching for frequent queries
  - Database query optimization
  - Pagination for all list endpoints
  - Lazy loading on frontend
  - Bundle size optimization
- [ ] **UX Polish**:
  - Onboarding flow (guided tour)
  - Empty states
  - Error boundaries
  - Loading skeletons
  - Dark/light theme toggle
  - Responsive design (mobile-friendly)

#### Deliverables

- Users can create custom agents
- CLI tool for terminal-first workflow
- Webhooks for external integrations
- Polished, production-ready UI

---

### Phase 11: Production Hardening (Week 33–35)

**Goal**: Production-ready infrastructure, monitoring, and reliability.

#### Tasks

- [ ] **Monitoring Stack**:
  - Prometheus metrics (request latency, error rates, queue depth)
  - Grafana dashboards (system health, agent performance)
  - Sentry error tracking
  - OpenTelemetry traces
  - Health check endpoints with deep checks (DB, Redis, MinIO)
- [ ] **Security Hardening**:
  - Security audit of all endpoints
  - CORS configuration
  - Rate limiting on all public endpoints
  - Input sanitization audit
  - Dependency vulnerability scan
  - CSP headers
  - API key rotation mechanism
- [ ] **Reliability**:
  - Database backups (automated daily)
  - Redis persistence configuration
  - Graceful shutdown for Celery workers
  - Dead letter queue for permanently failed tasks
  - Database connection pooling
- [ ] **Load Testing**:
  - Simulate 100 concurrent users
  - Identify bottlenecks
  - Optimize hot paths
- [ ] **Documentation**:
  - API documentation (auto-generated from FastAPI)
  - User guide
  - Admin guide
  - Contributing guide

#### Deliverables

- Production-ready infrastructure
- Monitoring dashboards live
- Security audit passed
- Load test results documented

---

## 9. API Design Overview

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
POST   /v1/auth/webhook              # Clerk webhook
GET    /v1/users/me                   # Current user

# Projects
POST   /v1/projects                   # Create project
GET    /v1/projects                   # List projects
GET    /v1/projects/:id               # Get project
PATCH  /v1/projects/:id               # Update project
DELETE /v1/projects/:id               # Archive project

# Tasks
POST   /v1/projects/:id/tasks         # Create task
GET    /v1/projects/:id/tasks         # List tasks (DAG)
GET    /v1/tasks/:id                   # Get task detail
PATCH  /v1/tasks/:id                   # Update task
POST   /v1/tasks/:id/cancel           # Cancel task
POST   /v1/tasks/:id/retry            # Retry task

# Agents
POST   /v1/tasks/:id/execute          # Execute task with agent
GET    /v1/agents                      # List available agents
GET    /v1/agents/:type/config         # Get agent config
PATCH  /v1/agents/:type/config         # Update agent config

# Artifacts
GET    /v1/projects/:id/artifacts      # List artifacts
GET    /v1/artifacts/:id               # Get artifact
GET    /v1/artifacts/:id/versions      # List versions
GET    /v1/artifacts/:id/diff          # Compare versions

# Approvals
GET    /v1/approvals/pending           # List pending approvals
POST   /v1/approvals/:id/approve       # Approve
POST   /v1/approvals/:id/reject        # Reject

# Analytics
GET    /v1/analytics/costs             # Cost breakdown
GET    /v1/analytics/usage             # Token usage
GET    /v1/analytics/agents            # Agent performance

# Teams
POST   /v1/teams                       # Create team
GET    /v1/teams/:id                   # Get team
POST   /v1/teams/:id/invite            # Invite member
DELETE /v1/teams/:id/members/:uid      # Remove member

# Audit
GET    /v1/audit-logs                  # Search audit logs
GET    /v1/audit-logs/export           # Export logs

# WebSocket
WS     /ws/projects/:id               # Real-time project updates
WS     /ws/tasks/:id                   # Real-time task/agent stream
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
    "code": "TASK_NOT_FOUND",
    "message": "Task with id xyz not found",
    "details": {}
  },
  "meta": {
    "request_id": "uuid",
    "timestamp": "ISO8601"
  }
}
```

---

## 10. Security Model

### Authentication Flow

```
User → Clerk (login) → JWT → Frontend stores token
Frontend → API request with JWT → FastAPI middleware verifies → Route handler
```

### API Key Flow

```
User creates API key → Backend generates random key → Hash with bcrypt → Store hash
User sends X-API-Key header → Backend hashes incoming key → Compare with stored hash
```

### Encryption

- **At rest**: API keys hashed with bcrypt, LLM provider keys encrypted with AES-256-GCM
- **In transit**: TLS 1.3 everywhere
- **Secrets**: Never logged, never returned in API responses (only key prefix)

### RBAC Matrix

| Action          | Owner | Admin | Member | Viewer |
| --------------- | ----- | ----- | ------ | ------ |
| Create project  | ✅    | ✅    | ✅     | ❌     |
| Delete project  | ✅    | ✅    | ❌     | ❌     |
| Run agents      | ✅    | ✅    | ✅     | ❌     |
| Approve changes | ✅    | ✅    | ❌     | ❌     |
| View projects   | ✅    | ✅    | ✅     | ✅     |
| Manage team     | ✅    | ✅    | ❌     | ❌     |
| Manage billing  | ✅    | ❌    | ❌     | ❌     |
| View audit logs | ✅    | ✅    | ✅     | ✅     |
| Export data     | ✅    | ✅    | ❌     | ❌     |

### Rate Limiting

- Per-user: 100 requests/minute (API), 20 requests/minute (LLM calls)
- Per-agent: Configurable per agent type
- Global: Circuit breaker triggers at 50% error rate

---

## 11. Testing Strategy

### Test Pyramid

```
         ╱╲
        ╱ E2E ╲         ~10 tests  (Playwright)
       ╱────────╲
      ╱Integration╲     ~50 tests  (Testcontainers + real DB)
     ╱──────────────╲
    ╱   Unit Tests    ╲  ~200 tests (pytest + vitest)
   ╱────────────────────╲
```

### Backend Testing

- **Unit tests**: Every service method, every agent's input/output validation
- **Integration tests**: API endpoints with real PostgreSQL (Testcontainers)
- **Agent tests**: Mock LLM responses, verify prompt construction and output parsing
- **Celery tests**: Verify task routing, retry, timeout, cancellation

### Frontend Testing

- **Unit tests**: Component rendering, state management
- **Integration tests**: Page-level tests with mocked API
- **E2E tests**: Critical flows (sign up → create project → run agent → approve)

### CI Pipeline

```yaml
on: pull_request
jobs:
  lint: ruff + eslint + prettier
  type-check: mypy + tsc
  test-backend: pytest --cov (with Testcontainers)
  test-frontend: vitest --coverage
  e2e: playwright (on merge to main only)
  security: pip-audit + npm audit
```

---

## 12. Deployment Strategy

### Local Development

```bash
# One command to start everything
docker compose up -d

# Or use Makefile
make dev        # Start all services
make test       # Run all tests
make migrate    # Run DB migrations
make seed       # Seed test data
```

### Staging

- Auto-deploy on merge to `develop` branch
- Same infrastructure as production (scaled down)
- Seeded with test data

### Production

- Deploy on tagged releases (`v1.0.0`)
- Blue-green deployment (zero downtime)
- Database migrations run as pre-deploy step
- Health checks gate traffic routing

### Recommended Hosting (Budget-Friendly Start)

| Service       | Provider                     | Estimated Cost |
| ------------- | ---------------------------- | -------------- |
| API + Workers | Railway or Fly.io            | ~$10-20/mo     |
| Frontend      | Vercel (free tier)           | $0             |
| PostgreSQL    | Neon (free tier) or Supabase | $0-10/mo       |
| Redis         | Upstash (free tier)          | $0             |
| File Storage  | Cloudflare R2 (free tier)    | $0             |
| Auth          | Clerk (free tier, 10k MAU)   | $0             |
| Monitoring    | Grafana Cloud (free tier)    | $0             |
| **Total**     |                              | **~$10-30/mo** |

---

## 13. Monitoring & Observability

### Key Metrics

- **API**: Request rate, latency (p50/p95/p99), error rate
- **Agents**: Execution time, success rate, tokens used, cost
- **Queue**: Depth, processing time, failed task rate
- **System**: CPU, memory, disk, DB connections

### Alerting Rules

| Alert           | Condition             | Severity |
| --------------- | --------------------- | -------- |
| High error rate | > 5% 5xx in 5min      | Critical |
| Agent stuck     | No heartbeat for 5min | Warning  |
| Queue depth     | > 100 pending tasks   | Warning  |
| Budget exceeded | Project spend > limit | Critical |
| DB connections  | > 80% pool used       | Warning  |

### Log Format

```json
{
  "timestamp": "2026-03-25T10:30:00Z",
  "level": "info",
  "message": "Agent completed task",
  "correlation_id": "req-abc-123",
  "agent_type": "coder",
  "task_id": "task-xyz",
  "project_id": "proj-456",
  "duration_ms": 3200,
  "tokens_used": 1500,
  "cost_usd": 0.023
}
```

---

## Summary Timeline

| Phase                           | Duration   | Key Milestone                      |
| ------------------------------- | ---------- | ---------------------------------- |
| **Phase 0** — Foundation        | Week 1–2   | Dev environment running            |
| **Phase 1** — Auth & Users      | Week 3–4   | Users can sign up and log in       |
| **Phase 2** — Projects & Tasks  | Week 5–7   | Task DAG engine working            |
| **Phase 3** — Planner Agent     | Week 8–10  | First agent generates PRDs         |
| **Phase 4** — Coder + Artifacts | Week 11–14 | Code generation + review pipeline  |
| **Phase 5** — Testing & Debug   | Week 15–17 | Auto-testing + debugging           |
| **Phase 6** — Docs & Security   | Week 18–19 | Auto-docs + security scanning      |
| **Phase 7** — Cost Analytics    | Week 20–21 | Full cost visibility               |
| **Phase 8** — Teams             | Week 22–24 | Multi-user collaboration           |
| **Phase 9** — DevOps Agent      | Week 25–27 | CI/CD generation + Git integration |
| **Phase 10** — Advanced         | Week 28–32 | Custom agents, CLI, webhooks       |
| **Phase 11** — Production       | Week 33–35 | Monitoring, hardening, launch      |

> **Total: ~35 weeks (8–9 months) to full production launch**
> MVP (Phases 0–4): ~14 weeks (3.5 months) — user can describe a project, get a plan, and generate code with review.

---

## Quick Start Commands (When You Begin Phase 0)

```bash
# Create the monorepo
mkdir forgemind && cd forgemind
mkdir -p apps/web apps/api packages/shared docker .github/workflows

# Initialize backend
cd apps/api
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install fastapi uvicorn sqlalchemy alembic celery redis pydantic litellm python-socketio structlog sentry-sdk

# Initialize frontend
cd ../web
npx create-next-app@latest . --typescript --tailwind --app --eslint
npm install @clerk/nextjs zustand @tanstack/react-query socket.io-client

# Initialize Docker
cd ../../docker
# Create docker-compose.yml with PostgreSQL, Redis, MinIO
```

---

_This document is your single source of truth for the ForgeMind project. Update it as you complete phases and make architectural decisions._
