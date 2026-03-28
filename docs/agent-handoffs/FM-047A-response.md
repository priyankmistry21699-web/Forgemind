# FM-047A — Policy-Based Approval Rules

## What was done

Replaced the hardcoded `APPROVAL_REQUIRED_TASK_TYPES = {"architecture", "review"}` with a configurable policy engine. Governance policies support multiple triggers and actions, enabling flexible approval workflows without code changes.

## Files created

- `apps/api/app/models/governance_policy.py` — `GovernancePolicy` model:
  - `PolicyTrigger` enum: `TASK_TYPE`, `COST_THRESHOLD`, `ARTIFACT_TYPE`, `AGENT_ACTION`, `CUSTOM`
  - `PolicyAction` enum: `REQUIRE_APPROVAL`, `AUTO_APPROVE`, `BLOCK`, `NOTIFY`
  - `name`, `trigger`, `action`, `rules` (JSON), `project_id` (null = global), `enabled`, `priority`
- `apps/api/app/services/governance_service.py` — Full CRUD:
  - `create_policy`, `get_policy`, `list_policies`, `update_policy`, `delete_policy`
  - `list_policies` respects project scope + global policies, ordered by priority descending
  - `update_policy` uses `allowed_fields` whitelist for safe partial updates
- `apps/api/app/api/routes/governance.py` — Routes: `POST /governance/policies`, `GET /governance/policies`, `GET /governance/policies/{id}`, `PATCH /governance/policies/{id}`, `DELETE /governance/policies/{id}`
- `apps/api/app/schemas/governance.py` — Schemas including `PolicyEvaluation` result model
- `apps/api/alembic/versions/2026_03_29_0012_0013_add_governance_policies.py` — Migration creating `governance_policies`

## Files modified

- `apps/api/app/db/base.py` — Added `GovernancePolicy` import
- `apps/api/app/api/router.py` — Registered `governance_router`

## Design decisions

- Policies are scoped: `project_id=None` = global, else project-specific. Listing always includes global
- Priority ordering ensures deterministic evaluation when multiple policies match
- `rules` JSON is freeform to support different trigger types (e.g., `{"task_types": [...]}`, `{"cost_threshold_usd": 10.0}`)
- Evaluation logic (matching policies against runtime events) is CRUD-only in the service — actual enforcement integration with `execution_service` is deferred
