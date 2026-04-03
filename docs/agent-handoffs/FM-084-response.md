# FM-084 — Architecture Rule Engine

## Summary

Implemented a rule definition and evaluation engine for architecture governance. Supports 5 rule categories with category-specific evaluators that check the architecture graph and record pass/fail results with violating node/edge references.

## Deliverables

### Service (`apps/api/app/services/architecture_rule_service.py`)

- **`create_rule(db, project_id, data)`** — Create an ArchitectureRule with category, rule_config JSON, severity, enabled flag
- **`list_rules(db, project_id)`** — List all rules for a project
- **`evaluate_rule(db, rule_id)`** — Run a rule against the current graph; dispatch to category-specific evaluator; create ArchitectureRuleResult
- **`list_rule_results(db, project_id)`** — List all evaluation results for a project
- **`_evaluate_import_rule(db, rule, project_id)`** — Check for forbidden import patterns between node types
- **`_evaluate_layer_rule(db, rule, project_id)`** — Validate layer isolation constraints
- **`_evaluate_dependency_rule(db, rule, project_id)`** — Check dependency direction and cycle constraints
- **`_evaluate_ownership_rule(db, rule, project_id)`** — Verify node ownership/path conventions

### Rule Categories

1. **import_rule** — Forbidden import patterns (e.g., routes must not import models directly)
2. **layer_rule** — Layer isolation constraints (e.g., services cannot depend on routes)
3. **dependency_rule** — Dependency direction and cycle detection
4. **ownership_rule** — Node path/naming conventions (e.g., all services must be in services/ directory)
5. **boundary_rule** — Module boundary enforcement

### Route Endpoints (4)

- `POST /projects/{pid}/architecture/rules` — Create rule
- `GET /projects/{pid}/architecture/rules` — List rules
- `POST /projects/{pid}/architecture/rules/{rid}/evaluate` — Evaluate rule
- `GET /projects/{pid}/architecture/rule-results` — List results

## Tests

9 tests covering:

- `TestArchitectureRuleService` (3 tests) — create rule, import rule pass, import rule violation
- `TestArchitectureRuleRoutes` (4 tests) — create/list/evaluate rule routes, list results
- `TestOwnershipRuleEvaluator` (2 tests) — ownership violation, ownership pass

## Test Results

- **Total**: 482 passing
- **Regression**: None
