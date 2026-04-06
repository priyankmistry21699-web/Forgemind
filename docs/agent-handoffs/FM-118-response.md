# FM-118 — Spec/Plan Bootstrap from Project Templates

## Goal

Inject template spec_defaults and plan_defaults into LLM prompt generation for SPEC and PLAN artifacts.

## What Was Implemented

- `spec_service.py` enhanced: when project has a template with `spec_defaults`, those are injected as a guidance section in the LLM prompt
- `plan_artifact_service.py` enhanced: when project has a template with `plan_defaults`, those are injected as a guidance section in the LLM prompt
- Template influence is advisory — LLM uses the defaults as starting context, not rigid overrides
- Prompt injection is safe — template content is clearly delimited and sandboxed

## Files

- `apps/api/app/services/spec_service.py`
- `apps/api/app/services/plan_artifact_service.py`

## Status

✅ Complete. See also [FM-111-120-response.md](FM-111-120-response.md) for full milestone context.
