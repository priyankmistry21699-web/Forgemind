"""Planner service — converts a user prompt into a project, run, and planning tasks.

Attempts to call an LLM via LiteLLM to generate a real planning result.
Falls back to stub data if the LLM call fails or no API key is configured.
"""

import logging
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.llm import llm_json_completion
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
ALLOWED_TASK_TYPES = {"planning", "codegen", "verification", "testing", "deployment", "architecture", "review"}
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

        normalized.append({
            "title": title.strip()[:MAX_TITLE_LEN],
            "description": str(phase.get("description", ""))[:MAX_DESCRIPTION_LEN] if phase.get("description") else None,
            "task_type": task_type,
            "agent_hint": agent_hint,
            "requires_approval": requires_approval,
            "order_index": i,
        })

        if len(normalized) >= MAX_PHASES:
            break

    return normalized


def _normalize_plan(raw: dict[str, Any]) -> dict[str, Any]:
    """Normalize and validate an entire LLM plan output.

    Ensures all fields have correct types and safe values for persistence
    and frontend rendering.
    """
    return {
        "project_name": str(raw["project_name"]).strip()[:255] if isinstance(raw.get("project_name"), str) else None,
        "overview": str(raw["overview"]).strip() if isinstance(raw.get("overview"), str) else None,
        "architecture_summary": str(raw["architecture_summary"]).strip() if isinstance(raw.get("architecture_summary"), str) else None,
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
            {"title": "Analyse requirements from prompt", "description": "Parse and understand the user's request.", "task_type": "planning", "agent_hint": "planner", "requires_approval": False, "order_index": 0},
            {"title": "Design system architecture", "description": "Define components, interfaces, and data flow.", "task_type": "architecture", "agent_hint": "architect", "requires_approval": True, "order_index": 1},
            {"title": "Generate project scaffold", "description": "Create initial project structure and boilerplate.", "task_type": "codegen", "agent_hint": "coder", "requires_approval": False, "order_index": 2},
            {"title": "Review generated output", "description": "Validate the scaffold against requirements.", "task_type": "review", "agent_hint": "reviewer", "requires_approval": True, "order_index": 3},
            {"title": "Create test plan", "description": "Define test strategy and initial test cases.", "task_type": "testing", "agent_hint": "tester", "requires_approval": False, "order_index": 4},
        ],
        "next_steps": [
            "Configure an LLM API key",
            "Re-run planning to get real results",
        ],
    }


# -------------------------------------------------------------------
# LLM planning
# -------------------------------------------------------------------


async def _generate_plan(prompt: str) -> dict[str, Any]:
    """Attempt LLM planning, normalize the output, fall back to stub on failure."""
    raw = await llm_json_completion(
        prompt,
        system=PLANNER_SYSTEM_PROMPT,
    )

    if raw and isinstance(raw, dict) and isinstance(raw.get("phases"), list) and len(raw.get("phases", [])) > 0:
        normalized = _normalize_plan(raw)
        # After normalization, phases may be empty if all were invalid
        if normalized["phases"]:
            logger.info("LLM planner returned valid result with %d phases", len(normalized["phases"]))
            return normalized
        logger.warning("LLM planner returned phases but all were invalid after normalization")

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
    """

    # 0. Generate the plan (LLM with normalization, or stub)
    plan = await _generate_plan(prompt)
    is_stub = plan.get("overview", "").startswith("Stub planning result")

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

    # 2. Create the first run
    run = Run(
        run_number=1,
        status=RunStatus.PLANNING,
        trigger="prompt",
        project_id=project.id,
    )
    db.add(run)
    await db.flush()

    # 3. Create tasks from plan phases (already normalized)
    phases = plan.get("phases", [])
    if not phases:
        phases = _build_stub_plan(prompt)["phases"]

    tasks: list[Task] = []
    for i, phase in enumerate(phases):
        description = phase.get("description") or f"Auto-generated task ({phase.get('task_type', 'generic')})"
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
    for obj in [project, run, *tasks]:
        await db.refresh(obj)

    # 4. Create planner result (data is already normalized/coerced)
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
