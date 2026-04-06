"""FM-106: PLAN artifact generation, SPEC→PLAN linking, and export.

Creates a formal PLAN artifact from the SPEC, links it via
spec_artifact_id, and provides markdown export.
"""

import uuid
import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.llm import llm_completion
from app.models.artifact import Artifact, ArtifactType
from app.models.execution_event import EventType
from app.models.run import Run, RunStatus
from app.services import event_service, spec_service, constitution_service, adr_service

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# System prompt for structured PLAN generation
# ---------------------------------------------------------------------------

_PLAN_SYSTEM = """\
You are a software project planner. Given a SPEC document (and optional \
project constitution), produce a structured PLAN in Markdown with sections:
  - Overview
  - Phases (numbered, each with title, description, dependencies, deliverables)
  - Milestones
  - Risk Mitigation
  - Timeline Estimate

Be specific. Each phase should map to actionable work.
"""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def generate_plan_artifact(
    db: AsyncSession,
    *,
    run_id: uuid.UUID,
    project_id: uuid.UUID,
    user_prompt: str | None = None,
) -> Artifact:
    """Generate a PLAN artifact linked to the run's SPEC.

    Steps:
      1. Load existing SPEC for this run (required).
      2. Gather constitution context.
      3. Call LLM for structured plan (fallback to stub).
      4. Create PLAN artifact with spec_artifact_id FK.
      5. Transition run to PLANNING if in SPECIFYING.
      6. Emit PLAN_CREATED governance event.
    """
    # 1) Load SPEC
    spec = await spec_service.get_spec_for_run(db, run_id)
    if spec is None:
        raise ValueError(
            "Cannot generate PLAN: no SPEC artifact found for this run. "
            "Use /fm.specify first."
        )

    # 2) Constitution context
    constitution_section = await constitution_service.get_constitution_for_prompt(
        db, project_id
    )

    # FM-107: Architecture context for ADR-aware planning
    arch_context = await adr_service.get_architecture_context_for_prompt(db, project_id)

    # FM-118: Template plan defaults
    template_plan_context = await _get_template_plan_context(db, project_id)

    # 3) Build prompt
    parts: list[str] = []
    if constitution_section:
        parts.append(f"## Project Constitution\n{constitution_section}")
    if arch_context:
        parts.append(arch_context)
    if template_plan_context:
        parts.append(f"## Template Plan Guidance\n{template_plan_context}")
    parts.append(f"## Specification\n{spec.content}")
    if user_prompt:
        parts.append(f"## Additional Instructions\n{user_prompt}")
    full_prompt = "\n\n".join(parts)

    plan_content = await llm_completion(
        full_prompt,
        system=_PLAN_SYSTEM,
        max_tokens=3000,
    )

    if plan_content is None:
        plan_content = _build_stub_plan(spec.content)

    # FM-107: Enrich plan with ADR section from architecture graph
    plan_content = await adr_service.enrich_plan_with_adr(
        db,
        project_id=project_id,
        plan_content=plan_content,
        spec_content=spec.content,
    )

    # 4) Create PLAN artifact linked to SPEC
    plan_artifact = Artifact(
        run_id=run_id,
        project_id=project_id,
        artifact_type=ArtifactType.PLAN,
        title=f"PLAN linked to SPEC {str(spec.id)[:8]}",
        content=plan_content,
        spec_artifact_id=spec.id,
    )
    db.add(plan_artifact)
    await db.flush()
    await db.refresh(plan_artifact)

    # 5) Transition to PLANNING
    run_result = await db.execute(select(Run).where(Run.id == run_id))
    run = run_result.scalar_one_or_none()
    if run and run.status == RunStatus.SPECIFYING:
        run.status = RunStatus.PLANNING
        db.add(run)
        await db.flush()

    # 6) Emit event
    await event_service.emit_event(
        db,
        event_type=EventType.PLAN_CREATED,
        summary="PLAN artifact generated from SPEC",
        project_id=project_id,
        run_id=run_id,
        artifact_id=plan_artifact.id,
        metadata={
            "title": plan_artifact.title,
            "spec_artifact_id": str(spec.id),
        },
    )

    logger.info("PLAN artifact %s created for run %s", plan_artifact.id, run_id)
    return plan_artifact


async def get_plan_for_run(
    db: AsyncSession,
    run_id: uuid.UUID,
) -> Artifact | None:
    """Return the latest PLAN artifact for a run, if any."""
    result = await db.execute(
        select(Artifact)
        .where(Artifact.run_id == run_id, Artifact.artifact_type == ArtifactType.PLAN)
        .order_by(Artifact.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def export_plan_markdown(
    db: AsyncSession,
    run_id: uuid.UUID,
) -> str | None:
    """Export the PLAN artifact as downloadable markdown.

    Returns None if no PLAN exists.
    """
    plan = await get_plan_for_run(db, run_id)
    if plan is None:
        return None

    # Combine with SPEC context for a complete export
    spec = await spec_service.get_spec_for_run(db, run_id)
    parts: list[str] = []
    parts.append(f"<!-- ForgeMind PLAN Export — Run {run_id} -->\n")
    if spec:
        parts.append("---\n# SPEC (linked)\n")
        parts.append(spec.content or "")
        parts.append("\n---\n")
    parts.append("# PLAN\n")
    parts.append(plan.content or "")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Export route helper
# ---------------------------------------------------------------------------


async def get_plan_export_data(
    db: AsyncSession,
    run_id: uuid.UUID,
) -> dict[str, Any]:
    """Return plan data for the export endpoint."""
    plan = await get_plan_for_run(db, run_id)
    if plan is None:
        return {"exists": False}
    spec = await spec_service.get_spec_for_run(db, run_id)
    return {
        "exists": True,
        "plan_id": str(plan.id),
        "plan_title": plan.title,
        "spec_id": str(spec.id) if spec else None,
        "markdown": await export_plan_markdown(db, run_id),
    }


# ---------------------------------------------------------------------------
# Stub fallback
# ---------------------------------------------------------------------------


def _build_stub_plan(spec_content: str) -> str:
    """Build a structured plan template when LLM is unavailable."""
    return "\n".join(
        [
            "# Execution Plan",
            "",
            "## Overview",
            "Plan generated from specification (LLM unavailable — stub).",
            "",
            "## Phases",
            "",
            "### Phase 1: Analysis",
            "- Description: Analyse requirements from SPEC",
            "- Dependencies: None",
            "- Deliverables: Detailed task breakdown",
            "",
            "### Phase 2: Implementation",
            "- Description: Implement tasks from analysis",
            "- Dependencies: Phase 1",
            "- Deliverables: Working code/configuration",
            "",
            "### Phase 3: Review & Validation",
            "- Description: Review output against SPEC acceptance criteria",
            "- Dependencies: Phase 2",
            "- Deliverables: Test report, review artifact",
            "",
            "## Milestones",
            "- [ ] Analysis complete",
            "- [ ] Implementation complete",
            "- [ ] Validation pass",
            "",
            "## Risk Mitigation",
            "- Monitor LLM quality at each phase",
            "- Require human approval before advancing phases",
            "",
            "## Timeline Estimate",
            "- Estimated phases: 3",
            "- Depends on task complexity and approvals",
        ]
    )


async def _get_template_plan_context(
    db: AsyncSession,
    project_id: uuid.UUID,
) -> str | None:
    """FM-118: Build plan-influencing context from the project's template."""
    from app.models.project import Project
    from app.services import project_template_service

    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project or not project.template_id:
        return None

    template = await project_template_service.get_template(db, project.template_id)
    if not template or not template.plan_defaults:
        return None

    defaults = template.plan_defaults
    parts: list[str] = []

    if "default_workstreams" in defaults:
        parts.append(
            "**Suggested workstreams:** " + ", ".join(defaults["default_workstreams"])
        )

    if "architecture_checklist" in defaults:
        parts.append(
            "**Architecture checklist:** "
            + ", ".join(defaults["architecture_checklist"])
        )

    return "\n".join(parts) if parts else None
