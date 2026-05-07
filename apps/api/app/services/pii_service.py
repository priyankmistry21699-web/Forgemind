"""FM-247: PII detection and masking service."""

from __future__ import annotations

import re
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.platform_ops import PIIPattern, PIIPatternType

# Built-in patterns seeded on first use
_BUILTIN_PATTERNS = [
    {"name": "email", "pattern": r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", "category": "email", "severity": "medium"},
    {"name": "ssn_us", "pattern": r"\b\d{3}-\d{2}-\d{4}\b", "category": "ssn", "severity": "high"},
    {"name": "credit_card", "pattern": r"\b(?:\d[ -]?){13,16}\b", "category": "credit_card", "severity": "critical"},
    {"name": "phone_us", "pattern": r"\b(?:\+1\s?)?\(?\d{3}\)?[\s.\-]?\d{3}[\s.\-]?\d{4}\b", "category": "phone", "severity": "medium"},
    {"name": "api_key_generic", "pattern": r"(?i)(api[_\-]?key|token|secret)['\"]?\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{20,}", "category": "api_key", "severity": "high"},
    {"name": "aws_access_key", "pattern": r"\bAKIA[0-9A-Z]{16}\b", "category": "api_key", "severity": "critical"},
    {"name": "private_key_header", "pattern": r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----", "category": "private_key", "severity": "critical"},
]


async def seed_builtin_patterns(db: AsyncSession) -> None:
    """Idempotently seed built-in PII patterns."""
    for p in _BUILTIN_PATTERNS:
        existing = await db.execute(
            select(PIIPattern).where(PIIPattern.name == p["name"])
        )
        if existing.scalar_one_or_none() is None:
            db.add(PIIPattern(
                name=p["name"],
                pattern_type=PIIPatternType.REGEX,
                pattern=p["pattern"],
                category=p["category"],
                severity=p["severity"],
            ))
    await db.flush()


async def scan_content(
    db: AsyncSession,
    content: str,
    *,
    mask: bool = False,
) -> dict[str, Any]:
    """Scan content for PII. Returns findings and optionally masked content."""
    result = await db.execute(
        select(PIIPattern).where(PIIPattern.enabled.is_(True))
    )
    patterns = list(result.scalars().all())

    findings: list[dict] = []
    masked = content

    for p in patterns:
        if p.pattern_type == PIIPatternType.REGEX:
            try:
                compiled = re.compile(p.pattern)
                matches = list(compiled.finditer(content))
                for m in matches:
                    findings.append({
                        "pattern": p.name,
                        "category": p.category,
                        "severity": p.severity,
                        "start": m.start(),
                        "end": m.end(),
                        "value_preview": content[m.start():m.start() + 4] + "***",
                    })
                if mask and matches:
                    masked = compiled.sub(f"[REDACTED:{p.category.upper()}]", masked)
            except re.error:
                continue

    return {
        "total_findings": len(findings),
        "findings": findings[:100],
        "has_critical": any(f["severity"] == "critical" for f in findings),
        "masked_content": masked if mask else None,
    }


async def scan_artifact(
    db: AsyncSession,
    artifact_id: uuid.UUID,
    *,
    mask: bool = False,
) -> dict[str, Any]:
    """Scan an artifact's content for PII."""
    from app.models.artifact import Artifact

    artifact = await db.get(Artifact, artifact_id)
    if artifact is None:
        return {"error": "Artifact not found"}

    result = await scan_content(db, artifact.content or "", mask=mask)
    result["artifact_id"] = str(artifact_id)
    return result
