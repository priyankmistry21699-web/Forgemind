# FM-103 — Constitution UI & Governance Hooks

## Summary

Built the `ConstitutionEditor` React component for editing project constitutions from the project detail page. Includes API client integration, TypeScript type definitions, and governance audit events (CONSTITUTION_UPDATED) emitted on create/update/delete.

## Deliverables

- `apps/web/components/projects/constitution-editor.tsx` — full editor UI with form fields for preamble, constraints, goals, anti-goals
- API client methods for constitution CRUD in `apps/web/lib/api.ts`
- TypeScript types in `packages/schemas/src/` for constitution payloads
- `ConstitutionEditor` mounted on project detail page (`apps/web/app/dashboard/projects/[projectId]/page.tsx`)
- `CONSTITUTION_UPDATED` execution events emitted on mutations

## Known Gaps

- Governance event emission tests added in FM-110 hardening

## Test Results

- Covered by `TestFM103_GovernanceEvents` (added tests for constitution audit events)
