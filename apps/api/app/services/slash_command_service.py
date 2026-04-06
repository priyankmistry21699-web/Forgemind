"""FM-104: Slash command parsing and routing for spec-driven workflow phases.

Supported commands:
  /fm.specify  — trigger SPEC generation
  /fm.plan     — trigger planning flow
  /fm.tasks    — generate tasks from plan
  /fm.implement — start implementation/execution
"""

import re
import uuid
import logging
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Command definitions
# ---------------------------------------------------------------------------

COMMAND_PREFIX = "/fm."

KNOWN_COMMANDS = {
    "specify": "Generate a SPEC artifact for the current run",
    "plan": "Generate a PLAN from the current SPEC",
    "tasks": "Generate tasks from the current PLAN",
    "implement": "Start implementation/execution of planned tasks",
}

# Regex: /fm.<command> followed by optional arguments
_COMMAND_PATTERN = re.compile(
    r"^/fm\.(specify|plan|tasks|implement)(?:\s+(.*))?$",
    re.IGNORECASE | re.DOTALL,
)


@dataclass
class ParsedCommand:
    """Result of parsing a slash command from a chat message."""

    command: str  # e.g. "specify", "plan"
    args: str  # everything after the command
    raw: str  # original message


@dataclass
class CommandResult:
    """Structured result from executing a slash command."""

    command: str
    action: str
    success: bool
    summary: str
    artifact_id: str | None = None
    run_id: str | None = None
    task_ids: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


def parse_command(message: str) -> ParsedCommand | None:
    """Parse a slash command from a chat message.

    Returns None if the message is not a slash command.
    """
    stripped = message.strip()
    match = _COMMAND_PATTERN.match(stripped)
    if match is None:
        return None
    return ParsedCommand(
        command=match.group(1).lower(),
        args=(match.group(2) or "").strip(),
        raw=stripped,
    )


def is_slash_command(message: str) -> bool:
    """Check if a message starts with a known slash command."""
    return parse_command(message) is not None


def list_commands() -> list[dict[str, str]]:
    """Return list of available commands with descriptions for autocomplete."""
    return [
        {"command": f"/fm.{name}", "description": desc}
        for name, desc in KNOWN_COMMANDS.items()
    ]


# ---------------------------------------------------------------------------
# Command execution
# ---------------------------------------------------------------------------


async def execute_command(
    db: AsyncSession,
    run_id: uuid.UUID,
    parsed: ParsedCommand,
) -> CommandResult:
    """Route a parsed command to the appropriate service and return a result."""
    from app.models.run import Run
    from sqlalchemy import select

    # Verify run exists
    run_result = await db.execute(select(Run).where(Run.id == run_id))
    run = run_result.scalar_one_or_none()
    if run is None:
        return CommandResult(
            command=parsed.command,
            action="error",
            success=False,
            summary="Run not found",
        )

    if parsed.command == "specify":
        return await _handle_specify(db, run, parsed.args)
    elif parsed.command == "plan":
        return await _handle_plan(db, run, parsed.args)
    elif parsed.command == "tasks":
        return await _handle_tasks(db, run, parsed.args)
    elif parsed.command == "implement":
        return await _handle_implement(db, run, parsed.args)
    else:
        return CommandResult(
            command=parsed.command,
            action="error",
            success=False,
            summary=f"Unknown command: {parsed.command}",
        )


async def _handle_specify(db: AsyncSession, run: Any, args: str) -> CommandResult:
    """Handle /fm.specify — generate a SPEC artifact."""
    from app.services import spec_service

    try:
        spec = await spec_service.generate_spec(
            db,
            run_id=run.id,
            project_id=run.project_id,
            user_prompt=args or None,
        )
        return CommandResult(
            command="specify",
            action="spec_generated",
            success=True,
            summary=f"SPEC artifact created: {spec.title}",
            artifact_id=str(spec.id),
            run_id=str(run.id),
        )
    except Exception as e:
        logger.exception("Failed to generate spec")
        return CommandResult(
            command="specify",
            action="error",
            success=False,
            summary=f"Failed to generate SPEC: {e}",
        )


async def _handle_plan(db: AsyncSession, run: Any, args: str) -> CommandResult:
    """Handle /fm.plan — generate a PLAN artifact from the SPEC."""
    from app.services import plan_artifact_service

    try:
        plan = await plan_artifact_service.generate_plan_artifact(
            db,
            run_id=run.id,
            project_id=run.project_id,
            user_prompt=args or None,
        )
        return CommandResult(
            command="plan",
            action="plan_generated",
            success=True,
            summary=f"PLAN artifact created: {plan.title}",
            artifact_id=str(plan.id),
            run_id=str(run.id),
        )
    except Exception as e:
        logger.exception("Failed to generate plan")
        return CommandResult(
            command="plan",
            action="error",
            success=False,
            summary=f"Failed to generate PLAN: {e}",
        )


async def _handle_tasks(db: AsyncSession, run: Any, args: str) -> CommandResult:
    """Handle /fm.tasks — list or generate tasks for the run."""
    from app.models.task import Task
    from sqlalchemy import select

    task_result = await db.execute(
        select(Task).where(Task.run_id == run.id).order_by(Task.order_index)
    )
    tasks = list(task_result.scalars().all())

    if not tasks:
        return CommandResult(
            command="tasks",
            action="no_tasks",
            success=True,
            summary="No tasks found for this run. Use /fm.plan first to generate a plan.",
        )

    task_lines = []
    for t in tasks:
        task_lines.append(f"- [{t.status.value}] {t.title} ({t.task_type})")

    return CommandResult(
        command="tasks",
        action="tasks_listed",
        success=True,
        summary=f"{len(tasks)} tasks in this run:\n" + "\n".join(task_lines),
        task_ids=[str(t.id) for t in tasks],
        details={
            "total": len(tasks),
            "by_status": _count_by_status(tasks),
        },
    )


async def _handle_implement(db: AsyncSession, run: Any, args: str) -> CommandResult:
    """Handle /fm.implement — transition run to RUNNING state."""
    from app.services import run_lifecycle_service
    from app.models.run import RunStatus

    result = await run_lifecycle_service.transition_run(db, run.id, RunStatus.RUNNING)

    if result.get("transitioned"):
        return CommandResult(
            command="implement",
            action="implementation_started",
            success=True,
            summary=f"Run transitioned to RUNNING ({result['from_status']} → {result['to_status']})",
            run_id=str(run.id),
        )
    else:
        return CommandResult(
            command="implement",
            action="transition_blocked",
            success=False,
            summary=f"Cannot start implementation: {result.get('reason', 'unknown')}",
            run_id=str(run.id),
        )


def _count_by_status(tasks: list) -> dict[str, int]:
    counts: dict[str, int] = {}
    for t in tasks:
        counts[t.status.value] = counts.get(t.status.value, 0) + 1
    return counts
