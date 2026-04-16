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
    from sqlalchemy import case, literal_column

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


async def analyze_file_complexity(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    file_path: str,
    source_code: str,
    threshold: float = 10.0,
) -> list[ComplexityMetric]:
    """Compute complexity for all functions in a file and persist."""
    from sqlalchemy import delete as sa_delete
    await db.execute(
        sa_delete(ComplexityMetric).where(
            ComplexityMetric.project_id == project_id,
            ComplexityMetric.file_path == file_path,
        )
    )

    functions = _compute_cyclomatic_complexity(source_code)
    # Also count total lines
    loc = len(source_code.split("\n"))

    metrics: list[ComplexityMetric] = []
    for fn in functions:
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
        value=float(len(functions)),
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
) -> list[ComplexityMetric]:
    """Get functions/files with highest complexity."""
    query = select(ComplexityMetric).where(
        ComplexityMetric.project_id == project_id,
        ComplexityMetric.metric_type == metric_type,
    )
    if exceeds_only:
        query = query.where(ComplexityMetric.exceeds_threshold.is_(True))

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
