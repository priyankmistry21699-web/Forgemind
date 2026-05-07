# ForgeMind — Project Memory

> A graph-oriented knowledge base for agents and new contributors. Each file focuses on **relationships**, not prose: who calls what, who owns what, where to change what.

Read these in order on your first pass:

| # | File | What it answers |
| :-- | :-- | :-- |
| 1 | [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md) | What ForgeMind is · product goals · subsystems · status at HEAD |
| 2 | [REPO_MAP.md](REPO_MAP.md) | Top-level layout · entry points · where things live |
| 3 | [BACKEND_GRAPH.md](BACKEND_GRAPH.md) | 53 routers → 109 services → 42 models · core infra · cross-service edges |
| 4 | [FRONTEND_GRAPH.md](FRONTEND_GRAPH.md) | 25 dashboard routes · 33 lib clients · components · chart system |
| 5 | [INTEGRATIONS_GRAPH.md](INTEGRATIONS_GRAPH.md) | Slack · email · PagerDuty · GitHub App · webhooks · API keys · SDKs |
| 6 | [REQUEST_FLOWS.md](REQUEST_FLOWS.md) | End-to-end traces for the 7 most important flows |
| 7 | [CHANGE_GUIDE.md](CHANGE_GUIDE.md) | "If you need to change X, start here" recipes |
| 8 | [MILESTONE_TO_CODE_MAP.md](MILESTONE_TO_CODE_MAP.md) | FM-xxx milestones → concrete files |
| 9 | [graph/](graph/) | **Neo4j / yEd / Cytoscape property-graph export** — auto-generated Cypher · GraphML · JSON |

## Conventions used in these docs

- `apps/api/app/...` paths are backend, `apps/web/...` are frontend, `packages/...` are shared.
- **A → B** means "A calls / imports / depends on B".
- **Owned by** = primary module that defines/mutates the entity. **Used by** = consumers.
- Counts reflect HEAD (`main`) at the time of the last memory refresh. If a count feels off, trust the code and refresh.
- These docs are **non-normative** — they describe what the code does, not what it should do. If they contradict code, code wins and the doc should be updated.

## Canonical references outside project-memory

- [`../ARCHITECTURE.md`](../ARCHITECTURE.md) — 13-section system design (the "why")
- [`../REPOSITORY_GUIDE.md`](../REPOSITORY_GUIDE.md) — folder-level navigation
- [`../DEVELOPMENT_WORKFLOW.md`](../DEVELOPMENT_WORKFLOW.md) — how to run / test / migrate
- [`../MILESTONE_SUMMARY.md`](../MILESTONE_SUMMARY.md) — wave-by-wave V4 narrative
- [`../api-ecosystem.md`](../api-ecosystem.md) · [`../analytics-portfolio.md`](../analytics-portfolio.md) · [`../code-intelligence.md`](../code-intelligence.md) — topical deep-dives
