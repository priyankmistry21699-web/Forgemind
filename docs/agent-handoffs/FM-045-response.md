# FM-045 — Execution Quality Eval Suite

## What was done

Created a JSON-driven evaluation suite with 23 benchmark cases across 4 categories (topic detection, connector recommendations, retry policies, chatbot stubs), validating the intelligence layer introduced in FM-041 through FM-044.

## Files created

- `apps/api/evals/test_quality_evals.py` — Eval test classes:
  - `TestTopicDetectionEvals`: Parametrized tests validating `detect_topics()` against benchmark cases
  - `TestConnectorRecommendationEvals`: Parametrized tests validating `recommend_connectors()` output (connector inclusion and priority levels)
  - `TestRetryPolicyEvals`: Two sub-categories — `policy_selection` (sync) verifying `get_policy_for_task()` + `get_max_retries()`, and `exhaustion_handling` / `no_retry_policy` (async DB fixtures) verifying `can_retry()` correctness
  - `TestChatbotStubEvals`: Verifies `_build_stub_response()` detects blockers, failures, approvals correctly
- `apps/api/evals/datasets/eval_benchmarks.json` — JSON dataset with 23 benchmark cases
- `apps/api/evals/__init__.py` — Package init
- `apps/api/evals/conftest.py` — Eval-specific fixtures

## Design decisions

- Eval dataset is JSON-file-driven (`eval_benchmarks.json`) — allows adding new cases without code changes
- Uses `pytest.mark.parametrize` for data-driven testing from the JSON file
- Mixes synchronous (pure function) and async (DB-dependent) evals
- Separate `evals/` directory — not in `tests/`, indicating these are quality benchmarks, not unit tests
