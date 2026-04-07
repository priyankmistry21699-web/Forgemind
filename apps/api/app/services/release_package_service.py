"""FM-131: Release package service — generation, CRUD, and lifecycle."""

from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.artifact import Artifact
from app.models.execution_checkpoint import ExecutionCheckpoint
from app.models.release_ops import ReleasePackage, ReleaseStatus
from app.models.run import Run
from app.models.task import Task, TaskStatus
from app.schemas.release_ops import ReleasePackageCreate, ReleasePackageUpdate
from app.services import release_confidence_service

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------


async def create_release_package(
    db: AsyncSession,
    *,
    run_id: uuid.UUID,
    project_id: uuid.UUID,
    data: ReleasePackageCreate,
) -> ReleasePackage:
    """Create a new release package for a run."""
    # Build artifact manifest from run artifacts
    manifest = data.artifact_manifest
    if manifest is None:
        manifest = await _build_artifact_manifest(db, run_id)

    # Build changelog from run events/tasks
    changelog = data.changelog
    if changelog is None:
        changelog = await _build_changelog(db, run_id)

    # Snapshot confidence at creation time
    confidence = await release_confidence_service.compute_release_confidence(db, run_id)

    pkg = ReleasePackage(
        project_id=project_id,
        run_id=run_id,
        version=data.version,
        status=ReleaseStatus.DRAFT,
        summary=data.summary,
        artifact_manifest=manifest,
        changelog=changelog,
        confidence_snapshot=confidence,
        target_environment_id=data.target_environment_id,
        created_by=data.created_by,
    )
    db.add(pkg)
    await db.flush()
    logger.info("Created release package %s (v%s) for run %s", pkg.id, pkg.version, run_id)
    return pkg


async def get_release_package(
    db: AsyncSession,
    package_id: uuid.UUID,
) -> ReleasePackage | None:
    result = await db.execute(
        select(ReleasePackage).where(ReleasePackage.id == package_id)
    )
    return result.scalar_one_or_none()


async def list_release_packages(
    db: AsyncSession,
    run_id: uuid.UUID,
) -> list[ReleasePackage]:
    result = await db.execute(
        select(ReleasePackage)
        .where(ReleasePackage.run_id == run_id)
        .order_by(ReleasePackage.created_at.desc())
    )
    return list(result.scalars().all())


async def list_project_releases(
    db: AsyncSession,
    project_id: uuid.UUID,
) -> list[ReleasePackage]:
    result = await db.execute(
        select(ReleasePackage)
        .where(ReleasePackage.project_id == project_id)
        .order_by(ReleasePackage.created_at.desc())
    )
    return list(result.scalars().all())


async def update_release_package(
    db: AsyncSession,
    package_id: uuid.UUID,
    data: ReleasePackageUpdate,
) -> ReleasePackage | None:
    pkg = await get_release_package(db, package_id)
    if pkg is None:
        return None

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(pkg, field, value)

    await db.flush()
    await db.refresh(pkg)
    return pkg


# ---------------------------------------------------------------------------
# Generation helpers
# ---------------------------------------------------------------------------


async def _build_artifact_manifest(
    db: AsyncSession,
    run_id: uuid.UUID,
) -> dict[str, Any]:
    """Build an artifact manifest from all run artifacts."""
    result = await db.execute(
        select(Artifact).where(Artifact.run_id == run_id)
    )
    artifacts = list(result.scalars().all())

    by_type: dict[str, list[dict]] = {}
    for a in artifacts:
        entry = {
            "id": str(a.id),
            "title": a.title,
            "version": a.version,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        by_type.setdefault(a.artifact_type.value, []).append(entry)

    return {
        "total_artifacts": len(artifacts),
        "by_type": by_type,
        "has_spec": bool(by_type.get("spec")),
        "has_plan": bool(by_type.get("plan")),
        "has_implementation": bool(by_type.get("implementation")),
    }


async def _build_changelog(
    db: AsyncSession,
    run_id: uuid.UUID,
) -> dict[str, Any]:
    """Build a changelog summary from completed tasks."""
    result = await db.execute(
        select(Task).where(Task.run_id == run_id).order_by(Task.order_index)
    )
    tasks = list(result.scalars().all())

    entries = []
    for t in tasks:
        if t.status == TaskStatus.COMPLETED:
            entries.append({
                "task_id": str(t.id),
                "title": t.title,
                "task_type": t.task_type,
                "agent": t.assigned_agent_slug,
            })

    return {
        "total_changes": len(entries),
        "entries": entries,
    }


async def generate_release_package(
    db: AsyncSession,
    *,
    run_id: uuid.UUID,
    project_id: uuid.UUID,
    version: str | None = None,
) -> ReleasePackage:
    """Auto-generate a release package from run state.

    Captures artifact manifest, changelog, confidence snapshot,
    and rollback metadata in a single operation.
    """
    run_result = await db.execute(select(Run).where(Run.id == run_id))
    run = run_result.scalar_one_or_none()
    if run is None:
        raise ValueError(f"Run {run_id} not found")

    if version is None:
        count_result = await db.execute(
            select(func.count(ReleasePackage.id)).where(
                ReleasePackage.project_id == project_id
            )
        )
        count = count_result.scalar() or 0
        version = f"0.{count + 1}.0"

    # Build rollback metadata
    rollback = await _build_rollback_metadata(db, run_id)

    data = ReleasePackageCreate(
        version=version,
        summary=f"Release package generated from run #{run.run_number}",
        created_by="system",
    )

    pkg = await create_release_package(
        db, run_id=run_id, project_id=project_id, data=data
    )
    pkg.rollback_metadata = rollback
    await db.flush()
    return pkg


async def _build_rollback_metadata(
    db: AsyncSession,
    run_id: uuid.UUID,
) -> dict[str, Any]:
    """Build rollback recovery metadata from checkpoints."""
    result = await db.execute(
        select(ExecutionCheckpoint)
        .where(ExecutionCheckpoint.run_id == run_id)
        .order_by(ExecutionCheckpoint.sequence_number.desc())
    )
    checkpoints = list(result.scalars().all())

    if not checkpoints:
        return {
            "has_rollback_points": False,
            "checkpoint_count": 0,
            "latest_checkpoint": None,
        }

    latest = checkpoints[0]
    return {
        "has_rollback_points": True,
        "checkpoint_count": len(checkpoints),
        "latest_checkpoint": {
            "id": str(latest.id),
            "type": latest.checkpoint_type.value,
            "sequence": latest.sequence_number,
            "summary": latest.summary,
            "created_at": latest.created_at.isoformat() if latest.created_at else None,
        },
        "rollback_chain": [
            {
                "id": str(cp.id),
                "type": cp.checkpoint_type.value,
                "sequence": cp.sequence_number,
            }
            for cp in checkpoints[:5]
        ],
    }
