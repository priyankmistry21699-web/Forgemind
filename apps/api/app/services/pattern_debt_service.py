"""Pattern Detection & Technical Debt services — FM-185/186.

FM-185: Configurable pattern rules + scanning for occurrences.
FM-186: Technical debt tracking with trend snapshots.
"""

import logging
import re
import uuid
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
    return occurrences


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
    query = select(PatternOccurrence).where(
        PatternOccurrence.project_id == project_id
    )
    if rule_id:
        query = query.where(PatternOccurrence.rule_id == rule_id)
    if file_path:
        query = query.where(PatternOccurrence.file_path == file_path)

    count_q = select(sa_func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar_one()

    result = await db.execute(
        query.order_by(PatternOccurrence.detected_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return list(result.scalars().all()), total


# ── FM-186: Technical Debt Tracking ──────────────────────────────


_DEBT_MARKERS = re.compile(
    r"\b(TODO|FIXME|HACK|XXX|DEPRECATED)\b", re.IGNORECASE
)

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
        row.debt_type.value if hasattr(row.debt_type, 'value') else str(row.debt_type): {
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
