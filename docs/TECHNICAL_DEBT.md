# Technical Debt — ForgeMind API

Discovered during FM-010A validation pass.

## TD-001: `depends_on` ARRAY column

**Location:** `app/models/task.py` — `depends_on: ARRAY(UUID)`
**Risk:** Medium
**Description:** Task dependencies are stored as a PostgreSQL UUID array on the task row itself. This is convenient for reads but:

- No foreign-key integrity enforcement on dependency IDs
- Cannot efficiently query "which tasks depend on X?" without array containment scan
- Harder to model richer relationship metadata (e.g., dependency type, optional/required)

**Recommended future action:** Migrate to a `task_dependencies` junction table when the orchestrator needs to query reverse dependencies or enforce integrity. Not urgent for MVP.

---

## TD-002: SKIPPED dependencies not treated as "satisfied"

**Location:** `app/services/task_service.py` — `_promote_ready_tasks()`
**Risk:** Low–Medium
**Description:** When checking if a blocked task's dependencies are satisfied, only COMPLETED tasks count. If a dependency is SKIPPED, downstream tasks stay BLOCKED forever.

**Recommended future action:** Decide whether SKIPPED should count as "satisfied" (like COMPLETED) or require manual intervention. Update `_promote_ready_tasks()` accordingly.

---

## TD-003: HTTPException in service layer

**Location:** `app/services/project_service.py`, `app/services/task_service.py`
**Risk:** Low
**Description:** Services raise `fastapi.HTTPException` directly, coupling them to HTTP semantics. Makes it harder to reuse services from non-HTTP contexts (e.g., Celery tasks, CLI).

**Recommended future action:** Define domain exceptions (e.g., `NotFoundError`, `InvalidStateTransitionError`) in a `core/exceptions.py` module. Map them to HTTP responses in route handlers or via FastAPI exception handlers.

---

## TD-004: No `updated_at` trigger at DB level

**Location:** All model `updated_at` columns
**Risk:** Low
**Description:** `onupdate=func.now()` only triggers when SQLAlchemy detects a change via the ORM. Direct SQL updates or bulk operations bypass it.

**Recommended future action:** Add a PostgreSQL trigger function on each table to set `updated_at = NOW()` on every UPDATE. Not needed until bulk operations are introduced.

---

## TD-005: No concurrency protection on task state transitions

**Location:** `app/services/task_service.py` — `update_task_status()`
**Risk:** Low (single-agent)
**Description:** Status transitions use optimistic reads with no row-level locking. Two concurrent requests could race on the same task transition.

**Recommended future action:** Add `SELECT ... FOR UPDATE` (via `with_for_update()`) when transitioning task status, once concurrent agent execution is enabled.

---

## TD-006: API routes not under versioned prefix

**Location:** `app/api/router.py`
**Risk:** Low
**Description:** All routes are mounted at root (`/health`, `/projects`, etc.) rather than under `/api/v1/`. Fine for now but should be namespaced before public-facing clients depend on the URL structure.

**Recommended future action:** Mount `api_router` under `settings.api_v1_prefix` in `main.py` (the setting already exists).

---

## TD-007: Planner output quality not yet validated against real LLM

**Location:** `app/services/planner_service.py`
**Risk:** Medium
**Discovered:** FM-020A
**Description:** The `PLANNER_SYSTEM_PROMPT` has not been tested against actual LLM providers yet (no API key configured during development). The normalization layer (`_normalize_plan`) was added in FM-020A to handle malformed output, but real-world prompt engineering will need iteration once LLM calls are live.

**Recommended future action:** Run a test harness with the 5 representative prompts against at least 2 providers (OpenAI, Anthropic) and tune the system prompt based on actual output quality. Check for: generic/shallow plans, inconsistent stack recommendations, hallucinated technologies, and excessive phases.

---

## TD-008: Linear-only task dependency chains

**Location:** `app/services/planner_service.py` — dependency wiring
**Risk:** Low–Medium
**Discovered:** FM-020A
**Description:** All phases from the planner are wired as a strictly linear chain (task N depends on task N-1). The DAG model supports arbitrary dependency graphs via `depends_on: ARRAY(UUID)`, but the planner doesn't produce parallel-safe dependency metadata yet.

**Recommended future action:** Extend the planner prompt to return dependency hints per phase. Allow the service to wire non-linear DAGs when the LLM indicates parallelizable phases.

---

## TD-009: `response_format: json_object` not universally supported

**Location:** `app/core/llm.py` — `llm_json_completion()`
**Risk:** Low (mitigated by `litellm.drop_params = True`)
**Discovered:** FM-020A
**Description:** The `response_format: {"type": "json_object"}` parameter only works with OpenAI-compatible models. LiteLLM's `drop_params = True` silently drops it for unsupported providers, which means the model may return non-JSON. The `json.loads` catch handles this gracefully (returns None → stub fallback), but it means non-OpenAI providers may always fall back to stub mode.

**Recommended future action:** For non-OpenAI providers, consider adding a retry with explicit "respond in JSON only" instruction, or use a structured output library that postprocesses free-text into JSON.

---

## TD-010: Worker has no retry/backoff for failed tasks

**Location:** `apps/worker/worker/main.py`
**Risk:** Medium
**Discovered:** FM-024
**Description:** When a task execution fails, it is marked FAILED with no automatic retry. The task state machine allows FAILED → READY retry, but nothing triggers it automatically.

**Recommended future action:** Add configurable retry count and exponential backoff. Consider a dead-letter queue for tasks that exceed retry limits.

---

## TD-011: Agent resolution uses in-memory scan

**Location:** `app/services/agent_service.py` — `resolve_agent_for_task_type()`
**Risk:** Low
**Discovered:** FM-022
**Description:** Agent-to-task-type resolution loads all active agents and scans in Python. Fine for 5 agents but won't scale to many agents or frequent resolution calls.

**Recommended future action:** Use a PostgreSQL JSON containment query (`@>`) or a junction table for agent-task-type mappings.

---

## TD-012: Fixed agents produce standalone artifacts without prior context

**Location:** `apps/worker/worker/agents/`
**Risk:** Medium
**Discovered:** FM-025
**Description:** Each fixed agent receives only the task title/description as context. It has no access to prior artifacts from earlier tasks in the same run. A reviewer can't see the coder's output, a tester can't see the architecture.

**Recommended future action:** Build an artifact context pipeline that feeds prior run artifacts into agent prompts, enabling chained reasoning across execution steps.

---

## TD-013: Approval required only for fixed task types

**Location:** `app/services/execution_service.py` — `APPROVAL_REQUIRED_TASK_TYPES`
**Risk:** Low–Medium
**Discovered:** FM-026
**Description:** Approval requests are auto-created only when task type is `architecture` or `review`. This is hardcoded in a Python set. There's no policy engine or per-project configuration for approval rules.

**Recommended future action:** Introduce an approval policy model (per-project or global) that specifies which task types, agent slugs, or artifact types require human approval. Migrate the hardcoded set to policy-based evaluation.

---

## TD-014: No real-time event streaming

**Location:** `app/api/routes/events.py`, frontend event timeline
**Risk:** Low
**Discovered:** FM-027
**Description:** Execution events are fetched via polling (page load). There's no real-time push mechanism (WebSocket, SSE) for live event streaming to the frontend.

**Recommended future action:** Add a Server-Sent Events (SSE) endpoint or WebSocket channel for real-time event delivery. Consider Redis pub/sub for cross-worker event broadcasting.

---

## TD-015: Approval decision has no authorization check

**Location:** `app/services/approval_service.py` — `resolve_approval()`
**Risk:** Medium
**Discovered:** FM-026
**Description:** Any caller can approve or reject any approval request. The `decided_by` field is set from the auth stub's fixed UUID. There's no ownership check, role-based access, or team assignment for approvals.

**Recommended future action:** Implement proper authorization: approvals should be assigned to specific users/roles, and only authorized users should be able to resolve them.

---

## TD-016: Retry/cancel event types reuse existing enum values

**Location:** `app/services/execution_service.py` — `retry_task()`, `cancel_task()`
**Risk:** Low
**Discovered:** FM-032
**Description:** `retry_task` emits `TASK_CLAIMED` with `{"action": "retry"}` metadata and `cancel_task` emits `TASK_FAILED` with `{"action": "cancel"}` metadata. These reuse existing event types rather than having dedicated `TASK_RETRIED` and `TASK_CANCELLED` enum values.

**Recommended future action:** Add `TASK_RETRIED` and `TASK_CANCELLED` to `EventType` enum via an Alembic migration. Update the service to emit the correct event types.

---

## TD-017: Chat service has no conversation memory

**Location:** `app/services/chat_service.py` — `chat_about_run()`
**Risk:** Low–Medium
**Discovered:** FM-033
**Description:** Each chat message is a standalone request — the LLM receives the full run context but no previous conversation history. Multi-turn conversations lose prior context.

**Recommended future action:** Add a `chat_messages` table or in-memory session store that tracks conversation history per run. Feed previous messages into the LLM prompt for coherent multi-turn dialogue.

---

## TD-018: Agent hint from planner not validated against registered agents

**Location:** `app/services/planner_service.py` — `_normalize_phases()`
**Risk:** Low
**Discovered:** FM-034
**Description:** The `agent_hint` resolved from `TASK_TYPE_AGENT_MAP` or LLM output is stored directly in `assigned_agent_slug` without validating that the agent slug actually exists in the agent registry. If a task_type or LLM output references a non-existent agent, the worker will fail to find it.

**Recommended future action:** Validate `agent_hint` against registered agent slugs during plan normalization, falling back to `None` (let the worker resolve) for unknown slugs.

---

## TD-019: Run memory cache is in-process only

**Location:** `app/services/run_memory_service.py` — `_run_summary_cache`
**Risk:** Medium
**Discovered:** FM-039
**Description:** The run summary cache is a simple in-process Python dict with LRU eviction. In a multi-worker deployment, each process has its own cache with no cross-process invalidation. The cache could also serve stale data if external changes (e.g., direct DB updates, approval decisions from the API) don't trigger invalidation.

**Recommended future action:** Move the cache to Redis with TTL-based expiration. Publish invalidation events via Redis pub/sub so all workers/API instances clear stale cache entries.

---

## TD-020: Composition scoring uses hardcoded weights

**Location:** `app/services/composition_service.py` — `score_agent_for_capability()`
**Risk:** Low
**Discovered:** FM-036
**Description:** The capability scoring function uses fixed weights (0.6 for task_type match, 0.4 for capability overlap). These values are arbitrary and not tuned against real execution outcomes.

**Recommended future action:** Make scoring weights configurable per deployment. Consider learning optimal weights from execution history (which agent succeeded most for which task type).

---

## TD-021: Connector recommendations are keyword-based only

**Location:** `app/services/connector_service.py` — `STACK_CONNECTOR_MAP`
**Risk:** Low
**Discovered:** FM-038
**Description:** Connector recommendation logic uses a static keyword → connector mapping. It doesn't understand semantic relationships (e.g., "CI/CD" should recommend GitHub Actions but only matches if "github" is in the text).

**Recommended future action:** Use the LLM to analyse project description and recommend connectors, or implement a richer matching system with synonym expansion.

---

## TD-012: ~~Fixed agents produce standalone artifacts without prior context~~ RESOLVED

**Resolved by:** FM-037 — `build_handoff_context()` now injects upstream artifact content into all agent prompts.

---

## TD-010: ~~Worker has no retry/backoff for failed tasks~~ PARTIALLY RESOLVED

**Partially resolved by:** FM-040 — `adaptive_orchestrator.auto_retry_task()` provides auto-retry up to 2 attempts with agent re-routing. Full exponential backoff and dead-letter queue still needed for production.
