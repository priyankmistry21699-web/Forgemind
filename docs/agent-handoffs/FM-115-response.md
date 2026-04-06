# FM-115 — Template-Based Project Creation Flow

## Goal

Allow project creation to accept a template_id and automatically seed constitution and phase profiles from the template.

## What Was Implemented

- `project_service.create_project()` accepts optional `template_id` parameter
- When template is provided: applies constitution text, seeds phase_profiles from template config
- Frontend template selector component on project creation form
- Template config applied at creation time (not retroactively)

## Files

- `apps/api/app/services/project_service.py`
- `apps/frontend/src/components/TemplateSelector.tsx`
- `apps/frontend/src/pages/CreateProject.tsx`

## Status

✅ Complete. See also [FM-111-120-response.md](FM-111-120-response.md) for full milestone context.
