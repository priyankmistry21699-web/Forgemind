# 6 · Request & Data Flows

> End-to-end traces through the seven most important flows. Each flow lists concrete files in call order.

---

## Flow 1 · Generic API request

```
Browser / SDK
   │  HTTPS /api/v1/<domain>/...
   ▼
CORSMiddleware                                      core/config.py (allowed_origins)
   ▼
RateLimitMiddleware                                 core/rate_limit.py
   ▼
RequestLoggingMiddleware                            core/logging_middleware.py
   ▼
MetricsMiddleware                                   core/metrics_middleware.py
   ▼
IPAllowlistMiddleware                               core/ip_allowlist_middleware.py
   ▼
api_router                                          apps/api/app/api/routes/__init__.py
   ▼
routes/<domain>.py  —  thin handler
   ▼  Depends(get_current_user) / require_scope
core/auth.py · core/authz_deps.py
   ▼
services/<domain>_service.py  (business logic, DB, LLM)
   ▼
models/<domain>.py  →  AsyncSession  →  Postgres
   ▼
Pydantic schema response  (schemas/<domain>.py)
   ▼
MetricsMiddleware records status/duration  →  JSON log line  →  response
```

---

## Flow 2 · Prompt → plan → run (the core engine loop)

```
User submits prompt (dashboard/projects/[projectId]/prompt)
   ▼
lib/planner.ts  →  POST /api/v1/planner/intake
   ▼
routes/planner.py
   ▼
services/planner_service.py
   │    • builds system + user prompt
   │    • calls core/llm.py (→ LiteLLM)           ── records cost via cost_tracking_service
   │    • validates via spec_plan_validation_service
   │    • writes PlannerResult (models/planner_result.py)
   ▼
services/spec_service.py  →  creates Spec
services/plan_artifact_service.py  →  writes plan artifact
services/spec_plan_approval_service.py  →  approval gate if required
   ▼
approval_service.submit() (if gated)
   ▼ (on approve)
services/execution_service.py  →  creates Run + Tasks
   │    • emits execution_event via event_service
   │    • stream_service fans out to SSE subscribers
   ▼
Worker claims task (apps/worker/worker/main.py)
   ▼
agents/<role>_agent.py  →  executes step
   ▼
writes Artifact · ExecutionEvent · optional ReplaySnapshot
   ▼
frontend SSE subscription (lib/stream.ts) updates run detail live
```

Touches: `planner_service`, `core/llm.py`, `cost_tracking_service`, `spec_service`, `plan_artifact_service`, `spec_plan_approval_service`, `approval_service`, `execution_service`, `event_service`, `stream_service`, `artifact_service`, `replay_service`.

---

## Flow 3 · Dashboard widget render

```
Page mount (e.g. dashboard/analytics/page.tsx)
   ▼
lib/dashboards.ts  →  GET /api/v1/analytics/dashboards/{id}
   ▼
routes/analytics.py  →  project_overview_service / execution_health_service /
                        structural_health_service / velocity_quality_service
   ▼
returns  { widgets: [...] }  (widget defs + data rows)
   ▼
components/dashboard/dashboard-grid.tsx          layout
   ▼
components/dashboard/widget-renderer.tsx         dispatch by widget.type
   ▼
components/dashboard/widget-data-adapter.ts      shape normalization
   ▼
components/dashboard/charts/<type>.tsx           pure-SVG render
```

Live refresh: widgets with `live: true` subscribe via `lib/stream.ts` to `/api/v1/streaming/analytics/{id}`.

---

## Flow 4 · Code-intelligence query

```
User opens dashboard/code-explorer/
   ▼
lib/*  →  GET /api/v1/code-intelligence/{project}/...
   ▼
routes/code_intelligence.py
   ▼  branches by query:
┌──────────────────────────────────────────────────────────┐
│ graph lookup   → code_graph_service (reads code_intelligence model) │
│ refactor recs  → refactor_recommendation_service          │
│ debt / patterns→ pattern_debt_service                     │
│ flakiness      → flakiness_complexity_service             │
│ conventions    → convention_service                       │
└──────────────────────────────────────────────────────────┘
   ▼
impact analysis (dashboard/architecture/)
   routes/architecture.py
     → architecture_service → topology_mapper_service
                             → drift_detection_service
                             → architecture_rule_service
                             → impact_analysis_service ──reads──▶ code_graph_service
```

Repo sync that populates these: `repo_service` + `github_client` + `code_ops_service`.

---

## Flow 5 · Webhook fan-out (outbound)

```
some_service.create/update triggers business event
   ▼
notification_service.enqueue(event, project_id, subjects)
   ▼  (persists Notification rows)
background_scheduler tick or inline call
   ▼
notification_delivery_service.process_pending()
   │   for each active subscription:
   ├── channel=slack     → webhook_connector_service.dispatch_webhook(slack_endpoint)
   ├── channel=pagerduty → webhook_connector_service.dispatch_webhook(pd_endpoint)
   ├── channel=email     → email_service.send(smtp)
   └── channel=inapp     → persisted for UI inbox
   ▼
webhook_connector_service.fire_event()  (for generic subscribers)
   ▼
webhook_connector_service.record_delivery / mark_delivery_success|failed
   ▼
WebhookDelivery rows visible at dashboard/connectors/ + dashboard/notifications/
```

Credentials used here are fetched from `credential_vault_service` + decrypted via `encryption_service`.

---

## Flow 6 · GitHub inbound → internal state

```
GitHub → POST /api/v1/github/webhook
   ▼
routes/github_integration.py
   ▼
webhook_service.verify_github_signature(body, sig)
   ▼
webhook_service.ingest_event(event_type, payload)
   ▼ dispatch:
process_pr_event           → pr_service                  (PR record, merge readiness)
process_workflow_run_event → ci_pipeline_service         (CI status / failures)
process_issues_event       → issue_sync_service
process_push_event         → code_ops_service            (diff intelligence)
process_release_event      → release_gate_service        (release ops)
process_check_run_event    → ci_pipeline_service
   ▼
execution_event + stream_service  →  live UI updates at dashboard/runs, /releases, /reviews
```

---

## Flow 7 · SDK → API → backend

Applies to both [`python_client.py`](../../apps/api/app/sdk/python_client.py) and [`typescript_client.ts`](../../apps/api/app/sdk/typescript_client.ts).

```
client = ForgeMindClient(base_url, api_key)            auth header bearer or X-API-Key
client.runs.list(project_id=...)
   ▼ HTTP GET /api/v1/runs?project_id=...
   ▼ Rate limit + auth middleware
   ▼ routes/runs.py  →  execution_service.list_runs()
   ▼ Pydantic response schema
   ▼ client deserializes to typed objects
```

Streaming (SSE) helper:

```
client.runs.stream(run_id) →  GET /api/v1/streaming/runs/{id}
   ▼  stream_service fans out execution_event rows
   ▼  client yields typed events
```

---

## Flow 8 · Replay

```
User opens dashboard/replay/{run_id}
   ▼
lib/replay.ts  →  GET /api/v1/replay/{run_id}
   ▼
routes/replay.py  →  replay_service.load(run_id)
   ▼
services/replay_service.py
   │   reads ReplaySnapshot rows (hash-addressed) +
   │   associated execution_event chain
   ▼
deterministic reconstruction of agent state at step N
```

Replay snapshots are SHA-256 hashed so integrity can be verified at load time.

---

## Flow 9 · Approvals

```
service flags a request as needing approval (e.g. spec_plan_approval_service)
   ▼
approval_service.create(request_type, subject_id, policy, required_roles)
   ▼
approval_enhanced_service (trust scoring, delegation rules)
   ▼
notification_service  (inbox + webhook fan-out via Flow 5)
   ▼
reviewer opens dashboard/approvals/
   ▼
lib/approvals.ts → POST /api/v1/approvals/{id}/decisions
   ▼
routes/approvals.py → approval_service.record_decision()
   ▼
on approve:
  callback to originating service (e.g. execution_service.start_run())
  audit_log_service.record()
```
