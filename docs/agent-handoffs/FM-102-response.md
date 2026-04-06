# FM-102 — Project Constitution Model

## Goal

Create a persistent AI behavior rulebook per project that is injected into SPEC generation, PLAN generation, and chat prompts.

## What Was Implemented

- `ProjectConstitution` SQLAlchemy model with fields: `id`, `project_id` (unique FK), `title`, `content`, `summary`, `version`, `created_at`, `updated_at`
- `ConstitutionRead`, `ConstitutionCreate`, `ConstitutionUpdate` Pydantic schemas
- `constitution_service.py` — 5 functions: `get_constitution`, `create_or_update_constitution` (version bumping), `delete_constitution`, `build_constitution_prompt_section`, `get_constitution_for_prompt`
- REST routes with RBAC: `GET/PUT/PATCH/DELETE /projects/{project_id}/constitution`
- Constitution content injected into spec_service and plan_artifact_service via `get_constitution_for_prompt()`

## Files Changed/Added

- `apps/api/app/models/project_constitution.py` — ORM model
- `apps/api/app/schemas/constitution.py` — Pydantic schemas (ConstitutionRead, Create, Update)
- `apps/api/app/services/constitution_service.py` — CRUD + prompt injection
- `apps/api/app/api/routes/constitution.py` — 4 REST endpoints with RBAC
- `packages/schemas/src/constitution.ts` — TypeScript `Constitution` interface
- `apps/web/types/constitution.ts` — re-export from @forgemind/types

## Test Coverage

- `TestFM102_Constitution` — 6 tests (create, update w/ version bump, get, delete, prompt generation, null handling)

## Known Gaps

- Constitution not injected into legacy `plan_from_prompt` (creates new projects where no constitution exists yet; injection happens at SPEC/PLAN generation level)

## Result

✅ Complete — 6 tests passing
