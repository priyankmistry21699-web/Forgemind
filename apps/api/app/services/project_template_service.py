"""FM-114: Project Template service — CRUD + built-in seed data."""

import uuid
import logging
from typing import Any

from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project_template import ProjectTemplate
from app.schemas.project_template import ProjectTemplateCreate, ProjectTemplateUpdate

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Built-in templates — real, useful config (not empty scaffolding)
# ---------------------------------------------------------------------------

BUILTIN_TEMPLATES: list[dict[str, Any]] = [
    {
        "slug": "rest-api",
        "name": "REST API Service",
        "description": "Backend API project with structured endpoints, database layer, auth, and test coverage.",
        "category": "backend",
        "constitution_template": {
            "title": "REST API Project Constitution",
            "content": (
                "## Project Constitution — REST API\n\n"
                "### Guiding Principles\n"
                "1. Every endpoint must have request/response schema validation.\n"
                "2. All database operations use async sessions and proper transaction boundaries.\n"
                "3. Authentication and authorization are enforced on all non-public routes.\n"
                "4. Tests are required for all service functions and route handlers.\n"
                "5. Error responses follow RFC 7807 problem detail format.\n\n"
                "### Constraints\n"
                "- No raw SQL in route handlers — use service layer.\n"
                "- All list endpoints must support pagination.\n"
                "- Secrets must never appear in response payloads or logs.\n"
            ),
            "summary": "Governs a REST API project with schema validation, auth, and test requirements.",
        },
        "default_governance_config": {
            "require_spec_approval": True,
            "require_plan_approval": True,
            "auto_approve_minor_changes": False,
        },
        "default_phase_profiles": [
            {"phase": "specify", "agent_slug": "planner-agent", "priority": 0},
            {"phase": "plan", "agent_slug": "planner-agent", "priority": 0},
            {"phase": "implement", "agent_slug": "coder-agent", "priority": 0},
            {"phase": "review", "agent_slug": "reviewer-agent", "priority": 0},
        ],
        "suggested_task_types": [
            "architecture",
            "codegen",
            "testing",
            "documentation",
            "review",
        ],
        "spec_defaults": {
            "required_sections": [
                "Problem / Objective",
                "API Endpoints",
                "Data Models",
                "Auth Requirements",
                "Error Handling",
                "Acceptance Criteria",
            ],
            "constraints": [
                "RESTful conventions",
                "pagination on lists",
                "schema validation",
            ],
        },
        "plan_defaults": {
            "default_workstreams": [
                "database-schema",
                "service-layer",
                "routes",
                "tests",
                "documentation",
            ],
            "architecture_checklist": [
                "data model design",
                "endpoint structure",
                "auth flow",
                "error handling",
            ],
        },
    },
    {
        "slug": "frontend-app",
        "name": "Frontend Application",
        "description": "Web frontend project with component architecture, routing, state management, and accessibility standards.",
        "category": "frontend",
        "constitution_template": {
            "title": "Frontend App Project Constitution",
            "content": (
                "## Project Constitution — Frontend App\n\n"
                "### Guiding Principles\n"
                "1. Components must be composable and follow single-responsibility.\n"
                "2. All interactive elements must be keyboard-accessible.\n"
                "3. State management must be predictable — prefer server state over client state.\n"
                "4. Loading, error, and empty states must be handled for every async operation.\n"
                "5. Styling must use design tokens / CSS variables for consistency.\n\n"
                "### Constraints\n"
                "- No inline styles — use class-based or utility-first CSS.\n"
                "- API calls must go through typed client functions, never raw fetch.\n"
                "- Form inputs must validate on blur and on submit.\n"
            ),
            "summary": "Governs a frontend app with component standards, accessibility, and state management rules.",
        },
        "default_governance_config": {
            "require_spec_approval": True,
            "require_plan_approval": False,
            "auto_approve_minor_changes": True,
        },
        "default_phase_profiles": [
            {"phase": "specify", "agent_slug": "planner-agent", "priority": 0},
            {"phase": "plan", "agent_slug": "planner-agent", "priority": 0},
            {"phase": "implement", "agent_slug": "coder-agent", "priority": 0},
            {"phase": "review", "agent_slug": "reviewer-agent", "priority": 0},
        ],
        "suggested_task_types": ["codegen", "review", "testing", "documentation"],
        "spec_defaults": {
            "required_sections": [
                "Problem / Objective",
                "User Stories",
                "Component Breakdown",
                "Routing / Navigation",
                "Acceptance Criteria",
            ],
            "constraints": ["accessibility", "responsive design", "typed API clients"],
        },
        "plan_defaults": {
            "default_workstreams": [
                "components",
                "pages",
                "state",
                "api-integration",
                "styling",
                "tests",
            ],
            "architecture_checklist": [
                "component hierarchy",
                "data flow",
                "routing",
                "error boundaries",
            ],
        },
    },
    {
        "slug": "data-pipeline",
        "name": "Data Pipeline",
        "description": "ETL/data processing project with source connectors, transformation logic, validation, and scheduling.",
        "category": "data",
        "constitution_template": {
            "title": "Data Pipeline Project Constitution",
            "content": (
                "## Project Constitution — Data Pipeline\n\n"
                "### Guiding Principles\n"
                "1. Every transformation must be idempotent and replay-safe.\n"
                "2. Input data must be validated before processing.\n"
                "3. All pipeline stages must emit structured logs for observability.\n"
                "4. Schema changes require explicit migration steps.\n"
                "5. Sensitive data must be masked or encrypted at rest.\n\n"
                "### Constraints\n"
                "- No hard-coded connection strings — use configuration.\n"
                "- Pipeline failures must produce actionable error reports.\n"
                "- Batch sizes must be configurable per stage.\n"
            ),
            "summary": "Governs a data pipeline with idempotency, validation, and observability rules.",
        },
        "default_governance_config": {
            "require_spec_approval": True,
            "require_plan_approval": True,
            "auto_approve_minor_changes": False,
        },
        "default_phase_profiles": [
            {"phase": "specify", "agent_slug": "planner-agent", "priority": 0},
            {"phase": "plan", "agent_slug": "planner-agent", "priority": 0},
            {"phase": "implement", "agent_slug": "coder-agent", "priority": 0},
            {"phase": "validate", "agent_slug": "reviewer-agent", "priority": 0},
        ],
        "suggested_task_types": ["architecture", "codegen", "testing", "deployment"],
        "spec_defaults": {
            "required_sections": [
                "Problem / Objective",
                "Data Sources",
                "Transformations",
                "Output Schema",
                "SLA / Performance",
                "Acceptance Criteria",
            ],
            "constraints": ["idempotency", "schema validation", "error recovery"],
        },
        "plan_defaults": {
            "default_workstreams": [
                "source-connectors",
                "transformations",
                "validation",
                "output",
                "monitoring",
                "tests",
            ],
            "architecture_checklist": [
                "data lineage",
                "error handling",
                "scaling strategy",
                "schema management",
            ],
        },
    },
    {
        "slug": "cli-tool",
        "name": "CLI Tool",
        "description": "Command-line application with argument parsing, subcommands, output formatting, and user documentation.",
        "category": "tooling",
        "constitution_template": {
            "title": "CLI Tool Project Constitution",
            "content": (
                "## Project Constitution — CLI Tool\n\n"
                "### Guiding Principles\n"
                "1. Every command must have --help documentation.\n"
                "2. Output must support human-readable and machine-readable (JSON) formats.\n"
                "3. Exit codes must be meaningful (0 = success, 1 = error, 2 = usage error).\n"
                "4. Configuration should support file, environment variable, and flag sources.\n"
                "5. Destructive operations must require confirmation unless --force is passed.\n\n"
                "### Constraints\n"
                "- No interactive prompts in non-TTY mode.\n"
                "- All file paths must be validated before operations.\n"
                "- Error messages must be actionable.\n"
            ),
            "summary": "Governs a CLI tool with documentation, output format, and safety rules.",
        },
        "default_governance_config": {
            "require_spec_approval": False,
            "require_plan_approval": False,
            "auto_approve_minor_changes": True,
        },
        "default_phase_profiles": [
            {"phase": "specify", "agent_slug": "planner-agent", "priority": 0},
            {"phase": "implement", "agent_slug": "coder-agent", "priority": 0},
        ],
        "suggested_task_types": ["codegen", "testing", "documentation"],
        "spec_defaults": {
            "required_sections": [
                "Problem / Objective",
                "Commands / Subcommands",
                "Input / Output",
                "Configuration",
                "Acceptance Criteria",
            ],
            "constraints": ["exit codes", "help text", "JSON output option"],
        },
        "plan_defaults": {
            "default_workstreams": [
                "argument-parsing",
                "commands",
                "output-formatting",
                "config",
                "tests",
                "docs",
            ],
            "architecture_checklist": [
                "command structure",
                "config resolution",
                "error handling",
            ],
        },
    },
]


# ---------------------------------------------------------------------------
# Service functions
# ---------------------------------------------------------------------------


async def seed_builtin_templates(db: AsyncSession) -> list[ProjectTemplate]:
    """Seed all built-in templates. Skips any that already exist by slug."""
    created = []
    for tpl_data in BUILTIN_TEMPLATES:
        result = await db.execute(
            select(ProjectTemplate).where(ProjectTemplate.slug == tpl_data["slug"])
        )
        if result.scalar_one_or_none() is not None:
            continue

        template = ProjectTemplate(
            slug=tpl_data["slug"],
            name=tpl_data["name"],
            description=tpl_data["description"],
            category=tpl_data["category"],
            constitution_template=tpl_data.get("constitution_template"),
            default_governance_config=tpl_data.get("default_governance_config"),
            default_phase_profiles=tpl_data.get("default_phase_profiles"),
            suggested_task_types=tpl_data.get("suggested_task_types"),
            spec_defaults=tpl_data.get("spec_defaults"),
            plan_defaults=tpl_data.get("plan_defaults"),
            is_builtin=True,
            is_active=True,
        )
        db.add(template)
        created.append(template)

    if created:
        await db.flush()
        logger.info("Seeded %d built-in templates", len(created))
    return created


async def list_templates(
    db: AsyncSession,
    *,
    category: str | None = None,
    active_only: bool = True,
) -> tuple[list[ProjectTemplate], int]:
    """List templates, optionally filtered by category."""
    query = select(ProjectTemplate)
    if active_only:
        query = query.where(ProjectTemplate.is_active.is_(True))
    if category:
        query = query.where(ProjectTemplate.category == category)

    count_result = await db.execute(
        select(sa_func.count()).select_from(query.subquery())
    )
    total = count_result.scalar_one()

    result = await db.execute(query.order_by(ProjectTemplate.name))
    return list(result.scalars().all()), total


async def get_template(
    db: AsyncSession,
    template_id: uuid.UUID,
) -> ProjectTemplate | None:
    """Get a template by ID."""
    result = await db.execute(
        select(ProjectTemplate).where(ProjectTemplate.id == template_id)
    )
    return result.scalar_one_or_none()


async def get_template_by_slug(
    db: AsyncSession,
    slug: str,
) -> ProjectTemplate | None:
    """Get a template by slug."""
    result = await db.execute(
        select(ProjectTemplate).where(ProjectTemplate.slug == slug)
    )
    return result.scalar_one_or_none()


async def create_template(
    db: AsyncSession,
    data: ProjectTemplateCreate,
) -> ProjectTemplate:
    """Create a new custom template."""
    # Check slug uniqueness
    existing = await get_template_by_slug(db, data.slug)
    if existing:
        raise ValueError(f"Template with slug '{data.slug}' already exists")

    template = ProjectTemplate(
        slug=data.slug,
        name=data.name,
        description=data.description,
        category=data.category,
        constitution_template=data.constitution_template,
        default_governance_config=data.default_governance_config,
        default_phase_profiles=data.default_phase_profiles,
        suggested_task_types=data.suggested_task_types,
        spec_defaults=data.spec_defaults,
        plan_defaults=data.plan_defaults,
        is_builtin=False,
        is_active=True,
    )
    db.add(template)
    await db.flush()
    await db.refresh(template)
    logger.info("Created template %s (%s)", template.slug, template.id)
    return template


async def update_template(
    db: AsyncSession,
    template_id: uuid.UUID,
    data: ProjectTemplateUpdate,
) -> ProjectTemplate:
    """Update an existing template."""
    template = await get_template(db, template_id)
    if template is None:
        raise ValueError(f"Template {template_id} not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(template, field, value)

    await db.flush()
    await db.refresh(template)
    return template
