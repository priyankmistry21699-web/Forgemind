# FM-031 — Artifact Detail View & Navigation

## Status: DONE

## What was implemented

1. **`apps/web/lib/artifacts.ts`** — Added `fetchArtifact(artifactId)` function calling `GET /artifacts/{artifactId}`
2. **`apps/web/app/dashboard/artifacts/[artifactId]/page.tsx`** — New artifact detail page with:
   - Breadcrumb navigation (Dashboard / Project / Run / Artifact)
   - Header with title + artifact type badge (color-coded by type)
   - 4 metadata cards (Type, Version, Created By, Last Updated)
   - Context links to parent project, run, and task
   - Metadata JSON display (if present)
   - Full content rendering in pre-formatted block
   - Loading skeleton and error states
3. **`apps/web/components/artifacts/artifact-list-section.tsx`** — Made artifact titles clickable links to the detail page

## Key decisions

- Artifact types have distinct color badges (plan_summary=purple, architecture=cyan, implementation=blue, etc.)
- Detail page fetches parent project and run in parallel for breadcrumb display
- Content is rendered in a `<pre>` block with horizontal scrolling for code artifacts
