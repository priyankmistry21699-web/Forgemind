# FM-102 — Project Constitution Model

## Summary

Introduced the `ProjectConstitution` ORM model — a persistent AI behavior rulebook per project containing preamble, constraints, goals, and anti-goals. Includes full CRUD service, Pydantic schemas, and REST API routes. Constitution content is injected into SPEC generation, PLAN generation, and chat prompts.

## Deliverables

- `ProjectConstitution` SQLAlchemy model with `project_id` FK, `preamble`, `constraints`, `goals`, `anti_goals` fields
- `ConstitutionCreate`, `ConstitutionUpdate`, `ConstitutionOut` Pydantic schemas
- `constitution_service.py` — `get_constitution`, `upsert_constitution`, `delete_constitution`, `build_constitution_prompt_section`
- REST routes: `GET/PUT/DELETE /api/projects/{id}/constitution`
- Prompt injection into spec and plan generation pipelines

## Known Gaps

- Constitution not injected into legacy `plan_from_prompt` (creates new projects, no constitution exists yet)

## Test Results

- Covered by `TestFM102_Constitution` (7 tests)
