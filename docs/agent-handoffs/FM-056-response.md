# FM-056 — Notification Delivery Service

## What was done

Added external notification delivery to three channels (Slack, email, webhook) with per-user delivery configuration. Delivery is fire-and-forget — failures are logged but never block notification creation.

## Files created

- `apps/api/app/services/notification_delivery_service.py` — Delivery service:
  - `deliver_notification(db, notification)`: Fetches active delivery configs for the user and dispatches to each channel; returns list of `{channel, status, detail}` results
  - `_deliver_webhook(config, notification)`: HTTP POST to configured webhook URL
  - `_deliver_slack(config, notification)`: Posts to Slack webhook endpoint
  - `_deliver_email(config, notification)`: Email delivery (SMTP-ready)
  - Each channel delivery is independent — one failure doesn't block others

## Files modified

- `apps/api/app/models/notification.py` — Added `NotificationDeliveryConfig` model:
  - `user_id` FK, `channel` enum (`SLACK`, `EMAIL`, `WEBHOOK`), `status` enum (`ACTIVE`, `PAUSED`, `DISABLED`)
  - `config` (JSON) for channel-specific settings (URL, email address, etc.)
- `apps/api/app/services/notification_service.py` — Added delivery config CRUD:
  - Create, list, update, delete delivery configs per user
- `apps/api/alembic/versions/2026_03_27_0019_add_collaboration_and_code_ops.py` — Creates `notification_delivery_configs` table
- `apps/api/app/api/router.py` — Added delivery config routes

## Design decisions

- Fire-and-forget delivery — never blocks notification creation
- Multiple channels per user — each configured independently
- Status field (`ACTIVE`/`PAUSED`/`DISABLED`) allows disabling without deleting
- Failures are logged but non-blocking — delivery attempts are best-effort
- Channel-specific config stored in JSON for flexibility
