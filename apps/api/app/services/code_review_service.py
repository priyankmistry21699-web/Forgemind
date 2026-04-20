"""Code review routing — CODEOWNERS-based reviewer suggestion and scoring.

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


async def suggest_reviewers(
    db: AsyncSession,
    repository_link_id: uuid.UUID,
    file_paths: list[str],
    *,
    max_reviewers: int = 5,
    exclude_user_ids: list[uuid.UUID] | None = None,
) -> list[dict]:
    """Suggest and rank reviewers for a set of changed files.

    Scoring algorithm:
    1. Match each file against CODEOWNERS rules for the repository.
    2. Count how many distinct files each owner covers (coverage breadth).
    3. Weight more-specific patterns higher (longer pattern = higher specificity).
    4. Compute a composite score = coverage_count * (1 + avg_specificity / 100).
    5. Deduplicate owners, sort descending by score, return top N.

    Args:
        repository_link_id: The repository to check ownership rules against.
        file_paths: List of changed file paths in the PR.
        max_reviewers: Maximum number of reviewers to suggest.
        exclude_user_ids: User IDs to exclude (e.g. the PR author).

    Returns:
        Ranked list of reviewer suggestions with scores and matched files.
    """
    if not file_paths:
        return []

    exclude_set = set(exclude_user_ids) if exclude_user_ids else set()

    # Fetch all ownership rules for the repo
    result = await db.execute(
        select(CodeOwnership).where(
            CodeOwnership.repository_link_id == repository_link_id
        )
    )
    rules = list(result.scalars().all())

    if not rules:
        return []

    # Build per-owner statistics
    # Key: (owner_user_id_str | None, owner_team_name | None)
    owner_files: dict[tuple, list[str]] = {}
    owner_specificities: dict[tuple, list[int]] = {}

    for fp in file_paths:
        for rule in rules:
            if fnmatch.fnmatch(fp, rule.file_pattern):
                owner_key = (
                    str(rule.owner_user_id) if rule.owner_user_id else None,
                    rule.owner_team_name,
                )

                # Skip excluded users
                if rule.owner_user_id and rule.owner_user_id in exclude_set:
                    continue

                if owner_key not in owner_files:
                    owner_files[owner_key] = []
                    owner_specificities[owner_key] = []

                if fp not in owner_files[owner_key]:
                    owner_files[owner_key].append(fp)
                owner_specificities[owner_key].append(len(rule.file_pattern))

    # Score and rank
    scored: list[dict] = []
    for owner_key, files in owner_files.items():
        coverage_count = len(files)
        specificities = owner_specificities[owner_key]
        avg_specificity = (
            sum(specificities) / len(specificities) if specificities else 0
        )
        score = round(coverage_count * (1 + avg_specificity / 100), 2)

        scored.append(
            {
                "owner_user_id": owner_key[0],
                "owner_team_name": owner_key[1],
                "coverage_count": coverage_count,
                "total_files": len(file_paths),
                "coverage_ratio": round(coverage_count / len(file_paths), 2),
                "avg_specificity": round(avg_specificity, 1),
                "score": score,
                "matched_files": files,
            }
        )

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:max_reviewers]
