# API, Webhooks & Ecosystem — Developer Guide (FM-201 → FM-210)

## Overview

ForgeMind exposes a **versioned public API** (`/api/v1/`), **API key authentication**, **rate limiting**, **webhook connectors**, and integrations with external services (Slack, GitHub notifications, CI/CD).

---

## API Authentication

Two authentication methods are supported:

1. **JWT tokens** — for browser-based sessions (existing auth flow).
2. **API keys** — for programmatic access and integrations.

### API Key Lifecycle

```
POST   /api-keys          — Create a new API key (returns raw key once)
GET    /api-keys          — List all keys for the current org
DELETE /api-keys/{id}     — Revoke a key
```

Keys are scoped: `["read", "write", "admin"]`. The raw key is shown only on creation; the database stores a SHA-256 hash.

---

## Versioned API (`/api/v1/`)

All core endpoint groups are mounted under `/api/v1/`:

| Prefix                      | Router                   | Description                          |
| --------------------------- | ------------------------ | ------------------------------------ |
| `/api/v1/projects`          | projects_router          | Project CRUD and settings            |
| `/api/v1/runs`              | runs_router              | Run lifecycle and history            |
| `/api/v1/tasks`             | tasks_router             | Task management                      |
| `/api/v1/costs`             | costs_router             | Cost tracking and budgets            |
| `/api/v1/code-intelligence` | code_intelligence_router | Dependency graph, patterns, coverage |
| `/api/v1/analytics`         | analytics_router         | Metrics, health, velocity            |
| `/api/v1/approvals`         | approvals_router         | Spec and plan approvals              |
| `/api/v1/governance`        | governance_router        | Compliance and audit                 |
| `/api/v1/ecosystem`         | ecosystem_router         | Webhooks and connectors              |

### OpenAPI Specification

FastAPI auto-generates an OpenAPI 3.x specification. Completeness is validated in `TestOpenAPISpecCompleteness`:

- All 8 core `/api/v1/` route groups are present in the spec paths.
- Schemas section is populated with Pydantic model definitions.
- Every path has at least one HTTP operation.
- `api-v1` tag is present on versioned routes.
- Spec is fully JSON-serializable.

Access the interactive docs at `/docs` (Swagger UI) or `/redoc` (ReDoc).

---

## Rate Limiting (FM-202)

All `/api/v1/` routes are protected by a sliding-window rate limiter.

### How It Works

- Rate limits are enforced per API key (or per IP for unauthenticated requests).
- Tier-based: configurable `max_requests` and `window_seconds` per key tier.
- Standard headers are returned on every response:

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 997
X-RateLimit-Reset: 1714003200
```

- When the limit is exceeded, the API returns `429 Too Many Requests`.

### Configuration

Rate limit tiers are defined in `api_key_service.require_rate_limit()`. Override per key by setting `rate_limit_tier` on the API key model.

---

## Webhook Connectors (FM-205 → FM-208)

### Registering a Connector

```python
await webhook_connector_service.register_connector(
    db, name="GitHub Notifications",
    connector_type=ConnectorType.SOURCE,
    config_json={
        "webhook_url": "https://example.com/webhook",
        "secret": "whsec_...",
        "health_url": "https://example.com/health",
    },
)
```

### Connector Types

| Type          | Direction | Example                        |
| ------------- | --------- | ------------------------------ |
| SOURCE        | Inbound   | GitHub webhook → ForgeMind     |
| SINK          | Outbound  | ForgeMind → Slack notification |
| BIDIRECTIONAL | Both      | CI/CD integration              |

### Webhook Security

- **Signature validation:** Inbound webhooks are verified using HMAC-SHA256 signatures.
- **Secret rotation:** Connector secrets can be rotated without downtime.
- **Replay protection:** Timestamp validation rejects events older than 5 minutes.

### Health Checks

```python
result = await webhook_connector_service.health_check_connector(db, connector_id)
# {"probe": "http_ok", "new_status": "active", "status_code": 200}
```

Connectors transition to `ERROR` status on failed health checks and `ACTIVE` on success.

---

## Integration Setup

### Slack Integration

1. Create a SINK connector with `webhook_url` pointing to your Slack incoming webhook.
2. Configure event subscriptions: `run.completed`, `alert.triggered`, `approval.requested`.
3. ForgeMind sends formatted Slack blocks for each subscribed event.

### GitHub Integration

1. Create a SOURCE connector for inbound GitHub webhooks.
2. Set `secret` to match the GitHub webhook secret.
3. Supported events: `push`, `pull_request`, `check_run`.

### CI/CD Integration

1. Use API keys with `["read", "write"]` scopes.
2. POST run results to `/api/v1/runs/{id}/complete` with artifact data.
3. Query `/api/v1/code-intelligence/coverage` to track coverage trends.

---

## Security Considerations

- API keys are hashed (SHA-256) at rest — raw keys cannot be recovered.
- Rate limiting prevents brute-force and DoS attacks.
- Webhook signatures prevent spoofed events.
- Scoped keys enforce least-privilege access.
- All endpoints require authentication (JWT or API key).

---

## External Integrations (FM-204 → FM-207)

### Slack Integration (FM-204)

Full Slack Bot integration via `integration_service.py`:

- **Slash commands:** `/forgemind status`, `/forgemind run`, `/forgemind help`
- **Interactive actions:** Approve/reject buttons processed via action handler
- **Message posting:** `slack_post_message(channel, text, blocks=None)` via Bot API
- **Signature verification:** `verify_slack_signature()` validates Slack request signatures

Routes: `POST /integrations/slack/commands`, `/actions`, `/post`

### Jira Integration (FM-205)

Bidirectional Jira Cloud sync via `integration_service.py`:

- **Issue CRUD:** `jira_create_issue()`, `jira_get_issue()`, `jira_transition_issue()`
- **Field mapping:** 5 fields (title↔summary, description, status, assignee, priority)
- **Status sync:** Bidirectional mapping (ForgeMind ↔ Jira status names)
- **Auth:** Basic auth via email + API token

Routes: `POST /integrations/jira/issues`, `GET /integrations/jira/issues/{key}`

### PagerDuty Integration (FM-206)

PagerDuty Events API v2 via `integration_service.py`:

- **Incident creation:** `pagerduty_create_incident()` with severity mapping
- **Auto-resolution:** `pagerduty_resolve_incident()` by dedup key
- **Severity mapping:** critical→critical, high→error, warning→warning, low/info→info

Routes: `POST /integrations/pagerduty/incidents`, `/resolve`

### Email Notification Channel (FM-207)

SMTP-based email delivery via `email_service.py`:

- **Templates:** 3 HTML templates (notification, alert, digest)
- **Digest aggregation:** `add_to_digest()` / `flush_digest()` for batching
- **Preferences:** Per-category enable/disable, `unsubscribe()` support
- **Dev mode:** Falls back to logging when no SMTP host configured
- **SMTP:** TLS, configurable host/port/credentials via `configure_smtp()`

---

## Python SDK (FM-209)

Async Python client in `app/sdk/python_client.py`:

```python
async with ForgeMindClient(base_url="http://localhost:8000", api_key="fm_...") as client:
    projects = await client.list_projects()
    impact = await client.analyze_impact(project_id, ["src/main.py"])
    tests = await client.select_tests(project_id, ["src/main.py"], mode="standard")
```

Covers: projects, tasks, code intelligence, analytics, webhooks, API keys.
