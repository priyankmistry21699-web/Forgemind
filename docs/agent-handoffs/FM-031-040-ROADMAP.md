# FM-031 to FM-040 — Operator Control & Adaptive Multi-Agent Foundations

> Phase goal: Move ForgeMind from **controlled execution + observability** to **operator control + execution chat + adaptive multi-agent behavior**.

---

## What this phase adds

| Task       | One-liner                         | Analogy                                         |
| ---------- | --------------------------------- | ----------------------------------------------- |
| **FM-031** | Artifact detail page              | Open each work document fully                   |
| **FM-032** | Retry/rerun/cancel controls       | Give managers retry/cancel controls             |
| **FM-033** | Execution chatbot starts          | Add an operations assistant to answer questions |
| **FM-034** | Better plan → execution mapping   | Improve how strategy turns into assignments     |
| **FM-035** | Operator UX polish                | Make the office workflow smooth                 |
| **FM-036** | Dynamic agent composition starts  | Hire specialists depending on the job           |
| **FM-037** | Structured agent handoffs         | Improve handoffs between departments            |
| **FM-038** | Connector intelligence starts     | Identify required external vendors/tools        |
| **FM-039** | Execution memory/context improves | Keep institutional memory                       |
| **FM-040** | Adaptive execution loop v1        | Let the company adapt when plans change         |

**Order: strictly sequential, no batching.**

---

## Milestone 7 — Operator Control & Interaction (FM-031 to FM-035)

### FM-031 — Artifact detail view and navigation

**Purpose:** Make artifacts first-class inspectable outputs — open the actual work product, not just see its title.

**What it does:**

- Artifact detail page with full content rendering
- Metadata display (agent, task, run, project, timestamps)
- Links from run/project pages to artifacts
- Better navigation: artifact ↔ task ↔ run ↔ project

**Why it matters:** Artifacts are what ForgeMind actually produces. If users can't inspect them properly, the system feels shallow.

**Files:**

- `apps/web/app/dashboard/artifacts/[artifactId]/page.tsx`
- `apps/web/lib/artifacts.ts`
- `apps/web/types/artifact.ts`
- `apps/web/components/artifacts/*`
- Backend: possibly add/improve artifact detail endpoint

---

### FM-032 — Execution control actions

**Purpose:** Give the operator basic controls — not just read-only visibility.

**What it does:**

- Retry failed task
- Rerun task
- Cancel a queued/running task
- Possibly re-open downstream tasks safely
- Event logging for all control actions

**Why it matters:** Real systems fail. Without retry/cancel/rerun, users are stuck. ForgeMind cannot feel operationally mature without execution controls.

**Files:**

- `apps/api/app/services/execution_service.py`
- `apps/api/app/services/task_service.py`
- `apps/api/app/api/routes/tasks.py`
- Event logging updates
- Frontend: run detail page controls, task action buttons, action confirmations

---

### FM-033 — Execution chatbot foundation

**Purpose:** The beginning of the second chatbot system — a chat assistant that explains what ForgeMind is doing.

**What it does:**

- Chat interface that answers: what happened in this run? what is blocked? what artifact was produced? what should I approve? why did this fail?
- First version: retrieval/summarization based over tasks, artifacts, approvals, events
- Context assembly from run data
- LiteLLM-powered summarization/generation

**Why it matters:** Execution systems become hard to understand if the user has to manually inspect every page. The chatbot gives explanation, summarization, and operator assistance. Major product differentiator.

**Files:**

- `apps/web/app/dashboard/runs/[runId]/chat` or embedded chat panel
- Chat UI components + types
- Backend: chat route/service, context assembly, LiteLLM integration

---

### FM-034 — Planner-to-execution handoff refinement

**Purpose:** Improve the quality of how plans map to executable tasks — make plans more executable, not just readable.

**What it does:**

- Better phase → task translation
- Task type assignment refinement
- Agent role mapping
- Dependency generation improvements
- Artifact expectation definition
- Approval checkpoint insertion

**Why it matters:** If the plan is weakly mapped to execution, agents get poor instructions, artifacts are inconsistent, handoffs are messy, and execution quality suffers.

**Files:**

- `apps/api/app/services/planner_service.py`
- `apps/api/app/services/task_service.py`
- `apps/api/app/services/agent_service.py`
- `apps/api/app/services/execution_service.py`
- Planner schemas/types
- Docs/debt updates

---

### FM-035 — End-to-end operator UX polish

**Purpose:** Polish the full operator experience — make ForgeMind feel like a real control console.

**What it does:**

- Navigation improvements
- Page consistency
- Labels/messages refinement
- Empty/loading/error states
- Cross-links between project/run/task/artifact/approval/chat
- First-time operator clarity
- README + milestone docs

**Why it matters:** By now ForgeMind has many moving parts. Without strong UX polish, it can feel fragmented.

**Files:**

- Dashboard, run, artifact, approval, chat pages
- Sidebar/nav components
- README + milestone docs

---

## Milestone 8 — Adaptive Multi-Agent Foundations (FM-036 to FM-040)

### FM-036 — Dynamic agent composition foundations

**Purpose:** ForgeMind starts moving beyond fixed agents — decides which agents it needs for the problem.

**What it does:**

- Capability-based composition layer
- Determine required agent roles from plan/task set
- Instantiate task-specific agent teams
- Keep fixed core roles, allow adaptive role selection

**Why it matters:** Different projects need different teams. ForgeMind becomes much more powerful when it can adapt its team to the project.

**Files:**

- `packages/agents/*`
- `apps/api/app/services/agent_service.py`
- `packages/orchestrator/*`
- Capability mapping models/schemas
- Docs/debt updates

---

### FM-037 — Agent handoff and collaboration model

**Purpose:** With multiple agents, they need cleaner handoff behavior — structured work passing.

**What it does:**

- Handoff metadata
- Upstream/downstream artifact expectations
- Agent-to-agent context packaging
- Better transition rules between agent outputs

**Why it matters:** Without explicit handoffs, reviewer may not know what coder produced, tester may not know assumptions, architecture and implementation can drift.

**Files:**

- Artifact schema/model metadata
- Execution service
- Agent logic
- Orchestration layer
- Event log enrichment

---

### FM-038 — Connector intelligence foundation

**Purpose:** ForgeMind begins understanding which external systems/tools are required for a project.

**What it does:**

- Connector recommendation logic
- Connector registry or typed connector definitions
- Mapping between project type and likely required connectors
- Stub connector requirement artifacts

**Why it matters:** Major differentiator for real-world execution. ForgeMind should tell users what connectors are needed, why, and when they block execution.

**Files:**

- Connector models/config
- Planner service
- Project/run metadata
- Artifact generation for connector requirements

---

### FM-039 — Execution memory and contextual reasoning

**Purpose:** As runs become more complex, ForgeMind needs memory of prior outputs, decisions, and context.

**What it does:**

- Improved context handling across task history, approvals, artifacts, agent outputs, event summaries
- Used by: execution chatbot, dynamic agents, retries/reruns, operator explanations
- Summary caches for efficient context retrieval

**Why it matters:** Without memory, each execution step becomes too stateless and repetitive. Makes the system smarter over the course of a run.

**Files:**

- Event service
- Artifact service
- Chat context assembly
- Orchestration context builders
- Summary caches

---

### FM-040 — Adaptive execution loop v1

**Purpose:** The milestone where ForgeMind begins behaving like an adaptive system rather than a scripted executor.

**What it does:**

- Choose next best task/agent path more intelligently
- React to failures/rejections
- Re-route or re-plan parts of execution
- Use richer context from memory, artifacts, approvals, and events

**Why it matters:** Transitions from linear/fixed-role/manually-steered execution to adaptive execution, contextual rerouting, smarter orchestration.

**Files:**

- Orchestrator logic
- Execution service
- Planner/execution handoff logic
- Agent selection logic
- Memory/context services
- Approval and retry logic integration

---

## What ForgeMind becomes after FM-040

- Plans projects with structured architecture + stack
- Creates tasks and artifacts via fixed + partially dynamic agents
- Pauses for human approvals at critical points
- Records and explains execution through event logs + chatbot
- Adapts execution based on feedback/context
- Begins connector-aware orchestration
- Provides operator controls (retry/cancel/rerun)

> **An operator-centered AI execution platform with the start of dynamic multi-agent behavior.**
