# FM-071 — Implementation Checklist

> **Title**: Advanced Frontend Parity I — Trust, Replay, Council, Governance  
> **Status**: Not started  
> **Priority**: P0  
> **Dependencies**: None  
> **Reference**: FORGEMIND_ROADMAP_V3.md

---

## Pre-Implementation Audit

### Backend API Verification

These endpoints already exist and are wired in `apps/api/app/api/router.py`:

| Subsystem | Route File | Key Endpoints |
|---|---|---|
| **Trust** | `routes/trust.py` | `GET /trust/scores` → `TrustScoreList`, `GET /trust/runs/{id}/risk-summary` |
| **Replay** | `routes/replay.py` | `GET /runs/{id}/trace` → `ExecutionTrace`, `GET /tasks/{id}/snapshots` → `ReplaySnapshotList`, `GET /replay/snapshots/{id}` |
| **Council** | `routes/council.py` | `GET /council/sessions` → `CouncilSessionList`, `GET /council/sessions/{id}` → `CouncilSessionRead` |
| **Governance** | `routes/governance.py` | `GET /governance/policies` → `GovernancePolicyList`, `GET /governance/policies/{id}` → `GovernancePolicyRead` |

### Existing Backend Files (do NOT recreate)

| Layer | Trust | Replay | Council | Governance |
|---|---|---|---|---|
| Model | `models/trust_score.py` | `models/replay_snapshot.py` | `models/council.py` | `models/governance_policy.py` |
| Service | `services/trust_scoring_service.py` | `services/replay_service.py` | `services/council_service.py` | `services/governance_service.py` |
| Schema | `schemas/trust.py` | `schemas/replay.py` | `schemas/council.py` | `schemas/governance.py` |
| Route | `api/routes/trust.py` | `api/routes/replay.py` | `api/routes/council.py` | `api/routes/governance.py` |

All paths relative to `apps/api/app/`.

---

## File-by-File Implementation Plan

### Step 1: TypeScript Types (4 files)

Match the backend Pydantic schemas exactly. All `uuid.UUID` → `string`, all `datetime` → `string`, all `dict | None` → `Record<string, unknown> | null`.

---

#### 1.1 `apps/web/types/trust.ts`

```ts
export type RiskLevel = "low" | "medium" | "high" | "critical";
export type EntityType = "task" | "artifact" | "run";

export interface TrustScore {
  id: string;
  entity_type: EntityType;
  entity_id: string;
  trust_score: number;
  confidence: number;
  risk_level: RiskLevel;
  factors: Record<string, unknown> | null;
  project_id: string | null;
  run_id: string | null;
  assessed_at: string;
}

export interface TrustScoreList {
  items: TrustScore[];
  total: number;
}

export interface RiskSummary {
  run_id: string;
  overall_risk: RiskLevel;
  total_assessments: number;
  risk_breakdown: Record<string, number>;
  high_risk_tasks: string[];
}
```

---

#### 1.2 `apps/web/types/replay.ts`

```ts
export interface ReplaySnapshot {
  id: string;
  task_id: string;
  run_id: string;
  project_id: string;
  agent_slug: string;
  input_snapshot: Record<string, unknown> | null;
  prompt_snapshot: string | null;
  model_used: string | null;
  temperature: number | null;
  output_snapshot: Record<string, unknown> | null;
  error: string | null;
  tokens_used: number;
  duration_ms: number;
  cost_usd: number;
  replay_hash: string | null;
  is_replay: boolean;
  original_snapshot_id: string | null;
  sequence_number: number;
  created_at: string;
}

export interface ReplaySnapshotList {
  items: ReplaySnapshot[];
  total: number;
}

export interface ExecutionTrace {
  run_id: string;
  total_steps: number;
  snapshots: ReplaySnapshot[];
  total_tokens: number;
  total_cost_usd: number;
  total_duration_ms: number;
}
```

---

#### 1.3 `apps/web/types/council.ts`

```ts
export type CouncilStatus = "convened" | "deliberating" | "decided" | "deadlocked" | "escalated";
export type DecisionMethod = "consensus" | "majority" | "supermajority" | "weighted";
export type VoteDecision = "approve" | "reject" | "abstain" | "modify";

export interface CouncilVote {
  id: string;
  session_id: string;
  agent_slug: string;
  decision: VoteDecision;
  reasoning: string | null;
  confidence: number;
  weight: number;
  suggested_modifications: Record<string, unknown> | null;
  created_at: string;
}

export interface CouncilSession {
  id: string;
  project_id: string;
  run_id: string | null;
  task_id: string | null;
  topic: string;
  description: string | null;
  context: Record<string, unknown> | null;
  status: CouncilStatus;
  decision_method: DecisionMethod;
  final_decision: string | null;
  decision_rationale: string | null;
  decision_metadata: Record<string, unknown> | null;
  convened_at: string;
  decided_at: string | null;
  votes: CouncilVote[];
  created_at: string;
  updated_at: string;
}

export interface CouncilSessionList {
  items: CouncilSession[];
  total: number;
}
```

---

#### 1.4 `apps/web/types/governance.ts`

```ts
export type PolicyTrigger = "task_type" | "cost_threshold" | "artifact_type" | "agent_action" | "custom";
export type PolicyAction = "require_approval" | "auto_approve" | "block" | "notify";

export interface GovernancePolicy {
  id: string;
  name: string;
  description: string | null;
  trigger: PolicyTrigger;
  action: PolicyAction;
  rules: Record<string, unknown> | null;
  project_id: string | null;
  enabled: boolean;
  priority: number;
  created_at: string;
  updated_at: string;
}

export interface GovernancePolicyList {
  items: GovernancePolicy[];
  total: number;
}
```

---

### Step 2: API Client Libraries (4 files)

Follow the pattern established in `apps/web/lib/activity.ts` — import `apiFetch` from `@/lib/api`, import types, export async functions.

---

#### 2.1 `apps/web/lib/trust.ts`

```ts
import { apiFetch } from "@/lib/api";
import type { TrustScoreList, RiskSummary } from "@/types/trust";

export async function fetchTrustScores(
  offset = 0,
  limit = 50,
): Promise<TrustScoreList> {
  return apiFetch<TrustScoreList>(`/trust/scores?offset=${offset}&limit=${limit}`);
}

export async function fetchRunRiskSummary(runId: string): Promise<RiskSummary> {
  return apiFetch<RiskSummary>(`/trust/runs/${runId}/risk-summary`);
}
```

---

#### 2.2 `apps/web/lib/replay.ts`

```ts
import { apiFetch } from "@/lib/api";
import type { ExecutionTrace, ReplaySnapshotList, ReplaySnapshot } from "@/types/replay";

export async function fetchExecutionTrace(runId: string): Promise<ExecutionTrace> {
  return apiFetch<ExecutionTrace>(`/runs/${runId}/trace`);
}

export async function fetchTaskSnapshots(
  taskId: string,
  offset = 0,
  limit = 50,
): Promise<ReplaySnapshotList> {
  return apiFetch<ReplaySnapshotList>(
    `/tasks/${taskId}/snapshots?offset=${offset}&limit=${limit}`,
  );
}

export async function fetchSnapshot(snapshotId: string): Promise<ReplaySnapshot> {
  return apiFetch<ReplaySnapshot>(`/replay/snapshots/${snapshotId}`);
}
```

---

#### 2.3 `apps/web/lib/council.ts`

```ts
import { apiFetch } from "@/lib/api";
import type { CouncilSessionList, CouncilSession } from "@/types/council";

export async function fetchCouncilSessions(
  offset = 0,
  limit = 50,
): Promise<CouncilSessionList> {
  return apiFetch<CouncilSessionList>(`/council/sessions?offset=${offset}&limit=${limit}`);
}

export async function fetchCouncilSession(sessionId: string): Promise<CouncilSession> {
  return apiFetch<CouncilSession>(`/council/sessions/${sessionId}`);
}
```

---

#### 2.4 `apps/web/lib/governance.ts`

```ts
import { apiFetch } from "@/lib/api";
import type { GovernancePolicyList, GovernancePolicy } from "@/types/governance";

export async function fetchGovernancePolicies(
  offset = 0,
  limit = 50,
): Promise<GovernancePolicyList> {
  return apiFetch<GovernancePolicyList>(`/governance/policies?offset=${offset}&limit=${limit}`);
}

export async function fetchGovernancePolicy(policyId: string): Promise<GovernancePolicy> {
  return apiFetch<GovernancePolicy>(`/governance/policies/${policyId}`);
}
```

---

### Step 3: Dashboard Pages (4 files)

Follow the pattern from `apps/web/app/dashboard/activity/page.tsx`:
- `"use client"` directive
- `useCallback` + `useEffect` + `useState` for data loading
- Breadcrumb → Header → Error → Loading → Empty → Data display
- CSS vars: `var(--color-text)`, `var(--color-text-muted)`, `var(--color-text-dim)`, `var(--color-border)`, `var(--color-bg-card)`, `var(--color-bg-secondary)`, `var(--color-accent)`

---

#### 3.1 `apps/web/app/dashboard/trust/page.tsx`

Key elements:
- Page title: "Trust Scores"
- Subtitle: "Risk assessment and trust scoring across platform entities"
- Display: card list of trust scores
- Each card shows: entity type badge, trust score (0–1), confidence (0–1), risk level badge (color-coded: green/yellow/orange/red), factors expandable
- Risk level colors: low → emerald, medium → yellow, high → orange, critical → red
- Empty state: "No trust assessments recorded yet."

---

#### 3.2 `apps/web/app/dashboard/replay/page.tsx`

Key elements:
- Page title: "Execution Replay"
- Input: Run ID text field (similar to escalations pattern with `projectId`)
- When run ID provided: fetch execution trace, display timeline of snapshots
- Each snapshot card: agent slug, model used, tokens, duration, cost, hash
- Sequence number ordering
- Is-replay indicator badge
- Empty state: "Enter a run ID to view execution trace."

---

#### 3.3 `apps/web/app/dashboard/council/page.tsx`

Key elements:
- Page title: "Council Sessions"
- Subtitle: "Multi-agent decision-making history"
- Display: session list cards
- Each card: topic, status badge (convened/deliberating/decided/deadlocked/escalated), decision method, vote count
- Status colors: decided → emerald, deliberating → blue, deadlocked → red, escalated → orange, convened → gray
- Expandable vote breakdown per session
- Empty state: "No council sessions convened yet."

---

#### 3.4 `apps/web/app/dashboard/governance/page.tsx`

Key elements:
- Page title: "Governance Policies"
- Display: policy list cards
- Each card: name, trigger type badge, action type badge, enabled/disabled status, priority number
- Trigger colors: task_type → blue, cost_threshold → orange, artifact_type → purple, agent_action → teal, custom → gray
- Action colors: require_approval → yellow, auto_approve → green, block → red, notify → blue
- Filter by enabled/disabled if feasible
- Empty state: "No governance policies configured yet."

---

### Step 4: Sidebar Update (1 file)

#### Edit `apps/web/components/layout/sidebar.tsx`

**Changes needed:**

1. Add 4 new entries to `NAV_ITEMS` array *after* the Escalations entry and *before* the Agents entry:

```ts
{
  label: "Trust",
  href: "/dashboard/trust",
  icon: /* shield icon SVG */,
},
{
  label: "Replay",
  href: "/dashboard/replay",
  icon: /* play-circle icon SVG */,
},
{
  label: "Council",
  href: "/dashboard/council",
  icon: /* users icon SVG */,
},
{
  label: "Governance",
  href: "/dashboard/governance",
  icon: /* book-open icon SVG */,
},
```

2. The existing Agents, Connectors, and Settings entries remain `disabled: true` — those get enabled in FM-073.

---

### Step 5: Tests

#### 5.1 Backend — Verify API routes return expected shapes

Add or verify in `apps/api/tests/`:
- `test_trust.py` — test `GET /trust/scores` returns `{"items": [...], "total": N}`
- `test_replay.py` — test `GET /runs/{id}/trace` returns `ExecutionTrace` shape
- `test_council.py` — test `GET /council/sessions` returns `CouncilSessionList` shape
- `test_governance.py` — test `GET /governance/policies` returns `GovernancePolicyList` shape

Check if these test files already exist before creating new ones.

#### 5.2 Frontend — Component smoke tests (if test framework exists)

Check if `apps/web` has Jest/Vitest/Playwright configured. If so:
- Test each page renders without crashing
- Test loading/error/empty states
- Test data display with mock API responses

---

## Implementation Order

```
1. types/trust.ts, types/replay.ts, types/council.ts, types/governance.ts     (parallel)
2. lib/trust.ts, lib/replay.ts, lib/council.ts, lib/governance.ts             (parallel)
3. dashboard/trust/page.tsx                                                     (sequential)
4. dashboard/replay/page.tsx                                                    (sequential)
5. dashboard/council/page.tsx                                                   (sequential)
6. dashboard/governance/page.tsx                                                (sequential)
7. sidebar.tsx update                                                           (after pages exist)
8. Backend test verification                                                    (parallel with frontend)
9. Manual smoke test — all 4 pages load from sidebar
```

---

## Completion Checklist

- [ ] `apps/web/types/trust.ts` created
- [ ] `apps/web/types/replay.ts` created
- [ ] `apps/web/types/council.ts` created
- [ ] `apps/web/types/governance.ts` created
- [ ] `apps/web/lib/trust.ts` created
- [ ] `apps/web/lib/replay.ts` created
- [ ] `apps/web/lib/council.ts` created
- [ ] `apps/web/lib/governance.ts` created
- [ ] `apps/web/app/dashboard/trust/page.tsx` created
- [ ] `apps/web/app/dashboard/replay/page.tsx` created
- [ ] `apps/web/app/dashboard/council/page.tsx` created
- [ ] `apps/web/app/dashboard/governance/page.tsx` created
- [ ] `apps/web/components/layout/sidebar.tsx` updated with 4 new nav items
- [ ] All 4 pages accessible from sidebar
- [ ] All 4 pages load backend data successfully
- [ ] Loading/error/empty states work on all pages
- [ ] Backend test coverage verified
- [ ] `FM-071-response.md` written in `docs/agent-handoffs/`

---

## Post-Completion

After FM-071 is done:
1. Mark FM-071 as ✅ in `FORGEMIND_ROADMAP_V3.md` tracker
2. Move FM-071 from Backlog to Done in `TASKS.md`
3. Update `MILESTONE_SUMMARY.md` with Milestone 14
4. Create `docs/agent-handoffs/FM-071-response.md` with implementation evidence
5. Proceed to FM-072 (costs, audit, knowledge, vault — same pattern)
