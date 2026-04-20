"""Pattern Detection & Technical Debt services — FM-185/186.

FM-185: Configurable pattern rules + scanning for occurrences.
FM-186: Technical debt tracking with all 4 debt sources:
        comment, pattern, age, complexity.
"""

import ast
import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, func as sa_func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.code_intelligence import (
    PatternRule,
    PatternType,
    PatternSeverity,
    PatternOccurrence,
    DebtEntry,
    DebtType,
    DebtSnapshot,
)

logger = logging.getLogger(__name__)


# ── FM-185: Pattern Detection ────────────────────────────────────


async def create_pattern_rule(
    db: AsyncSession,
    *,
    name: str,
    pattern_type: PatternType,
    language: str = "python",
    rule_definition: str,
    severity: PatternSeverity = PatternSeverity.WARNING,
    description: str | None = None,
) -> PatternRule:
    """Create a configurable pattern detection rule."""
    rule = PatternRule(
        name=name,
        description=description,
        pattern_type=pattern_type,
        language=language,
        rule_definition=rule_definition,
        severity=severity,
    )
    db.add(rule)
    await db.flush()
    return rule


async def list_pattern_rules(
    db: AsyncSession,
    *,
    active_only: bool = True,
    language: str | None = None,
) -> list[PatternRule]:
    """List all pattern rules, optionally filtered."""
    query = select(PatternRule)
    if active_only:
        query = query.where(PatternRule.active.is_(True))
    if language:
        query = query.where(PatternRule.language == language)
    result = await db.execute(query.order_by(PatternRule.created_at.desc()))
    return list(result.scalars().all())


async def scan_file_for_patterns(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    file_path: str,
    source_code: str,
    rules: list[PatternRule] | None = None,
) -> list[PatternOccurrence]:
    """Scan source code against rules and record occurrences."""
    if rules is None:
        rules = await list_pattern_rules(db)

    # Clear old occurrences for this file
    await db.execute(
        delete(PatternOccurrence).where(
            PatternOccurrence.project_id == project_id,
            PatternOccurrence.file_path == file_path,
        )
    )

    lines = source_code.split("\n")
    occurrences: list[PatternOccurrence] = []

    for rule in rules:
        try:
            pattern = re.compile(rule.rule_definition, re.MULTILINE)
        except re.error:
            continue

        for i, line in enumerate(lines, start=1):
            if pattern.search(line):
                occ = PatternOccurrence(
                    project_id=project_id,
                    rule_id=rule.id,
                    file_path=file_path,
                    line_start=i,
                    line_end=i,
                    snippet=line.strip()[:500],
                )
                db.add(occ)
                occurrences.append(occ)

    await db.flush()

    # FM-185: Auto-create knowledge base entries for significant patterns
    await _create_kb_entries_for_significant_patterns(
        db,
        project_id=project_id,
        file_path=file_path,
        occurrences=occurrences,
        rules=rules,
    )

    return occurrences


# ── FM-185: Knowledge Base Integration ───────────────────────────

# Severity levels that trigger KB entry creation.
_KB_SIGNIFICANT_SEVERITIES = {PatternSeverity.CRITICAL, PatternSeverity.WARNING}


async def _create_kb_entries_for_significant_patterns(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    file_path: str,
    occurrences: list[PatternOccurrence],
    rules: list[PatternRule],
) -> list[Any]:
    """Create knowledge-base entries for high-severity pattern detections.

    Only CRITICAL and WARNING occurrences produce entries — INFO patterns
    are too noisy and best-practice / positive patterns are not issues.
    """
    from app.services import knowledge_service
    from app.models.project_knowledge import KnowledgeType

    rule_map = {r.id: r for r in rules}
    created: list[Any] = []

    # Group occurrences by rule to avoid duplicate KB entries per scan
    rule_occurrences: dict[uuid.UUID, list[PatternOccurrence]] = {}
    for occ in occurrences:
        rule_occurrences.setdefault(occ.rule_id, []).append(occ)

    for rule_id, occs in rule_occurrences.items():
        rule = rule_map.get(rule_id)
        if rule is None:
            continue
        if rule.severity not in _KB_SIGNIFICANT_SEVERITIES:
            continue
        if rule.pattern_type == PatternType.POSITIVE_PATTERN:
            continue  # positive patterns are not issues

        lines = ", ".join(str(o.line_start) for o in occs[:10])
        snippet_sample = occs[0].snippet if occs else ""

        entry = await knowledge_service.create_knowledge(
            db,
            project_id=project_id,
            knowledge_type=KnowledgeType.PATTERN,
            title=f"Pattern detected: {rule.name} in {file_path}",
            content=(
                f"Rule '{rule.name}' ({rule.severity.value}) matched "
                f"{len(occs)} time(s) in {file_path} at line(s) {lines}.\n"
                f"Description: {rule.description or 'N/A'}\n"
                f"Sample: {snippet_sample}"
            ),
            tags=["pattern-detection", rule.severity.value, rule.name],
            metadata={
                "rule_id": str(rule_id),
                "rule_name": rule.name,
                "severity": rule.severity.value,
                "file_path": file_path,
                "occurrence_count": len(occs),
            },
        )
        created.append(entry)

    return created


async def get_pattern_occurrences(
    db: AsyncSession,
    project_id: uuid.UUID,
    *,
    rule_id: uuid.UUID | None = None,
    file_path: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> tuple[list[PatternOccurrence], int]:
    """List detected pattern occurrences with filters."""
    query = select(PatternOccurrence).where(PatternOccurrence.project_id == project_id)
    if rule_id:
        query = query.where(PatternOccurrence.rule_id == rule_id)
    if file_path:
        query = query.where(PatternOccurrence.file_path == file_path)

    count_q = select(sa_func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar_one()

    result = await db.execute(
        query.order_by(PatternOccurrence.detected_at.desc()).offset(offset).limit(limit)
    )
    return list(result.scalars().all()), total


# ── FM-186: Technical Debt Tracking ──────────────────────────────


_DEBT_MARKERS = re.compile(r"\b(TODO|FIXME|HACK|XXX|DEPRECATED)\b", re.IGNORECASE)

DEBT_MARKER_SCORE: dict[str, float] = {
    "todo": 1.0,
    "fixme": 2.0,
    "hack": 3.0,
    "xxx": 2.5,
    "deprecated": 1.5,
}


async def scan_file_for_debt(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    file_path: str,
    source_code: str,
) -> list[DebtEntry]:
    """Scan source for TODO/FIXME/HACK markers and record as debt."""
    # Clear old entries for this file
    await db.execute(
        delete(DebtEntry).where(
            DebtEntry.project_id == project_id,
            DebtEntry.file_path == file_path,
        )
    )

    lines = source_code.split("\n")
    entries: list[DebtEntry] = []

    for i, line in enumerate(lines, start=1):
        match = _DEBT_MARKERS.search(line)
        if match:
            marker = match.group(1).lower()
            entry = DebtEntry(
                project_id=project_id,
                file_path=file_path,
                debt_type=DebtType.COMMENT,
                description=line.strip()[:500],
                score=DEBT_MARKER_SCORE.get(marker, 1.0),
                line_number=i,
            )
            db.add(entry)
            entries.append(entry)

    await db.flush()
    return entries


async def scan_file_for_pattern_debt(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    file_path: str,
) -> list[DebtEntry]:
    """Scan PatternOccurrences for a file and create PATTERN debt entries.

    Maps anti-pattern occurrences detected by FM-185 into the debt ledger.
    Severity-based scoring: CRITICAL=5, WARNING=3, INFO=1.
    """
    SEVERITY_SCORE = {
        PatternSeverity.CRITICAL: 5.0,
        PatternSeverity.WARNING: 3.0,
        PatternSeverity.INFO: 1.0,
    }

    # Remove existing pattern debt for the file
    await db.execute(
        delete(DebtEntry).where(
            DebtEntry.project_id == project_id,
            DebtEntry.file_path == file_path,
            DebtEntry.debt_type == DebtType.PATTERN,
        )
    )

    # Join occurrences with their rule to get severity
    query = (
        select(PatternOccurrence, PatternRule)
        .join(PatternRule, PatternOccurrence.rule_id == PatternRule.id)
        .where(
            PatternOccurrence.project_id == project_id,
            PatternOccurrence.file_path == file_path,
        )
    )
    result = await db.execute(query)
    rows = result.all()

    entries: list[DebtEntry] = []
    for occ, rule in rows:
        score = SEVERITY_SCORE.get(rule.severity, 1.0) if rule.severity else 1.0
        entry = DebtEntry(
            project_id=project_id,
            file_path=file_path,
            debt_type=DebtType.PATTERN,
            description=f"Pattern [{rule.name}]: {occ.snippet or ''}".strip()[:500],
            score=score,
            line_number=occ.line_start,
        )
        db.add(entry)
        entries.append(entry)

    await db.flush()
    return entries


async def scan_file_for_age_debt(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    file_path: str,
    source_code: str,
    last_modified: datetime | None = None,
    age_threshold_days: int = 180,
) -> list[DebtEntry]:
    """Create AGE debt entry if a file hasn't been modified recently.

    Files not modified within age_threshold_days get an age-based debt
    entry with score proportional to how old they are.
    """
    # Remove existing age debt for the file
    await db.execute(
        delete(DebtEntry).where(
            DebtEntry.project_id == project_id,
            DebtEntry.file_path == file_path,
            DebtEntry.debt_type == DebtType.AGE,
        )
    )

    if last_modified is None:
        return []

    now = datetime.now(timezone.utc)
    if last_modified.tzinfo is None:
        last_modified = last_modified.replace(tzinfo=timezone.utc)

    age_days = (now - last_modified).days
    if age_days < age_threshold_days:
        return []

    # Score scales with age: base 1.0 + 0.5 per 90 days beyond threshold
    extra = (age_days - age_threshold_days) / 90
    score = round(1.0 + extra * 0.5, 2)
    lines = source_code.count("\n") + 1

    entry = DebtEntry(
        project_id=project_id,
        file_path=file_path,
        debt_type=DebtType.AGE,
        description=f"File not modified in {age_days} days ({lines} lines)",
        score=min(score, 10.0),  # cap at 10
        line_number=None,
    )
    db.add(entry)
    await db.flush()
    return [entry]


async def scan_file_for_complexity_debt(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    file_path: str,
    source_code: str,
    complexity_threshold: float = 10.0,
) -> list[DebtEntry]:
    """Create COMPLEXITY debt entries for overly complex functions.

    Parses the file's AST to compute cyclomatic complexity per function,
    then creates debt entries for functions exceeding the threshold.
    """
    # Remove existing complexity debt for the file
    await db.execute(
        delete(DebtEntry).where(
            DebtEntry.project_id == project_id,
            DebtEntry.file_path == file_path,
            DebtEntry.debt_type == DebtType.COMPLEXITY,
        )
    )

    entries: list[DebtEntry] = []
    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        return entries

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            complexity = _compute_cyclomatic(node)
            if complexity >= complexity_threshold:
                score = round((complexity - complexity_threshold) * 0.5 + 2.0, 2)
                entry = DebtEntry(
                    project_id=project_id,
                    file_path=file_path,
                    debt_type=DebtType.COMPLEXITY,
                    description=f"Function '{node.name}' has cyclomatic complexity {complexity}",
                    score=min(score, 10.0),
                    line_number=node.lineno,
                )
                db.add(entry)
                entries.append(entry)

    await db.flush()
    return entries


def _compute_cyclomatic(node: ast.AST) -> int:
    """Compute cyclomatic complexity for a single AST node."""
    complexity = 1
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
            complexity += 1
        elif isinstance(child, ast.ExceptHandler):
            complexity += 1
        elif isinstance(child, ast.BoolOp):
            complexity += len(child.values) - 1
        elif isinstance(child, ast.Assert):
            complexity += 1
    return complexity


async def scan_file_for_all_debt(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    file_path: str,
    source_code: str,
    last_modified: datetime | None = None,
    age_threshold_days: int = 180,
    complexity_threshold: float = 10.0,
) -> list[DebtEntry]:
    """Run all 4 debt scanners on a file.

    Returns the combined list of debt entries from comment markers,
    pattern occurrences, file age, and function complexity.
    """
    entries: list[DebtEntry] = []

    # 1. Comment markers (TODO/FIXME/HACK)
    entries.extend(
        await scan_file_for_debt(
            db,
            project_id=project_id,
            file_path=file_path,
            source_code=source_code,
        )
    )

    # 2. Pattern-based debt (from FM-185 PatternOccurrence)
    entries.extend(
        await scan_file_for_pattern_debt(
            db,
            project_id=project_id,
            file_path=file_path,
        )
    )

    # 3. Age-based debt
    entries.extend(
        await scan_file_for_age_debt(
            db,
            project_id=project_id,
            file_path=file_path,
            source_code=source_code,
            last_modified=last_modified,
            age_threshold_days=age_threshold_days,
        )
    )

    # 4. Complexity-based debt
    entries.extend(
        await scan_file_for_complexity_debt(
            db,
            project_id=project_id,
            file_path=file_path,
            source_code=source_code,
            complexity_threshold=complexity_threshold,
        )
    )

    return entries


async def list_debt_entries(
    db: AsyncSession,
    project_id: uuid.UUID,
    *,
    debt_type: DebtType | None = None,
    file_path: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> tuple[list[DebtEntry], int]:
    """List debt entries with optional filters."""
    query = select(DebtEntry).where(DebtEntry.project_id == project_id)
    if debt_type:
        query = query.where(DebtEntry.debt_type == debt_type)
    if file_path:
        query = query.where(DebtEntry.file_path == file_path)

    total = (
        await db.execute(select(sa_func.count()).select_from(query.subquery()))
    ).scalar_one()

    result = await db.execute(
        query.order_by(DebtEntry.score.desc()).offset(offset).limit(limit)
    )
    return list(result.scalars().all()), total


async def get_debt_summary(
    db: AsyncSession,
    project_id: uuid.UUID,
) -> dict[str, Any]:
    """Aggregate debt score and entry count."""
    result = await db.execute(
        select(
            sa_func.count(DebtEntry.id).label("entry_count"),
            sa_func.coalesce(sa_func.sum(DebtEntry.score), 0.0).label("total_score"),
        ).where(DebtEntry.project_id == project_id)
    )
    row = result.one()
    return {
        "project_id": str(project_id),
        "entry_count": row.entry_count,
        "total_score": round(float(row.total_score), 2),
    }


async def take_debt_snapshot(
    db: AsyncSession,
    project_id: uuid.UUID,
) -> DebtSnapshot:
    """Take a point-in-time debt snapshot for trend tracking."""
    summary = await get_debt_summary(db, project_id)

    # Breakdown by type
    type_q = (
        select(
            DebtEntry.debt_type,
            sa_func.count(DebtEntry.id).label("count"),
            sa_func.sum(DebtEntry.score).label("score"),
        )
        .where(DebtEntry.project_id == project_id)
        .group_by(DebtEntry.debt_type)
    )
    rows = (await db.execute(type_q)).all()
    breakdown = {
        row.debt_type.value
        if hasattr(row.debt_type, "value")
        else str(row.debt_type): {
            "count": row.count,
            "score": round(float(row.score or 0), 2),
        }
        for row in rows
    }

    snap = DebtSnapshot(
        project_id=project_id,
        total_score=summary["total_score"],
        entry_count=summary["entry_count"],
        breakdown=breakdown,
    )
    db.add(snap)
    await db.flush()
    return snap


# ── FM-185: Built-in Pattern Rules ───────────────────────────────

BUILTIN_RULES: list[dict[str, str]] = [
    {
        "name": "bare-except",
        "rule_definition": r"except\s*:",
        "severity": "warning",
        "description": "Bare except catches all exceptions including SystemExit/KeyboardInterrupt",
    },
    {
        "name": "print-statement",
        "rule_definition": r"\bprint\s*\(",
        "severity": "info",
        "description": "print() in production code; prefer logging",
    },
    {
        "name": "hardcoded-password",
        "rule_definition": r"(?i)(password|secret|token)\s*=\s*['\"][^'\"]+['\"]",
        "severity": "critical",
        "description": "Hardcoded credential in source code",
    },
    {
        "name": "star-import",
        "rule_definition": r"from\s+\S+\s+import\s+\*",
        "severity": "warning",
        "description": "Wildcard import pollutes namespace",
    },
    {
        "name": "todo-without-ticket",
        "rule_definition": r"#\s*TODO(?!\s*\()",
        "severity": "info",
        "description": "TODO comment without a ticket reference",
    },
    {
        "name": "magic-number",
        "rule_definition": r"(?<!=)\s\b(?:[2-9]\d{2,}|[1-9]\d{3,})\b(?!\s*[=:])",
        "severity": "info",
        "description": "Large literal number; consider named constant",
    },
    {
        "name": "mutable-default-arg",
        "rule_definition": r"def\s+\w+\([^)]*(?:\[\]|\{\})\s*(?:,|\))",
        "severity": "warning",
        "description": "Mutable default argument (list/dict)",
    },
    {
        "name": "assert-in-production",
        "rule_definition": r"^\s*assert\s+",
        "severity": "warning",
        "description": "assert statements are stripped with -O; use explicit checks",
    },
    # --- positive-pattern rules ---
    {
        "name": "type-annotations",
        "pattern_type": "positive_pattern",
        "rule_definition": r"def\s+\w+\([^)]*:\s*\w+",
        "severity": "info",
        "description": "Function uses type annotations for parameters",
    },
    {
        "name": "logging-usage",
        "pattern_type": "positive_pattern",
        "rule_definition": r"logger\.\w+\(|logging\.\w+\(",
        "severity": "info",
        "description": "Proper logging framework used instead of print()",
    },
    {
        "name": "context-manager",
        "pattern_type": "positive_pattern",
        "rule_definition": r"\bwith\s+\w+",
        "severity": "info",
        "description": "Context manager used for resource management",
    },
]


async def seed_builtin_rules(
    db: AsyncSession,
    *,
    language: str = "python",
) -> list[PatternRule]:
    """Seed built-in pattern detection rules (idempotent).

    Only creates rules whose names don't already exist.
    """
    existing_q = await db.execute(select(PatternRule.name))
    existing_names = set(r[0] for r in existing_q.all())

    created: list[PatternRule] = []
    for defn in BUILTIN_RULES:
        if defn["name"] in existing_names:
            continue
        rule = PatternRule(
            name=defn["name"],
            description=defn.get("description"),
            pattern_type=PatternType(defn.get("pattern_type", "anti_pattern")),
            language=language,
            rule_definition=defn["rule_definition"],
            severity=PatternSeverity(defn["severity"]),
        )
        db.add(rule)
        created.append(rule)

    if created:
        await db.flush()
    return created


# ── FM-186: Debt Budget Threshold Warning ────────────────────────


async def check_debt_budget(
    db: AsyncSession,
    project_id: uuid.UUID,
    *,
    score_threshold: float = 50.0,
) -> dict[str, Any]:
    """Check if project debt exceeds a configurable budget threshold.

    Returns warning info when total_score >= score_threshold.
    """
    summary = await get_debt_summary(db, project_id)
    total = summary["total_score"]
    exceeded = total >= score_threshold

    return {
        "project_id": str(project_id),
        "total_score": total,
        "entry_count": summary["entry_count"],
        "threshold": score_threshold,
        "exceeded": exceeded,
        "severity": "critical"
        if total >= score_threshold * 2
        else ("warning" if exceeded else "ok"),
    }
