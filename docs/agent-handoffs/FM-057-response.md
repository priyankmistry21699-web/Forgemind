# FM-057 — Escalation Rules & Events

## What was done

Built a per-project escalation engine with configurable rules (6 trigger types × 5 action types) and an audit trail of escalation events, including cooldown support to prevent spam escalations.

## Files created

- `apps/api/app/models/escalation.py` — Models:
  - `EscalationRule`: `project_id` FK (indexed), `name`, `trigger` enum, `action` enum, `rules` (JSON), `cooldown_minutes` (default 30), `is_active` (bool)
  - Trigger enum (6 types): `TASK_TIMEOUT`, `RUN_FAILURE`, `APPROVAL_TIMEOUT`, `BUDGET_EXCEEDED`, `TRUST_SCORE_LOW`, `CUSTOM`
  - Action enum (5 types): `NOTIFY`, `PAUSE_RUN`, `REASSIGN`, `ESCALATE_USER`, `AUTO_CANCEL`
  - `EscalationEvent`: `rule_id` FK (indexed), `project_id` FK, `trigger_data` (JSON), `action_taken` (str), `resolved` (bool)
- `apps/api/app/services/escalation_service.py` — Escalation service:
  - Rules CRUD: `create_rule()`, `get_rule()`, `list_rules()`, `update_rule()`, `delete_rule()`
  - Events: `trigger_escalation(db, rule_id, trigger_data)`, `list_events()`, `resolve_event()`
- `apps/api/app/api/routes/escalation.py` — Routes: `POST /projects/{id}/escalation/rules` (CRUD), `GET /projects/{id}/escalation/events`
- Schemas for rules and events

## Files modified

- `apps/api/alembic/versions/2026_03_27_0019_add_collaboration_and_code_ops.py` — Creates `escalation_rules` and `escalation_events` tables
- `apps/api/app/db/base.py` — Added `EscalationRule`, `EscalationEvent` imports
- `apps/api/app/api/router.py` — Registered `escalation_router`

## Design decisions

- Rules are per-project scoped — each project defines its own escalation policies
- Triggers and actions are decoupled — any trigger can map to any action
- `rules` JSON allows complex conditions specific to each trigger type
- Cooldown prevents spam escalations from the same rule
- `EscalationEvent` provides a complete audit trail with `trigger_data` context
