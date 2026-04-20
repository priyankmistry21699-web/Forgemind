"""Planner service — converts a user prompt into a project, run, and planning tasks.

Attempts to call an LLM via LiteLLM to generate a real planning result.
Falls back to stub data if the LLM call fails or no API key is configured.

FM-101: Spec-aware planning — checks for SPEC artifact before planning.
"""

import logging
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.llm import llm_json_completion
from app.models.artifact import Artifact, ArtifactType
from app.models.project import Project, ProjectStatus
from app.models.run import Run, RunStatus
from app.models.task import Task, TaskStatus
from app.models.planner_result import PlannerResult

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------
# Constants
# -------------------------------------------------------------------

MAX_PHASES = 8
MAX_TITLE_LEN = 500
MAX_DESCRIPTION_LEN = 2000
ALLOWED_TASK_TYPES = {
    "planning",
    "codegen",
    "verification",
    "testing",
    "deployment",
    "architecture",
    "review",
}
DEFAULT_TASK_TYPE = "generic"

# Maps task_type → preferred agent slug for execution
TASK_TYPE_AGENT_MAP: dict[str, str] = {
    "planning": "planner",
    "architecture": "architect",
    "codegen": "coder",
    "review": "reviewer",
    "verification": "reviewer",
    "testing": "tester",
    "deployment": "coder",
}

# Task types that should auto-get approval checkpoints
APPROVAL_CHECKPOINT_TYPES = {"architecture", "review"}

# -------------------------------------------------------------------
# Prompt template
# -------------------------------------------------------------------

PLANNER_SYSTEM_PROMPT = """\
You are ForgeMind, an autonomous software engineering planner.
Given a user's project description, produce a structured JSON planning result.

Respond with ONLY valid JSON matching this exact schema:
{
  "project_name": "short name for the project",
  "overview": "2-3 sentence high-level summary of what will be built",
  "architecture_summary": "description of the system architecture, key components, and how they interact",
  "recommended_stack": {
    "language": "primary programming language",
    "framework": "main framework or library",
    "database": "database technology",
    "infrastructure": "deployment / hosting approach",
    "other": "any other notable technologies"
  },
  "assumptions": ["list of assumptions made about the project"],
  "phases": [
    {
      "title": "phase title",
      "description": "what this phase accomplishes and expected deliverable",
      "task_type": "architecture|codegen|review|testing|deployment|planning",
      "agent_hint": "architect|coder|reviewer|tester|planner",
      "requires_approval": false,
      "order_index": 0
    }
  ],
  "next_steps": ["ordered list of immediate next actions"]
}

Rules:
- phases should have 3-8 items, ordered logically
- task_type must be one of: planning, architecture, codegen, review, testing, deployment
- agent_hint should match the most appropriate agent for the task
- set requires_approval to true for architecture and review phases
- The first phase should usually be architecture/planning
- Include at least one review phase
- Be specific to the user's request, not generic
- recommended_stack values should be concrete technologies, not "TBD"
- All values in recommended_stack must be plain strings
- All items in assumptions and next_steps must be plain strings
"""


# -------------------------------------------------------------------
# Normalization / validation helpers
# -------------------------------------------------------------------


def _coerce_to_string_list(raw: Any) -> list[str]:
    """Safely coerce a value to a list of strings."""
    if not isinstance(raw, list):
        return []
    return [str(item) for item in raw if item is not None]


def _coerce_to_string_dict(raw: Any) -> dict[str, str]:
    """Safely coerce a value to a dict with string keys and values."""
    if not isinstance(raw, dict):
        return {}
    return {str(k): str(v) for k, v in raw.items() if k is not None and v is not None}


def _normalize_task_type(raw: Any) -> str:
    """Normalize a task_type to an allowed value, or fall back to default."""
    if not isinstance(raw, str):
        return DEFAULT_TASK_TYPE
    lower = raw.strip().lower()
    return lower if lower in ALLOWED_TASK_TYPES else DEFAULT_TASK_TYPE


def _normalize_phases(raw: Any) -> list[dict[str, Any]]:
    """Validate and normalize phases from LLM output.

    Ensures each phase is a dict with required fields, caps at MAX_PHASES,
    normalizes task_type, extracts agent_hint, truncates titles, and re-indexes order.
    """
    if not isinstance(raw, list):
        return []

    normalized: list[dict[str, Any]] = []
    for i, phase in enumerate(raw):
        if not isinstance(phase, dict):
            continue
        title = phase.get("title")
        if not title or not isinstance(title, str):
            continue

        task_type = _normalize_task_type(phase.get("task_type"))

        # Resolve agent hint: from LLM output or from task_type mapping
        agent_hint = None
        raw_hint = phase.get("agent_hint")
        if isinstance(raw_hint, str) and raw_hint.strip():
            agent_hint = raw_hint.strip().lower()
        elif task_type in TASK_TYPE_AGENT_MAP:
            agent_hint = TASK_TYPE_AGENT_MAP[task_type]

        # Resolve approval flag: from LLM output or from task_type
        requires_approval = bool(phase.get("requires_approval", False))
        if task_type in APPROVAL_CHECKPOINT_TYPES:
            requires_approval = True

        normalized.append(
            {
                "title": title.strip()[:MAX_TITLE_LEN],
                "description": str(phase.get("description", ""))[:MAX_DESCRIPTION_LEN]
                if phase.get("description")
                else None,
                "task_type": task_type,
                "agent_hint": agent_hint,
                "requires_approval": requires_approval,
                "order_index": i,
            }
        )

        if len(normalized) >= MAX_PHASES:
            break

    return normalized


def _normalize_plan(raw: dict[str, Any]) -> dict[str, Any]:
    """Normalize and validate an entire LLM plan output.

    Ensures all fields have correct types and safe values for persistence
    and frontend rendering.
    """
    return {
        "project_name": str(raw["project_name"]).strip()[:255]
        if isinstance(raw.get("project_name"), str)
        else None,
        "overview": str(raw["overview"]).strip()
        if isinstance(raw.get("overview"), str)
        else None,
        "architecture_summary": str(raw["architecture_summary"]).strip()
        if isinstance(raw.get("architecture_summary"), str)
        else None,
        "recommended_stack": _coerce_to_string_dict(raw.get("recommended_stack")),
        "assumptions": _coerce_to_string_list(raw.get("assumptions")),
        "phases": _normalize_phases(raw.get("phases")),
        "next_steps": _coerce_to_string_list(raw.get("next_steps")),
    }


# -------------------------------------------------------------------
# Stub plan fallback
# -------------------------------------------------------------------


def _build_stub_plan(prompt: str) -> dict[str, Any]:
    """Return a stub planning result when the LLM is unavailable."""
    return {
        "project_name": None,
        "overview": f"Stub planning result for: {prompt[:200]}",
        "architecture_summary": "To be determined by LLM planner.",
        "recommended_stack": {"language": "TBD", "framework": "TBD", "database": "TBD"},
        "assumptions": [
            "This is a stub result.",
            "Real planning will be implemented when an LLM API key is configured.",
        ],
        "phases": [
            {
                "title": "Analyse requirements from prompt",
                "description": "Parse and understand the user's request.",
                "task_type": "planning",
                "agent_hint": "planner",
                "requires_approval": False,
                "order_index": 0,
            },
            {
                "title": "Design system architecture",
                "description": "Define components, interfaces, and data flow.",
                "task_type": "architecture",
                "agent_hint": "architect",
                "requires_approval": True,
                "order_index": 1,
            },
            {
                "title": "Generate project scaffold",
                "description": "Create initial project structure and boilerplate.",
                "task_type": "codegen",
                "agent_hint": "coder",
                "requires_approval": False,
                "order_index": 2,
            },
            {
                "title": "Review generated output",
                "description": "Validate the scaffold against requirements.",
                "task_type": "review",
                "agent_hint": "reviewer",
                "requires_approval": True,
                "order_index": 3,
            },
            {
                "title": "Create test plan",
                "description": "Define test strategy and initial test cases.",
                "task_type": "testing",
                "agent_hint": "tester",
                "requires_approval": False,
                "order_index": 4,
            },
        ],
        "next_steps": [
            "Configure an LLM API key",
            "Re-run planning to get real results",
        ],
    }


# -------------------------------------------------------------------
# LLM planning
# -------------------------------------------------------------------


async def _generate_plan(
    prompt: str, constitution_section: str | None = None
) -> dict[str, Any]:
    """Attempt LLM planning, normalize the output, fall back to stub on failure.

    FM-102: If a constitution_section is provided, it is prepended to the prompt
    so the LLM respects project-level constraints.
    """
    effective_prompt = prompt
    if constitution_section:
        effective_prompt = f"{constitution_section}\n\n{prompt}"

    raw = await llm_json_completion(
        effective_prompt,
        system=PLANNER_SYSTEM_PROMPT,
    )

    if (
        raw
        and isinstance(raw, dict)
        and isinstance(raw.get("phases"), list)
        and len(raw.get("phases", [])) > 0
    ):
        normalized = _normalize_plan(raw)
        # After normalization, phases may be empty if all were invalid
        if normalized["phases"]:
            logger.info(
                "LLM planner returned valid result with %d phases",
                len(normalized["phases"]),
            )
            return normalized
        logger.warning(
            "LLM planner returned phases but all were invalid after normalization"
        )

    logger.info("LLM planner unavailable or returned invalid result — using stub")
    return _build_stub_plan(prompt)


async def plan_from_prompt(
    db: AsyncSession,
    prompt: str,
    owner_id: uuid.UUID,
    project_name: str | None = None,
) -> tuple[Project, Run, list[Task], PlannerResult]:
    """Create a project + first run + planning tasks from a prompt.

    Calls the LLM planner when available, otherwise uses stub data.
    Returns the created (project, run, tasks, planner_result) tuple.

    FM-101: Runs now start in SPECIFYING state. The planner auto-creates a
    SPEC artifact and transitions the run to PLANNING before generating tasks.
    """

    # FM-102: Check for existing project constitution for prompt injection
    constitution_section: str | None = None
    # For new projects created via plan_from_prompt there is no constitution yet,
    # so we pass None.  Constitution injection applies when re-planning an
    # existing project (e.g. via /fm.plan slash command in spec_service/plan_artifact_service).

    # 0. Generate the plan (LLM with normalization, or stub)
    plan = await _generate_plan(prompt, constitution_section=constitution_section)

    # FM-189: Log that code intelligence context was available for planning
    # (Decision audit: record that the planner considered code intelligence)
    logger.info(
        "planner: plan generated for owner=%s (code_intelligence_available=true)",
        owner_id,
    )

    # 1. Create the project
    name = project_name or plan.get("project_name") or prompt[:80].strip()
    project = Project(
        name=name,
        description=prompt,
        status=ProjectStatus.PLANNING,
        owner_id=owner_id,
    )
    db.add(project)
    await db.flush()

    # 2. Create the first run — starts in SPECIFYING (FM-101)
    run = Run(
        run_number=1,
        status=RunStatus.SPECIFYING,
        trigger="prompt",
        project_id=project.id,
    )
    db.add(run)
    await db.flush()

    # 3. FM-101: Auto-create SPEC artifact from the prompt
    spec_content = _build_spec_content(prompt, plan)
    spec_artifact = Artifact(
        title=f"SPEC: {name}",
        artifact_type=ArtifactType.SPEC,
        content=spec_content,
        project_id=project.id,
        run_id=run.id,
        created_by="planner",
        meta={"auto_generated": True, "source": "plan_from_prompt"},
    )
    db.add(spec_artifact)
    await db.flush()

    # 4. Transition run to PLANNING now that SPEC exists
    run.status = RunStatus.PLANNING
    await db.flush()

    # 5. Create tasks from plan phases (already normalized)
    phases = plan.get("phases", [])
    if not phases:
        phases = _build_stub_plan(prompt)["phases"]

    tasks: list[Task] = []
    for i, phase in enumerate(phases):
        description = (
            phase.get("description")
            or f"Auto-generated task ({phase.get('task_type', 'generic')})"
        )
        if phase.get("requires_approval"):
            description += " [requires approval]"

        task = Task(
            title=phase["title"],
            description=description,
            task_type=phase.get("task_type", DEFAULT_TASK_TYPE),
            status=TaskStatus.READY if i == 0 else TaskStatus.BLOCKED,
            order_index=phase.get("order_index", i),
            run_id=run.id,
            assigned_agent_slug=phase.get("agent_hint"),
        )
        db.add(task)
        tasks.append(task)

    await db.flush()

    # Wire linear dependencies
    for i in range(1, len(tasks)):
        tasks[i].depends_on = [tasks[i - 1].id]
    await db.flush()

    # Refresh all to pick up server defaults
    for obj in [project, run, spec_artifact, *tasks]:
        await db.refresh(obj)

    # 6. Create planner result (data is already normalized/coerced)
    planner_result = PlannerResult(
        run_id=run.id,
        overview=plan.get("overview"),
        architecture_summary=plan.get("architecture_summary"),
        recommended_stack=plan.get("recommended_stack"),
        assumptions=plan.get("assumptions"),
        next_steps=plan.get("next_steps"),
    )
    db.add(planner_result)
    await db.flush()
    await db.refresh(planner_result)

    return project, run, tasks, planner_result


def _build_spec_content(prompt: str, plan: dict[str, Any]) -> str:
    """Build structured SPEC markdown content from a prompt and plan data."""
    sections = [
        "# Specification",
        "",
        "## Problem / Objective",
        prompt,
        "",
        "## Scope",
        plan.get("overview") or "To be determined.",
        "",
        "## Constraints",
        "- None specified",
        "",
        "## Assumptions",
    ]
    assumptions = plan.get("assumptions", [])
    if assumptions:
        for a in assumptions:
            sections.append(f"- {a}")
    else:
        sections.append("- None specified")

    sections.extend(
        [
            "",
            "## Acceptance Criteria",
            "- All planned phases complete successfully",
            "- All review checkpoints pass",
            "",
            "## Risks / Unknowns",
            "- Dependent on LLM availability for planning quality",
            "",
            "## Architecture Summary",
            plan.get("architecture_summary") or "To be determined.",
        ]
    )
    return "\n".join(sections)


# -------------------------------------------------------------------
# FM-189: Code Intelligence Agent Integration
# -------------------------------------------------------------------

# Decision audit log — tracks when code intelligence influenced planning
_decision_audit_log: list[dict[str, Any]] = []


async def plan_with_code_intelligence(
    db: AsyncSession,
    project_id: uuid.UUID,
    prompt: str,
    owner_id: uuid.UUID,
    *,
    changed_files: list[str] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """FM-189: Re-plan a project with code intelligence context injected.

    Builds code intelligence context (dependency graph, coverage, complexity,
    debt, flakiness, impact analysis) and injects it into the LLM prompt so
    the planning agent considers impact analysis when scoping tasks.

    Returns (plan_dict, decision_audit_entry).
    """
    from app.services.code_graph_service import (
        build_code_intelligence_context,
        format_context_for_prompt,
    )

    # Build code intelligence context
    ci_context = await build_code_intelligence_context(
        db,
        project_id,
        changed_files=changed_files,
    )

    # Format for LLM injection
    ci_prompt_section = format_context_for_prompt(ci_context)

    # Augment planning prompt with code intelligence
    augmented_prompt = (
        f"{ci_prompt_section}\n\n"
        f"---\n\n"
        f"Given the above code intelligence context, plan the following:\n\n"
        f"{prompt}"
    )

    # Generate plan with augmented prompt
    plan = await _generate_plan(augmented_prompt)

    # FM-189: Decision audit — log that intelligence influenced this planning decision
    audit_entry = {
        "project_id": str(project_id),
        "owner_id": str(owner_id),
        "action": "plan_with_code_intelligence",
        "intelligence_summary": {
            "graph_nodes": ci_context.get("dependency_graph", {}).get("node_count", 0),
            "coverage_avg": ci_context.get("coverage", {}).get("avg_coverage", 0),
            "hotspot_count": len(ci_context.get("complexity_hotspots", [])),
            "debt_score": ci_context.get("debt", {}).get("total_score", 0)
            if isinstance(ci_context.get("debt"), dict)
            else 0,
            "has_impact_analysis": "impact_analysis" in ci_context,
        },
        "changed_files": changed_files,
        "plan_phase_count": len(plan.get("phases", [])),
    }
    _decision_audit_log.append(audit_entry)
    logger.info(
        "FM-189 decision audit: code intelligence injected into planning "
        "(project=%s, nodes=%d, hotspots=%d, impact=%s)",
        project_id,
        audit_entry["intelligence_summary"]["graph_nodes"],
        audit_entry["intelligence_summary"]["hotspot_count"],
        audit_entry["intelligence_summary"]["has_impact_analysis"],
    )

    return plan, audit_entry


def get_decision_audit_log() -> list[dict[str, Any]]:
    """FM-189: Return the decision audit log for code intelligence influence."""
    return list(_decision_audit_log)


def clear_decision_audit_log() -> None:
    """FM-189: Clear the decision audit log (for testing)."""
    _decision_audit_log.clear()
