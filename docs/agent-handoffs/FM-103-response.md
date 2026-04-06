# FM-103 — Constitution UI & Governance Hooks

## Goal

Provide a UI for editing project constitutions and emit governance audit events on mutations.

## What Was Implemented

- `ConstitutionEditor` React component (155 lines) with full CRUD: title input, content textarea, Save + Delete buttons, version badge, error/success toasts
- `apps/web/lib/constitution.ts` — API client with `fetchConstitution`, `saveConstitution`, `deleteConstitution`
- `ConstitutionEditor` mounted on project detail page under "Project Constitution" heading
- `CONSTITUTION_UPDATED` execution events emitted on create, update, and delete in `constitution_service.py`
- TypeScript types via `packages/schemas/src/constitution.ts` and `apps/web/types/constitution.ts`

## Files Changed/Added

- `apps/web/components/projects/constitution-editor.tsx` — editor component (155 lines)
- `apps/web/lib/constitution.ts` — API client (35 lines)
- `apps/web/app/dashboard/projects/[projectId]/page.tsx` — mounted ConstitutionEditor
- `apps/web/types/constitution.ts` — TypeScript type re-exports
- `apps/api/app/services/constitution_service.py` — emits EventType.CONSTITUTION_UPDATED

## Test Coverage

- `TestFM103_GovernanceEvents` — 3 tests (create emits event, update emits event, delete emits event)

## Design Notes

- Governance events use `EventType.CONSTITUTION_UPDATED` with project_id context
- Events include metadata with action type ("created", "updated", "deleted")

## Result

✅ Complete — 3 tests passing
