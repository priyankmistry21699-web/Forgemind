# FM-037 — Agent Handoff & Collaboration Model

## What was done

Built an artifact-based handoff system so each agent receives context from upstream completed tasks, enabling chained reasoning across execution steps.

## Files modified

- `apps/worker/worker/agents/base.py` — Added `build_handoff_context(db, task)`:
  - Queries upstream completed tasks (same run, lower order_index)
  - Fetches their latest artifact content (up to 5 artifacts, 3000 chars each)
  - Builds rich context string with "=== Prior Work (upstream artifacts) ===" section
  - Falls back gracefully to basic `_task_context()` when no upstream work exists

- `apps/worker/worker/agents/architect_agent.py` — Updated to use `build_handoff_context`, system prompt references "prior work context"
- `apps/worker/worker/agents/coder_agent.py` — Updated with context about architecture documents and upstream decisions
- `apps/worker/worker/agents/reviewer_agent.py` — Updated to reference specific upstream artifacts when critiquing
- `apps/worker/worker/agents/tester_agent.py` — Updated to base tests on actual upstream artifacts
- `apps/worker/worker/main.py` — Enhanced completion log with handoff indicator

## Design decisions

- Only upstream tasks (lower order_index) are included — agents never see future work
- Artifact content is truncated to prevent context window overflow
- Each agent's system prompt is customized to reference the types of upstream work most relevant to its role
