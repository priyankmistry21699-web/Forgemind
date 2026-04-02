"""Domain constants and enums — single source of truth for allowed values.

These mirror the string unions defined in the backend models and
the TypeScript types in @forgemind/types.
"""

PROJECT_STATUSES = frozenset({
    "draft",
    "planning",
    "active",
    "paused",
    "completed",
    "failed",
})

RUN_STATUSES = frozenset({
    "pending",
    "planning",
    "running",
    "paused",
    "completed",
    "failed",
})

TASK_STATUSES = frozenset({
    "pending",
    "blocked",
    "ready",
    "running",
    "completed",
    "failed",
    "skipped",
})

ARTIFACT_TYPES = frozenset({
    "plan_summary",
    "architecture",
    "implementation",
    "review",
    "test_report",
    "documentation",
    "other",
})

AGENT_STATUSES = frozenset({
    "active",
    "inactive",
    "deprecated",
})
