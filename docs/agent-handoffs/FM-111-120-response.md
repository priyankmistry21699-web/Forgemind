# FM-111 through FM-120 — Phase Routing, Templates & Project Bootstrapping

## Goal

Implement ForgeMind's Phase Routing, Templates, and Project Bootstrapping block — enabling phase-aware agent assignment, reusable project templates with real config, template-based project creation, governance inheritance, knowledge-driven constitution suggestions, and template influence on SPEC/PLAN generation.

## What Was Implemented

### FM-111 — Phase Agent Profile Data Model

- `PhaseAgentProfile` ORM model with `WorkflowPhase` enum (specify, plan, tasks, implement, review, validate)
- `UniqueConstraint(project_id, phase)` ensures one agent per phase per project
- Full CRUD service: `upsert_profile`, `list_profiles`, `get_agent_slug_for_phase`, `delete_profile`, `bulk_set_profiles`
- Validates agent exists and is active before assignment

### FM-112 — Composition Engine Phase-Aware Routing

- Added `resolve_agent_for_phase()` to `composition_service.py`
- Priority: phase profile lookup → capability-based fallback
- Returns `(slug, source)` tuple for observable routing decisions
- Logs all routing decisions

### FM-113 — Phase Agent Profile UI

- `phase-profile-editor.tsx` component with per-phase agent dropdowns
- "Auto (capability-based)" default option
- Real-time save on change, mounted on project detail page
- `lib/phase-profiles.ts` API client

### FM-114 — Project Template Model and Seeding

- `ProjectTemplate` ORM model with JSON config fields: `constitution_template`, `default_governance_config`, `default_phase_profiles`, `suggested_task_types`, `spec_defaults`, `plan_defaults`
- 4 built-in templates with real content:
  - **rest-api** (backend) — 5-principle constitution, 6 required spec sections, 5 plan workstreams
  - **frontend-app** (frontend) — accessibility-focused constitution
  - **data-pipeline** (data) — idempotency-focused, pipeline-specific spec sections
  - **cli-tool** (tooling) — CLI-specific constitution, minimal phase profiles
- Idempotent `seed_builtin_templates()` added to app startup

### FM-115 — Template-Based Project Creation Flow

- `project_service.create_project()` accepts optional `template_id`
- Template application handled by `template_inheritance_service.apply_template_to_project()`
- Project create form updated with template selector dropdown
- `lib/templates.ts` API client for frontend

### FM-116 — Template Inheritance for Constitution & Policies

- `template_inheritance_service.py` with three-tier resolution: system → template → project override
- `SYSTEM_DEFAULTS` governance config as base layer
- `resolve_governance_config()` merges all layers
- `apply_template_to_project()` seeds constitution and phase profiles from template

### FM-117 — Knowledge-Driven Constitution Suggestions

- `ConstitutionSuggestion` ORM model with `SuggestionStatus` enum (pending, accepted, rejected, expired)
- 5 built-in suggestion rules: missing-tests, review-gaps, error-handling, architecture-review, smaller-phases
- `generate_suggestions()` analyzes project history signals, deduplicates by title
- `resolve_suggestion()` — accept appends to constitution, reject marks rejected. Never auto-mutates.
- `constitution-suggestions.tsx` frontend component with Generate/Accept/Reject UI

### FM-118 — Spec/Plan Bootstrap from Project Templates

- `spec_service.py` includes template `spec_defaults` (required_sections, constraints) in LLM prompt
- `plan_artifact_service.py` includes template `plan_defaults` (workstreams, architecture_checklist) in prompt
- Both use lazy loading via `_get_template_spec_context()` / `_get_template_plan_context()` helpers

### FM-119 — Local Mode Support for Templates & Phase Profiles

- `LocalConfig` dataclass extended with `template_slug` (str) and `phase_profiles` (dict[str, str])
- Full round-trip serialization/deserialization via YAML config

### FM-120 — Tests & Hardening

- 38 new tests in `test_fm111_120_phase_routing.py`
- Alembic migration `0023` for 3 new tables + projects.template_id
- All 580 tests passing (542 prior + 38 new)

## Test Coverage

| Test Class                          | Count | Feature Covered                     |
| ----------------------------------- | ----- | ----------------------------------- |
| TestPhaseAgentProfileService        | 7     | Phase profile CRUD                  |
| TestResolveAgentForPhase            | 2     | Phase routing & fallback            |
| TestProjectTemplateService          | 5     | Template CRUD & seeding             |
| TestTemplateProjectCreation         | 2     | Template-based project creation     |
| TestTemplateInheritance             | 3     | Governance inheritance resolution   |
| TestConstitutionSuggestions         | 5     | Suggestion CRUD & resolution        |
| TestTemplateSpecPlanInfluence       | 4     | Template context in spec/plan       |
| TestLocalModeConfig                 | 3     | Local config template fields        |
| TestPhaseProfileEndpoints           | 2     | HTTP endpoint smoke tests           |
| TestTemplateEndpoints               | 3     | Template API endpoints              |
| TestConstitutionSuggestionEndpoints | 2     | Suggestion API endpoints            |

## Files Created / Modified

### New Files (Backend)

| File                                            | Purpose                         |
| ----------------------------------------------- | ------------------------------- |
| `models/phase_agent_profile.py`                 | PhaseAgentProfile ORM model     |
| `models/project_template.py`                    | ProjectTemplate ORM model       |
| `models/constitution_suggestion.py`             | ConstitutionSuggestion model    |
| `schemas/phase_agent_profile.py`                | Pydantic schemas                |
| `schemas/project_template.py`                   | Pydantic schemas                |
| `schemas/constitution_suggestion.py`            | Pydantic schemas                |
| `services/phase_agent_profile_service.py`       | Phase profile CRUD service      |
| `services/project_template_service.py`          | Template management + seeding   |
| `services/template_inheritance_service.py`      | 3-tier inheritance resolution   |
| `services/constitution_suggestion_service.py`   | Suggestion generation/resolve   |
| `routes/phase_agent_profiles.py`                | Phase profile REST endpoints    |
| `routes/project_templates.py`                   | Template REST endpoints         |
| `routes/constitution_suggestions.py`            | Suggestion REST endpoints       |
| `alembic/versions/0023_*.py`                    | Migration for new tables        |
| `tests/test_fm111_120_phase_routing.py`         | 38 comprehensive tests          |

### New Files (Frontend)

| File                                            | Purpose                         |
| ----------------------------------------------- | ------------------------------- |
| `packages/schemas/src/phase-agent-profile.ts`   | TypeScript types                |
| `packages/schemas/src/project-template.ts`      | TypeScript types                |
| `packages/schemas/src/constitution-suggestion.ts`| TypeScript types                |
| `apps/web/lib/phase-profiles.ts`                | API client                      |
| `apps/web/lib/templates.ts`                     | API client                      |
| `apps/web/lib/constitution-suggestions.ts`      | API client                      |
| `components/projects/phase-profile-editor.tsx`  | Phase routing UI                |
| `components/projects/constitution-suggestions.tsx`| Suggestion management UI      |

### Modified Files

| File                          | Change                                    |
| ----------------------------- | ----------------------------------------- |
| `models/project.py`          | Added template_id FK, phase_profiles rel  |
| `db/base.py`                 | Registered 3 new models                   |
| `schemas/project.py`         | Added template_id to Create/Read          |
| `services/project_service.py`| Template-based creation                   |
| `services/composition_service.py`| resolve_agent_for_phase()            |
| `services/spec_service.py`   | Template spec context in prompt           |
| `services/plan_artifact_service.py`| Template plan context in prompt     |
| `api/router.py`              | Registered 3 new routers                  |
| `main.py`                    | Template seeding in lifespan              |
| `project.ts` (schemas)       | Added template_id field                   |
| `index.ts` (schemas)         | Registered 3 new type modules             |
| `projects.ts` (lib)          | template_id in createProject              |
| `project-create-form.tsx`    | Template selector dropdown                |
| `project detail page.tsx`    | Mounted phase editor + suggestions        |
| `config.py` (local)          | template_slug + phase_profiles fields     |

## Architecture Decisions

- **Phase profiles use agent_id FK** (not slug) for referential integrity, but `get_agent_slug_for_phase` resolves to slug for compatibility with `task.assigned_agent_slug`
- **Templates use JSON config fields** for flexibility — avoids separate config tables
- **Built-in templates carry real, useful config** — constitutions with actual engineering principles, not empty text
- **Suggestions never auto-mutate** — always require explicit accept/reject
- **Three-tier inheritance**: system defaults → template → project override
- **Lazy template context loading** in spec/plan services — only queries template when project has one
