"""Architecture approval workflow service.

FM-089: Create ApprovalRequest entries for risky architectural changes,
leveraging the existing approval model and adding architecture-specific
context (impact assessment linkage, thresholds).
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.approval_request import ApprovalRequest, ApprovalStatus
from app.models.architecture import ChangeImpactAssessment, ImpactSeverity


# Severity levels that auto-trigger approval
AUTO_APPROVAL_THRESHOLD = {ImpactSeverity.HIGH, ImpactSeverity.CRITICAL}

# Stable prefix used to tag architecture-related approvals.
# Both creation and filtering use this constant so the pattern stays in sync.
_TITLE_PREFIX = "[arch-change]"


async def maybe_create_approval(
    db: AsyncSession,
    *,
    assessment_id: uuid.UUID,
    requested_by: str = "system",
) -> ApprovalRequest | None:
    """Create an ApprovalRequest when the impact assessment severity
    exceeds the auto-approval threshold.  Returns None if no approval needed.
    """
    assessment = await db.get(ChangeImpactAssessment, assessment_id)
    if assessment is None:
        return None

    if assessment.severity not in AUTO_APPROVAL_THRESHOLD:
        return None

    approval = ApprovalRequest(
        project_id=assessment.project_id,
        title=f"{_TITLE_PREFIX} Impact severity: {assessment.severity.value}",
        description=(
            f"Impact assessment {assessment.id} flagged a {assessment.severity.value}-severity "
            f"change with blast radius {assessment.blast_radius}. "
            f"Rationale: {assessment.rationale}"
        ),
        status=ApprovalStatus.PENDING,
    )
    db.add(approval)
    await db.flush()
    return approval


async def list_architecture_approvals(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    status: ApprovalStatus | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[ApprovalRequest], int]:
    """List architecture-related approval requests for a project."""
    base = select(ApprovalRequest).where(
        ApprovalRequest.project_id == project_id,
        ApprovalRequest.title.startswith(_TITLE_PREFIX),
    )
    if status:
        base = base.where(ApprovalRequest.status == status)

    from sqlalchemy import func as sa_func

    total_result = await db.execute(
        select(sa_func.count()).select_from(base.subquery())
    )
    total = total_result.scalar() or 0

    result = await db.execute(
        base.order_by(ApprovalRequest.created_at.desc()).offset(offset).limit(limit)
    )
    return list(result.scalars().all()), total
