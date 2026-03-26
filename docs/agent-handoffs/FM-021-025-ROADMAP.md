# FM-021 to FM-025 — Execution Agent Foundations

> Phase goal: Turn ForgeMind from an **AI planning system** into an **early execution platform**.
> This is **not** full dynamic multi-agent autonomy — it builds the execution foundation carefully.

---

## What this phase adds

| Task       | One-liner                    | Analogy                                           |
| ---------- | ---------------------------- | ------------------------------------------------- |
| **FM-021** | Artifact storage             | File cabinet for work outputs                     |
| **FM-022** | Agent role registry          | Define employee roles                             |
| **FM-023** | Task execution service       | How employees take and finish assignments         |
| **FM-024** | Worker/orchestrator runtime  | Operations office that assigns work automatically |
| **FM-025** | First fixed execution agents | Hire first small worker team                      |

**Order: strictly sequential, no batching.**

---

## FM-021 — Execution artifact model and persistence

**Purpose:** Give ForgeMind a way to store outputs from tasks and agents.

An `Artifact` model linked to project / run / task. Stores things like:

- plan summary, architecture draft, implementation notes, review comments, test report

**Files:**

- `apps/api/app/models/artifact.py`
- `apps/api/app/schemas/artifact.py`
- `apps/api/app/services/artifact_service.py`
- `apps/api/app/api/routes/artifacts.py`
- Alembic migration

---

## FM-022 — Agent registry and capability model

**Purpose:** Define what agents exist and what each one can do.

Initial agent roles: planner, architect, coder, reviewer, tester.
Each agent has: name, type, capabilities, status/config.
Could be DB model, config-driven registry, or service-level abstraction.

**Files:**

- `apps/api/app/models/agent.py` or config registry
- `apps/api/app/schemas/agent.py`
- `apps/api/app/services/agent_registry.py`
- `apps/api/app/api/routes/agents.py`

---

## FM-023 — Execution service for task claiming and completion

**Purpose:** First actual execution behavior — agent picks up a task, works on it, marks it done.

Execution logic: claim ready task → mark running → complete/fail → attach artifacts → assign agent role.

**Files:**

- `apps/api/app/services/execution_service.py`
- `apps/api/app/services/task_service.py` (extended)
- `apps/api/app/services/artifact_service.py` (integrated)
- `apps/api/app/api/routes/tasks.py` (extended) or new execution routes

---

## FM-024 — Worker/orchestrator foundation

**Purpose:** Background execution runtime — process tasks outside normal web request cycle.

Polling ready tasks → dispatching → processing in background → updating statuses.
Options: lightweight worker loop, Celery, Redis-backed execution process.

**Files:**

- `apps/worker/*`
- `packages/orchestrator/*`
- Docker Compose update for worker service
- Backend service integration

---

## FM-025 — First fixed execution agents

**Purpose:** First time ForgeMind gets actual execution agents.

Fixed roles (not dynamic yet): coder, reviewer, tester.

- Coder → implementation draft
- Reviewer → review/critique
- Tester → test plan or test suggestions

**Files:**

- `packages/agents/*`
- `apps/worker/*`
- `apps/api/app/services/execution_service.py` (extended)
- Agent registry integration
- Artifact generation logic

---

## After FM-025, ForgeMind can:

1. Create project and plan
2. Persist task outputs as artifacts
3. Know which agent types exist
4. Assign/claim tasks
5. Run a background execution loop
6. Let fixed agents produce first execution outputs

## Still NOT yet after FM-025:

- Dynamic agent creation per problem
- Real connector intelligence
- Strong approval workflows
- Complex human-in-the-loop governance
- Artifact versioning
- Replayable runs
- Self-healing execution

---

## Chatbot fit

| Chatbot               | Status after FM-025                  |
| --------------------- | ------------------------------------ |
| **Planning chatbot**  | Already exists in early form         |
| **Execution chatbot** | Becomes possible after/around FM-025 |

---

## Tech stack additions

- Redis for worker/orchestrator patterns
- Possible Celery or lightweight worker loop
- MinIO may start becoming useful for blob artifact storage (later)
- LiteLLM reused for execution agents
