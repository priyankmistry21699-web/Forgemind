TASK ID:
FM-009

STATUS:
done

SUMMARY:
Implemented prompt intake endpoint (POST /planner/intake) that accepts a natural-language prompt and creates a Project (status=PLANNING), a Run (run_number=1, trigger=prompt), and 3 stub planning tasks (analyse → scaffold → verify) with wired dependencies. The planner service is a stub ready to be replaced with LLM-based decomposition in later phases.

FILES CHANGED:

- apps/api/app/schemas/prompt_intake.py (created — PromptIntakeRequest, PromptIntakeResponse)
- apps/api/app/services/planner_service.py (created — plan_from_prompt stub)
- apps/api/app/api/routes/planner.py (created — POST /planner/intake endpoint)
- apps/api/app/api/router.py (updated — registered planner_router)
- apps/api/README.md (updated — endpoint table)

IMPLEMENTATION NOTES:

- Prompt min_length=10 to reject trivially short inputs; max_length=5000 for safety
- Project name defaults to first 80 chars of prompt if not explicitly provided
- Three stub tasks created: analyse (READY), scaffold (BLOCKED), verify (BLOCKED)
- Dependencies wired: scaffold depends_on → [analyse.id], verify depends_on → [scaffold.id]
- All objects created in a single transaction (auto-committed by get_db dependency)
- Service function returns (project, run, tasks) tuple — clean separation from HTTP layer
- Response includes project_id, run_id, tasks_created count, and created_at timestamp

ASSUMPTIONS:

- Stub tasks are placeholder — real decomposition will come from LLM integration (FM-020+)
- Single run per prompt intake for now; re-run capability comes later
- No validation that the prompt is "meaningful" — just length checks

BLOCKERS:

- None

NEXT RECOMMENDED STEP:

- FM-010: Task DAG + orchestration
