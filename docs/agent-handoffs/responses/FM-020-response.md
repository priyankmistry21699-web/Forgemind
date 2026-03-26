# FM-020 Response — Real Planner Architecture/Tech Stack Generation

## Status: COMPLETE

---

## Files Modified

| File                                       | Change                                                                                              |
| ------------------------------------------ | --------------------------------------------------------------------------------------------------- |
| `apps/api/app/services/planner_service.py` | Contains the full planner prompt template + LLM integration (implemented in FM-019, validated here) |

## No Additional Files Created

FM-020 validates and finalizes the end-to-end pipeline built across FM-017 through FM-019. All code was already in place.

---

## End-to-End Pipeline

```
User prompt
  → POST /planner/intake
    → planner_service.plan_from_prompt()
      → _generate_plan() → llm_json_completion() with PLANNER_SYSTEM_PROMPT
        → LLM returns structured JSON (or stub fallback)
      → Creates Project (name from LLM or prompt)
      → Creates Run (status=PLANNING)
      → Creates Tasks from plan["phases"] (linear dependency chain)
      → Creates PlannerResult (overview, architecture, stack, assumptions, next_steps)
    → Returns PromptIntakeResponse

Frontend:
  → Dashboard submits prompt → gets project_id + run_id
  → Project detail page fetches project + latest run
  → PlannerResultView fetches GET /runs/{runId}/plan
  → Renders: Overview, Architecture, Stack (pills), Assumptions (bullets), Next Steps (numbered)
  → RunTaskList renders task phases with status badges
```

---

## Planner Prompt Template

The system prompt instructs the LLM to output JSON with:

| Field                  | Type     | Purpose                                                                 |
| ---------------------- | -------- | ----------------------------------------------------------------------- |
| `project_name`         | string   | Short project name (used if user didn't provide one)                    |
| `overview`             | string   | 2-3 sentence summary                                                    |
| `architecture_summary` | string   | System architecture description                                         |
| `recommended_stack`    | object   | `language`, `framework`, `database`, `infrastructure`, `other`          |
| `assumptions`          | string[] | Planning assumptions                                                    |
| `phases`               | object[] | 3-8 task phases with `title`, `description`, `task_type`, `order_index` |
| `next_steps`           | string[] | Immediate next actions                                                  |

### Validation

- LLM response must be valid JSON
- Must contain `overview` and `phases` keys
- Falls back to stub if validation fails

---

## Example Flow

**User says:** "Build me an autonomous YouTube pipeline that monitors channels, downloads new videos, transcribes them, generates summaries, and publishes to a blog"

**With API key configured**, LLM returns:

- `project_name`: "YouTube Pipeline"
- `overview`: Real description of the pipeline
- `architecture_summary`: Microservice architecture with queue, workers, etc.
- `recommended_stack`: `{language: "Python", framework: "FastAPI", database: "PostgreSQL", infrastructure: "Docker Compose", other: "Celery, Whisper, yt-dlp"}`
- `phases`: 5-7 detailed phases (design, scraper, transcription, summarizer, publisher, deployment)
- `next_steps`: Concrete actions

**Without API key**, stub data is returned with "TBD" values and generic phases.

---

## Technical Debt: None introduced
