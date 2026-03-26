# FM-029 — Frontend Approval Inbox & Decision Flow — Response

**Status:** DONE
**Date:** 2025-07-15

---

## Files Created

| File                                              | Purpose                                               |
| ------------------------------------------------- | ----------------------------------------------------- |
| `apps/web/components/approvals/approval-card.tsx` | Interactive approval card with approve/reject actions |
| `apps/web/app/dashboard/approvals/page.tsx`       | Approval inbox page with filter tabs                  |

## Files Modified

| File                                     | Change                            |
| ---------------------------------------- | --------------------------------- |
| `apps/web/components/layout/sidebar.tsx` | Added "Approvals" navigation item |

## Approval Card Features

- Status badge (pending=amber, approved=green, rejected=red)
- Title, description, creation timestamp
- **For pending approvals:**
  - Comment textarea for decision rationale
  - Approve button (green) and Reject button (red)
  - Loading state during API call
  - Error display on failure
- **For resolved approvals:**
  - Decision details: who decided, when, and comment

## Approval Inbox Features

- Page header with pending count badge
- Filter tabs: All, Pending, Resolved
- Loading skeleton state (3 placeholder cards)
- Error state with message
- Empty states customized per active filter
- `onDecided` callback refreshes the list after any decision

## Design Decisions

1. **Filter tabs** — All/Pending/Resolved as client-side tabs with API-level filtering via status query param.
2. **Inline decision flow** — Approve/reject directly on the card, no modal or separate page.
3. **Immediate refresh** — After any decision, full approval list re-fetched to update counts and filter results.
4. **Comment optional** — Textarea provided but not required for decisions.

## Acceptance Criteria Met

- [x] Approval inbox page at /dashboard/approvals
- [x] Filter tabs for all/pending/resolved
- [x] Approve and reject actions with comment field
- [x] Loading, error, and empty states
- [x] Sidebar navigation link to approvals
- [x] List refreshes after decision
