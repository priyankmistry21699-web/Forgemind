# FM-116 — Template Inheritance for Constitution & Policies

## Goal

Implement 3-tier governance resolution: system defaults → template → project overrides.

## What Was Implemented

- `template_inheritance_service.py` with `resolve_governance_config()` — merges governance from system defaults, template config (if project has template), and project-level overrides
- Constitution resolution: project constitution takes priority, falls back to template constitution, then system default
- Governance fields (approval thresholds, retry limits, escalation rules) merge at each tier
- Template application helper for bulk-applying template to existing projects

## Files

- `apps/api/app/services/template_inheritance_service.py`

## Status

✅ Complete. See also [FM-111-120-response.md](FM-111-120-response.md) for full milestone context.
