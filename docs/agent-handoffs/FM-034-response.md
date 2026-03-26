# FM-034 — Planner-to-Execution Handoff Refinement

## Status: DONE

## What was implemented

All changes in **`apps/api/app/services/planner_service.py`**:

1. **Expanded `ALLOWED_TASK_TYPES`** — Added "architecture" and "review" (now 7 types: planning, architecture, codegen, review, verification, testing, deployment)
2. **`TASK_TYPE_AGENT_MAP`** — New mapping from task_type to preferred agent slug:
   - planning→planner, architecture→architect, codegen→coder, review→reviewer, verification→reviewer, testing→tester, deployment→coder
3. **`APPROVAL_CHECKPOINT_TYPES`** — Set of {"architecture", "review"} for auto-flagging approval requirements
4. **Updated `PLANNER_SYSTEM_PROMPT`** — Richer JSON schema with `agent_hint` and `requires_approval` fields per phase. Instructions to include architecture and review phases.
5. **Updated `_normalize_phases()`** — Extracts agent_hint (LLM output → fallback to TASK_TYPE_AGENT_MAP) and requires_approval (LLM output → fallback to APPROVAL_CHECKPOINT_TYPES)
6. **Updated `_build_stub_plan()`** — 5 phases (planning, architecture, codegen, review, testing) with agent hints and approval flags
7. **Updated `plan_from_prompt()`** — Sets `assigned_agent_slug=phase.get("agent_hint")` and appends " [requires approval]" to descriptions when flagged

## Technical debt

- TD-018: Agent hint not validated against registered agents (could reference non-existent slug)
