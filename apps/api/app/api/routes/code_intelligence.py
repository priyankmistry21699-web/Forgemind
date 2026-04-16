"""Code Intelligence routes — FM-181 through FM-188.

Dependency graph, impact analysis, coverage mapping, pattern detection,
technical debt, test flakiness, and complexity metrics.
"""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user_id
from app.db.session import get_db
from app.services.authz_service import check_project_permission, Action
from app.services import code_graph_service
from app.services import pattern_debt_service
from app.services import flakiness_complexity_service

router = APIRouter(prefix="/code-intelligence")


# ── Inline Schemas ───────────────────────────────────────────────


class ScanFileRequest(BaseModel):
    file_path: str
    source_code: str


class RecordDependencyRequest(BaseModel):
    source_file: str
    target_file: str
    dependency_type: str = "import"
    import_name: str | None = None


class RecordCoverageRequest(BaseModel):
    source_file: str
    test_file: str
    coverage_pct: float | None = None


class ImpactAnalysisRequest(BaseModel):
    changed_files: list[str]
    max_depth: int = 5


class PatternRuleCreate(BaseModel):
    name: str
    pattern_type: str = "anti_pattern"
    language: str = "python"
    rule_definition: str
    severity: str = "warning"
    description: str | None = None


class TestResultRecord(BaseModel):
    test_name: str
    test_file: str
    outcome: str
    duration_ms: int | None = None
    error_message: str | None = None
    run_id: uuid.UUID | None = None


class ComplexityRequest(BaseModel):
    file_path: str
    source_code: str
    threshold: float = 10.0


# ── FM-181: Dependency Graph ─────────────────────────────────────


@router.post("/projects/{project_id}/dependencies/scan")
async def scan_file_dependencies(
    project_id: uuid.UUID,
    data: ScanFileRequest,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Scan a Python file and record its import dependencies."""
    await check_project_permission(db, project_id, user_id, Action.PROJECT_VIEW)
    deps = await code_graph_service.scan_file_dependencies(
        db, project_id=project_id, file_path=data.file_path, source_code=data.source_code,
    )
    return {"file_path": data.file_path, "dependencies_found": len(deps)}


@router.get("/projects/{project_id}/dependencies/graph")
async def get_dependency_graph(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Get the full dependency graph for a project."""
    await check_project_permission(db, project_id, user_id, Action.PROJECT_VIEW)
    return await code_graph_service.get_dependency_graph(db, project_id)


@router.get("/projects/{project_id}/dependencies/{file_path:path}")
async def get_file_dependencies(
    project_id: uuid.UUID,
    file_path: str,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Get dependencies of a specific file."""
    await check_project_permission(db, project_id, user_id, Action.PROJECT_VIEW)
    deps = await code_graph_service.get_file_dependencies(db, project_id, file_path)
    return {
        "file_path": file_path,
        "dependencies": [
            {"target": d.target_file, "type": d.dependency_type.value if d.dependency_type else "import",
             "import_name": d.import_name}
            for d in deps
        ],
    }


# ── FM-182: Impact Analysis ──────────────────────────────────────


@router.post("/projects/{project_id}/impact-analysis")
async def analyze_impact(
    project_id: uuid.UUID,
    data: ImpactAnalysisRequest,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Analyze downstream impact of file changes."""
    await check_project_permission(db, project_id, user_id, Action.PROJECT_VIEW)
    return await code_graph_service.analyze_impact(
        db, project_id, data.changed_files, max_depth=data.max_depth,
    )


# ── FM-183: Coverage Mapping ─────────────────────────────────────


@router.post("/projects/{project_id}/coverage")
async def record_coverage(
    project_id: uuid.UUID,
    data: RecordCoverageRequest,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Record a source-to-test coverage mapping."""
    await check_project_permission(db, project_id, user_id, Action.PROJECT_EDIT)
    mapping = await code_graph_service.record_coverage(
        db, project_id=project_id,
        source_file=data.source_file,
        test_file=data.test_file,
        coverage_pct=data.coverage_pct,
    )
    return {"id": str(mapping.id), "source_file": data.source_file, "test_file": data.test_file}


@router.get("/projects/{project_id}/coverage/summary")
async def get_coverage_summary(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Get coverage summary for a project."""
    await check_project_permission(db, project_id, user_id, Action.PROJECT_VIEW)
    return await code_graph_service.get_coverage_summary(db, project_id)


@router.get("/projects/{project_id}/coverage/{source_file:path}")
async def get_tests_for_source(
    project_id: uuid.UUID,
    source_file: str,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Get all test files covering a source file."""
    await check_project_permission(db, project_id, user_id, Action.PROJECT_VIEW)
    maps = await code_graph_service.get_tests_for_source(db, project_id, source_file)
    return {
        "source_file": source_file,
        "tests": [
            {"test_file": m.test_file, "coverage_pct": m.coverage_pct}
            for m in maps
        ],
    }


# ── FM-185: Pattern Detection ────────────────────────────────────


@router.post("/pattern-rules")
async def create_pattern_rule(
    data: PatternRuleCreate,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Create a code pattern detection rule."""
    from app.models.code_intelligence import PatternType, PatternSeverity
    rule = await pattern_debt_service.create_pattern_rule(
        db,
        name=data.name,
        pattern_type=PatternType(data.pattern_type),
        language=data.language,
        rule_definition=data.rule_definition,
        severity=PatternSeverity(data.severity),
        description=data.description,
    )
    return {"id": str(rule.id), "name": rule.name}


@router.get("/pattern-rules")
async def list_pattern_rules(
    active_only: bool = Query(True),
    language: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """List all pattern detection rules."""
    rules = await pattern_debt_service.list_pattern_rules(
        db, active_only=active_only, language=language,
    )
    return {
        "rules": [
            {"id": str(r.id), "name": r.name, "pattern_type": r.pattern_type.value if r.pattern_type else None,
             "severity": r.severity.value if r.severity else None, "active": r.active}
            for r in rules
        ]
    }


@router.post("/projects/{project_id}/patterns/scan")
async def scan_file_patterns(
    project_id: uuid.UUID,
    data: ScanFileRequest,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Scan a file for code pattern occurrences."""
    await check_project_permission(db, project_id, user_id, Action.PROJECT_VIEW)
    occs = await pattern_debt_service.scan_file_for_patterns(
        db, project_id=project_id, file_path=data.file_path, source_code=data.source_code,
    )
    return {"file_path": data.file_path, "occurrences_found": len(occs)}


@router.get("/projects/{project_id}/patterns")
async def get_pattern_occurrences(
    project_id: uuid.UUID,
    rule_id: uuid.UUID | None = Query(None),
    file_path: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """List detected pattern occurrences for a project."""
    await check_project_permission(db, project_id, user_id, Action.PROJECT_VIEW)
    occs, total = await pattern_debt_service.get_pattern_occurrences(
        db, project_id, rule_id=rule_id, file_path=file_path, limit=limit, offset=offset,
    )
    return {
        "total": total,
        "items": [
            {"id": str(o.id), "rule_id": str(o.rule_id), "file_path": o.file_path,
             "line_start": o.line_start, "snippet": o.snippet}
            for o in occs
        ],
    }


# ── FM-186: Technical Debt ───────────────────────────────────────


@router.post("/projects/{project_id}/debt/scan")
async def scan_file_debt(
    project_id: uuid.UUID,
    data: ScanFileRequest,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Scan a file for TODO/FIXME/HACK debt markers."""
    await check_project_permission(db, project_id, user_id, Action.PROJECT_VIEW)
    entries = await pattern_debt_service.scan_file_for_debt(
        db, project_id=project_id, file_path=data.file_path, source_code=data.source_code,
    )
    return {"file_path": data.file_path, "debt_entries_found": len(entries)}


@router.get("/projects/{project_id}/debt")
async def list_debt_entries(
    project_id: uuid.UUID,
    file_path: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """List technical debt entries for a project."""
    await check_project_permission(db, project_id, user_id, Action.PROJECT_VIEW)
    entries, total = await pattern_debt_service.list_debt_entries(
        db, project_id, file_path=file_path, limit=limit, offset=offset,
    )
    return {
        "total": total,
        "items": [
            {"id": str(e.id), "file_path": e.file_path, "debt_type": e.debt_type.value if e.debt_type else None,
             "description": e.description, "score": e.score, "line_number": e.line_number}
            for e in entries
        ],
    }


@router.get("/projects/{project_id}/debt/summary")
async def get_debt_summary(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Get aggregated debt summary for a project."""
    await check_project_permission(db, project_id, user_id, Action.PROJECT_VIEW)
    return await pattern_debt_service.get_debt_summary(db, project_id)


@router.post("/projects/{project_id}/debt/snapshot")
async def take_debt_snapshot(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Take a point-in-time debt snapshot for trend tracking."""
    await check_project_permission(db, project_id, user_id, Action.PROJECT_EDIT)
    snap = await pattern_debt_service.take_debt_snapshot(db, project_id)
    return {"id": str(snap.id), "total_score": snap.total_score, "entry_count": snap.entry_count}


# ── FM-187: Test Flakiness ───────────────────────────────────────


@router.post("/projects/{project_id}/test-results")
async def record_test_result(
    project_id: uuid.UUID,
    data: TestResultRecord,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Record a test execution result."""
    await check_project_permission(db, project_id, user_id, Action.PROJECT_EDIT)
    from app.models.code_intelligence import TestOutcome
    tr = await flakiness_complexity_service.record_test_result(
        db, project_id=project_id, test_name=data.test_name, test_file=data.test_file,
        outcome=TestOutcome(data.outcome), duration_ms=data.duration_ms,
        error_message=data.error_message, run_id=data.run_id,
    )
    return {"id": str(tr.id), "test_name": data.test_name, "outcome": data.outcome}


@router.get("/projects/{project_id}/flaky-tests")
async def get_flaky_tests(
    project_id: uuid.UUID,
    min_runs: int = Query(3, ge=2),
    min_flip_rate: float = Query(0.1, ge=0.0, le=1.0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Identify flaky tests by analyzing pass/fail flip rate."""
    await check_project_permission(db, project_id, user_id, Action.PROJECT_VIEW)
    return await flakiness_complexity_service.get_flaky_tests(
        db, project_id, min_runs=min_runs, min_flip_rate=min_flip_rate, limit=limit,
    )


@router.post("/projects/{project_id}/flaky-tests/{test_name:path}/quarantine")
async def quarantine_test(
    project_id: uuid.UUID,
    test_name: str,
    quarantined: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Quarantine or un-quarantine a flaky test."""
    await check_project_permission(db, project_id, user_id, Action.PROJECT_EDIT)
    updated = await flakiness_complexity_service.quarantine_test(
        db, project_id, test_name, quarantined=quarantined,
    )
    return {"test_name": test_name, "quarantined": quarantined, "records_updated": updated}


@router.get("/projects/{project_id}/flakiness/summary")
async def get_flakiness_summary(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Get test flakiness summary stats."""
    await check_project_permission(db, project_id, user_id, Action.PROJECT_VIEW)
    return await flakiness_complexity_service.get_test_flakiness_summary(db, project_id)


# ── FM-188: Complexity Metrics ───────────────────────────────────


@router.post("/projects/{project_id}/complexity/analyze")
async def analyze_file_complexity(
    project_id: uuid.UUID,
    data: ComplexityRequest,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Analyze code complexity for a file."""
    await check_project_permission(db, project_id, user_id, Action.PROJECT_VIEW)
    metrics = await flakiness_complexity_service.analyze_file_complexity(
        db, project_id=project_id, file_path=data.file_path,
        source_code=data.source_code, threshold=data.threshold,
    )
    return {"file_path": data.file_path, "metrics_count": len(metrics)}


@router.get("/projects/{project_id}/complexity/hotspots")
async def get_complexity_hotspots(
    project_id: uuid.UUID,
    exceeds_only: bool = Query(True),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Get functions/files with highest complexity."""
    await check_project_permission(db, project_id, user_id, Action.PROJECT_VIEW)
    hotspots = await flakiness_complexity_service.get_complexity_hotspots(
        db, project_id, exceeds_only=exceeds_only, limit=limit,
    )
    return {
        "hotspots": [
            {"file_path": h.file_path, "function_name": h.function_name,
             "value": h.value, "threshold": h.threshold, "exceeds": h.exceeds_threshold}
            for h in hotspots
        ]
    }


@router.get("/projects/{project_id}/complexity/summary")
async def get_complexity_summary(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Get complexity summary stats for a project."""
    await check_project_permission(db, project_id, user_id, Action.PROJECT_VIEW)
    return await flakiness_complexity_service.get_complexity_summary(db, project_id)
