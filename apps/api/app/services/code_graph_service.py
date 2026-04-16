"""Code Intelligence services — FM-181/182/183.

FM-181: Dependency graph building from Python AST imports.
FM-182: Impact analysis — find downstream dependents of a changed file.
FM-183: Test coverage mapping — link source files to test files.
"""

import ast
import hashlib
import logging
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

    imports = _extract_imports_from_source(source_code)
    deps = []
    for imp in imports:
        # Convert module path to file path heuristic
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
