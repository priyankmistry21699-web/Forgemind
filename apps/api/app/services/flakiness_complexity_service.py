"""Test Flakiness & Complexity services — FM-187/188.

FM-187: Test flakiness detection — track test outcomes, compute flip rates.
FM-188: Code complexity metrics — cyclomatic/cognitive complexity analysis.
"""

import ast
import logging
import uuid
from typing import Any

from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.code_intelligence import (
    TestResult,
    TestOutcome,
    ComplexityMetric,
    MetricType,
)

logger = logging.getLogger(__name__)


# ── FM-187: Test Flakiness Detection ─────────────────────────────


async def record_test_result(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    run_id: uuid.UUID | None = None,
    test_name: str,
    test_file: str,
    outcome: TestOutcome,
    duration_ms: int | None = None,
    error_message: str | None = None,
) -> TestResult:
    """Record a single test execution result."""
    tr = TestResult(
        project_id=project_id,
        run_id=run_id,
        test_name=test_name,
        test_file=test_file,
        outcome=outcome,
        duration_ms=duration_ms,
        error_message=error_message,
    )
    db.add(tr)
    await db.flush()
    return tr


async def get_flaky_tests(
    db: AsyncSession,
    project_id: uuid.UUID,
    *,
    min_runs: int = 3,
    min_flip_rate: float = 0.1,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Identify flaky tests by computing pass/fail flip rate.

    A test is flaky if it alternates between pass and fail across runs.
    Flip rate = (number of status changes) / (total runs - 1).
    """
    from sqlalchemy import case

    # Get tests with enough history
    subq = (
        select(
            TestResult.test_name,
            TestResult.test_file,
            sa_func.count(TestResult.id).label("total_runs"),
            sa_func.sum(
                case((TestResult.outcome == TestOutcome.PASSED, 1), else_=0)
            ).label("pass_count"),
            sa_func.sum(
                case((TestResult.outcome == TestOutcome.FAILED, 1), else_=0)
            ).label("fail_count"),
        )
        .where(TestResult.project_id == project_id)
        .group_by(TestResult.test_name, TestResult.test_file)
        .having(sa_func.count(TestResult.id) >= min_runs)
    ).subquery()

    result = await db.execute(
        select(subq).where(
            subq.c.pass_count > 0,
            subq.c.fail_count > 0,
        ).limit(limit)
    )
    rows = result.all()

    flaky = []
    for row in rows:
        total = row.total_runs
        flip_rate = min(row.pass_count, row.fail_count) / total if total > 0 else 0
        if flip_rate >= min_flip_rate:
            flaky.append({
                "test_name": row.test_name,
                "test_file": row.test_file,
                "total_runs": total,
                "pass_count": row.pass_count,
                "fail_count": row.fail_count,
                "flip_rate": round(flip_rate, 3),
            })
    return sorted(flaky, key=lambda x: x["flip_rate"], reverse=True)


async def quarantine_test(
    db: AsyncSession,
    project_id: uuid.UUID,
    test_name: str,
    *,
    quarantined: bool = True,
) -> int:
    """Set quarantine flag on all results for a test name."""
    result = await db.execute(
        select(TestResult).where(
            TestResult.project_id == project_id,
            TestResult.test_name == test_name,
        )
    )
    records = list(result.scalars().all())
    for rec in records:
        rec.quarantined = quarantined
    await db.flush()
    return len(records)


async def get_test_flakiness_summary(
    db: AsyncSession,
    project_id: uuid.UUID,
) -> dict[str, Any]:
    """Summary stats: total tests, flaky count, quarantined count."""
    result = await db.execute(
        select(
            sa_func.count(sa_func.distinct(TestResult.test_name)).label("total_tests"),
            sa_func.count(TestResult.id).label("total_results"),
        ).where(TestResult.project_id == project_id)
    )
    row = result.one()

    # Count quarantined
    q_result = await db.execute(
        select(sa_func.count(sa_func.distinct(TestResult.test_name))).where(
            TestResult.project_id == project_id,
            TestResult.quarantined.is_(True),
        )
    )
    quarantined_count = q_result.scalar_one()

    flaky = await get_flaky_tests(db, project_id)

    return {
        "project_id": str(project_id),
        "total_unique_tests": row.total_tests,
        "total_results": row.total_results,
        "flaky_count": len(flaky),
        "quarantined_count": quarantined_count,
    }


async def get_quarantined_test_report(
    db: AsyncSession,
    project_id: uuid.UUID,
    *,
    limit: int = 50,
) -> dict[str, Any]:
    """FM-187: Report on quarantined tests that are still being executed.

    Returns per-test stats for quarantined tests, showing recent outcomes
    so teams can decide when to un-quarantine.
    """
    from sqlalchemy import case

    subq = (
        select(
            TestResult.test_name,
            TestResult.test_file,
            sa_func.count(TestResult.id).label("total_runs"),
            sa_func.sum(
                case((TestResult.outcome == TestOutcome.PASSED, 1), else_=0)
            ).label("pass_count"),
            sa_func.sum(
                case((TestResult.outcome == TestOutcome.FAILED, 1), else_=0)
            ).label("fail_count"),
            sa_func.max(TestResult.recorded_at).label("last_run_at"),
        )
        .where(
            TestResult.project_id == project_id,
            TestResult.quarantined.is_(True),
        )
        .group_by(TestResult.test_name, TestResult.test_file)
    ).subquery()

    result = await db.execute(
        select(subq).order_by(subq.c.last_run_at.desc()).limit(limit)
    )
    rows = result.all()

    tests = []
    for row in rows:
        total = row.total_runs
        pass_rate = round(row.pass_count / total, 3) if total else 0.0
        tests.append({
            "test_name": row.test_name,
            "test_file": row.test_file,
            "total_runs": total,
            "pass_count": row.pass_count,
            "fail_count": row.fail_count,
            "pass_rate": pass_rate,
            "last_run_at": row.last_run_at.isoformat() if row.last_run_at else None,
            "recommendation": "un-quarantine" if pass_rate >= 0.9 and total >= 5 else "keep quarantined",
        })

    return {
        "project_id": str(project_id),
        "quarantined_tests": len(tests),
        "tests": tests,
    }


# ── FM-188: Code Complexity Metrics ──────────────────────────────


def _compute_cyclomatic_complexity(source_code: str) -> list[dict[str, Any]]:
    """Compute cyclomatic complexity per function using AST."""
    results = []
    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        return results

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            complexity = 1  # Base complexity
            for child in ast.walk(node):
                if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                    complexity += 1
                elif isinstance(child, ast.ExceptHandler):
                    complexity += 1
                elif isinstance(child, ast.BoolOp):
                    # Each 'and'/'or' adds a branch
                    complexity += len(child.values) - 1
                elif isinstance(child, ast.Assert):
                    complexity += 1
            results.append({
                "function_name": node.name,
                "complexity": complexity,
                "line": node.lineno,
            })
    return results


def _compute_cognitive_complexity(source_code: str) -> list[dict[str, Any]]:
    """Compute cognitive complexity per function using nesting-aware AST walk.

    Cognitive complexity differs from cyclomatic complexity by:
    - Penalizing deeply nested structures (nesting increment)
    - Penalizing breaks in linear flow (structural increment)
    - Not counting short-circuit operators the same way
    """
    results = []
    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        return results

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            score = _cognitive_visit_body(node.body, nesting=0)
            results.append({
                "function_name": node.name,
                "complexity": score,
                "line": node.lineno,
            })
    return results


def _cognitive_visit_body(stmts: list[ast.AST], nesting: int) -> int:
    """Visit a list of statements and accumulate cognitive complexity."""
    score = 0
    for stmt in stmts:
        if isinstance(stmt, (ast.If, ast.For, ast.While, ast.AsyncFor)):
            # Structural increment + nesting penalty
            score += 1 + nesting
            # Recurse into body at deeper nesting
            score += _cognitive_visit_body(stmt.body, nesting + 1)
            # Handle else/elif
            if stmt.orelse:
                if len(stmt.orelse) == 1 and isinstance(stmt.orelse[0], ast.If):
                    # elif: +1 structural, no extra nesting penalty
                    score += 1
                    elif_node = stmt.orelse[0]
                    score += _cognitive_visit_body(elif_node.body, nesting + 1)
                    # Recurse elif's orelse
                    if elif_node.orelse:
                        if len(elif_node.orelse) == 1 and isinstance(elif_node.orelse[0], ast.If):
                            score += _cognitive_visit_body([elif_node.orelse[0]], nesting)
                        else:
                            score += 1  # else
                            score += _cognitive_visit_body(elif_node.orelse, nesting + 1)
                else:
                    # else clause
                    score += 1
                    score += _cognitive_visit_body(stmt.orelse, nesting + 1)

        elif isinstance(stmt, ast.Try):
            score += _cognitive_visit_body(stmt.body, nesting)
            for handler in (stmt.handlers or []):
                score += 1 + nesting
                score += _cognitive_visit_body(handler.body, nesting + 1)
            score += _cognitive_visit_body(stmt.orelse or [], nesting)
            score += _cognitive_visit_body(stmt.finalbody or [], nesting)

        elif isinstance(stmt, (ast.With, ast.AsyncWith)):
            score += 1 + nesting
            score += _cognitive_visit_body(stmt.body, nesting + 1)

        elif isinstance(stmt, (ast.Break, ast.Continue)):
            score += 1

        elif isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Nested function increases nesting for its body
            score += _cognitive_visit_body(stmt.body, nesting + 1)

        elif isinstance(stmt, ast.Expr):
            # Check for BoolOp in expressions
            if isinstance(stmt.value, ast.BoolOp):
                score += 1

        elif isinstance(stmt, (ast.Assign, ast.Return, ast.AugAssign)):
            # Check for BoolOp/IfExp in value
            val = getattr(stmt, "value", None)
            if isinstance(val, ast.BoolOp):
                score += 1
            elif isinstance(val, ast.IfExp):
                score += 1 + nesting

    return score


async def analyze_file_complexity(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    file_path: str,
    source_code: str,
    threshold: float = 10.0,
) -> list[ComplexityMetric]:
    """Compute cyclomatic + cognitive complexity for all functions and persist."""
    from sqlalchemy import delete as sa_delete
    await db.execute(
        sa_delete(ComplexityMetric).where(
            ComplexityMetric.project_id == project_id,
            ComplexityMetric.file_path == file_path,
        )
    )

    cyclomatic_fns = _compute_cyclomatic_complexity(source_code)
    cognitive_fns = _compute_cognitive_complexity(source_code)
    loc = len(source_code.split("\n"))

    metrics: list[ComplexityMetric] = []

    # Cyclomatic per function
    for fn in cyclomatic_fns:
        m = ComplexityMetric(
            project_id=project_id,
            file_path=file_path,
            function_name=fn["function_name"],
            metric_type=MetricType.CYCLOMATIC,
            value=fn["complexity"],
            threshold=threshold,
            exceeds_threshold=fn["complexity"] > threshold,
        )
        db.add(m)
        metrics.append(m)

    # Cognitive per function
    for fn in cognitive_fns:
        m = ComplexityMetric(
            project_id=project_id,
            file_path=file_path,
            function_name=fn["function_name"],
            metric_type=MetricType.COGNITIVE,
            value=fn["complexity"],
            threshold=threshold,
            exceeds_threshold=fn["complexity"] > threshold,
        )
        db.add(m)
        metrics.append(m)

    # File-level LOC metric
    loc_metric = ComplexityMetric(
        project_id=project_id,
        file_path=file_path,
        function_name=None,
        metric_type=MetricType.LINES_OF_CODE,
        value=float(loc),
        threshold=None,
        exceeds_threshold=False,
    )
    db.add(loc_metric)
    metrics.append(loc_metric)

    # Function count metric
    fn_count = ComplexityMetric(
        project_id=project_id,
        file_path=file_path,
        function_name=None,
        metric_type=MetricType.FUNCTION_COUNT,
        value=float(len(cyclomatic_fns)),
        threshold=None,
        exceeds_threshold=False,
    )
    db.add(fn_count)
    metrics.append(fn_count)

    await db.flush()
    return metrics


async def get_complexity_hotspots(
    db: AsyncSession,
    project_id: uuid.UUID,
    *,
    metric_type: MetricType = MetricType.CYCLOMATIC,
    exceeds_only: bool = True,
    limit: int = 20,
    since_days: int | None = None,
) -> list[ComplexityMetric]:
    """Get functions/files with highest complexity.

    FM-188: Optional since_days filter for trend tracking across snapshots.
    """
    query = select(ComplexityMetric).where(
        ComplexityMetric.project_id == project_id,
        ComplexityMetric.metric_type == metric_type,
    )
    if exceeds_only:
        query = query.where(ComplexityMetric.exceeds_threshold.is_(True))
    if since_days is not None:
        from datetime import datetime, timedelta, timezone
        cutoff = datetime.now(timezone.utc) - timedelta(days=since_days)
        query = query.where(ComplexityMetric.snapshot_date >= cutoff)

    result = await db.execute(
        query.order_by(ComplexityMetric.value.desc()).limit(limit)
    )
    return list(result.scalars().all())


async def get_complexity_summary(
    db: AsyncSession,
    project_id: uuid.UUID,
) -> dict[str, Any]:
    """Summary stats for complexity metrics."""
    from sqlalchemy import case as sa_case
    result = await db.execute(
        select(
            sa_func.count(ComplexityMetric.id).label("total_metrics"),
            sa_func.avg(ComplexityMetric.value).label("avg_complexity"),
            sa_func.max(ComplexityMetric.value).label("max_complexity"),
            sa_func.sum(
                sa_case(
                    (ComplexityMetric.exceeds_threshold == True, 1),  # noqa: E712
                    else_=0,
                )
            ).label("exceeds_count"),
        ).where(
            ComplexityMetric.project_id == project_id,
            ComplexityMetric.metric_type == MetricType.CYCLOMATIC,
        )
    )
    row = result.one()
    return {
        "project_id": str(project_id),
        "total_functions": row.total_metrics or 0,
        "avg_cyclomatic": round(float(row.avg_complexity or 0), 2),
        "max_cyclomatic": float(row.max_complexity or 0),
        "exceeds_threshold_count": int(row.exceeds_count or 0),
    }
