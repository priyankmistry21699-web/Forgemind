import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user_id
from app.db.session import get_db
from app.schemas.code_ops import (
    CodeMappingCreate,
    CodeMappingRead,
    CodeMappingList,
    PatchProposalCreate,
    PatchProposalUpdate,
    PatchProposalRead,
    PatchProposalList,
    ChangeReviewCreate,
    ChangeReviewRead,
    ChangeReviewList,
    BranchStrategyCreate,
    BranchStrategyUpdate,
    BranchStrategyRead,
    BranchStrategyList,
    PRDraftCreate,
    PRDraftUpdate,
    PRDraftRead,
    PRDraftList,
    PRDraftGenerateRequest,
    RepoActionApprovalCreate,
    RepoActionDecision,
    RepoActionApprovalRead,
    RepoActionApprovalList,
    SandboxExecutionCreate,
    SandboxExecutionRead,
    SandboxExecutionList,
    SandboxRunRequest,
)
from app.services import code_ops_service
from app.services.authz_service import check_project_permission, Action
from app.core.authz_deps import resolve_project_for_entity
from app.models.code_ops import (
    CodeMapping,
    PatchProposal,
    BranchStrategy,
    RepoActionApproval,
    SandboxExecution,
)

router = APIRouter()


# ── Code Mappings (FM-061) ──────────────────────────────────────


@router.post(
    "/projects/{project_id}/code-mappings",
    response_model=CodeMappingRead,
    status_code=201,
)
async def create_code_mapping(
    project_id: uuid.UUID,
    data: CodeMappingCreate,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> CodeMappingRead:
    await check_project_permission(db, project_id, user_id, Action.PROJECT_UPDATE)
    cm = await code_ops_service.create_code_mapping(
        db,
        project_id=project_id,
        artifact_id=data.artifact_id,
        file_path=data.file_path,
        language=data.language,
        metadata_=data.metadata_,
    )
    return CodeMappingRead.model_validate(cm)


@router.get(
    "/projects/{project_id}/code-mappings",
    response_model=CodeMappingList,
)
async def list_code_mappings(
    project_id: uuid.UUID,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> CodeMappingList:
    await check_project_permission(db, project_id, user_id, Action.PROJECT_VIEW)
    items, total = await code_ops_service.list_code_mappings(
        db,
        project_id,
        limit=limit,
        offset=offset,
    )
    return CodeMappingList(
        items=[CodeMappingRead.model_validate(m) for m in items],
        total=total,
    )


@router.delete("/code-mappings/{mapping_id}", status_code=204)
async def delete_code_mapping(
    mapping_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> None:
    # FM-212: check entity existence first so 404 is returned for unknown IDs;
    # NULL project_id then raises 403 instead of bypassing the auth check.
    from sqlalchemy import select as _select
    exists = (await db.execute(_select(CodeMapping.id).where(CodeMapping.id == mapping_id))).scalar_one_or_none()
    if exists is None:
        raise HTTPException(status_code=404, detail="Mapping not found")
    proj_id = await resolve_project_for_entity(db, CodeMapping, mapping_id)
    if proj_id is None:
        raise HTTPException(status_code=403, detail="Cannot determine project for this mapping")
    await check_project_permission(db, proj_id, user_id, Action.PROJECT_UPDATE)
    deleted = await code_ops_service.delete_code_mapping(db, mapping_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Mapping not found")


# ── Patch Proposals (FM-062) ────────────────────────────────────


@router.post(
    "/projects/{project_id}/patches",
    response_model=PatchProposalRead,
    status_code=201,
)
async def create_patch(
    project_id: uuid.UUID,
    data: PatchProposalCreate,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> PatchProposalRead:
    await check_project_permission(db, project_id, user_id, Action.PROJECT_EXECUTE_CODE)
    p = await code_ops_service.create_patch(
        db,
        project_id=project_id,
        title=data.title,
        diff_content=data.diff_content,
        description=data.description,
        target_branch=data.target_branch,
        rationale=data.rationale,
        created_by=user_id,
        target_files=data.target_files,
        patch_format=data.patch_format,
        proposed_by_agent=data.proposed_by_agent,
        readiness_state=data.readiness_state,
        linked_artifact_ids=data.linked_artifact_ids,
    )
    return PatchProposalRead.model_validate(p)


@router.get(
    "/projects/{project_id}/patches",
    response_model=PatchProposalList,
)
async def list_patches(
    project_id: uuid.UUID,
    status: str | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> PatchProposalList:
    await check_project_permission(db, project_id, user_id, Action.PROJECT_VIEW)
    items, total = await code_ops_service.list_patches(
        db,
        project_id,
        status_filter=status,
        limit=limit,
        offset=offset,
    )
    return PatchProposalList(
        items=[PatchProposalRead.model_validate(p) for p in items],
        total=total,
    )


@router.get("/patches/{patch_id}", response_model=PatchProposalRead)
async def get_patch(
    patch_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> PatchProposalRead:
    p = await code_ops_service.get_patch(db, patch_id)
    if p is None:
        raise HTTPException(status_code=404, detail="Patch not found")
    # FM-212: NULL project_id must never bypass the auth check
    if p.project_id is None:
        raise HTTPException(status_code=403, detail="Cannot determine project for this patch")
    await check_project_permission(db, p.project_id, user_id, Action.PROJECT_VIEW)
    return PatchProposalRead.model_validate(p)


@router.patch("/patches/{patch_id}", response_model=PatchProposalRead)
async def update_patch(
    patch_id: uuid.UUID,
    data: PatchProposalUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> PatchProposalRead:
    existing = await code_ops_service.get_patch(db, patch_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Patch not found")
    # FM-212: NULL project_id must never bypass the auth check
    if existing.project_id is None:
        raise HTTPException(status_code=403, detail="Cannot determine project for this patch")
    await check_project_permission(
        db, existing.project_id, user_id, Action.PROJECT_EXECUTE_CODE
    )
    p = await code_ops_service.update_patch(
        db,
        patch_id,
        **data.model_dump(exclude_unset=True),
    )
    if p is None:
        raise HTTPException(status_code=404, detail="Patch not found")
    return PatchProposalRead.model_validate(p)


# ── Change Reviews (FM-063/066) ─────────────────────────────────


@router.post(
    "/patches/{patch_id}/reviews",
    response_model=ChangeReviewRead,
    status_code=201,
)
async def create_review(
    patch_id: uuid.UUID,
    data: ChangeReviewCreate,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> ChangeReviewRead:
    proj_id = await resolve_project_for_entity(db, PatchProposal, patch_id)
    if proj_id is not None:
        await check_project_permission(db, proj_id, user_id, Action.PROJECT_REVIEW)
    r = await code_ops_service.create_review(
        db,
        patch_id=patch_id,
        reviewer_id=user_id,
        decision=data.decision,
        comment=data.comment,
        file_path=data.file_path,
        line_start=data.line_start,
        line_end=data.line_end,
        suggestion=data.suggestion,
    )
    return ChangeReviewRead.model_validate(r)


@router.get(
    "/patches/{patch_id}/reviews",
    response_model=ChangeReviewList,
)
async def list_reviews(
    patch_id: uuid.UUID,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> ChangeReviewList:
    proj_id = await resolve_project_for_entity(db, PatchProposal, patch_id)
    if proj_id is not None:
        await check_project_permission(db, proj_id, user_id, Action.PROJECT_VIEW)
    items, total = await code_ops_service.list_reviews(
        db,
        patch_id,
        limit=limit,
        offset=offset,
    )
    return ChangeReviewList(
        items=[ChangeReviewRead.model_validate(r) for r in items],
        total=total,
    )


# ── Branch Strategies (FM-064) ──────────────────────────────────


@router.post(
    "/projects/{project_id}/branch-strategies",
    response_model=BranchStrategyRead,
    status_code=201,
)
async def create_branch_strategy(
    project_id: uuid.UUID,
    data: BranchStrategyCreate,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> BranchStrategyRead:
    await check_project_permission(db, project_id, user_id, Action.PROJECT_EXECUTE_CODE)
    bs = await code_ops_service.create_branch_strategy(
        db,
        project_id=project_id,
        base_branch=data.base_branch,
        branch_pattern=data.branch_pattern,
        auto_create_branch=data.auto_create_branch,
        pr_target_branch=data.pr_target_branch,
        config=data.config,
    )
    return BranchStrategyRead.model_validate(bs)


@router.get(
    "/projects/{project_id}/branch-strategies",
    response_model=BranchStrategyList,
)
async def list_branch_strategies(
    project_id: uuid.UUID,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> BranchStrategyList:
    await check_project_permission(db, project_id, user_id, Action.PROJECT_VIEW)
    items, total = await code_ops_service.list_branch_strategies(
        db,
        project_id,
        limit=limit,
        offset=offset,
    )
    return BranchStrategyList(
        items=[BranchStrategyRead.model_validate(b) for b in items],
        total=total,
    )


@router.patch(
    "/branch-strategies/{strategy_id}",
    response_model=BranchStrategyRead,
)
async def update_branch_strategy(
    strategy_id: uuid.UUID,
    data: BranchStrategyUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> BranchStrategyRead:
    proj_id = await resolve_project_for_entity(db, BranchStrategy, strategy_id)
    if proj_id is not None:
        await check_project_permission(
            db, proj_id, user_id, Action.PROJECT_EXECUTE_CODE
        )
    bs = await code_ops_service.update_branch_strategy(
        db,
        strategy_id,
        **data.model_dump(exclude_unset=True),
    )
    if bs is None:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return BranchStrategyRead.model_validate(bs)


# ── PR Drafts (FM-065) ─────────────────────────────────────────


@router.post(
    "/projects/{project_id}/pr-drafts",
    response_model=PRDraftRead,
    status_code=201,
)
async def create_pr_draft(
    project_id: uuid.UUID,
    data: PRDraftCreate,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> PRDraftRead:
    await check_project_permission(db, project_id, user_id, Action.PROJECT_EXECUTE_CODE)
    pr = await code_ops_service.create_pr_draft(
        db,
        project_id=project_id,
        title=data.title,
        source_branch=data.source_branch,
        target_branch=data.target_branch,
        patch_id=data.patch_id,
        body=data.body,
        reviewers=data.reviewers,
        checklist=data.checklist,
        linked_artifacts=data.linked_artifacts,
    )
    return PRDraftRead.model_validate(pr)


@router.get(
    "/projects/{project_id}/pr-drafts",
    response_model=PRDraftList,
)
async def list_pr_drafts(
    project_id: uuid.UUID,
    status: str | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> PRDraftList:
    await check_project_permission(db, project_id, user_id, Action.PROJECT_VIEW)
    items, total = await code_ops_service.list_pr_drafts(
        db,
        project_id,
        status_filter=status,
        limit=limit,
        offset=offset,
    )
    return PRDraftList(
        items=[PRDraftRead.model_validate(p) for p in items],
        total=total,
    )


@router.get("/pr-drafts/{pr_id}", response_model=PRDraftRead)
async def get_pr_draft(
    pr_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> PRDraftRead:
    pr = await code_ops_service.get_pr_draft(db, pr_id)
    if pr is None:
        raise HTTPException(status_code=404, detail="PR draft not found")
    # FM-212: NULL project_id must never bypass the auth check
    if pr.project_id is None:
        raise HTTPException(status_code=403, detail="Cannot determine project for this PR draft")
    await check_project_permission(db, pr.project_id, user_id, Action.PROJECT_VIEW)
    return PRDraftRead.model_validate(pr)


@router.patch("/pr-drafts/{pr_id}", response_model=PRDraftRead)
async def update_pr_draft(
    pr_id: uuid.UUID,
    data: PRDraftUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> PRDraftRead:
    existing = await code_ops_service.get_pr_draft(db, pr_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="PR draft not found")
    # FM-212: NULL project_id must never bypass the auth check
    if existing.project_id is None:
        raise HTTPException(status_code=403, detail="Cannot determine project for this PR draft")
    await check_project_permission(
        db, existing.project_id, user_id, Action.PROJECT_EXECUTE_CODE
    )
    pr = await code_ops_service.update_pr_draft(
        db,
        pr_id,
        **data.model_dump(exclude_unset=True),
    )
    if pr is None:
        raise HTTPException(status_code=404, detail="PR draft not found")
    return PRDraftRead.model_validate(pr)


# ── Repo Action Approvals (FM-067) ──────────────────────────────


@router.post(
    "/projects/{project_id}/repo-approvals",
    response_model=RepoActionApprovalRead,
    status_code=201,
)
async def create_repo_approval(
    project_id: uuid.UUID,
    data: RepoActionApprovalCreate,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> RepoActionApprovalRead:
    await check_project_permission(db, project_id, user_id, Action.PROJECT_EXECUTE_CODE)
    a = await code_ops_service.create_repo_action_approval(
        db,
        project_id=project_id,
        action_type=data.action_type,
        reason=data.reason,
        context=data.context,
    )
    return RepoActionApprovalRead.model_validate(a)


@router.get(
    "/projects/{project_id}/repo-approvals",
    response_model=RepoActionApprovalList,
)
async def list_repo_approvals(
    project_id: uuid.UUID,
    status: str | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> RepoActionApprovalList:
    await check_project_permission(db, project_id, user_id, Action.PROJECT_VIEW)
    items, total = await code_ops_service.list_repo_action_approvals(
        db,
        project_id,
        status_filter=status,
        limit=limit,
        offset=offset,
    )
    return RepoActionApprovalList(
        items=[RepoActionApprovalRead.model_validate(a) for a in items],
        total=total,
    )


@router.post(
    "/repo-approvals/{approval_id}/decide",
    response_model=RepoActionApprovalRead,
)
async def decide_repo_approval(
    approval_id: uuid.UUID,
    data: RepoActionDecision,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> RepoActionApprovalRead:
    # C-3: null project_id must never bypass the auth check
    proj_id = await resolve_project_for_entity(db, RepoActionApproval, approval_id)
    if proj_id is None:
        raise HTTPException(status_code=403, detail="Cannot determine project for this approval")
    await check_project_permission(db, proj_id, user_id, Action.PROJECT_APPROVE)
    a = await code_ops_service.decide_repo_action(
        db,
        approval_id,
        decided_by=user_id,
        status=data.status,
        decision_comment=data.decision_comment,
    )
    if a is None:
        raise HTTPException(status_code=404, detail="Approval not found")
    return RepoActionApprovalRead.model_validate(a)


# ── Sandbox Executions (FM-068/069) ─────────────────────────────


@router.post(
    "/projects/{project_id}/sandbox",
    response_model=SandboxExecutionRead,
    status_code=201,
)
async def create_sandbox_execution(
    project_id: uuid.UUID,
    data: SandboxExecutionCreate,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> SandboxExecutionRead:
    await check_project_permission(db, project_id, user_id, Action.PROJECT_EXECUTE_CODE)
    s = await code_ops_service.create_sandbox_execution(
        db,
        project_id=project_id,
        command=data.command,
        task_id=data.task_id,
        patch_id=data.patch_id,
        working_directory=data.working_directory,
        environment=data.environment,
        timeout_seconds=data.timeout_seconds,
        allowed_commands=data.allowed_commands,
        resource_limits=data.resource_limits,
        isolated=data.isolated,
    )
    return SandboxExecutionRead.model_validate(s)


@router.get(
    "/projects/{project_id}/sandbox",
    response_model=SandboxExecutionList,
)
async def list_sandbox_executions(
    project_id: uuid.UUID,
    status: str | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> SandboxExecutionList:
    await check_project_permission(db, project_id, user_id, Action.PROJECT_VIEW)
    items, total = await code_ops_service.list_sandbox_executions(
        db,
        project_id,
        status_filter=status,
        limit=limit,
        offset=offset,
    )
    return SandboxExecutionList(
        items=[SandboxExecutionRead.model_validate(s) for s in items],
        total=total,
    )


@router.get("/sandbox/{execution_id}", response_model=SandboxExecutionRead)
async def get_sandbox_execution(
    execution_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> SandboxExecutionRead:
    s = await code_ops_service.get_sandbox_execution(db, execution_id)
    if s is None:
        raise HTTPException(status_code=404, detail="Execution not found")
    # FM-212: NULL project_id must never bypass the auth check
    if s.project_id is None:
        raise HTTPException(status_code=403, detail="Cannot determine project for this execution")
    await check_project_permission(db, s.project_id, user_id, Action.PROJECT_VIEW)
    return SandboxExecutionRead.model_validate(s)


# ── FM-067: PR Draft Generation Endpoint ────────────────────────


@router.post(
    "/projects/{project_id}/pr-drafts/generate",
    response_model=PRDraftRead,
    status_code=201,
)
async def generate_pr_draft(
    project_id: uuid.UUID,
    data: PRDraftGenerateRequest,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> PRDraftRead:
    """Generate a PR draft from a patch proposal."""
    await check_project_permission(db, project_id, user_id, Action.PROJECT_EXECUTE_CODE)
    try:
        pr = await code_ops_service.generate_pr_draft(
            db,
            project_id=project_id,
            patch_id=data.patch_id,
            target_branch=data.target_branch,
            include_checklist=data.include_checklist,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return PRDraftRead.model_validate(pr)


# ── FM-068: Approval Gate Check ─────────────────────────────────


@router.get("/projects/{project_id}/repo-approvals/check")
async def check_approval_gate(
    project_id: uuid.UUID,
    action_type: str = Query(...),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Check whether an action type has been approved for a project."""
    await check_project_permission(db, project_id, user_id, Action.PROJECT_VIEW)
    return await code_ops_service.check_approval_gate(db, project_id, action_type)


# ── FM-069: Sandbox Run Endpoint ────────────────────────────────


@router.post("/sandbox/run", response_model=SandboxExecutionRead)
async def run_sandbox(
    data: SandboxRunRequest,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> SandboxExecutionRead:
    """Execute a queued sandbox execution with safety controls."""
    # C-3: null project_id must never bypass the auth check
    # Check entity existence first so an unknown ID returns 404, not 403
    from sqlalchemy import select as _select
    exists_result = await db.execute(
        _select(SandboxExecution.id).where(SandboxExecution.id == data.execution_id)
    )
    if exists_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Execution not found")
    proj_id = await resolve_project_for_entity(db, SandboxExecution, data.execution_id)
    if proj_id is None:
        raise HTTPException(status_code=403, detail="Cannot determine project for this execution")
    await check_project_permission(
        db, proj_id, user_id, Action.PROJECT_EXECUTE_CODE
    )
    s = await code_ops_service.run_sandbox_execution(db, data.execution_id)
    if s is None:
        raise HTTPException(status_code=404, detail="Execution not found")
    await db.commit()
    return SandboxExecutionRead.model_validate(s)
