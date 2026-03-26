# FM-022 — Agent Registry & Capability Model — Response

**Status:** DONE
**Date:** 2025-07-15

---

## Files Created

| File                                                           | Purpose                                      |
| -------------------------------------------------------------- | -------------------------------------------- |
| `apps/api/app/models/agent.py`                                 | Agent SQLAlchemy model with AgentStatus enum |
| `apps/api/app/schemas/agent.py`                                | AgentRead, AgentList Pydantic schemas        |
| `apps/api/app/services/agent_service.py`                       | CRUD + seeding + agent resolution logic      |
| `apps/api/app/api/routes/agents.py`                            | GET /agents, GET /agents/{agent_id}          |
| `apps/api/alembic/versions/2026_03_26_0003_0004_add_agents.py` | Migration 0004 — agents table                |

## Files Modified

| File                         | Change                                        |
| ---------------------------- | --------------------------------------------- |
| `apps/api/app/db/base.py`    | Added Agent model import                      |
| `apps/api/app/api/router.py` | Mounted agents router                         |
| `apps/api/app/main.py`       | Added seed_default_agents in lifespan startup |

## Design Decisions

1. **AgentStatus enum** (active/inactive/deprecated) — allows agents to be soft-disabled without deletion.
2. **capabilities** and **supported_task_types** stored as JSON arrays — flexible for future expansion without schema changes.
3. **slug** field is unique and indexed — serves as the stable identifier for agent-task mapping.
4. **5 default agents** seeded on startup: planner, architect, coder, reviewer, tester — each with defined capabilities and supported task types.
5. **resolve_agent_for_task_type()** scans active agents' supported_task_types list — simple O(n) scan suitable for 5 agents. Documented as TD-011 for future optimization.

## Acceptance Criteria Met

- [x] Agent model with name, slug, description, status, capabilities, supported_task_types
- [x] AgentRead schema
- [x] seed_default_agents() populates 5 agents on startup (idempotent via slug check)
- [x] GET /agents returns all agents
- [x] GET /agents/{id} returns single agent
- [x] resolve_agent_for_task_type() maps task types to agents
- [x] Alembic migration 0004
