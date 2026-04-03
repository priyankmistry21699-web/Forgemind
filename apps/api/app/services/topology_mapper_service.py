"""Topology mapper service - codebase structure analysis.

FM-082: Populates the architecture graph from repo/codebase structure.
Scans directories, imports, and module boundaries to infer nodes/edges.
"""

import os
import re
import uuid
from collections import defaultdict

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.architecture import NodeType, EdgeType, SourceType
from app.services import architecture_service


# ── Import parsers ───────────────────────────────────────────────


def parse_python_imports(source: str) -> list[str]:
    """Extract import targets from Python source code."""
    imports: list[str] = []
    for line in source.splitlines():
        line = line.strip()
        if line.startswith("from "):
            match = re.match(r"from\s+([\w.]+)\s+import", line)
            if match:
                imports.append(match.group(1))
        elif line.startswith("import "):
            match = re.match(r"import\s+([\w.]+)", line)
            if match:
                imports.append(match.group(1))
    return imports


def parse_typescript_imports(source: str) -> list[str]:
    """Extract import paths from TypeScript/JavaScript source code."""
    imports: list[str] = []
    for match in re.finditer(r"""(?:import|from)\s+['"]([^'"]+)['"]""", source):
        imports.append(match.group(1))
    for match in re.finditer(r"""import\s+.*?\s+from\s+['"]([^'"]+)['"]""", source):
        if match.group(1) not in imports:
            imports.append(match.group(1))
    return imports


def classify_layer(path: str) -> str:
    """Classify a file into an architectural layer based on path."""
    path_lower = path.lower().replace("\\", "/")
    if "/routes/" in path_lower or "/api/" in path_lower:
        return "api"
    if "/services/" in path_lower:
        return "service"
    if "/models/" in path_lower:
        return "model"
    if "/schemas/" in path_lower:
        return "schema"
    if "/core/" in path_lower or "/middleware/" in path_lower:
        return "core"
    if "/components/" in path_lower:
        return "component"
    if "/lib/" in path_lower:
        return "library"
    if "/tests/" in path_lower or "/test/" in path_lower:
        return "test"
    if "/app/" in path_lower and "/page." in path_lower:
        return "page"
    return "other"


def detect_language(path: str) -> str | None:
    """Detect programming language from file extension."""
    ext = os.path.splitext(path)[1].lower()
    return {
        ".py": "python",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".js": "javascript",
        ".jsx": "javascript",
        ".go": "go",
        ".rs": "rust",
        ".java": "java",
    }.get(ext)


# ── Topology scanning ───────────────────────────────────────────


def scan_directory_structure(
    base_path: str,
    *,
    scan_python: bool = True,
    scan_typescript: bool = True,
) -> tuple[list[dict], list[dict]]:
    """Scan a directory tree and return (nodes, edges) as dicts.

    This is a pure function that reads the filesystem and returns
    structural information without touching the database.
    """
    nodes: list[dict] = []
    edges: list[dict] = []
    node_keys: dict[str, int] = {}  # key -> index in nodes list

    skip_dirs = {
        "node_modules",
        ".git",
        "__pycache__",
        ".next",
        ".venv",
        "venv",
        "dist",
        "build",
        ".mypy_cache",
        ".pytest_cache",
        "egg-info",
    }

    def _module_key(filepath: str) -> str:
        rel = os.path.relpath(filepath, base_path).replace("\\", "/")
        return rel

    for root, dirs, files in os.walk(base_path):
        dirs[:] = [
            d for d in dirs if d not in skip_dirs and not d.endswith(".egg-info")
        ]

        rel_root = os.path.relpath(root, base_path).replace("\\", "/")
        if rel_root == ".":
            rel_root = ""

        for fname in files:
            filepath = os.path.join(root, fname)
            lang = detect_language(fname)
            if lang is None:
                continue
            if lang == "python" and not scan_python:
                continue
            if lang in ("typescript", "javascript") and not scan_typescript:
                continue

            key = _module_key(filepath)
            layer = classify_layer(key)
            node_keys[key] = len(nodes)
            nodes.append(
                {
                    "node_type": NodeType.MODULE,
                    "key": key,
                    "name": fname,
                    "path": key,
                    "language": lang,
                    "metadata_": {"layer": layer},
                    "source_type": SourceType.INFERRED,
                }
            )

            # Parse imports
            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    source = f.read(64_000)  # cap read size
            except OSError:
                continue

            raw_imports: list[str] = []
            if lang == "python":
                raw_imports = parse_python_imports(source)
            elif lang in ("typescript", "javascript"):
                raw_imports = parse_typescript_imports(source)

            for imp in raw_imports:
                edges.append(
                    {
                        "from_key": key,
                        "to_import": imp,
                        "edge_type": EdgeType.IMPORTS,
                        "source_type": SourceType.INFERRED,
                    }
                )

    # Resolve edges: match import paths to known node keys
    resolved_edges: list[dict] = []
    for edge_raw in edges:
        target_import = edge_raw["to_import"]
        # Try direct match
        matched_key = _resolve_import(target_import, node_keys, base_path)
        if matched_key:
            resolved_edges.append(
                {
                    "from_key": edge_raw["from_key"],
                    "to_key": matched_key,
                    "edge_type": edge_raw["edge_type"],
                    "source_type": edge_raw["source_type"],
                    "confidence_score": 0.8,
                }
            )

    return nodes, resolved_edges


def _resolve_import(
    import_path: str,
    node_keys: dict[str, int],
    base_path: str,
) -> str | None:
    """Try to resolve an import string to a known node key."""
    # Python dotted import -> path
    as_path = import_path.replace(".", "/")
    candidates = [
        f"{as_path}.py",
        f"{as_path}/__init__.py",
        as_path,
    ]
    # TypeScript relative/absolute imports
    if import_path.startswith("./") or import_path.startswith("../"):
        ts_candidates = [
            f"{import_path}.ts",
            f"{import_path}.tsx",
            f"{import_path}/index.ts",
        ]
        candidates.extend(ts_candidates)
    # @/ alias (Next.js)
    if import_path.startswith("@/"):
        stripped = import_path[2:]
        candidates.extend(
            [
                f"{stripped}.ts",
                f"{stripped}.tsx",
                f"{stripped}/index.ts",
            ]
        )

    for c in candidates:
        normalized = c.replace("\\", "/").lstrip("/")
        if normalized in node_keys:
            return normalized

    return None


def compute_topology_summary(nodes: list[dict], edges: list[dict]) -> dict:
    """Compute summary statistics for a topology scan."""
    layers = set()
    for n in nodes:
        layer = (n.get("metadata_") or {}).get("layer", "other")
        layers.add(layer)

    # Compute in/out degree per node key
    in_degree: dict[str, int] = defaultdict(int)
    out_degree: dict[str, int] = defaultdict(int)
    node_keys_set = {n["key"] for n in nodes}

    for e in edges:
        out_degree[e["from_key"]] += 1
        in_degree[e["to_key"]] += 1

    # Isolated: no edges
    isolated = [
        n["key"]
        for n in nodes
        if in_degree.get(n["key"], 0) == 0 and out_degree.get(n["key"], 0) == 0
    ]

    # High centrality: top by total degree
    total_degree = {
        k: in_degree.get(k, 0) + out_degree.get(k, 0) for k in node_keys_set
    }
    sorted_by_degree = sorted(total_degree.items(), key=lambda x: x[1], reverse=True)
    high_centrality = [k for k, d in sorted_by_degree[:10] if d > 0]

    return {
        "components_found": len(nodes),
        "edges_found": len(edges),
        "layers": sorted(layers),
        "isolated_nodes": isolated[:20],
        "high_centrality_nodes": high_centrality,
    }


# ── DB persistence ───────────────────────────────────────────────


async def map_topology(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    base_path: str,
    scan_python: bool = True,
    scan_typescript: bool = True,
) -> dict:
    """Scan a directory and persist nodes/edges to the architecture graph."""
    raw_nodes, raw_edges = scan_directory_structure(
        base_path,
        scan_python=scan_python,
        scan_typescript=scan_typescript,
    )

    # Create nodes
    key_to_node: dict[str, uuid.UUID] = {}
    for n in raw_nodes:
        node = await architecture_service.create_node(
            db,
            project_id=project_id,
            node_type=n["node_type"],
            key=n["key"],
            name=n["name"],
            path=n.get("path"),
            language=n.get("language"),
            metadata_=n.get("metadata_"),
            source_type=n.get("source_type", SourceType.INFERRED),
        )
        key_to_node[n["key"]] = node.id

    # Create edges
    edge_count = 0
    for e in raw_edges:
        from_id = key_to_node.get(e["from_key"])
        to_id = key_to_node.get(e["to_key"])
        if from_id and to_id:
            await architecture_service.create_edge(
                db,
                project_id=project_id,
                from_node_id=from_id,
                to_node_id=to_id,
                edge_type=e["edge_type"],
                confidence_score=e.get("confidence_score", 0.8),
                source_type=e.get("source_type", SourceType.INFERRED),
            )
            edge_count += 1

    summary = compute_topology_summary(raw_nodes, raw_edges)
    summary["project_id"] = str(project_id)
    return summary
