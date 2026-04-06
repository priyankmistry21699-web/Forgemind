"""FM-124/125: Delivery Artifact and Review Package generation service.

Generates delivery-facing artifacts (changelogs, summaries, review packages)
from real run state using spec, plan, tasks, artifacts, approvals, and architecture.
"""

import uuid
import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.artifact import Artifact, ArtifactType
from app.models.run import Run
from app.models.task import Task, TaskStatus
from app.models.approval_request import ApprovalRequest
from app.models.execution_event import EventType
from app.services import event_service

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Delivery artifact types (extend existing ArtifactType)
# ---------------------------------------------------------------------------

DELIVERY_ARTIFACT_TYPES = {
    "implementation_summary",
    "changelog_draft",
    "release_note_draft",
    "completion_bundle",
    "review_package",
}


# ---------------------------------------------------------------------------
# FM-124: Delivery artifact generation
# ---------------------------------------------------------------------------


async def _gather_run_context(
    db: AsyncSession,
    run_id: uuid.UUID,
) -> dict[str, Any]:
    """Gather comprehensive run context for delivery artifact generation."""
    # Run info
    run_result = await db.execute(select(Run).where(Run.id == run_id))
    run = run_result.scalar_one_or_none()
    if run is None:
        return {"error": "run_not_found"}

    # Tasks
    task_result = await db.execute(
        select(Task).where(Task.run_id == run_id).order_by(Task.created_at)
    )
    tasks = list(task_result.scalars().all())
    task_summary = {
        "total": len(tasks),
        "completed": sum(1 for t in tasks if t.status == TaskStatus.COMPLETED),
        "failed": sum(1 for t in tasks if t.status == TaskStatus.FAILED),
        "pending": sum(
            1 for t in tasks if t.status in (TaskStatus.READY, TaskStatus.RUNNING)
        ),
        "tasks": [
            {
                "id": str(t.id),
                "title": t.title,
                "status": t.status.value,
                "type": t.task_type,
            }
            for t in tasks
        ],
    }

    # Artifacts
    art_result = await db.execute(
        select(Artifact).where(Artifact.run_id == run_id).order_by(Artifact.created_at)
    )
    artifacts = list(art_result.scalars().all())
    spec_artifact = next(
        (a for a in artifacts if a.artifact_type == ArtifactType.SPEC), None
    )
    plan_artifact = next(
        (a for a in artifacts if a.artifact_type == ArtifactType.PLAN), None
    )

    # Approvals
    approval_result = await db.execute(
        select(ApprovalRequest).where(ApprovalRequest.run_id == run_id)
    )
    approvals = list(approval_result.scalars().all())
    approval_summary = {
        "total": len(approvals),
        "approved": sum(1 for a in approvals if a.status.value == "approved"),
        "pending": sum(1 for a in approvals if a.status.value == "pending"),
        "rejected": sum(1 for a in approvals if a.status.value == "rejected"),
    }

    return {
        "run": {
            "id": str(run.id),
            "run_number": run.run_number,
            "status": run.status.value,
            "project_id": str(run.project_id),
        },
        "tasks": task_summary,
        "artifacts": [
            {"id": str(a.id), "title": a.title, "type": a.artifact_type.value}
            for a in artifacts
        ],
        "spec": {
            "id": str(spec_artifact.id),
            "title": spec_artifact.title,
            "content_preview": (spec_artifact.content or "")[:500],
        }
        if spec_artifact
        else None,
        "plan": {
            "id": str(plan_artifact.id),
            "title": plan_artifact.title,
            "content_preview": (plan_artifact.content or "")[:500],
        }
        if plan_artifact
        else None,
        "approvals": approval_summary,
    }


def _generate_implementation_summary(context: dict[str, Any]) -> str:
    """Generate a markdown implementation summary from run context."""
    run = context["run"]
    tasks = context["tasks"]
    lines = [
        f"# Implementation Summary — Run #{run['run_number']}",
        "",
        f"**Status**: {run['status']}",
        f"**Tasks**: {tasks['completed']}/{tasks['total']} completed",
        "",
    ]

    if context.get("spec"):
        lines += ["## Specification", "", context["spec"]["content_preview"], ""]

    if context.get("plan"):
        lines += ["## Plan", "", context["plan"]["content_preview"], ""]

    lines += ["## Task Breakdown", ""]
    for t in tasks["tasks"]:
        icon = (
            "✅"
            if t["status"] == "completed"
            else "❌"
            if t["status"] == "failed"
            else "⏳"
        )
        lines.append(f"- {icon} **{t['title']}** ({t['status']})")

    approvals = context.get("approvals", {})
    if approvals.get("total", 0) > 0:
        lines += [
            "",
            "## Approvals",
            f"- Approved: {approvals['approved']}",
            f"- Pending: {approvals['pending']}",
            f"- Rejected: {approvals['rejected']}",
        ]

    return "\n".join(lines)


def _generate_changelog_draft(context: dict[str, Any]) -> str:
    """Generate a changelog draft from run context."""
    run = context["run"]
    tasks = context["tasks"]
    lines = [
        f"# Changelog — Run #{run['run_number']}",
        "",
        "## Changes",
        "",
    ]
    for t in tasks["tasks"]:
        if t["status"] == "completed":
            lines.append(f"- {t['title']}")

    if not any(t["status"] == "completed" for t in tasks["tasks"]):
        lines.append("- No completed tasks yet")

    return "\n".join(lines)


def _generate_release_note_draft(context: dict[str, Any]) -> str:
    """Generate a release note draft from run context."""
    run = context["run"]
    tasks = context["tasks"]
    lines = [
        f"# Release Notes — Run #{run['run_number']}",
        "",
        "## Summary",
        f"This release completes {tasks['completed']} of {tasks['total']} planned tasks.",
        "",
        "## What's Included",
        "",
    ]
    for t in tasks["tasks"]:
        if t["status"] == "completed":
            lines.append(f"- {t['title']}")

    if tasks["failed"] > 0:
        lines += ["", "## Known Issues", ""]
        for t in tasks["tasks"]:
            if t["status"] == "failed":
                lines.append(f"- {t['title']} (failed)")

    return "\n".join(lines)


async def generate_delivery_artifact(
    db: AsyncSession,
    *,
    run_id: uuid.UUID,
    project_id: uuid.UUID,
    artifact_kind: str = "implementation_summary",
) -> Artifact:
    """Generate a delivery artifact from real run state."""
    if artifact_kind not in DELIVERY_ARTIFACT_TYPES:
        raise ValueError(f"Unknown delivery artifact kind: {artifact_kind}")

    context = await _gather_run_context(db, run_id)
    if "error" in context:
        raise ValueError(context["error"])

    generators = {
        "implementation_summary": _generate_implementation_summary,
        "changelog_draft": _generate_changelog_draft,
        "release_note_draft": _generate_release_note_draft,
        "completion_bundle": _generate_implementation_summary,  # reuse for now
    }

    content = generators.get(artifact_kind, _generate_implementation_summary)(context)

    artifact = Artifact(
        title=f"{artifact_kind.replace('_', ' ').title()} — Run #{context['run']['run_number']}",
        artifact_type=ArtifactType.DOCUMENTATION,
        content=content,
        meta={
            "delivery_kind": artifact_kind,
            "generated_from": "delivery_artifact_service",
        },
        project_id=project_id,
        run_id=run_id,
        created_by="system",
    )
    db.add(artifact)
    await db.flush()

    await event_service.emit_event(
        db,
        event_type=EventType.ARTIFACT_CREATED,
        summary=f"Delivery artifact generated: {artifact_kind}",
        project_id=project_id,
        run_id=run_id,
        metadata={"artifact_id": str(artifact.id), "delivery_kind": artifact_kind},
    )

    logger.info(
        "Delivery artifact %s (%s) created for run %s",
        artifact.id,
        artifact_kind,
        run_id,
    )
    return artifact


async def list_delivery_artifacts(
    db: AsyncSession,
    run_id: uuid.UUID,
) -> list[Artifact]:
    """List all delivery artifacts for a run."""
    result = await db.execute(
        select(Artifact)
        .where(Artifact.run_id == run_id)
        .where(Artifact.artifact_type == ArtifactType.DOCUMENTATION)
        .where(Artifact.meta["delivery_kind"].as_string().isnot(None))
        .order_by(Artifact.created_at)
    )
    return list(result.scalars().all())


# ---------------------------------------------------------------------------
# FM-125: Review package generation
# ---------------------------------------------------------------------------


async def generate_review_package(
    db: AsyncSession,
    *,
    run_id: uuid.UUID,
    project_id: uuid.UUID,
) -> Artifact:
    """Generate a reviewer-ready package from run state."""
    context = await _gather_run_context(db, run_id)
    if "error" in context:
        raise ValueError(context["error"])

    run = context["run"]
    tasks = context["tasks"]
    approvals = context["approvals"]

    lines = [
        f"# Review Package — Run #{run['run_number']}",
        "",
        "## Objective",
        f"Run #{run['run_number']} for project {run['project_id']}",
        "",
    ]

    if context.get("spec"):
        lines += [
            "## Specification",
            "",
            context["spec"]["content_preview"],
            "",
        ]

    if context.get("plan"):
        lines += [
            "## Plan",
            "",
            context["plan"]["content_preview"],
            "",
        ]

    lines += [
        "## Task Completion Snapshot",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Total tasks | {tasks['total']} |",
        f"| Completed | {tasks['completed']} |",
        f"| Failed | {tasks['failed']} |",
        f"| Pending | {tasks['pending']} |",
        "",
    ]

    if context["artifacts"]:
        lines += ["## Key Artifacts", ""]
        for a in context["artifacts"]:
            lines.append(f"- **{a['title']}** ({a['type']})")
        lines.append("")

    lines += [
        "## Approval State",
        "",
        f"- Approved: {approvals['approved']}",
        f"- Pending: {approvals['pending']}",
        f"- Rejected: {approvals['rejected']}",
        "",
    ]

    # Risks / unresolved
    risks = []
    if tasks["failed"] > 0:
        risks.append(f"{tasks['failed']} task(s) failed")
    if approvals["pending"] > 0:
        risks.append(f"{approvals['pending']} approval(s) pending")
    if approvals["rejected"] > 0:
        risks.append(f"{approvals['rejected']} approval(s) rejected")
    if tasks["completed"] < tasks["total"]:
        risks.append(f"Only {tasks['completed']}/{tasks['total']} tasks completed")

    lines += ["## Open Risks / Unresolved Items", ""]
    if risks:
        for r in risks:
            lines.append(f"- ⚠️ {r}")
    else:
        lines.append("- No open risks identified")
    lines.append("")

    # Recommended next actions
    lines += ["## Recommended Next Actions", ""]
    if tasks["pending"] > 0:
        lines.append("- Complete remaining tasks")
    if approvals["pending"] > 0:
        lines.append("- Resolve pending approvals")
    if tasks["failed"] > 0:
        lines.append("- Investigate failed tasks")
    if not risks:
        lines.append("- Ready for delivery")

    content = "\n".join(lines)

    artifact = Artifact(
        title=f"Review Package — Run #{run['run_number']}",
        artifact_type=ArtifactType.REVIEW,
        content=content,
        meta={
            "delivery_kind": "review_package",
            "generated_from": "delivery_artifact_service",
        },
        project_id=project_id,
        run_id=run_id,
        created_by="system",
    )
    db.add(artifact)
    await db.flush()

    await event_service.emit_event(
        db,
        event_type=EventType.ARTIFACT_CREATED,
        summary="Review package generated",
        project_id=project_id,
        run_id=run_id,
        metadata={"artifact_id": str(artifact.id), "delivery_kind": "review_package"},
    )

    logger.info("Review package %s created for run %s", artifact.id, run_id)
    return artifact
