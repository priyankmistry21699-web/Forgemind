"""Code Intelligence services — FM-181/182/183/184.

FM-181: Dependency graph building from Python AST + TypeScript regex imports.
FM-182: Impact analysis — find downstream dependents of a changed file.
FM-183: Test coverage mapping — link source files to test files.
FM-184: Intelligent test selection — compose FM-182 + FM-183.
"""

import ast
import hashlib
import json
import logging
import re
import uuid
from typing import Any

from sqlalchemy import select, func as sa_func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.code_intelligence import (
    ModuleDependency,
    DependencyType,
    CoverageMap,
)

# FM-181: hash cache for incremental scan
_file_hashes: dict[str, str] = {}

logger = logging.getLogger(__name__)


# ── FM-181: Dependency Graph ─────────────────────────────────────


def _extract_imports_from_source(source_code: str) -> list[dict[str, str]]:
    """Parse Python source and return import references."""
    imports: list[dict[str, str]] = []
    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        return imports

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append({"module": alias.name, "type": "import"})
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                imports.append(
                    {"module": f"{module}.{alias.name}" if module else alias.name,
                     "type": "import"}
                )
    return imports


# ── FM-181: TypeScript / ES6 / CommonJS import parser ────────────

# ES6:  import X from 'module'  |  import { X } from 'module'
#       import * as X from 'module'  |  import 'module'
_RE_ES6_IMPORT = re.compile(
    r"""import\s+(?:(?:[\w*{}\s,]+)\s+from\s+)?['"]([^'"]+)['"]""",
)

# ES6 re-export:  export { X } from 'module'  |  export * from 'module'
_RE_ES6_REEXPORT = re.compile(
    r"""export\s+(?:(?:[\w*{}\s,]+)\s+from\s+)['"]([^'"]+)['"]""",
)

# CommonJS:  require('module')
_RE_REQUIRE = re.compile(
    r"""(?:=\s*)?require\s*\(\s*['"]([^'"]+)['"]\s*\)""",
)

# Dynamic import():  import('module')
_RE_DYNAMIC_IMPORT = re.compile(
    r"""import\s*\(\s*['"]([^'"]+)['"]\s*\)""",
)

_TS_EXTENSIONS = frozenset({".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"})


def _extract_imports_from_typescript(source_code: str) -> list[dict[str, str]]:
    """Parse TypeScript / ES6 / CommonJS source and return import references.

    Uses regex-based parsing — reliable enough for static import extraction
    without requiring a full TS parser or tree-sitter dependency.
    """
    imports: list[dict[str, str]] = []
    seen: set[str] = set()

    for pattern in (_RE_ES6_IMPORT, _RE_ES6_REEXPORT, _RE_REQUIRE, _RE_DYNAMIC_IMPORT):
        for match in pattern.finditer(source_code):
            module = match.group(1)
            if module not in seen:
                seen.add(module)
                imports.append({"module": module, "type": "import"})

    return imports


def _is_typescript_file(file_path: str) -> bool:
    """Check if a file path looks like TypeScript / JavaScript."""
    import os
    _, ext = os.path.splitext(file_path)
    return ext.lower() in _TS_EXTENSIONS


def _ts_module_to_file(module_path: str) -> str:
    """Convert TypeScript module specifier to a file path heuristic.

    - Relative paths (./foo, ../bar) keep their structure + .ts extension
    - Bare specifiers (react, lodash) become package refs under node_modules/
    - @scoped packages preserved as-is
    """
    if module_path.startswith("."):
        # Relative import — add .ts if no extension present
        import os
        _, ext = os.path.splitext(module_path)
        if ext and ext.lower() in _TS_EXTENSIONS:
            return module_path
        return module_path + ".ts"
    # Bare / scoped package specifier
    return f"node_modules/{module_path}/index.ts"


async def record_dependency(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    source_file: str,
    target_file: str,
    dependency_type: DependencyType = DependencyType.IMPORT,
    import_name: str | None = None,
) -> ModuleDependency:
    """Record a single dependency edge."""
    dep = ModuleDependency(
        project_id=project_id,
        source_file=source_file,
        target_file=target_file,
        dependency_type=dependency_type,
        import_name=import_name,
    )
    db.add(dep)
    await db.flush()
    return dep


async def scan_file_dependencies(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    file_path: str,
    source_code: str,
    force: bool = False,
) -> list[ModuleDependency]:
    """Parse imports from a file and record all dependency edges.

    FM-181 incremental scan: skips re-scanning if source content hash
    is unchanged since last scan (unless force=True).
    """
    content_hash = hashlib.sha256(source_code.encode()).hexdigest()
    cache_key = f"{project_id}:{file_path}"
    if not force and _file_hashes.get(cache_key) == content_hash:
        # Content unchanged — return existing edges
        return await get_file_dependencies(db, project_id, file_path)
    _file_hashes[cache_key] = content_hash

    # Clear old edges for this source file
    await db.execute(
        delete(ModuleDependency).where(
            ModuleDependency.project_id == project_id,
            ModuleDependency.source_file == file_path,
        )
    )

    # FM-181: choose parser based on file extension
    if _is_typescript_file(file_path):
        imports = _extract_imports_from_typescript(source_code)
    else:
        imports = _extract_imports_from_source(source_code)

    deps = []
    for imp in imports:
        # Convert module path to file path heuristic
        if _is_typescript_file(file_path):
            target = _ts_module_to_file(imp["module"])
        else:
            target = imp["module"].replace(".", "/") + ".py"
        dep = ModuleDependency(
            project_id=project_id,
            source_file=file_path,
            target_file=target,
            dependency_type=DependencyType.IMPORT,
            import_name=imp["module"],
        )
        db.add(dep)
        deps.append(dep)

    await db.flush()
    return deps


async def get_file_dependencies(
    db: AsyncSession,
    project_id: uuid.UUID,
    file_path: str,
) -> list[ModuleDependency]:
    """Get all dependencies **of** a file (outgoing edges)."""
    result = await db.execute(
        select(ModuleDependency).where(
            ModuleDependency.project_id == project_id,
            ModuleDependency.source_file == file_path,
        )
    )
    return list(result.scalars().all())


async def get_file_dependents(
    db: AsyncSession,
    project_id: uuid.UUID,
    file_path: str,
) -> list[ModuleDependency]:
    """Get all files that depend **on** this file (incoming edges)."""
    result = await db.execute(
        select(ModuleDependency).where(
            ModuleDependency.project_id == project_id,
            ModuleDependency.target_file == file_path,
        )
    )
    return list(result.scalars().all())


async def get_dependency_graph(
    db: AsyncSession,
    project_id: uuid.UUID,
) -> dict[str, Any]:
    """Return the full dependency graph as nodes + edges."""
    result = await db.execute(
        select(ModuleDependency).where(
            ModuleDependency.project_id == project_id,
        )
    )
    deps = list(result.scalars().all())

    nodes: set[str] = set()
    edges = []
    for d in deps:
        nodes.add(d.source_file)
        nodes.add(d.target_file)
        edges.append({
            "source": d.source_file,
            "target": d.target_file,
            "type": d.dependency_type.value if d.dependency_type else "import",
            "import_name": d.import_name,
        })

    return {
        "project_id": str(project_id),
        "node_count": len(nodes),
        "edge_count": len(edges),
        "nodes": sorted(nodes),
        "edges": edges,
    }


# ── FM-182: Impact Analysis ──────────────────────────────────────


async def analyze_impact(
    db: AsyncSession,
    project_id: uuid.UUID,
    changed_files: list[str],
    *,
    max_depth: int = 5,
) -> dict[str, Any]:
    """BFS to find all downstream affected files from changed set."""
    visited: set[str] = set()
    frontier = list(changed_files)
    depth = 0
    layers: list[list[str]] = []

    while frontier and depth < max_depth:
        current_layer = []
        for f in frontier:
            if f not in visited:
                visited.add(f)
                current_layer.append(f)

        if not current_layer:
            break

        layers.append(current_layer)

        # Find all dependents of files in this layer
        result = await db.execute(
            select(ModuleDependency.source_file).where(
                ModuleDependency.project_id == project_id,
                ModuleDependency.target_file.in_(current_layer),
            )
        )
        frontier = [row[0] for row in result.all() if row[0] not in visited]
        depth += 1

    # FM-182: classify affected files as test vs source
    affected = sorted(visited - set(changed_files))
    affected_tests = [f for f in affected if _is_test_file(f)]
    affected_sources = [f for f in affected if not _is_test_file(f)]

    # FM-182: compute risk score based on blast radius
    total_aff = len(visited) - len(changed_files)
    depth = len(layers)
    risk_score = round(min(total_aff * 2.0 + depth * 3.0, 100.0), 2)
    if risk_score >= 70:
        risk_level = "high"
    elif risk_score >= 30:
        risk_level = "medium"
    else:
        risk_level = "low"

    return {
        "project_id": str(project_id),
        "changed_files": changed_files,
        "affected_files": affected,
        "affected_tests": affected_tests,
        "affected_sources": affected_sources,
        "total_affected": total_aff,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "depth_reached": depth,
        "layers": layers,
    }


def _is_test_file(file_path: str) -> bool:
    """Heuristic: a file is a test file if its basename starts with test_ or ends with _test."""
    import os
    base = os.path.basename(file_path)
    name = os.path.splitext(base)[0]
    return name.startswith("test_") or name.endswith("_test")


# ── FM-183: Test Coverage Mapping ────────────────────────────────


async def record_coverage(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    source_file: str,
    test_file: str,
    coverage_pct: float | None = None,
) -> CoverageMap:
    """Record or update a source → test coverage mapping."""
    result = await db.execute(
        select(CoverageMap).where(
            CoverageMap.project_id == project_id,
            CoverageMap.source_file == source_file,
            CoverageMap.test_file == test_file,
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        existing.coverage_pct = coverage_pct
        await db.flush()
        return existing

    mapping = CoverageMap(
        project_id=project_id,
        source_file=source_file,
        test_file=test_file,
        coverage_pct=coverage_pct,
    )
    db.add(mapping)
    await db.flush()
    return mapping


async def get_tests_for_source(
    db: AsyncSession,
    project_id: uuid.UUID,
    source_file: str,
) -> list[CoverageMap]:
    """Get all test files that cover a given source file."""
    result = await db.execute(
        select(CoverageMap).where(
            CoverageMap.project_id == project_id,
            CoverageMap.source_file == source_file,
        )
    )
    return list(result.scalars().all())


async def get_coverage_summary(
    db: AsyncSession,
    project_id: uuid.UUID,
) -> dict[str, Any]:
    """Get overall coverage stats for a project."""
    result = await db.execute(
        select(
            sa_func.count(CoverageMap.id).label("mapping_count"),
            sa_func.count(sa_func.distinct(CoverageMap.source_file)).label("covered_files"),
            sa_func.avg(CoverageMap.coverage_pct).label("avg_coverage"),
        ).where(CoverageMap.project_id == project_id)
    )
    row = result.one()
    return {
        "project_id": str(project_id),
        "mapping_count": row.mapping_count,
        "covered_files": row.covered_files,
        "avg_coverage": round(float(row.avg_coverage or 0), 2),
    }


async def get_coverage_gaps(
    db: AsyncSession,
    project_id: uuid.UUID,
) -> dict[str, Any]:
    """FM-183: Detect source files with no test coverage.

    Returns uncovered files ranked by their dependency count (importance).
    Files that are depended on by many others are listed first.
    """
    # All source files in the dependency graph
    all_sources_q = await db.execute(
        select(sa_func.distinct(ModuleDependency.source_file)).where(
            ModuleDependency.project_id == project_id,
        )
    )
    all_targets_q = await db.execute(
        select(sa_func.distinct(ModuleDependency.target_file)).where(
            ModuleDependency.project_id == project_id,
        )
    )
    all_files = set(r[0] for r in all_sources_q.all()) | set(r[0] for r in all_targets_q.all())

    # Covered source files
    covered_q = await db.execute(
        select(sa_func.distinct(CoverageMap.source_file)).where(
            CoverageMap.project_id == project_id,
        )
    )
    covered_files = set(r[0] for r in covered_q.all())

    uncovered = all_files - covered_files

    # Rank by incoming dependency count (how many files depend on this one)
    ranked: list[dict[str, Any]] = []
    for f in uncovered:
        dep_count_q = await db.execute(
            select(sa_func.count(ModuleDependency.id)).where(
                ModuleDependency.project_id == project_id,
                ModuleDependency.target_file == f,
            )
        )
        dep_count = dep_count_q.scalar_one()
        ranked.append({"file": f, "dependent_count": dep_count})

    ranked.sort(key=lambda x: x["dependent_count"], reverse=True)

    return {
        "project_id": str(project_id),
        "total_known_files": len(all_files),
        "covered_files": len(covered_files),
        "uncovered_files": len(uncovered),
        "gaps": ranked,
    }


# ── FM-183: Coverage Report Ingestion ────────────────────────────


async def ingest_coverage_report(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    report_json: str | dict,
    report_format: str = "pytest-cov",
) -> dict[str, Any]:
    """Ingest a coverage report (pytest-cov JSON, istanbul JSON, or LCOV text).

    Supports:
      - pytest-cov (coverage.py JSON)  — ``report_format="pytest-cov"``
      - istanbul (NYC JSON summary)    — ``report_format="istanbul"``
      - LCOV text                      — ``report_format="lcov"``

    Returns summary with count of files ingested.
    """
    if isinstance(report_json, str):
        if report_format == "lcov":
            file_metrics = _parse_lcov(report_json)
        else:
            report_json = json.loads(report_json)
            file_metrics = {}  # will be filled below
    else:
        file_metrics = {}

    if report_format == "pytest-cov" and isinstance(report_json, dict):
        file_metrics = _parse_pytest_cov(report_json)
    elif report_format == "istanbul" and isinstance(report_json, dict):
        file_metrics = _parse_istanbul(report_json)
    elif report_format == "lcov" and not file_metrics:
        file_metrics = {}

    created = 0
    for source_file, pct in file_metrics.items():
        # Upsert coverage — use a synthetic test_file placeholder when
        # the report only provides file-level metrics (no per-test info).
        result = await db.execute(
            select(CoverageMap).where(
                CoverageMap.project_id == project_id,
                CoverageMap.source_file == source_file,
                CoverageMap.test_file == "__coverage_report__",
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            existing.coverage_pct = pct
        else:
            db.add(CoverageMap(
                project_id=project_id,
                source_file=source_file,
                test_file="__coverage_report__",
                coverage_pct=pct,
            ))
        created += 1

    await db.flush()
    return {
        "project_id": str(project_id),
        "format": report_format,
        "files_ingested": created,
        "file_metrics": file_metrics,
    }


def _parse_pytest_cov(data: dict) -> dict[str, float]:
    """Parse coverage.py / pytest-cov JSON report → {file: pct}."""
    metrics: dict[str, float] = {}
    files = data.get("files", {})
    for file_path, info in files.items():
        summary = info.get("summary", {})
        pct = summary.get("percent_covered", 0.0)
        metrics[file_path] = round(float(pct), 2)
    # Also handle the flat format: {"<file>": {"executed_lines":[], ...}}
    if not files and "meta" not in data:
        for file_path, info in data.items():
            if isinstance(info, dict) and "summary" in info:
                metrics[file_path] = round(
                    float(info["summary"].get("percent_covered", 0.0)), 2
                )
    return metrics


def _parse_istanbul(data: dict) -> dict[str, float]:
    """Parse istanbul / NYC JSON summary → {file: pct}."""
    metrics: dict[str, float] = {}
    for file_path, info in data.items():
        if file_path == "total":
            continue
        if isinstance(info, dict):
            lines = info.get("lines", {})
            pct = lines.get("pct", 0.0)
            metrics[file_path] = round(float(pct), 2)
    return metrics


def _parse_lcov(text: str) -> dict[str, float]:
    """Parse LCOV tracefile text → {file: pct}."""
    metrics: dict[str, float] = {}
    current_file: str | None = None
    lines_hit = 0
    lines_found = 0
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("SF:"):
            current_file = line[3:]
            lines_hit = 0
            lines_found = 0
        elif line.startswith("LH:"):
            lines_hit = int(line[3:])
        elif line.startswith("LF:"):
            lines_found = int(line[3:])
        elif line == "end_of_record" and current_file:
            pct = (lines_hit / lines_found * 100) if lines_found else 0.0
            metrics[current_file] = round(pct, 2)
            current_file = None
    return metrics


# ── FM-184: Intelligent Test Selection ───────────────────────────

# Selection modes control how far into the dependency graph we look.
_MODE_DEPTH = {
    "minimal": 1,       # Direct dependents only
    "standard": 2,      # 1-hop transitive
    "comprehensive": 5,  # Full blast radius
}


async def select_tests_for_changes(
    db: AsyncSession,
    project_id: uuid.UUID,
    changed_files: list[str],
    *,
    mode: str = "standard",
) -> dict[str, Any]:
    """FM-184: Given changed files, select the minimal set of tests to run.

    Composes FM-182 (impact analysis) with FM-183 (coverage mapping) to
    produce a prioritised test list with confidence scoring.

    Modes:
      - minimal: only tests directly covering changed source files
      - standard: tests covering changed files + 1-hop transitive dependents
      - comprehensive: tests covering the full blast radius (max_depth=5)
    """
    max_depth = _MODE_DEPTH.get(mode, 2)

    # Step 1: Run impact analysis to find affected files
    impact = await analyze_impact(
        db, project_id, changed_files, max_depth=max_depth,
    )

    affected_sources = impact["affected_sources"]
    all_relevant = list(changed_files) + affected_sources

    # Step 2: Query coverage map for tests covering relevant source files
    test_set: dict[str, dict[str, Any]] = {}  # test_file → info

    for source_file in all_relevant:
        mappings = await get_tests_for_source(db, project_id, source_file)
        for m in mappings:
            if m.test_file == "__coverage_report__":
                continue
            if m.test_file not in test_set:
                test_set[m.test_file] = {
                    "test_file": m.test_file,
                    "covers": [],
                    "avg_coverage": 0.0,
                }
            test_set[m.test_file]["covers"].append(source_file)
            if m.coverage_pct is not None:
                # Running average
                info = test_set[m.test_file]
                n = len(info["covers"])
                prev_avg = info["avg_coverage"]
                info["avg_coverage"] = round(
                    prev_avg + (m.coverage_pct - prev_avg) / n, 2,
                )

    # Step 3: Also include tests found via impact analysis (naming-convention match)
    for test_file in impact["affected_tests"]:
        if test_file not in test_set:
            test_set[test_file] = {
                "test_file": test_file,
                "covers": [],
                "avg_coverage": 0.0,
            }

    selected = sorted(test_set.values(), key=lambda t: len(t["covers"]), reverse=True)

    # Step 4: Confidence scoring
    total_relevant = len(all_relevant)
    if total_relevant == 0:
        confidence = 1.0
    else:
        covered_sources = set()
        for info in selected:
            covered_sources.update(info["covers"])
        confidence = round(len(covered_sources) / total_relevant, 2)

    return {
        "project_id": str(project_id),
        "mode": mode,
        "changed_files": changed_files,
        "total_affected": impact["total_affected"],
        "risk_score": impact["risk_score"],
        "risk_level": impact["risk_level"],
        "selected_tests": selected,
        "test_count": len(selected),
        "confidence": confidence,
    }


# ── FM-189: Code Intelligence Agent Integration ──────────────────


async def build_code_intelligence_context(
    db: AsyncSession,
    project_id: uuid.UUID,
    *,
    changed_files: list[str] | None = None,
) -> dict[str, Any]:
    """FM-189: Build an aggregate code intelligence context for agent consumption.

    Packages dependency graph summary, coverage summary, complexity hotspots,
    debt summary, and optionally impact analysis into a single dict that can
    be injected into agent execution contexts.
    """
    from app.services import pattern_debt_service
    from app.services import flakiness_complexity_service

    # Core summaries that are always useful
    graph = await get_dependency_graph(db, project_id)
    coverage = await get_coverage_summary(db, project_id)
    coverage_gaps = await get_coverage_gaps(db, project_id)

    # Complexity hotspots — top 10 most complex functions
    hotspots = await flakiness_complexity_service.get_complexity_hotspots(
        db, project_id, exceeds_only=True, limit=10,
    )

    # Debt summary
    debt = await pattern_debt_service.get_debt_summary(db, project_id)

    # Flakiness snapshot
    flakiness = await flakiness_complexity_service.get_test_flakiness_summary(
        db, project_id,
    )

    context: dict[str, Any] = {
        "project_id": str(project_id),
        "dependency_graph": {
            "node_count": graph["node_count"],
            "edge_count": graph["edge_count"],
        },
        "coverage": {
            "mapping_count": coverage["mapping_count"],
            "covered_files": coverage["covered_files"],
            "avg_coverage": coverage["avg_coverage"],
            "gap_count": coverage_gaps["uncovered_files"],
        },
        "complexity_hotspots": [
            {
                "file": h.file_path,
                "function": h.function_name,
                "metric_type": h.metric_type.value if hasattr(h.metric_type, "value") else str(h.metric_type),
                "value": float(h.value),
            }
            for h in hotspots
        ],
        "debt": debt,
        "flakiness": flakiness,
    }

    # Optional: impact analysis when specific files are changing
    if changed_files:
        impact = await analyze_impact(db, project_id, changed_files)
        context["impact_analysis"] = {
            "changed_files": impact["changed_files"],
            "total_affected": impact["total_affected"],
            "risk_score": impact["risk_score"],
            "risk_level": impact["risk_level"],
            "affected_tests": impact["affected_tests"],
        }

    return context


def format_context_for_prompt(context: dict[str, Any]) -> str:
    """FM-189: Format code intelligence context into a text block for agent prompts.

    Returns a concise summary suitable for injection into LLM prompts.
    """
    lines: list[str] = []
    lines.append("## Code Intelligence Context")
    lines.append("")

    # Dependency graph
    dg = context.get("dependency_graph", {})
    lines.append(f"**Dependency Graph:** {dg.get('node_count', 0)} files, "
                 f"{dg.get('edge_count', 0)} dependencies")

    # Coverage
    cov = context.get("coverage", {})
    lines.append(f"**Coverage:** {cov.get('covered_files', 0)} files covered, "
                 f"avg {cov.get('avg_coverage', 0)}%, "
                 f"{cov.get('gap_count', 0)} gaps")

    # Complexity hotspots
    hotspots = context.get("complexity_hotspots", [])
    if hotspots:
        lines.append(f"**Complexity Hotspots:** {len(hotspots)} functions above threshold")
        for h in hotspots[:5]:
            lines.append(f"  - {h['file']}:{h['function']} ({h['metric_type']}={h['value']})")

    # Debt
    debt = context.get("debt", {})
    if isinstance(debt, dict):
        lines.append(f"**Technical Debt:** score={debt.get('total_score', 0)}, "
                     f"{debt.get('entry_count', 0)} entries")

    # Impact analysis (if present)
    impact = context.get("impact_analysis")
    if impact:
        lines.append(f"**Change Impact:** {impact['total_affected']} files affected, "
                     f"risk={impact['risk_level']} ({impact['risk_score']})")
        if impact.get("affected_tests"):
            lines.append(f"  Affected tests: {', '.join(impact['affected_tests'][:5])}")

    return "\n".join(lines)
