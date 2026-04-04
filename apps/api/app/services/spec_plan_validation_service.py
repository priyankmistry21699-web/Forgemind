"""FM-108: Spec-to-plan validation rules.

Validates that a PLAN artifact adequately covers the SPEC's scope,
constraints, and acceptance criteria. Used as a lifecycle gate — blocks
implementation if the plan is deemed incomplete.
"""

import re
import uuid
import logging
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.services import spec_service, plan_artifact_service

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Validation result
# ---------------------------------------------------------------------------


@dataclass
class ValidationIssue:
    """A single validation finding."""

    rule: str
    severity: str  # "error" | "warning"
    message: str


@dataclass
class SpecPlanValidationResult:
    """Complete validation result for a SPEC→PLAN pair."""

    run_id: str
    spec_id: str | None
    plan_id: str | None
    valid: bool
    issues: list[ValidationIssue] = field(default_factory=list)
    coverage: dict[str, bool] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "spec_id": self.spec_id,
            "plan_id": self.plan_id,
            "valid": self.valid,
            "issues": [
                {"rule": i.rule, "severity": i.severity, "message": i.message}
                for i in self.issues
            ],
            "coverage": self.coverage,
        }


# ---------------------------------------------------------------------------
# Validation rules
# ---------------------------------------------------------------------------

# Required sections in a valid SPEC
_SPEC_SECTIONS = [
    "Problem / Objective",
    "Scope",
    "Constraints",
    "Acceptance Criteria",
]

# Required sections in a valid PLAN
_PLAN_SECTIONS = [
    "Overview",
    "Phase",
]


def _has_section(content: str, section_name: str) -> bool:
    """Check if markdown content contains a section heading."""
    pattern = re.compile(rf"^#+\s+.*{re.escape(section_name)}", re.MULTILINE | re.IGNORECASE)
    return bool(pattern.search(content))


def _extract_spec_criteria(spec_content: str) -> list[str]:
    """Extract acceptance criteria lines from SPEC content."""
    criteria: list[str] = []
    in_criteria = False
    for line in spec_content.split("\n"):
        if re.match(r"^#+\s+Acceptance\s+Criteria", line, re.IGNORECASE):
            in_criteria = True
            continue
        if in_criteria:
            if re.match(r"^#+\s+", line):  # Next section
                break
            stripped = line.strip().lstrip("- ").strip()
            if stripped and stripped.lower() != "none specified":
                criteria.append(stripped)
    return criteria


def _extract_spec_constraints(spec_content: str) -> list[str]:
    """Extract constraint lines from SPEC content."""
    constraints: list[str] = []
    in_section = False
    for line in spec_content.split("\n"):
        if re.match(r"^#+\s+Constraints", line, re.IGNORECASE):
            in_section = True
            continue
        if in_section:
            if re.match(r"^#+\s+", line):
                break
            stripped = line.strip().lstrip("- ").strip()
            if stripped and stripped.lower() != "none specified":
                constraints.append(stripped)
    return constraints


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def validate_spec_plan(
    db: AsyncSession,
    run_id: uuid.UUID,
) -> SpecPlanValidationResult:
    """Validate that a run's PLAN adequately covers its SPEC.

    Returns a validation result with issues and coverage map.
    Errors block lifecycle transitions; warnings are advisory.
    """
    result = SpecPlanValidationResult(
        run_id=str(run_id),
        spec_id=None,
        plan_id=None,
        valid=True,
    )

    # Load SPEC
    spec = await spec_service.get_spec_for_run(db, run_id)
    if spec is None:
        result.valid = False
        result.issues.append(ValidationIssue(
            rule="spec_exists",
            severity="error",
            message="No SPEC artifact found. Generate a SPEC first (/fm.specify).",
        ))
        return result

    result.spec_id = str(spec.id)
    spec_content = spec.content or ""

    # Load PLAN
    plan = await plan_artifact_service.get_plan_for_run(db, run_id)
    if plan is None:
        result.valid = False
        result.issues.append(ValidationIssue(
            rule="plan_exists",
            severity="error",
            message="No PLAN artifact found. Generate a PLAN first (/fm.plan).",
        ))
        return result

    result.plan_id = str(plan.id)
    plan_content = plan.content or ""

    # Rule 1: PLAN links to SPEC
    if plan.spec_artifact_id != spec.id:
        result.issues.append(ValidationIssue(
            rule="plan_linked_to_spec",
            severity="warning",
            message="PLAN is not linked to the current SPEC via spec_artifact_id.",
        ))
    result.coverage["plan_linked_to_spec"] = (plan.spec_artifact_id == spec.id)

    # Rule 2: SPEC has required sections
    for section in _SPEC_SECTIONS:
        has = _has_section(spec_content, section)
        result.coverage[f"spec_section_{section}"] = has
        if not has:
            result.issues.append(ValidationIssue(
                rule="spec_completeness",
                severity="warning",
                message=f"SPEC is missing section: {section}",
            ))

    # Rule 3: PLAN has required sections
    for section in _PLAN_SECTIONS:
        has = _has_section(plan_content, section)
        result.coverage[f"plan_section_{section}"] = has
        if not has:
            result.issues.append(ValidationIssue(
                rule="plan_completeness",
                severity="error",
                message=f"PLAN is missing required section: {section}",
            ))
            result.valid = False

    # Rule 4: PLAN is not empty/trivial
    if len(plan_content.strip()) < 100:
        result.valid = False
        result.issues.append(ValidationIssue(
            rule="plan_substance",
            severity="error",
            message="PLAN content is too short (< 100 chars). Generate a proper plan.",
        ))
    result.coverage["plan_substance"] = len(plan_content.strip()) >= 100

    # Rule 5: Acceptance criteria coverage — check that plan mentions
    # key terms from each acceptance criterion
    criteria = _extract_spec_criteria(spec_content)
    criteria_covered = 0
    for criterion in criteria:
        # Check if key words from the criterion appear in plan
        words = [w for w in criterion.lower().split() if len(w) > 4]
        if not words:
            criteria_covered += 1
            continue
        matches = sum(1 for w in words if w in plan_content.lower())
        covered = matches >= max(1, len(words) // 3)
        if covered:
            criteria_covered += 1
        else:
            result.issues.append(ValidationIssue(
                rule="acceptance_criteria_coverage",
                severity="warning",
                message=f"PLAN may not address acceptance criterion: '{_truncate(criterion, 80)}'",
            ))
    total_criteria = len(criteria) or 1
    result.coverage["acceptance_criteria"] = criteria_covered >= total_criteria * 0.5

    # Rule 6: Constraints acknowledged
    constraints = _extract_spec_constraints(spec_content)
    if constraints and not any(
        c.lower().split()[0] in plan_content.lower()
        for c in constraints
        if c.split()
    ):
        result.issues.append(ValidationIssue(
            rule="constraints_acknowledged",
            severity="warning",
            message="PLAN does not appear to reference any SPEC constraints.",
        ))
    result.coverage["constraints_acknowledged"] = not bool(constraints) or any(
        c.lower().split()[0] in plan_content.lower()
        for c in constraints
        if c.split()
    )

    # Final: any errors → invalid
    if any(i.severity == "error" for i in result.issues):
        result.valid = False

    return result


def _truncate(text: str, length: int) -> str:
    if len(text) <= length:
        return text
    return text[: length - 3] + "..."
