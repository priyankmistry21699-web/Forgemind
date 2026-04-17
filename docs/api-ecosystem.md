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

| Prefix | Router | Description |
|--------|--------|-------------|
| `/api/v1/projects` | projects_router | Project CRUD and settings |
| `/api/v1/runs` | runs_router | Run lifecycle and history |
| `/api/v1/tasks` | tasks_router | Task management |
| `/api/v1/costs` | costs_router | Cost tracking and budgets |
| `/api/v1/code-intelligence` | code_intelligence_router | Dependency graph, patterns, coverage |
| `/api/v1/analytics` | analytics_router | Metrics, health, velocity |
| `/api/v1/approvals` | approvals_router | Spec and plan approvals |
| `/api/v1/governance` | governance_router | Compliance and audit |
| `/api/v1/ecosystem` | ecosystem_router | Webhooks and connectors |

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

| Type | Direction | Example |
|------|-----------|---------|
| SOURCE | Inbound | GitHub webhook → ForgeMind |
| SINK | Outbound | ForgeMind → Slack notification |
| BIDIRECTIONAL | Both | CI/CD integration |

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
