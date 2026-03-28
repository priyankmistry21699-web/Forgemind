# FM-047 — Multi-Agent Council Decision Engine + Cost Tracking

## What was done

Implemented a full council decision engine where multiple agents can vote on decisions using four methods (consensus, majority, supermajority, weighted), along with a cost tracking system that records per-call LLM usage with pre-configured rate tables.

## Files created

### Council Engine
- `apps/api/app/models/council.py` — Models:
  - `CouncilStatus` enum: `CONVENED` → `DELIBERATING` → `DECIDED` | `DEADLOCKED` | `ESCALATED`
  - `DecisionMethod` enum: `CONSENSUS`, `MAJORITY`, `SUPERMAJORITY`, `WEIGHTED`
  - `VoteDecision` enum: `APPROVE`, `REJECT`, `ABSTAIN`, `MODIFY`
  - `CouncilSession` model: FK to project/run/task, `topic`, `context` (JSON), `final_decision`, `decision_rationale`, `decision_metadata`, `votes` relationship
  - `CouncilVote` model: FK to session, `agent_slug`, `decision`, `reasoning`, `confidence` (float), `weight` (float), `suggested_modifications` (JSON)
- `apps/api/app/services/council_service.py` — Council service:
  - `convene_council(db, ...)`: Creates session in `CONVENED` state
  - `cast_vote(db, session_id, ...)`: Transitions session to `DELIBERATING` on first vote
  - `_resolve_decision(votes, method)`: Core algorithm implementing all 4 decision methods
  - `resolve_council(db, session_id)`: Resolves to `DECIDED` or `DEADLOCKED`
  - `escalate_council(db, session_id)`: Transitions to `ESCALATED` (terminal)
- `apps/api/app/api/routes/council.py` — Routes: `POST /council/sessions`, `GET /council/sessions`, `GET /council/sessions/{id}`, `POST /council/sessions/{id}/vote`, `POST /council/sessions/{id}/resolve`, `POST /council/sessions/{id}/escalate`
- `apps/api/app/schemas/council.py` — Read/create schemas for sessions and votes
- `apps/api/alembic/versions/2026_03_30_0016_add_council_tables.py` — Migration creating `council_sessions` + `council_votes`
- `apps/api/tests/test_fm046_050_v2.py` — Tests: `TestCouncilDecision` class

### Cost Tracking
- `apps/api/app/models/cost_record.py` — `CostRecord` model
- `apps/api/app/services/cost_tracking_service.py` — Cost service:
  - `MODEL_COSTS` dict: Per-token USD rates for gpt-4o, gpt-4o-mini, gpt-4-turbo, claude-3-{opus,sonnet,haiku}
  - `estimate_cost(model, prompt_tokens, completion_tokens)`: Returns USD float
  - `record_usage(db, ...)`: Creates `CostRecord` with auto-computed cost
  - `get_run_cost_summary(db, run_id)`: Aggregated totals
  - `get_project_cost_summary(db, project_id)`: Cross-run totals
  - `get_cost_breakdown_by_model(db, ...)`: Per-model breakdown
- `apps/api/app/api/routes/costs.py` — Routes for cost queries
- `apps/api/app/schemas/cost.py` — Cost schemas
- `apps/api/alembic/versions/2026_03_29_0011_0012_add_cost_records.py` — Migration creating `cost_records`

## Files modified

- `apps/api/app/db/base.py` — Added `CouncilSession`, `CouncilVote`, `CostRecord` imports
- `apps/api/app/api/router.py` — Registered `council_router` and `costs_router`

## Design decisions

- Council is asynchronous: agents vote independently, resolution is a separate explicit step
- Weighted voting uses `vote.weight × vote.confidence` — integrates with trust scoring
- Deadlock detection: if no method reaches threshold, result is `DEADLOCKED`
- Escalation is a terminal state (human must intervene)
- Cost tracking uses a pre-configured rate lookup table (`MODEL_COSTS`) — not real-time API billing
