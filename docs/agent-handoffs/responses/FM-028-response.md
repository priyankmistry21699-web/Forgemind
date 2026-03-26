# FM-028 — Frontend Execution Run View — Response

**Status:** DONE
**Date:** 2025-07-15

---

## Files Created

| File                                                      | Purpose                                                           |
| --------------------------------------------------------- | ----------------------------------------------------------------- |
| `apps/web/types/artifact.ts`                              | Artifact, ArtifactType, ArtifactList type definitions             |
| `apps/web/types/approval.ts`                              | Approval, ApprovalStatus, ApprovalList type definitions           |
| `apps/web/types/execution-event.ts`                       | ExecutionEvent, EventType, ExecutionEventList type definitions    |
| `apps/web/lib/artifacts.ts`                               | fetchArtifacts(projectId, runId?) API helper                      |
| `apps/web/lib/approvals.ts`                               | fetchApprovals(opts?), decideApproval(id, decision) API helpers   |
| `apps/web/lib/events.ts`                                  | fetchEvents(opts?) API helper                                     |
| `apps/web/lib/runs.ts`                                    | fetchRun(runId), fetchRunsByProject(projectId) API helpers        |
| `apps/web/components/artifacts/artifact-list-section.tsx` | Artifact list with type badges, version, creator, content preview |
| `apps/web/components/approvals/approval-list-section.tsx` | Read-only approval display with status badges                     |
| `apps/web/components/events/event-timeline-section.tsx`   | Vertical timeline with emoji icons per event type                 |
| `apps/web/app/dashboard/runs/[runId]/page.tsx`            | Full run detail page                                              |

## Files Modified

| File                                                   | Change                                             |
| ------------------------------------------------------ | -------------------------------------------------- |
| `apps/api/app/api/routes/runs.py`                      | Added GET /runs/{run_id} endpoint                  |
| `apps/web/types/task.ts`                               | Added assigned_agent_slug and error_message fields |
| `apps/web/app/dashboard/projects/[projectId]/page.tsx` | Linked run number to run detail page               |

## Run Detail Page Sections

1. **Breadcrumb** — Dashboard / Project Name / Run #N
2. **Run header** — Title, trigger, created date, status badge
3. **Summary cards** — Status, Artifacts count, Approvals (pending highlighted), Events count
4. **Tasks** — Reuses RunTaskList component
5. **Artifacts** — Type badges, version, creator, truncated content preview
6. **Approvals** — Status badges with pending items highlighted in amber
7. **Event Timeline** — Vertical timeline with emoji icons, agent badges, timestamps

## Design Decisions

1. **Two-phase data loading** — Fetch run first to get project_id, then parallel-fetch project, artifacts, approvals, events.
2. **Reused RunTaskList** — Existing task list component reused in run detail context.
3. **Content preview truncation** — Artifact content truncated at 2000 chars with "truncated" indicator.
4. **Empty state per section** — Each section shows a meaningful empty state when no items exist.

## Acceptance Criteria Met

- [x] Run detail page at /dashboard/runs/[runId]
- [x] Breadcrumb navigation: Dashboard → Project → Run
- [x] Summary cards showing key metrics
- [x] Task list, artifact list, approval list, event timeline sections
- [x] Loading skeleton and error states
- [x] Run linked from project detail page
