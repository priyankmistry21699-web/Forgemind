# FM-138 — Frontend Release Operations Surface

## Goal

UI for browsing releases, evaluating gates, and checking rollback readiness.

## What Was Implemented

- TypeScript type definitions for all release domain objects (`types/release-ops.ts`)
- API client functions for all release operations (`lib/release-ops.ts`)
- Release dashboard page (`dashboard/releases/page.tsx`) with project filter, release cards, gate evaluation panel, rollback readiness panel
- Sidebar navigation entry with download icon

## Key Files

- `apps/web/types/release-ops.ts`
- `apps/web/lib/release-ops.ts`
- `apps/web/app/dashboard/releases/page.tsx`
- `apps/web/components/layout/sidebar.tsx`

## Status

✅ Complete
