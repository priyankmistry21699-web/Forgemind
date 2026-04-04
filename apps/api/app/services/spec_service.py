"""FM-105: Structured SPEC generation service.

Generates a formal SPEC artifact for a run, combining:
  - User prompt / requirements
  - Project constitution (if present)
  - LLM-assisted structuring (with stub fallback)

The generated SPEC is stored as an ArtifactType.SPEC artifact and
triggers a SPEC_CREATED governance event.
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
from app.services import constitution_service, event_service

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# SPEC sections
# ---------------------------------------------------------------------------

_SPEC_SECTIONS = [
    "Problem / Objective",
    "Scope",
    "Constraints",
    "Assumptions",
    "Acceptance Criteria",
    "Risks / Unknowns",
    "Architecture Summary",
]

_SYSTEM_PROMPT = """\
You are a requirements engineer. Given a project description and optional \
constitution/rules, produce a structured SPEC document in Markdown with \
the following sections:
{sections}

Be specific and actionable. If information is missing, state reasonable \
assumptions.
""".format(sections="\n".join(f"  - {s}" for s in _SPEC_SECTIONS))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def generate_spec(
    db: AsyncSession,
    *,
    run_id: uuid.UUID,
    project_id: uuid.UUID,
    user_prompt: str | None = None,
) -> Artifact:
    """Generate a SPEC artifact for *run_id* and persist it.

    Steps:
      1. Gather run description + constitution context.
      2. Construct an LLM prompt for structured spec generation.
      3. Call LLM (fallback to stub if unavailable).
      4. Store as ArtifactType.SPEC artifact.
      5. Transition run to SPECIFYING if currently PENDING.
      6. Emit SPEC_CREATED governance event.
    """
    # 1) Gather context
    run = await _load_run(db, run_id)
    base_prompt = user_prompt or "No requirements provided."

    constitution_section = await constitution_service.get_constitution_for_prompt(
        db, project_id
    )

    # 2) Build full prompt
    parts: list[str] = []
    if constitution_section:
        parts.append(f"## Project Constitution\n{constitution_section}")
    parts.append(f"## User Requirements\n{base_prompt}")
    full_prompt = "\n\n".join(parts)

    # 3) Call LLM
    spec_content = await llm_completion(
        full_prompt,
        system=_SYSTEM_PROMPT,
        max_tokens=2048,
    )

    if spec_content is None:
        # Stub fallback — structured template
        spec_content = _build_stub_spec(base_prompt)

    # 4) Store artifact
    spec_artifact = Artifact(
        run_id=run_id,
        project_id=project_id,
        artifact_type=ArtifactType.SPEC,
        title=f"SPEC: {_truncate(base_prompt, 80)}",
        content=spec_content,
    )
    db.add(spec_artifact)
    await db.flush()
    await db.refresh(spec_artifact)

    # 5) Transition to SPECIFYING if still PENDING
    if run.status == RunStatus.PENDING:
        run.status = RunStatus.SPECIFYING
        db.add(run)
        await db.flush()

    # 6) Emit governance event
    await event_service.emit_event(
        db,
        event_type=EventType.SPEC_CREATED,
        summary=f"SPEC generated for run",
        project_id=project_id,
        run_id=run_id,
        artifact_id=spec_artifact.id,
        metadata={"title": spec_artifact.title},
    )

    logger.info("SPEC artifact %s created for run %s", spec_artifact.id, run_id)
    return spec_artifact


async def get_spec_for_run(
    db: AsyncSession,
    run_id: uuid.UUID,
) -> Artifact | None:
    """Return the latest SPEC artifact for a run, if any."""
    result = await db.execute(
        select(Artifact)
        .where(Artifact.run_id == run_id, Artifact.artifact_type == ArtifactType.SPEC)
        .order_by(Artifact.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _load_run(db: AsyncSession, run_id: uuid.UUID) -> Run:
    result = await db.execute(select(Run).where(Run.id == run_id))
    run = result.scalar_one_or_none()
    if run is None:
        raise ValueError(f"Run {run_id} not found")
    return run


def _truncate(text: str, length: int) -> str:
    text = text.replace("\n", " ").strip()
    if len(text) <= length:
        return text
    return text[: length - 3] + "..."


def _build_stub_spec(prompt: str) -> str:
    """Build a structured spec template when LLM is unavailable."""
    return "\n".join([
        "# Specification",
        "",
        "## Problem / Objective",
        prompt,
        "",
        "## Scope",
        "- To be determined via analysis",
        "",
        "## Constraints",
        "- None specified",
        "",
        "## Assumptions",
        "- Requirements are stable",
        "",
        "## Acceptance Criteria",
        "- All planned phases complete successfully",
        "- All review checkpoints pass",
        "",
        "## Risks / Unknowns",
        "- Dependent on LLM availability for planning quality",
        "",
        "## Architecture Summary",
        "- To be determined during planning phase",
    ])
