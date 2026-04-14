"""Code review routing — CODEOWNERS-based reviewer suggestion.

FM-157: Code Review Routing.
"""

import uuid
import fnmatch

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.github_integration import CodeOwnership


async def get_owners_for_files(
    db: AsyncSession,
    repository_link_id: uuid.UUID,
    file_paths: list[str],
) -> list[dict]:
    """Return matching code owners for a list of changed file paths."""
    result = await db.execute(
        select(CodeOwnership).where(
            CodeOwnership.repository_link_id == repository_link_id
        )
    )
    rules = list(result.scalars().all())

    matches: list[dict] = []
    seen: set[str] = set()
    for fp in file_paths:
        for rule in rules:
            if fnmatch.fnmatch(fp, rule.file_pattern):
                key = f"{rule.owner_user_id or rule.owner_team_name}:{fp}"
                if key not in seen:
                    seen.add(key)
                    matches.append(
                        {
                            "file": fp,
                            "pattern": rule.file_pattern,
                            "owner_user_id": (
                                str(rule.owner_user_id) if rule.owner_user_id else None
                            ),
                            "owner_team_name": rule.owner_team_name,
                        }
                    )
    return matches


async def upsert_ownership_rule(
    db: AsyncSession,
    repository_link_id: uuid.UUID,
    file_pattern: str,
    owner_user_id: uuid.UUID | None = None,
    owner_team_name: str | None = None,
) -> CodeOwnership:
    existing = await db.execute(
        select(CodeOwnership).where(
            CodeOwnership.repository_link_id == repository_link_id,
            CodeOwnership.file_pattern == file_pattern,
        )
    )
    rule = existing.scalar_one_or_none()
    if rule:
        rule.owner_user_id = owner_user_id
        rule.owner_team_name = owner_team_name
    else:
        rule = CodeOwnership(
            repository_link_id=repository_link_id,
            file_pattern=file_pattern,
            owner_user_id=owner_user_id,
            owner_team_name=owner_team_name,
        )
        db.add(rule)
    await db.flush()
    await db.refresh(rule)
    return rule
