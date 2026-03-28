# FM-060 — Collaboration Phase Hardening

## What was done

Integration-hardened the entire collaboration stack (FM-051 through FM-059) by wiring cross-service hooks, adding 27 integration tests (bringing total to 279), building 4 frontend pages, and updating the navigation. No new models were created — this was purely integration, testing, and UI work.

## Files created

- `apps/api/tests/test_collaboration_phase.py` — 27 integration tests covering:
  - Workspace-scoped projects (workspace_id FK)
  - Permission matrix validation (authz_service)
  - Membership deduplication (unique constraints)
  - Stream event delivery (publish_run_event)
  - Notification delivery configs (webhook/slack/email dispatching)
  - Escalation rules and event logging
  - Activity entry creation and filtering (project + workspace scopes)
  - User presence updates and lookups

### Frontend pages
- `apps/web/src/app/workspaces/page.tsx` — Workspace list page
- `apps/web/src/app/notifications/page.tsx` — Notification inbox page
- `apps/web/src/app/activity/page.tsx` — Activity feed page
- `apps/web/src/app/streaming/page.tsx` — Real-time streaming dashboard

### Frontend components and types
- `apps/web/src/components/` — Components for workspace cards, notification items, activity entries, stream event viewers
- `apps/web/src/types/` — TypeScript interfaces for workspace, notification, activity, and streaming data
- `apps/web/src/lib/` — API client functions for new endpoints

## Files modified

- `apps/api/app/services/execution_service.py` — Added hooks:
  - Approval decisions → notification creation + stream event publishing
  - Run/task state transitions → stream event publishing
- `apps/api/app/services/notification_service.py` — Wired `notification_delivery_service.deliver_notification()` post-creation
- `apps/api/app/services/escalation_service.py` — Wired lifecycle → escalation trigger hooks
- `apps/web/src/components/sidebar.tsx` — Added links: Workspaces, Notifications, Activity, Streaming
- `apps/web/src/components/top-nav.tsx` — Added notification indicator

## Design decisions

- Cross-service hooks are explicit function calls (not an event bus) for debuggability
- All hooks are fire-and-forget — failures in notifications/streaming never block the primary operation
- Frontend pages are read-only dashboards consuming the API — no inline editing
- 27 tests validate the integration seams, not individual service logic (that's covered by unit tests)
- Total test count: 279 passing across the full codebase
