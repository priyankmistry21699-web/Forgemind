"""Generate the ForgeMind project-memory graph.

Scans the repository for routes, services, models, dashboard pages, and lib
clients, parses their imports, and emits node/edge artifacts in three formats
so the graph can be loaded into Neo4j, yEd, Gephi, Cytoscape, or a custom D3
viewer.

Outputs (under docs/project-memory/graph/):
    forgemind-graph.cypher    Neo4j-loadable script (CREATE / MERGE)
    forgemind-graph.graphml   GraphML for yEd / Gephi / Cytoscape / Graphviz
    forgemind-graph.json      Plain JSON (nodes + edges)

Node types:
    Route, Service, Model, Schema, Page, LibClient

Edge types:
    CALLS           Route    -> Service           (route imports service)
    DEPENDS_ON      Service  -> Service           (service imports service)
    PERSISTS        Service  -> Model             (service imports model)
    VALIDATES_WITH  Route    -> Schema            (route imports schema)
    HITS            LibClient -> Route            (name-prefix match)
    USES            Page     -> LibClient         (filename match)

Re-run whenever the repo changes substantially::

    python scripts/generate_project_graph.py
"""

from __future__ import annotations

import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ROUTES_DIR = REPO / "apps" / "api" / "app" / "api" / "routes"
SERVICES_DIR = REPO / "apps" / "api" / "app" / "services"
MODELS_DIR = REPO / "apps" / "api" / "app" / "models"
SCHEMAS_DIR = REPO / "apps" / "api" / "app" / "schemas"
DASHBOARD_DIR = REPO / "apps" / "web" / "app" / "dashboard"
LIB_DIR = REPO / "apps" / "web" / "lib"

OUT_DIR = REPO / "docs" / "project-memory" / "graph"
OUT_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class Node:
    id: str
    label: str
    kind: str
    path: str


@dataclass
class Edge:
    source: str
    target: str
    kind: str


@dataclass
class Graph:
    nodes: dict[str, Node] = field(default_factory=dict)
    edges: list[Edge] = field(default_factory=list)

    def add_node(self, node: Node) -> None:
        self.nodes.setdefault(node.id, node)

    def add_edge(self, source: str, target: str, kind: str) -> None:
        if source in self.nodes and target in self.nodes and source != target:
            self.edges.append(Edge(source, target, kind))


def _python_files(directory: Path) -> list[Path]:
    if not directory.exists():
        return []
    return sorted(p for p in directory.iterdir() if p.is_file() and p.suffix == ".py" and p.stem != "__init__")


def _rel(path: Path) -> str:
    return path.relative_to(REPO).as_posix()


IMPORT_RE = re.compile(
    r"^\s*from\s+app\.(services|models|schemas)\.(\w+)\s+import",
    re.MULTILINE,
)


def _imports(py_file: Path, kind: str) -> set[str]:
    """Return the set of sibling module names imported from app.<kind>.*"""
    try:
        text = py_file.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return set()
    return {m.group(2) for m in IMPORT_RE.finditer(text) if m.group(1) == kind}


def build_backend(graph: Graph) -> None:
    # Nodes -----------------------------------------------------------------
    for f in _python_files(ROUTES_DIR):
        graph.add_node(Node(id=f"route:{f.stem}", label=f.stem, kind="Route", path=_rel(f)))
    for f in _python_files(SERVICES_DIR):
        graph.add_node(Node(id=f"service:{f.stem}", label=f.stem, kind="Service", path=_rel(f)))
    for f in _python_files(MODELS_DIR):
        graph.add_node(Node(id=f"model:{f.stem}", label=f.stem, kind="Model", path=_rel(f)))
    for f in _python_files(SCHEMAS_DIR):
        graph.add_node(Node(id=f"schema:{f.stem}", label=f.stem, kind="Schema", path=_rel(f)))

    # Edges -----------------------------------------------------------------
    for route in _python_files(ROUTES_DIR):
        src_id = f"route:{route.stem}"
        for svc in _imports(route, "services"):
            graph.add_edge(src_id, f"service:{svc}", "CALLS")
        for sch in _imports(route, "schemas"):
            graph.add_edge(src_id, f"schema:{sch}", "VALIDATES_WITH")
        for mdl in _imports(route, "models"):
            graph.add_edge(src_id, f"model:{mdl}", "PERSISTS")  # rare but record it

    for svc_file in _python_files(SERVICES_DIR):
        src_id = f"service:{svc_file.stem}"
        for other in _imports(svc_file, "services"):
            graph.add_edge(src_id, f"service:{other}", "DEPENDS_ON")
        for mdl in _imports(svc_file, "models"):
            graph.add_edge(src_id, f"model:{mdl}", "PERSISTS")


LIB_NAME_ALIASES = {
    # frontend lib module stem  ->  backend route module stem(s)
    "constitution-suggestions": ["constitution_suggestions"],
    "project-members": ["members"],
    "release-ops": ["release_ops"],
    "phase-profiles": ["phase_agent_profiles"],
    "stream": ["streaming"],
    "events": ["events"],
    "dashboards": ["analytics"],
    "knowledge": ["knowledge", "search_knowledge"],
    "planner": ["planner", "planner_results"],
    "governance": ["governance", "enterprise_governance"],
    "projects": ["projects", "project_templates"],
    "templates": ["project_templates"],
    "runs": ["runs", "run_lifecycle"],
    "vault": ["credential_vault"],
    "escalations": ["escalation"],
}


def build_frontend(graph: Graph) -> None:
    # Lib clients (typed API clients) --------------------------------------
    if LIB_DIR.exists():
        for f in sorted(LIB_DIR.iterdir()):
            if not f.is_file():
                continue
            if f.suffix not in {".ts", ".tsx"}:
                continue
            if f.stem in {"api", "auth-context"}:
                kind_label = "LibClient"  # treat shared helpers as lib clients too
            else:
                kind_label = "LibClient"
            graph.add_node(
                Node(id=f"lib:{f.stem}", label=f.stem, kind=kind_label, path=_rel(f))
            )

    # Dashboard pages -------------------------------------------------------
    if DASHBOARD_DIR.exists():
        for d in sorted(DASHBOARD_DIR.iterdir()):
            if not d.is_dir() or d.name.startswith("__"):
                continue
            graph.add_node(
                Node(id=f"page:{d.name}", label=d.name, kind="Page", path=_rel(d))
            )

    # Page -> LibClient: match by domain name (best-effort) ----------------
    for page_id, page in [(n.id, n) for n in graph.nodes.values() if n.kind == "Page"]:
        domain = page.label
        candidates = [domain, domain.replace("-", "_"), domain.rstrip("s")]
        for cand in candidates:
            lib_id = f"lib:{cand}"
            if lib_id in graph.nodes:
                graph.add_edge(page_id, lib_id, "USES")

    # LibClient -> Route: alias table + direct match ------------------------
    route_ids = {n.label: n.id for n in graph.nodes.values() if n.kind == "Route"}
    for lib in [n for n in graph.nodes.values() if n.kind == "LibClient"]:
        targets = LIB_NAME_ALIASES.get(lib.label, [lib.label.replace("-", "_")])
        for t in targets:
            if t in route_ids:
                graph.add_edge(lib.id, route_ids[t], "HITS")


# ----------------------------------------------------------------------------
# Emitters
# ----------------------------------------------------------------------------


def emit_json(graph: Graph, path: Path) -> None:
    payload = {
        "nodes": [n.__dict__ for n in graph.nodes.values()],
        "edges": [e.__dict__ for e in graph.edges],
        "counts": {
            "nodes": len(graph.nodes),
            "edges": len(graph.edges),
            "by_kind": _by_kind(graph),
        },
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _by_kind(graph: Graph) -> dict[str, int]:
    counts: dict[str, int] = {}
    for n in graph.nodes.values():
        counts[n.kind] = counts.get(n.kind, 0) + 1
    for e in graph.edges:
        counts[f"edge:{e.kind}"] = counts.get(f"edge:{e.kind}", 0) + 1
    return dict(sorted(counts.items()))


def emit_cypher(graph: Graph, path: Path) -> None:
    lines: list[str] = [
        "// ForgeMind project-memory graph — Neo4j Cypher bulk load.",
        "// Paste into Neo4j Browser (run as one script) or `cypher-shell < forgemind-graph.cypher`.",
        "// Clear previous load (optional):",
        "//   MATCH (n) WHERE n.forgemind = true DETACH DELETE n;",
        "",
    ]
    for n in graph.nodes.values():
        lines.append(
            f"MERGE (:{n.kind} {{id: {json.dumps(n.id)}, label: {json.dumps(n.label)}, "
            f"path: {json.dumps(n.path)}, forgemind: true}});"
        )
    lines.append("")
    for e in graph.edges:
        src = graph.nodes[e.source]
        dst = graph.nodes[e.target]
        lines.append(
            f"MATCH (a:{src.kind} {{id: {json.dumps(src.id)}}}), "
            f"(b:{dst.kind} {{id: {json.dumps(dst.id)}}}) "
            f"MERGE (a)-[:{e.kind}]->(b);"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def emit_graphml(graph: Graph, path: Path) -> None:
    ns = "http://graphml.graphdrawing.org/xmlns"
    ET.register_namespace("", ns)
    root = ET.Element(f"{{{ns}}}graphml")
    # key definitions
    for key_id, name, for_ in (
        ("k_kind", "kind", "node"),
        ("k_label", "label", "node"),
        ("k_path", "path", "node"),
        ("e_kind", "kind", "edge"),
    ):
        k = ET.SubElement(root, f"{{{ns}}}key")
        k.set("id", key_id)
        k.set("for", for_)
        k.set("attr.name", name)
        k.set("attr.type", "string")
    g = ET.SubElement(root, f"{{{ns}}}graph")
    g.set("id", "ForgeMind")
    g.set("edgedefault", "directed")
    for n in graph.nodes.values():
        node = ET.SubElement(g, f"{{{ns}}}node")
        node.set("id", n.id)
        for key_id, value in (("k_kind", n.kind), ("k_label", n.label), ("k_path", n.path)):
            d = ET.SubElement(node, f"{{{ns}}}data")
            d.set("key", key_id)
            d.text = value
    for i, e in enumerate(graph.edges):
        edge = ET.SubElement(g, f"{{{ns}}}edge")
        edge.set("id", f"e{i}")
        edge.set("source", e.source)
        edge.set("target", e.target)
        d = ET.SubElement(edge, f"{{{ns}}}data")
        d.set("key", "e_kind")
        d.text = e.kind
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    tree.write(path, encoding="utf-8", xml_declaration=True)


# ----------------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------------


def main() -> int:
    graph = Graph()
    build_backend(graph)
    build_frontend(graph)

    emit_json(graph, OUT_DIR / "forgemind-graph.json")
    emit_cypher(graph, OUT_DIR / "forgemind-graph.cypher")
    emit_graphml(graph, OUT_DIR / "forgemind-graph.graphml")

    summary = _by_kind(graph)
    print(f"nodes: {len(graph.nodes)}  edges: {len(graph.edges)}")
    for k, v in summary.items():
        print(f"  {k}: {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
