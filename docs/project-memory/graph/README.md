# ForgeMind · Project-Memory Graph

A **property graph** (Neo4j-style) of the repository, generated directly from the source by [`scripts/generate_project_graph.py`](../../../scripts/generate_project_graph.py).

## What's in here

| File | Format | Use in |
| :-- | :-- | :-- |
| [`forgemind-graph.cypher`](forgemind-graph.cypher) | Neo4j Cypher bulk load | Neo4j Browser / Desktop / `cypher-shell` |
| [`forgemind-graph.graphml`](forgemind-graph.graphml) | GraphML (W3C standard) | yEd · Gephi · Cytoscape · Graphviz preview extensions |
| [`forgemind-graph.json`](forgemind-graph.json) | Plain JSON (nodes + edges) | Cytoscape.js · D3 · custom viewers |

All three are kept in sync by the same generator.

## Schema

### Node labels

| Label | Count | Source |
| :-- | --: | :-- |
| `Route` | 57 | `apps/api/app/api/routes/*.py` |
| `Service` | 122 | `apps/api/app/services/*.py` |
| `Model` | 47 | `apps/api/app/models/*.py` |
| `Schema` | 38 | `apps/api/app/schemas/*.py` |
| `Page` | 29 | `apps/web/app/dashboard/*/` |
| `LibClient` | 37 | `apps/web/lib/*.ts(x)` |

Every node carries `id`, `label`, `path`, `forgemind: true`.

### Relationship types

| Type | From → To | Source signal |
| :-- | :-- | :-- |
| `CALLS` | Route → Service | route imports `app.services.<svc>` |
| `DEPENDS_ON` | Service → Service | service imports another service |
| `PERSISTS` | Service → Model | service imports `app.models.<m>` (also emitted from route when route touches a model directly) |
| `VALIDATES_WITH` | Route → Schema | route imports `app.schemas.<s>` |
| `USES` | Page → LibClient | folder-name / client-name match (best-effort) |
| `HITS` | LibClient → Route | client-name → route-name with alias table |

Edge counts at last generation: **CALLS 52 · DEPENDS_ON 7 · PERSISTS 347 · VALIDATES_WITH 39 · USES 53 · HITS 36** (total **534**).

> The generator surfaces **only import-visible** relationships. Dynamic / DI / facade calls are not captured. Treat this as a *high-confidence subset*, not an exhaustive call graph.

## How to view it

### Option A — Neo4j (recommended for querying)

1. Install **Neo4j Desktop** (https://neo4j.com/download/) → create a local DBMS → "Open with Browser".
2. In Neo4j Browser, paste the entire contents of [`forgemind-graph.cypher`](forgemind-graph.cypher) and run.
3. Explore:
   ```cypher
   MATCH (n) WHERE n.forgemind = true RETURN n LIMIT 300;
   ```

Useful queries:

```cypher
// What does the approvals route touch?
MATCH (r:Route {label:"approvals"})-[e]->(n)
RETURN r, e, n;

// Biggest service hubs (most outgoing dependencies)
MATCH (s:Service)-[r]->()
RETURN s.label AS service, count(r) AS out_degree
ORDER BY out_degree DESC LIMIT 10;

// Full path from a dashboard page to the model that stores its data
MATCH path = (p:Page {label:"approvals"})-[:USES]->(:LibClient)
             -[:HITS]->(:Route)-[:CALLS]->(:Service)-[:PERSISTS]->(:Model)
RETURN path LIMIT 25;

// Orphans (nodes with no edges)
MATCH (n) WHERE n.forgemind = true AND NOT (n)--()
RETURN labels(n)[0] AS kind, n.label;
```

### Option B — yEd (desktop, free)

1. Download yEd Graph Editor (https://www.yworks.com/products/yed).
2. `File → Open` → pick [`forgemind-graph.graphml`](forgemind-graph.graphml).
3. `Tools → Fit Node to Label`, then `Layout → Hierarchical` (or `Organic` / `Circular`).
4. Use `Edit → Properties Mapper` to color-code nodes by the `kind` attribute.

### Option C — Gephi / Cytoscape

Both read GraphML directly. Import → apply a layout (ForceAtlas in Gephi; CoSE in Cytoscape) → partition nodes by the `kind` attribute.

### Option D — VS Code inline

Install the extension **"Graphviz Interactive Preview"** or **"Graph Visualization"** and open the `.graphml` file, or use **"Cytoscape Preview for JSON"** on the `.json`.

### Option E — Web (no install)

Paste the Cypher file into Neo4j's free sandbox at https://sandbox.neo4j.com (or use the Neo4j Aura free tier) and run the same queries.

## Security context — FM-211 (resolved)

FM-211 security audit identified 13 vulnerabilities (VULN-1–13). All have been patched as of the V5 release. The CALLS edge count grew from 37 to **52** reflecting the new `authz_service` imports in the repaired routes (`planner_results`, `retry`, `artifacts`, `platform_ops`).

## Regenerating

Whenever routes/services/models/pages/lib clients change materially:

```bash
python scripts/generate_project_graph.py
```

This overwrites all three files in place. Commit the diff — treat them as derived artifacts, not hand-edited docs.

## Relation to the rest of project-memory

- The **prose adjacency tables** in [BACKEND_GRAPH.md](../BACKEND_GRAPH.md) / [FRONTEND_GRAPH.md](../FRONTEND_GRAPH.md) are hand-curated and include relationships the importer cannot see (DI, facades, scheduler triggers, SSE fan-out).
- This folder is the **machine-verified subset** — when the two disagree, the graph is the ground truth for imports; the prose is the ground truth for intent.
