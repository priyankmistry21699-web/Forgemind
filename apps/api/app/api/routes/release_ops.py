"""FM-131–137: Release operations routes.

Endpoints for release packages, environments, deployment readiness,
release gates, rollback readiness, post-release reports, and operational timeline.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user_id
from app.db.session import get_db
from app.models.release_ops import ReleaseStatus
from app.models.run import Run
from app.schemas.release_ops import (
    EnvironmentCreate,
    EnvironmentList,
    EnvironmentRead,
    EnvironmentUpdate,
    GateResultList,
    ReleasePackageCreate,
    ReleasePackageList,
    ReleasePackageRead,
    ReleasePackageUpdate,
)
from app.services import (
    deployment_readiness_service,
    environment_service,
    operational_timeline_service,
    post_release_service,
    release_gate_service,
    release_package_service,
    rollback_readiness_service,
)
from app.services.authz_service import Action, check_project_permission
from sqlalchemy import select

router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _resolve_project_for_run(
    db: AsyncSession,
    run_id: uuid.UUID,
) -> uuid.UUID:
    result = await db.execute(select(Run.project_id).where(Run.id == run_id))
    row = result.first()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found",
        )
    return row[0]


# ---------------------------------------------------------------------------
# FM-131: Release Packages
# ---------------------------------------------------------------------------


@router.post(
    "/runs/{run_id}/release-packages",
    status_code=status.HTTP_201_CREATED,
    response_model=ReleasePackageRead,
    tags=["release-ops"],
)
async def create_release_package(
    run_id: uuid.UUID,
    body: ReleasePackageCreate,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    pid = await _resolve_project_for_run(db, run_id)
    await check_project_permission(db, pid, user_id, Action.PROJECT_UPDATE)

    pkg = await release_package_service.create_release_package(
        db, run_id=run_id, project_id=pid, data=body
    )
    await db.commit()
    return pkg


@router.post(
    "/runs/{run_id}/release-packages/generate",
    status_code=status.HTTP_201_CREATED,
    response_model=ReleasePackageRead,
    tags=["release-ops"],
)
async def generate_release_package(
    run_id: uuid.UUID,
    version: str | None = None,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Auto-generate a release package from run state."""
    pid = await _resolve_project_for_run(db, run_id)
    await check_project_permission(db, pid, user_id, Action.PROJECT_UPDATE)

    try:
        pkg = await release_package_service.generate_release_package(
            db, run_id=run_id, project_id=pid, version=version
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    await db.commit()
    return pkg


@router.get(
    "/runs/{run_id}/release-packages",
    response_model=ReleasePackageList,
    tags=["release-ops"],
)
async def list_release_packages(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    pid = await _resolve_project_for_run(db, run_id)
    await check_project_permission(db, pid, user_id, Action.PROJECT_VIEW)

    items = await release_package_service.list_release_packages(db, run_id)
    return ReleasePackageList(items=items, total=len(items))


@router.get(
    "/release-packages/{package_id}",
    response_model=ReleasePackageRead,
    tags=["release-ops"],
)
async def get_release_package(
    package_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    pkg = await release_package_service.get_release_package(db, package_id)
    if pkg is None:
        raise HTTPException(status_code=404, detail="Release package not found")
    await check_project_permission(db, pkg.project_id, user_id, Action.PROJECT_VIEW)
    return pkg


@router.patch(
    "/release-packages/{package_id}",
    response_model=ReleasePackageRead,
    tags=["release-ops"],
)
async def update_release_package(
    package_id: uuid.UUID,
    body: ReleasePackageUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    pkg = await release_package_service.get_release_package(db, package_id)
    if pkg is None:
        raise HTTPException(status_code=404, detail="Release package not found")
    await check_project_permission(db, pkg.project_id, user_id, Action.PROJECT_UPDATE)

    updated = await release_package_service.update_release_package(db, package_id, body)
    await db.commit()
    return updated


@router.get(
    "/projects/{project_id}/release-packages",
    response_model=ReleasePackageList,
    tags=["release-ops"],
)
async def list_project_releases(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    await check_project_permission(db, project_id, user_id, Action.PROJECT_VIEW)
    items = await release_package_service.list_project_releases(db, project_id)
    return ReleasePackageList(items=items, total=len(items))


# ---------------------------------------------------------------------------
# FM-132: Deployment Environments
# ---------------------------------------------------------------------------


@router.post(
    "/projects/{project_id}/environments",
    status_code=status.HTTP_201_CREATED,
    response_model=EnvironmentRead,
    tags=["release-ops"],
)
async def create_environment(
    project_id: uuid.UUID,
    body: EnvironmentCreate,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    await check_project_permission(db, project_id, user_id, Action.PROJECT_UPDATE)
    env = await environment_service.create_environment(
        db, project_id=project_id, data=body
    )
    await db.commit()
    return env


@router.get(
    "/projects/{project_id}/environments",
    response_model=EnvironmentList,
    tags=["release-ops"],
)
async def list_environments(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    await check_project_permission(db, project_id, user_id, Action.PROJECT_VIEW)
    items = await environment_service.list_environments(db, project_id)
    return EnvironmentList(items=items, total=len(items))


@router.get(
    "/environments/{environment_id}",
    response_model=EnvironmentRead,
    tags=["release-ops"],
)
async def get_environment(
    environment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    env = await environment_service.get_environment(db, environment_id)
    if env is None:
        raise HTTPException(status_code=404, detail="Environment not found")
    await check_project_permission(db, env.project_id, user_id, Action.PROJECT_VIEW)
    return env


@router.patch(
    "/environments/{environment_id}",
    response_model=EnvironmentRead,
    tags=["release-ops"],
)
async def update_environment(
    environment_id: uuid.UUID,
    body: EnvironmentUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    env = await environment_service.get_environment(db, environment_id)
    if env is None:
        raise HTTPException(status_code=404, detail="Environment not found")
    await check_project_permission(db, env.project_id, user_id, Action.PROJECT_UPDATE)

    updated = await environment_service.update_environment(db, environment_id, body)
    await db.commit()
    return updated


@router.delete(
    "/environments/{environment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["release-ops"],
)
async def delete_environment(
    environment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    env = await environment_service.get_environment(db, environment_id)
    if env is None:
        raise HTTPException(status_code=404, detail="Environment not found")
    await check_project_permission(db, env.project_id, user_id, Action.PROJECT_UPDATE)

    await environment_service.delete_environment(db, environment_id)
    await db.commit()


# ---------------------------------------------------------------------------
# FM-133: Deployment Readiness
# ---------------------------------------------------------------------------


@router.get(
    "/release-packages/{package_id}/readiness/{environment_id}",
    tags=["release-ops"],
)
async def evaluate_readiness(
    package_id: uuid.UUID,
    environment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> dict:
    """Evaluate deployment readiness for a release package against an environment."""
    pkg = await release_package_service.get_release_package(db, package_id)
    if pkg is None:
        raise HTTPException(status_code=404, detail="Release package not found")
    await check_project_permission(db, pkg.project_id, user_id, Action.PROJECT_VIEW)

    result = await deployment_readiness_service.evaluate_readiness(
        db, release_package_id=package_id, environment_id=environment_id
    )
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


# ---------------------------------------------------------------------------
# FM-134: Release Gates
# ---------------------------------------------------------------------------


@router.post(
    "/release-packages/{package_id}/gates/evaluate",
    tags=["release-ops"],
)
async def evaluate_gates(
    package_id: uuid.UUID,
    environment_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> dict:
    """Evaluate release gates for a package."""
    pkg = await release_package_service.get_release_package(db, package_id)
    if pkg is None:
        raise HTTPException(status_code=404, detail="Release package not found")
    await check_project_permission(db, pkg.project_id, user_id, Action.PROJECT_UPDATE)

    result = await release_gate_service.evaluate_gates(
        db, release_package_id=package_id, environment_id=environment_id
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    await db.commit()
    return result


@router.get(
    "/release-packages/{package_id}/gates",
    response_model=GateResultList,
    tags=["release-ops"],
)
async def list_gate_results(
    package_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    pkg = await release_package_service.get_release_package(db, package_id)
    if pkg is None:
        raise HTTPException(status_code=404, detail="Release package not found")
    await check_project_permission(db, pkg.project_id, user_id, Action.PROJECT_VIEW)

    items = await release_gate_service.list_gate_results(db, package_id)
    return GateResultList(items=items, total=len(items))


# ---------------------------------------------------------------------------
# FM-135: Rollback Readiness
# ---------------------------------------------------------------------------


@router.get(
    "/release-packages/{package_id}/rollback-readiness",
    tags=["release-ops"],
)
async def get_rollback_readiness(
    package_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> dict:
    pkg = await release_package_service.get_release_package(db, package_id)
    if pkg is None:
        raise HTTPException(status_code=404, detail="Release package not found")
    await check_project_permission(db, pkg.project_id, user_id, Action.PROJECT_VIEW)

    result = await rollback_readiness_service.evaluate_rollback_readiness(
        db, release_package_id=package_id
    )
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


# ---------------------------------------------------------------------------
# FM-136: Post-Release Reports & Outcome Tracking
# ---------------------------------------------------------------------------


@router.get(
    "/release-packages/{package_id}/report",
    tags=["release-ops"],
)
async def get_post_release_report(
    package_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> dict:
    pkg = await release_package_service.get_release_package(db, package_id)
    if pkg is None:
        raise HTTPException(status_code=404, detail="Release package not found")
    await check_project_permission(db, pkg.project_id, user_id, Action.PROJECT_VIEW)

    result = await post_release_service.generate_post_release_report(
        db, release_package_id=package_id
    )
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.post(
    "/release-packages/{package_id}/outcome",
    tags=["release-ops"],
)
async def record_outcome(
    package_id: uuid.UUID,
    outcome: str,
    notes: str | None = None,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> dict:
    """Record a release outcome (deployed, rolled_back, failed)."""
    pkg = await release_package_service.get_release_package(db, package_id)
    if pkg is None:
        raise HTTPException(status_code=404, detail="Release package not found")
    await check_project_permission(db, pkg.project_id, user_id, Action.PROJECT_UPDATE)

    try:
        release_status = ReleaseStatus(outcome)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid outcome. Must be one of: deployed, rolled_back, failed",
        )

    result = await post_release_service.record_outcome(
        db, release_package_id=package_id, status=release_status, notes=notes
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    await db.commit()
    return result


# ---------------------------------------------------------------------------
# FM-137: Operational Timeline
# ---------------------------------------------------------------------------


@router.get(
    "/runs/{run_id}/timeline",
    tags=["release-ops"],
)
async def get_operational_timeline(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> dict:
    pid = await _resolve_project_for_run(db, run_id)
    await check_project_permission(db, pid, user_id, Action.PROJECT_VIEW)

    result = await operational_timeline_service.build_operational_timeline(
        db, run_id=run_id
    )
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result
