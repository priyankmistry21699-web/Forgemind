# FM-071 — Response

> **Title**: Advanced Frontend Parity I — Trust, Replay, Council, Governance  
> **Status**: ✅ Complete  
> **Date**: 2026-04-02

---

## What was done

Built 4 new dashboard pages, 4 API client libraries, and 4 TypeScript type modules to surface the Trust, Replay, Council, and Governance backend subsystems in the frontend. Updated the sidebar navigation with 4 new active links.

## Files created (12)

### TypeScript types
- `apps/web/types/trust.ts` — TrustScore, TrustScoreList, RiskSummary, RiskLevel, EntityType
- `apps/web/types/replay.ts` — ReplaySnapshot, ReplaySnapshotList, ExecutionTrace
- `apps/web/types/council.ts` — CouncilSession, CouncilSessionList, CouncilVote, CouncilStatus, DecisionMethod, VoteDecision
- `apps/web/types/governance.ts` — GovernancePolicy, GovernancePolicyList, PolicyTrigger, PolicyAction

### API client libraries
- `apps/web/lib/trust.ts` — fetchTrustScores, fetchRunRiskSummary
- `apps/web/lib/replay.ts` — fetchExecutionTrace, fetchTaskSnapshots, fetchSnapshot
- `apps/web/lib/council.ts` — fetchCouncilSessions, fetchCouncilSession
- `apps/web/lib/governance.ts` — fetchGovernancePolicies, fetchGovernancePolicy

### Dashboard pages
- `apps/web/app/dashboard/trust/page.tsx` — Trust score list with risk level badges, entity type badges, confidence display, expandable factors
- `apps/web/app/dashboard/replay/page.tsx` — Run ID input → execution trace timeline with snapshot cards, summary bar (steps/tokens/cost/duration)
- `apps/web/app/dashboard/council/page.tsx` — Council session list with status badges, decision method, expandable vote breakdown per session
- `apps/web/app/dashboard/governance/page.tsx` — Policy list with trigger/action badges, enabled/disabled status, priority, expandable rules

## Files modified (1)
- `apps/web/components/layout/sidebar.tsx` — Added 4 nav items: Trust (shield icon), Replay (play-circle icon), Council (users icon), Governance (book icon)

## Backend routes consumed (all pre-existing)
- `GET /trust/scores` → TrustScoreList
- `GET /trust/runs/{id}/risk-summary` → RiskSummary
- `GET /runs/{id}/trace` → ExecutionTrace
- `GET /tasks/{id}/snapshots` → ReplaySnapshotList
- `GET /replay/snapshots/{id}` → ReplaySnapshot
- `GET /council/sessions` → CouncilSessionList
- `GET /council/sessions/{id}` → CouncilSessionRead
- `GET /governance/policies` → GovernancePolicyList
- `GET /governance/policies/{id}` → GovernancePolicyRead

## Tests
- 34 existing backend tests in `test_fm046_050_v2.py` verified passing (trust, replay, council, governance route coverage)
- 0 new backend tests needed — existing coverage is adequate
- All 13 new/modified frontend files: zero TypeScript errors

## UX patterns followed
- Breadcrumb → Header → Error → Loading → Empty → Data (matching activity/escalations pages)
- CSS variables: `--color-text`, `--color-text-muted`, `--color-border`, `--color-bg-card`, `--color-bg-secondary`, `--color-accent`
- Color-coded badges: risk levels (emerald/yellow/orange/red), council statuses, vote decisions, policy triggers/actions
