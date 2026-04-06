# FM-117 — Knowledge-Driven Constitution Suggestions

## Goal

Generate advisory constitution improvement proposals based on run/task signals.

## What Was Implemented

- `ConstitutionSuggestion` ORM model with PENDING/ACCEPTED/REJECTED/EXPIRED lifecycle
- 5 signal-driven suggestion rules:
  1. High failure rate → suggest stricter validation requirements
  2. Frequent retries → suggest retry budget limits  
  3. Long execution times → suggest time-boxing policy
  4. Knowledge reuse patterns → suggest knowledge-first approach
  5. Approval bottlenecks → suggest approval threshold adjustments
- `constitution_suggestion_service.py`: generate_suggestions, list_suggestions, resolve_suggestion
- **Never auto-applied** — all suggestions require explicit human acceptance
- REST routes at `/api/projects/{id}/constitution-suggestions`

## Files

- `apps/api/app/models/constitution_suggestion.py`
- `apps/api/app/services/constitution_suggestion_service.py`
- `apps/api/app/schemas/constitution_suggestion.py`
- `apps/api/app/routes/constitution_suggestion_routes.py`

## Status

✅ Complete. See also [FM-111-120-response.md](FM-111-120-response.md) for full milestone context.
