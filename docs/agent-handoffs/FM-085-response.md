# FM-085 — Architecture Dashboard Frontend

## Summary

Created the architecture intelligence dashboard page, API client library, TypeScript type definitions, and sidebar navigation integration. The dashboard displays graph statistics, drift summary, rule results, refactor recommendations, and a structural health score.

## Deliverables

### Dashboard Page (`apps/web/app/dashboard/architecture/page.tsx`)

- Full dashboard with graph stats (node/edge counts), drift summary (by severity), rule evaluation results, refactor recommendations list, and structural health score display
- Stat cards for key metrics, severity badges for drifts and violations
- Health score donut/display with letter grade
- Uses `?project=<id>` query parameter for project scoping
- Loading, error, and empty states handled

### API Client (`apps/web/lib/architecture.ts`)

12 functions:

- `fetchArchitectureGraph` — GET full graph
- `fetchArchitectureNodes` — GET node list
- `fetchArchitectureEdges` — GET edge list
- `fetchArchitectureSnapshots` — GET snapshots
- `mapTopology` — POST topology scan
- `detectDrift` — POST drift detection
- `fetchDrifts` — GET drift list
- `fetchArchitectureRules` — GET rules
- `fetchRuleResults` — GET results
- `generateDesignDoc` — POST design doc
- `analyseImpact` — POST impact analysis
- `fetchRecommendations` — GET recommendations
- `fetchHealthScore` — GET health score

### TypeScript Types (`packages/schemas/src/architecture.ts`)

19 interfaces + 8 type unions:

- ArchitectureNode, ArchitectureNodeList, ArchitectureEdge, ArchitectureEdgeList, ArchitectureGraph, ArchitectureSnapshot, ArchitectureSnapshotList
- TopologySummary, ArchitectureDrift, ArchitectureDriftList
- ArchitectureRule, ArchitectureRuleList, ArchitectureRuleResult, ArchitectureRuleResultList
- DesignDoc, ChangeImpactAssessment, RefactorRecommendation, RefactorRecommendationList
- HealthScoreDetails, StructuralHealthScore

### Type Re-exports (`apps/web/types/architecture.ts`)

- Re-exports from `@forgemind/types` package

### Sidebar Navigation

- "Architecture" link added to sidebar component pointing to `/dashboard/architecture`

## Tests

7 tests covering RBAC on architecture routes:

- `TestArchitectureRBAC` (7 tests) — node create, drift detect, rule create, impact analysis, view graph, snapshot create, viewer cannot manage

## Test Results

- **Total**: 482 passing
- **Regression**: None
