# FM-030 — End-to-End Execution UX Polish — Response

**Status:** DONE
**Date:** 2025-07-15

---

## Files Modified

| File                                     | Change                                                                         |
| ---------------------------------------- | ------------------------------------------------------------------------------ |
| `apps/web/app/dashboard/page.tsx`        | Added pending approvals to stats row, "View Approvals" quick action with badge |
| `apps/web/components/layout/sidebar.tsx` | Added usePathname-based active state highlighting, bumped version to v0.2.0    |

## Dashboard Polish

- **Stats row** — Replaced "Connectors" stat with "Pending Approvals" showing live count and "Needs attention" / "All clear" note
- **Quick Actions** — Added "View Approvals" link with pending count badge (amber), removed disabled "Add Connector" button
- **Data loading** — Dashboard now fetches pending approvals alongside projects using Promise.all

## Sidebar Polish

- **Active state** — Uses `usePathname()` to highlight the current nav item with distinct background and font weight
- **Smart matching** — Dashboard matched exactly, sub-paths (e.g., /dashboard/approvals) matched via startsWith
- **Version bump** — Footer updated from v0.1.0 to v0.2.0

## Navigation Flow (End-to-End)

1. **Dashboard** → See project count, pending approvals, quick actions
2. **Dashboard → Project** → See project details, latest run link
3. **Project → Run Detail** → See tasks, artifacts, approvals, event timeline
4. **Sidebar → Approvals** → Filter and decide pending approvals
5. **Approval decided** → Event logged, list refreshed

## Design Decisions

1. **Minimal, targeted changes** — Only polished navigation and stats; no unnecessary rewrites.
2. **Promise.all for parallel fetch** — Dashboard loads projects and approvals concurrently.
3. **Active nav via pathname** — Simple usePathname approach, no context provider needed.

## Acceptance Criteria Met

- [x] Dashboard reflects pending approval state
- [x] Navigation across projects, runs, approvals is coherent
- [x] Sidebar highlights current page
- [x] Quick actions provide direct paths to key surfaces
- [x] Version bumped to v0.2.0
