# FM-114 — Project Template Model and Seeding

## Goal

Create a reusable project template system with built-in templates containing real configuration content.

## What Was Implemented

- `ProjectTemplate` ORM model with JSON config blob (constitution, governance, phase_profiles, spec_defaults, plan_defaults)
- 4 built-in templates: `rest-api`, `frontend-app`, `data-pipeline`, `cli-tool`
- Each template includes real constitution text, actual governance config, meaningful spec/plan defaults
- Idempotent `seed_default_templates()` — safe to run on every startup
- CRUD service with list, get, create, update
- REST routes at `/api/templates`

## Files

- `apps/api/app/models/project_template.py`
- `apps/api/app/services/project_template_service.py`
- `apps/api/app/schemas/project_template.py`
- `apps/api/app/routes/template_routes.py`

## Status

✅ Complete. See also [FM-111-120-response.md](FM-111-120-response.md) for full milestone context.
