# FM-035 — End-to-End Operator UX Polish

## Status: DONE

## What was implemented

### Sidebar & Navigation

1. **`apps/web/components/layout/sidebar.tsx`** — Multiple improvements:
   - Fixed Dashboard active-state to highlight for all `/dashboard/*` child routes (projects, runs, artifacts) that don't match a more-specific sidebar item
   - Removed disabled "Projects" item (redundant with Dashboard which shows projects)
   - Bumped version to v0.3.0 (post Milestone 7)
   - Extracted `isItemActive()` helper for cleaner active-state logic

### Dashboard

2. **`apps/web/app/dashboard/page.tsx`** — UX improvements:
   - Made "Pending Approvals" stat card a clickable `<Link>` to /dashboard/approvals with hover accent border and "Needs attention →" text
   - Removed disabled "View Agents" phantom button from Quick Actions
   - Renamed "View Approvals" to "Review Approvals" for clearer operator intent

### Page Consistency

3. **`apps/web/app/dashboard/approvals/page.tsx`** — Added breadcrumb navigation (Dashboard / Approvals) matching the pattern used by project, run, and artifact detail pages

### Cross-Links

4. **`apps/web/app/dashboard/projects/[projectId]/page.tsx`** — Added:
   - Artifact list section (shows latest run's artifacts on project page)
   - Approval list section with pending count badge
   - Fetches artifacts and approvals alongside project and run data

### Section Labels

5. **`apps/web/app/dashboard/runs/[runId]/page.tsx`** — Enhanced section headings:
   - Artifacts heading shows count
   - Approvals heading shows pending badge when there are pending approvals
   - Event Timeline heading shows count

### Documentation

6. Updated `docs/agent-handoffs/TASKS.md` — Added Milestone 7 (FM-031-035) to Done, Milestone 8 backlog
7. Updated `docs/MILESTONE_SUMMARY.md` — Added Milestone 7 section, updated capabilities, task count (37), version
8. Updated `docs/TECHNICAL_DEBT.md` — Added TD-016, TD-017, TD-018
9. Created FM-031 through FM-035 response docs
