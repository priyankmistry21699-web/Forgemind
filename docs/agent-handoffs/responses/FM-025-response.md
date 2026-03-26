# FM-025 — First Fixed Execution Agents — Response

**Status:** DONE
**Date:** 2025-07-15

---

## Files Created

| File                                           | Purpose                                                           |
| ---------------------------------------------- | ----------------------------------------------------------------- |
| `apps/worker/worker/agents/base.py`            | `_task_context()` helper — builds context string from task fields |
| `apps/worker/worker/agents/architect_agent.py` | Architecture agent — LLM-powered with stub fallback               |
| `apps/worker/worker/agents/coder_agent.py`     | Coder agent — LLM-powered with stub fallback                      |
| `apps/worker/worker/agents/reviewer_agent.py`  | Reviewer agent — LLM-powered with stub fallback                   |
| `apps/worker/worker/agents/tester_agent.py`    | Tester agent — LLM-powered with stub fallback                     |

## Files Modified

| File                                    | Change                                                |
| --------------------------------------- | ----------------------------------------------------- |
| `apps/worker/worker/agents/registry.py` | Populated AGENT_HANDLERS with 4 agent handler imports |

## Design Decisions

1. **4 agents** (architect, coder, reviewer, tester) — planner agent already exists via FM-009/FM-019 planner service. These 4 cover the standard software engineering workflow.
2. **LLM → stub fallback pattern** — each agent tries `llm_completion()` first; if it fails (no API key, provider error), falls back to a structured stub output. This allows the worker to function without LLM keys during development.
3. **Shared `_task_context()` helper** — all agents build context from the same task fields (title, description, type). Documented as TD-012 that agents don't yet see prior artifacts in the chain.
4. **Artifact types**: architect→"architecture", coder→"implementation", reviewer→"review", tester→"test_report". These map to meaningful categories for future UI display and filtering.
5. **System prompts** are role-specific and instruct the LLM to produce structured markdown output appropriate to each agent's role.

## Agent Summary

| Agent     | Slug      | Artifact Type  | System Prompt Focus                              |
| --------- | --------- | -------------- | ------------------------------------------------ |
| Architect | architect | architecture   | System design, component diagrams, tech stack    |
| Coder     | coder     | implementation | Code generation, best practices, implementation  |
| Reviewer  | reviewer  | review         | Code review, quality assessment, recommendations |
| Tester    | tester    | test_report    | Test planning, test cases, coverage strategy     |

## Acceptance Criteria Met

- [x] 4 agent handlers registered in AGENT_HANDLERS
- [x] Each agent calls LiteLLM with role-appropriate system prompt
- [x] Graceful fallback to stub output when LLM fails
- [x] Each agent returns {artifact_title, artifact_content, artifact_type}
- [x] Shared base helper for task context extraction
- [x] All agents integrate into the dispatch flow from FM-024
