"""Code operations service — enhanced CRUD + execution logic.

FM-061–069: Code mapping, patch proposals, reviews, branches, PR drafts,
repo action approvals, and sandbox execution with safety controls.
"""

import asyncio
import logging
import os
import subprocess
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.code_ops import (
    CodeMapping, PatchProposal, ChangeReview,
    BranchStrategy, PRDraft, RepoActionApproval,
    SandboxExecution, SandboxStatus, PatchStatus,
)

logger = logging.getLogger(__name__)

# FM-069: Command allowlist for sandbox safety
SANDBOX_COMMAND_ALLOWLIST = {
    "python", "python3", "pip", "pytest", "echo", "cat", "ls", "pwd",
    "node", "npm", "npx", "tsc", "eslint", "prettier",
    "go", "cargo", "rustc", "javac", "java",
    "git", "diff", "grep", "find", "wc", "head", "tail", "sort",
}

# FM-069: Max sandbox execution time (seconds)
MAX_SANDBOX_TIMEOUT = 300


# ── Code Mappings (FM-061) ──────────────────────────────────────

async def create_code_mapping(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    artifact_id: uuid.UUID,
    file_path: str,
    language: str | None = None,
    metadata_: dict | None = None,
) -> CodeMapping:
    cm = CodeMapping(
        project_id=project_id,
        artifact_id=artifact_id,
        file_path=file_path,
        language=language,
        metadata_=metadata_,
    )
    db.add(cm)
    await db.flush()
    await db.refresh(cm)
    return cm


async def list_code_mappings(
    db: AsyncSession,
    project_id: uuid.UUID,
    *,
    limit: int = 100,
    offset: int = 0,
) -> tuple[list[CodeMapping], int]:
    query = select(CodeMapping).where(CodeMapping.project_id == project_id)
    total = (await db.execute(
        select(sa_func.count()).select_from(query.subquery())
    )).scalar_one()
    result = await db.execute(
        query.order_by(CodeMapping.created_at.desc()).offset(offset).limit(limit)
    )
    return list(result.scalars().all()), total


async def delete_code_mapping(
    db: AsyncSession, mapping_id: uuid.UUID
) -> bool:
    result = await db.execute(
        select(CodeMapping).where(CodeMapping.id == mapping_id)
    )
    cm = result.scalar_one_or_none()
    if cm is None:
        return False
    await db.delete(cm)
    await db.flush()
    return True


# ── Patch Proposals (FM-062) ────────────────────────────────────

async def create_patch(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    title: str,
    diff_content: str,
    description: str | None = None,
    target_branch: str = "main",
    rationale: str | None = None,
    created_by: uuid.UUID | None = None,
    target_files: list | None = None,
    patch_format: str | None = None,
    proposed_by_agent: str | None = None,
    readiness_state: str | None = None,
    linked_artifact_ids: list | None = None,
) -> PatchProposal:
    p = PatchProposal(
        project_id=project_id,
        title=title,
        description=description,
        diff_content=diff_content,
        target_branch=target_branch,
        rationale=rationale,
        created_by=created_by,
        target_files=target_files,
        patch_format=patch_format,
        proposed_by_agent=proposed_by_agent,
        readiness_state=readiness_state,
        linked_artifact_ids=linked_artifact_ids,
    )
    db.add(p)
    await db.flush()
    await db.refresh(p)
    return p


async def get_patch(
    db: AsyncSession, patch_id: uuid.UUID
) -> PatchProposal | None:
    result = await db.execute(
        select(PatchProposal).where(PatchProposal.id == patch_id)
    )
    return result.scalar_one_or_none()


async def list_patches(
    db: AsyncSession,
    project_id: uuid.UUID,
    *,
    status_filter: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[PatchProposal], int]:
    query = select(PatchProposal).where(PatchProposal.project_id == project_id)
    if status_filter:
        query = query.where(PatchProposal.status == status_filter)
    total = (await db.execute(
        select(sa_func.count()).select_from(query.subquery())
    )).scalar_one()
    result = await db.execute(
        query.order_by(PatchProposal.created_at.desc()).offset(offset).limit(limit)
    )
    return list(result.scalars().all()), total


async def update_patch(
    db: AsyncSession,
    patch_id: uuid.UUID,
    **updates: Any,
) -> PatchProposal | None:
    p = await get_patch(db, patch_id)
    if p is None:
        return None
    allowed = {
        "title", "description", "diff_content", "target_branch", "status", "rationale",
        "target_files", "patch_format", "readiness_state", "linked_artifact_ids",
    }
    for k, v in updates.items():
        if k in allowed and v is not None:
            setattr(p, k, v)
    await db.flush()
    await db.refresh(p)
    return p


# ── Change Reviews (FM-063/066) ─────────────────────────────────

async def create_review(
    db: AsyncSession,
    *,
    patch_id: uuid.UUID,
    reviewer_id: uuid.UUID,
    decision: str,
    comment: str | None = None,
    file_path: str | None = None,
    line_start: int | None = None,
    line_end: int | None = None,
    suggestion: str | None = None,
) -> ChangeReview:
    r = ChangeReview(
        patch_id=patch_id,
        reviewer_id=reviewer_id,
        decision=decision,
        comment=comment,
        file_path=file_path,
        line_start=line_start,
        line_end=line_end,
        suggestion=suggestion,
    )
    db.add(r)
    await db.flush()
    await db.refresh(r)
    return r


async def list_reviews(
    db: AsyncSession,
    patch_id: uuid.UUID,
    *,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[ChangeReview], int]:
    query = select(ChangeReview).where(ChangeReview.patch_id == patch_id)
    total = (await db.execute(
        select(sa_func.count()).select_from(query.subquery())
    )).scalar_one()
    result = await db.execute(
        query.order_by(ChangeReview.created_at.desc()).offset(offset).limit(limit)
    )
    return list(result.scalars().all()), total


# ── Branch Strategies (FM-064) ──────────────────────────────────

async def create_branch_strategy(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    base_branch: str = "main",
    branch_pattern: str = "forgemind/{task_id}",
    auto_create_branch: bool = True,
    pr_target_branch: str = "main",
    config: dict | None = None,
) -> BranchStrategy:
    bs = BranchStrategy(
        project_id=project_id,
        base_branch=base_branch,
        branch_pattern=branch_pattern,
        auto_create_branch=auto_create_branch,
        pr_target_branch=pr_target_branch,
        config=config,
    )
    db.add(bs)
    await db.flush()
    await db.refresh(bs)
    return bs


async def list_branch_strategies(
    db: AsyncSession,
    project_id: uuid.UUID,
    *,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[BranchStrategy], int]:
    query = select(BranchStrategy).where(
        BranchStrategy.project_id == project_id
    )
    total = (await db.execute(
        select(sa_func.count()).select_from(query.subquery())
    )).scalar_one()
    result = await db.execute(
        query.order_by(BranchStrategy.created_at.desc()).offset(offset).limit(limit)
    )
    return list(result.scalars().all()), total


async def update_branch_strategy(
    db: AsyncSession,
    strategy_id: uuid.UUID,
    **updates: Any,
) -> BranchStrategy | None:
    result = await db.execute(
        select(BranchStrategy).where(BranchStrategy.id == strategy_id)
    )
    bs = result.scalar_one_or_none()
    if bs is None:
        return None
    allowed = {"base_branch", "branch_pattern", "auto_create_branch", "pr_target_branch", "config"}
    for k, v in updates.items():
        if k in allowed and v is not None:
            setattr(bs, k, v)
    await db.flush()
    await db.refresh(bs)
    return bs


# ── PR Drafts (FM-065) ─────────────────────────────────────────

async def create_pr_draft(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    title: str,
    source_branch: str,
    target_branch: str = "main",
    patch_id: uuid.UUID | None = None,
    body: str | None = None,
    reviewers: list | None = None,
    checklist: list | None = None,
    linked_artifacts: list | None = None,
) -> PRDraft:
    pr = PRDraft(
        project_id=project_id,
        patch_id=patch_id,
        title=title,
        body=body,
        source_branch=source_branch,
        target_branch=target_branch,
        reviewers=reviewers,
        checklist=checklist,
        linked_artifacts=linked_artifacts,
    )
    db.add(pr)
    await db.flush()
    await db.refresh(pr)
    return pr


async def get_pr_draft(
    db: AsyncSession, pr_id: uuid.UUID
) -> PRDraft | None:
    result = await db.execute(
        select(PRDraft).where(PRDraft.id == pr_id)
    )
    return result.scalar_one_or_none()


async def list_pr_drafts(
    db: AsyncSession,
    project_id: uuid.UUID,
    *,
    status_filter: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[PRDraft], int]:
    query = select(PRDraft).where(PRDraft.project_id == project_id)
    if status_filter:
        query = query.where(PRDraft.status == status_filter)
    total = (await db.execute(
        select(sa_func.count()).select_from(query.subquery())
    )).scalar_one()
    result = await db.execute(
        query.order_by(PRDraft.created_at.desc()).offset(offset).limit(limit)
    )
    return list(result.scalars().all()), total


async def update_pr_draft(
    db: AsyncSession,
    pr_id: uuid.UUID,
    **updates: Any,
) -> PRDraft | None:
    pr = await get_pr_draft(db, pr_id)
    if pr is None:
        return None
    allowed = {"title", "body", "source_branch", "target_branch", "status",
               "reviewers", "checklist", "linked_artifacts"}
    for k, v in updates.items():
        if k in allowed and v is not None:
            setattr(pr, k, v)
    await db.flush()
    await db.refresh(pr)
    return pr


# ── Repo Action Approvals (FM-067) ──────────────────────────────

async def create_repo_action_approval(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    action_type: str,
    reason: str | None = None,
    context: dict | None = None,
) -> RepoActionApproval:
    a = RepoActionApproval(
        project_id=project_id,
        action_type=action_type,
        reason=reason,
        context=context,
    )
    db.add(a)
    await db.flush()
    await db.refresh(a)
    return a


async def decide_repo_action(
    db: AsyncSession,
    approval_id: uuid.UUID,
    *,
    decided_by: uuid.UUID,
    status: str,
    decision_comment: str | None = None,
) -> RepoActionApproval | None:
    result = await db.execute(
        select(RepoActionApproval).where(RepoActionApproval.id == approval_id)
    )
    a = result.scalar_one_or_none()
    if a is None:
        return None
    a.status = status
    a.decided_by = decided_by
    a.decision_comment = decision_comment
    a.decided_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(a)
    return a


async def list_repo_action_approvals(
    db: AsyncSession,
    project_id: uuid.UUID,
    *,
    status_filter: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[RepoActionApproval], int]:
    query = select(RepoActionApproval).where(
        RepoActionApproval.project_id == project_id
    )
    if status_filter:
        query = query.where(RepoActionApproval.status == status_filter)
    total = (await db.execute(
        select(sa_func.count()).select_from(query.subquery())
    )).scalar_one()
    result = await db.execute(
        query.order_by(RepoActionApproval.created_at.desc()).offset(offset).limit(limit)
    )
    return list(result.scalars().all()), total


# ── Sandbox Executions (FM-068/069) ─────────────────────────────

async def create_sandbox_execution(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    command: str,
    task_id: uuid.UUID | None = None,
    patch_id: uuid.UUID | None = None,
    working_directory: str | None = None,
    environment: dict | None = None,
    timeout_seconds: int = 60,
    allowed_commands: list | None = None,
    resource_limits: dict | None = None,
    isolated: bool = True,
) -> SandboxExecution:
    s = SandboxExecution(
        project_id=project_id,
        task_id=task_id,
        patch_id=patch_id,
        command=command,
        working_directory=working_directory,
        environment=environment,
        timeout_seconds=min(timeout_seconds, MAX_SANDBOX_TIMEOUT),
        allowed_commands=allowed_commands,
        resource_limits=resource_limits,
        isolated=isolated,
    )
    db.add(s)
    await db.flush()
    await db.refresh(s)
    return s


async def get_sandbox_execution(
    db: AsyncSession, execution_id: uuid.UUID
) -> SandboxExecution | None:
    result = await db.execute(
        select(SandboxExecution).where(SandboxExecution.id == execution_id)
    )
    return result.scalar_one_or_none()


async def complete_sandbox_execution(
    db: AsyncSession,
    execution_id: uuid.UUID,
    *,
    status: SandboxStatus,
    stdout: str | None = None,
    stderr: str | None = None,
    exit_code: int | None = None,
    duration_ms: int | None = None,
) -> SandboxExecution | None:
    s = await get_sandbox_execution(db, execution_id)
    if s is None:
        return None
    s.status = status
    s.stdout = stdout
    s.stderr = stderr
    s.exit_code = exit_code
    s.duration_ms = duration_ms
    s.completed_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(s)
    return s


async def list_sandbox_executions(
    db: AsyncSession,
    project_id: uuid.UUID,
    *,
    status_filter: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[SandboxExecution], int]:
    query = select(SandboxExecution).where(
        SandboxExecution.project_id == project_id
    )
    if status_filter:
        query = query.where(SandboxExecution.status == status_filter)
    total = (await db.execute(
        select(sa_func.count()).select_from(query.subquery())
    )).scalar_one()
    result = await db.execute(
        query.order_by(SandboxExecution.created_at.desc()).offset(offset).limit(limit)
    )
    return list(result.scalars().all()), total


# ── FM-067: PR Draft Generation ─────────────────────────────────

async def generate_pr_draft(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    patch_id: uuid.UUID,
    target_branch: str = "main",
    include_checklist: bool = True,
) -> PRDraft:
    """Generate a PR draft from a patch proposal."""
    patch = await get_patch(db, patch_id)
    if patch is None:
        raise ValueError("Patch not found")

    title = f"[ForgeMind] {patch.title}"
    body_parts = [f"## Description\n\n{patch.description or 'Auto-generated from patch proposal.'}"]
    if patch.rationale:
        body_parts.append(f"## Rationale\n\n{patch.rationale}")
    if patch.target_files:
        files_list = "\n".join(f"- `{f}`" for f in patch.target_files)
        body_parts.append(f"## Changed Files\n\n{files_list}")
    body_parts.append(f"\n---\n*Generated by ForgeMind from patch `{patch.id}`*")
    body = "\n\n".join(body_parts)

    source_branch = f"forgemind/patch-{str(patch.id)[:8]}"

    checklist = None
    if include_checklist:
        checklist = [
            {"item": "Code reviewed", "checked": False},
            {"item": "Tests passing", "checked": False},
            {"item": "No security issues", "checked": False},
        ]

    linked_artifacts = []
    if patch.linked_artifact_ids:
        linked_artifacts = patch.linked_artifact_ids

    pr = PRDraft(
        project_id=project_id,
        patch_id=patch_id,
        title=title,
        body=body,
        source_branch=source_branch,
        target_branch=target_branch,
        checklist=checklist,
        linked_artifacts=linked_artifacts,
    )
    db.add(pr)
    await db.flush()
    await db.refresh(pr)
    return pr


# ── FM-068: Approval gate check ─────────────────────────────────

async def check_approval_gate(
    db: AsyncSession,
    project_id: uuid.UUID,
    action_type: str,
) -> dict[str, Any]:
    """Check if an action requires approval and whether it's been granted."""
    query = (
        select(RepoActionApproval)
        .where(
            RepoActionApproval.project_id == project_id,
            RepoActionApproval.action_type == action_type,
        )
        .order_by(RepoActionApproval.created_at.desc())
        .limit(1)
    )
    result = await db.execute(query)
    approval = result.scalar_one_or_none()

    if approval is None:
        return {"requires_approval": True, "approved": False, "approval_id": None}

    return {
        "requires_approval": True,
        "approved": approval.status == "approved",
        "approval_id": str(approval.id),
        "status": approval.status,
    }


# ── FM-069: Sandbox Execution Runner ────────────────────────────

def _validate_command(command: str, allowed: list[str] | None = None) -> str | None:
    """Validate a command against the allowlist. Returns error message or None."""
    parts = command.strip().split()
    if not parts:
        return "Empty command"

    base_cmd = Path(parts[0]).name

    effective_allowlist = set(allowed) if allowed else SANDBOX_COMMAND_ALLOWLIST
    if base_cmd not in effective_allowlist:
        return f"Command '{base_cmd}' not in allowlist"

    dangerous_patterns = ["&&", "||", ";", "|", "`", "$(", "${", ">>", ">"]
    for pattern in dangerous_patterns:
        if pattern in command:
            return f"Dangerous pattern '{pattern}' detected in command"

    return None


async def run_sandbox_execution(
    db: AsyncSession,
    execution_id: uuid.UUID,
) -> SandboxExecution | None:
    """Actually run a queued sandbox execution with safety controls."""
    s = await get_sandbox_execution(db, execution_id)
    if s is None:
        return None

    if s.status != SandboxStatus.QUEUED:
        logger.warning("Sandbox %s not in queued state (current: %s)", execution_id, s.status)
        return s

    error = _validate_command(s.command, s.allowed_commands)
    if error:
        s.status = SandboxStatus.FAILED
        s.stderr = f"Command validation failed: {error}"
        s.exit_code = -1
        s.completed_at = datetime.now(timezone.utc)
        await db.flush()
        await db.refresh(s)
        return s

    cwd = s.working_directory
    if cwd and not os.path.isdir(cwd):
        s.status = SandboxStatus.FAILED
        s.stderr = f"Working directory not found: {cwd}"
        s.exit_code = -1
        s.completed_at = datetime.now(timezone.utc)
        await db.flush()
        await db.refresh(s)
        return s

    s.status = SandboxStatus.RUNNING
    await db.flush()

    start_time = time.monotonic()
    timeout = min(s.timeout_seconds, MAX_SANDBOX_TIMEOUT)

    try:
        proc = await asyncio.create_subprocess_shell(
            s.command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
        )
        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(), timeout=timeout
            )
            s.stdout = stdout_bytes.decode("utf-8", errors="replace")[:50000]
            s.stderr = stderr_bytes.decode("utf-8", errors="replace")[:50000]
            s.exit_code = proc.returncode
            s.status = SandboxStatus.COMPLETED if proc.returncode == 0 else SandboxStatus.FAILED
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            s.status = SandboxStatus.TIMEOUT
            s.stderr = f"Execution timed out after {timeout}s"
            s.exit_code = -1
    except Exception as exc:
        s.status = SandboxStatus.FAILED
        s.stderr = f"Execution error: {exc}"
        s.exit_code = -1

    elapsed_ms = int((time.monotonic() - start_time) * 1000)
    s.duration_ms = elapsed_ms
    s.completed_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(s)
    return s
