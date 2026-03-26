# FM-019 Response — LiteLLM Integration and Planner Provider Config

## Status: COMPLETE

---

## Files Created

| File                       | Purpose                                                                             |
| -------------------------- | ----------------------------------------------------------------------------------- |
| `apps/api/app/core/llm.py` | LLM client wrapper — `llm_completion()` and `llm_json_completion()` async functions |

## Files Modified

| File                                       | Change                                                                                                                                            |
| ------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| `apps/api/pyproject.toml`                  | Added `litellm>=1.50.0` to dependencies                                                                                                           |
| `apps/api/app/core/config.py`              | Added planner LLM settings: `PLANNER_MODEL`, `PLANNER_TEMPERATURE`, `PLANNER_MAX_TOKENS`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY` |
| `apps/api/app/services/planner_service.py` | Rewired to call `_generate_plan()` which uses `llm_json_completion()` with graceful fallback to stub                                              |

---

## LLM Client (`app/core/llm.py`)

- `llm_completion(prompt, system, model, temperature, max_tokens, response_format)` → `str | None`
- `llm_json_completion(prompt, system, model, temperature, max_tokens)` → `dict | None`
- Graceful import — if `litellm` is not installed, returns `None`
- Graceful failure — any exception during LLM call is logged and returns `None`
- Uses settings defaults for model/temperature/max_tokens but allows per-call overrides
- `litellm.drop_params = True` to ignore unsupported params per provider

## Config Settings

| Setting               | Env Var               | Default  |
| --------------------- | --------------------- | -------- |
| `planner_model`       | `PLANNER_MODEL`       | `gpt-4o` |
| `planner_temperature` | `PLANNER_TEMPERATURE` | `0.4`    |
| `planner_max_tokens`  | `PLANNER_MAX_TOKENS`  | `4096`   |
| `openai_api_key`      | `OPENAI_API_KEY`      | `""`     |
| `anthropic_api_key`   | `ANTHROPIC_API_KEY`   | `""`     |
| `google_api_key`      | `GOOGLE_API_KEY`      | `""`     |

---

## Planner Service Updates

- `_generate_plan(prompt)` — calls `llm_json_completion()` with the system prompt, validates response has `overview` and `phases` keys, falls back to `_build_stub_plan()` on failure
- Tasks now created from `plan["phases"]` instead of hardcoded list
- Linear dependencies wired automatically for any number of phases
- Project name can come from LLM response (`plan["project_name"]`)

## Fallback Behavior

| Scenario                                     | Result             |
| -------------------------------------------- | ------------------ |
| No `litellm` installed                       | Stub data          |
| No API key configured                        | Stub data          |
| LLM returns invalid JSON                     | Stub data          |
| LLM returns valid JSON missing required keys | Stub data          |
| Network error / timeout                      | Stub data          |
| LLM returns valid structured JSON            | Real planning data |

---

## Technical Debt: None introduced

The `.env.example` already included `LITELLM_MODEL`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, and `GOOGLE_API_KEY` from FM-001.
