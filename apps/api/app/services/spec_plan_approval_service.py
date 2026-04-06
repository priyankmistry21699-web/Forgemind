"""FM-109: Approval integration for SPEC/PLAN artifacts.

Provides functions to:
  - Create approval requests for SPEC and PLAN artifacts
  - Check approval status before allowing lifecycle transitions
  - Wire into the transition gating pipeline
"""

import uuid
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.approval_request import ApprovalRequest, ApprovalStatus
from app.models.artifact import Artifact, ArtifactType
from app.schemas.approval import ApprovalCreate
from app.services import approval_service

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def request_spec_approval(
    db: AsyncSession,
    *,
    run_id: uuid.UUID,
    project_id: uuid.UUID,
) -> ApprovalRequest | None:
    """Create an approval request for the run's SPEC artifact.

    Returns the ApprovalRequest if created, or None if no SPEC exists or
    an approval is already pending.
    """
    spec = await _get_artifact_by_type(db, run_id, ArtifactType.SPEC)
    if spec is None:
        logger.info("No SPEC artifact for run %s — skipping approval", run_id)
        return None

    # Check for existing pending approval on this artifact
    existing = await _find_pending_approval(db, artifact_id=spec.id)
    if existing is not None:
        logger.info("Approval already pending for SPEC %s", spec.id)
        return existing

    approval_data = ApprovalCreate(
        title=f"SPEC Approval: {spec.title or 'Untitled'}",
        description=(
            f"Review and approve the SPEC artifact before planning begins.\n\n"
            f"---\n{(spec.content or '')[:2000]}"
        ),
        project_id=project_id,
        run_id=run_id,
        artifact_id=spec.id,
    )
    return await approval_service.create_approval(db, approval_data)


async def request_plan_approval(
    db: AsyncSession,
    *,
    run_id: uuid.UUID,
    project_id: uuid.UUID,
) -> ApprovalRequest | None:
    """Create an approval request for the run's PLAN artifact.

    Returns the ApprovalRequest if created, or None if no PLAN exists or
    an approval is already pending.
    """
    plan = await _get_artifact_by_type(db, run_id, ArtifactType.PLAN)
    if plan is None:
        logger.info("No PLAN artifact for run %s — skipping approval", run_id)
        return None

    existing = await _find_pending_approval(db, artifact_id=plan.id)
    if existing is not None:
        logger.info("Approval already pending for PLAN %s", plan.id)
        return existing

    approval_data = ApprovalCreate(
        title=f"PLAN Approval: {plan.title or 'Untitled'}",
        description=(
            f"Review and approve the PLAN artifact before implementation begins.\n\n"
            f"---\n{(plan.content or '')[:2000]}"
        ),
        project_id=project_id,
        run_id=run_id,
        artifact_id=plan.id,
    )
    return await approval_service.create_approval(db, approval_data)


async def is_spec_approved(
    db: AsyncSession,
    run_id: uuid.UUID,
) -> bool:
    """Check whether the run's SPEC has an approved approval request.

    Returns True if:
      - No SPEC exists (vacuously approved — nothing to approve)
      - No approval request exists for the SPEC (not gated)
      - The approval request is APPROVED
    """
    spec = await _get_artifact_by_type(db, run_id, ArtifactType.SPEC)
    if spec is None:
        return True
    return await _is_artifact_approved(db, spec.id)


async def is_plan_approved(
    db: AsyncSession,
    run_id: uuid.UUID,
) -> bool:
    """Check whether the run's PLAN has an approved approval request.

    Returns True if:
      - No PLAN exists (vacuously approved)
      - No approval request exists for the PLAN (not gated)
      - The approval request is APPROVED
    """
    plan = await _get_artifact_by_type(db, run_id, ArtifactType.PLAN)
    if plan is None:
        return True
    return await _is_artifact_approved(db, plan.id)


async def get_artifact_approval_status(
    db: AsyncSession,
    run_id: uuid.UUID,
) -> dict:
    """Return approval status for both SPEC and PLAN artifacts of a run."""
    spec = await _get_artifact_by_type(db, run_id, ArtifactType.SPEC)
    plan = await _get_artifact_by_type(db, run_id, ArtifactType.PLAN)

    spec_approval = None
    plan_approval = None

    if spec:
        spec_approval = await _get_artifact_approval(db, spec.id)
    if plan:
        plan_approval = await _get_artifact_approval(db, plan.id)

    return {
        "spec": {
            "artifact_id": str(spec.id) if spec else None,
            "exists": spec is not None,
            "approval_status": spec_approval.status.value
            if spec_approval
            else "not_requested",
            "approval_id": str(spec_approval.id) if spec_approval else None,
        },
        "plan": {
            "artifact_id": str(plan.id) if plan else None,
            "exists": plan is not None,
            "approval_status": plan_approval.status.value
            if plan_approval
            else "not_requested",
            "approval_id": str(plan_approval.id) if plan_approval else None,
        },
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _get_artifact_by_type(
    db: AsyncSession,
    run_id: uuid.UUID,
    artifact_type: ArtifactType,
) -> Artifact | None:
    result = await db.execute(
        select(Artifact)
        .where(Artifact.run_id == run_id, Artifact.artifact_type == artifact_type)
        .order_by(Artifact.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def _find_pending_approval(
    db: AsyncSession,
    *,
    artifact_id: uuid.UUID,
) -> ApprovalRequest | None:
    result = await db.execute(
        select(ApprovalRequest).where(
            ApprovalRequest.artifact_id == artifact_id,
            ApprovalRequest.status == ApprovalStatus.PENDING,
        )
    )
    return result.scalar_one_or_none()


async def _is_artifact_approved(
    db: AsyncSession,
    artifact_id: uuid.UUID,
) -> bool:
    """Check if an artifact has a non-rejected approval (approved or no request)."""
    result = await db.execute(
        select(ApprovalRequest)
        .where(
            ApprovalRequest.artifact_id == artifact_id,
        )
        .order_by(ApprovalRequest.created_at.desc())
        .limit(1)
    )
    approval = result.scalar_one_or_none()
    if approval is None:
        return True  # Not gated — no approval requested
    if approval.status == ApprovalStatus.REJECTED:
        return False
    return approval.status == ApprovalStatus.APPROVED


async def _get_artifact_approval(
    db: AsyncSession,
    artifact_id: uuid.UUID,
) -> ApprovalRequest | None:
    result = await db.execute(
        select(ApprovalRequest)
        .where(
            ApprovalRequest.artifact_id == artifact_id,
        )
        .order_by(ApprovalRequest.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()
