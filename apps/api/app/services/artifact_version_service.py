"""Artifact versioning service — version history, diff, and tagging.

FM-168: Track artifact versions over time, compute text diffs,
and support version tagging.
"""

import uuid
import difflib
import logging

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.artifact import Artifact

logger = logging.getLogger(__name__)


async def get_version_history(
    db: AsyncSession,
    artifact_id: uuid.UUID,
) -> list[Artifact]:
    """Get the full version chain for an artifact.

    Walks up the parent_version_id chain to find all versions,
    then returns them sorted by version number ascending.
    """
    # Get the starting artifact
    result = await db.execute(
        select(Artifact).where(Artifact.id == artifact_id)
    )
    artifact = result.scalar_one_or_none()
    if not artifact:
        return []

    # Find all artifacts with the same title, project, and type — these form a version chain
    # Also include any linked via parent_version_id
    chain = await db.execute(
        select(Artifact).where(
            and_(
                Artifact.project_id == artifact.project_id,
                Artifact.title == artifact.title,
                Artifact.artifact_type == artifact.artifact_type,
            )
        ).order_by(Artifact.version.asc(), Artifact.created_at.asc())
    )
    return list(chain.scalars().all())


async def create_new_version(
    db: AsyncSession,
    parent_artifact_id: uuid.UUID,
    *,
    content: str,
    created_by: str | None = None,
    version_tag: str | None = None,
) -> Artifact | None:
    """Create a new version of an artifact, chaining from the parent."""
    result = await db.execute(
        select(Artifact).where(Artifact.id == parent_artifact_id)
    )
    parent = result.scalar_one_or_none()
    if not parent:
        return None

    new_version = Artifact(
        title=parent.title,
        artifact_type=parent.artifact_type,
        content=content,
        meta=parent.meta,
        version=parent.version + 1,
        parent_version_id=parent.id,
        version_tag=version_tag,
        project_id=parent.project_id,
        run_id=parent.run_id,
        task_id=parent.task_id,
        created_by=created_by or parent.created_by,
    )
    db.add(new_version)
    await db.flush()
    return new_version


async def diff_versions(
    db: AsyncSession,
    artifact_id: uuid.UUID,
    version_a: int,
    version_b: int,
) -> dict | None:
    """Compute a text diff between two versions of an artifact.

    Returns a dict with diff_lines, additions count, deletions count.
    """
    # Get the artifact to find its chain key
    result = await db.execute(
        select(Artifact).where(Artifact.id == artifact_id)
    )
    base = result.scalar_one_or_none()
    if not base:
        return None

    # Find version A
    va_result = await db.execute(
        select(Artifact).where(
            Artifact.project_id == base.project_id,
            Artifact.title == base.title,
            Artifact.artifact_type == base.artifact_type,
            Artifact.version == version_a,
        )
    )
    art_a = va_result.scalar_one_or_none()

    # Find version B
    vb_result = await db.execute(
        select(Artifact).where(
            Artifact.project_id == base.project_id,
            Artifact.title == base.title,
            Artifact.artifact_type == base.artifact_type,
            Artifact.version == version_b,
        )
    )
    art_b = vb_result.scalar_one_or_none()

    if not art_a or not art_b:
        return None

    text_a = (art_a.content or "").splitlines(keepends=True)
    text_b = (art_b.content or "").splitlines(keepends=True)

    diff = list(
        difflib.unified_diff(
            text_a,
            text_b,
            fromfile=f"v{version_a}",
            tofile=f"v{version_b}",
            lineterm="",
        )
    )

    additions = sum(1 for line in diff if line.startswith("+") and not line.startswith("+++"))
    deletions = sum(1 for line in diff if line.startswith("-") and not line.startswith("---"))

    return {
        "artifact_id": str(artifact_id),
        "version_a": version_a,
        "version_b": version_b,
        "diff_lines": diff,
        "additions": additions,
        "deletions": deletions,
    }


async def tag_version(
    db: AsyncSession,
    artifact_id: uuid.UUID,
    version_tag: str,
) -> Artifact | None:
    """Tag a specific artifact version."""
    result = await db.execute(
        select(Artifact).where(Artifact.id == artifact_id)
    )
    art = result.scalar_one_or_none()
    if not art:
        return None
    art.version_tag = version_tag
    await db.flush()
    return art
