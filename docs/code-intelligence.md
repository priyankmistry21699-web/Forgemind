# Code Intelligence — Developer Guide (FM-181 → FM-190)

## Overview

ForgeMind's Code Intelligence layer automatically analyses your codebase to build a **dependency graph**, perform **impact analysis**, track **test coverage mapping**, detect **anti-patterns & technical debt**, monitor **test flakiness**, and measure **code complexity**.

All features are project-scoped and accessible via the `/api/v1/code-intelligence/` endpoints.

---

## Features

### FM-181 — Dependency Graph

Parses **Python** and **TypeScript/JavaScript** source files to extract import statements, storing edges in the `module_dependencies` table.

**Key service:** `code_graph_service.scan_file_dependencies(db, project_id, file_path, source_code)`

- **Python parser:** AST-based — resolves `import`, `from … import`, relative imports.
- **TypeScript parser:** Regex-based — resolves ES6 `import` (default, named, namespace, side-effect), `export … from`, CommonJS `require()`, and dynamic `import()`. Supports `.ts`, `.tsx`, `.js`, `.jsx`, `.mjs`, `.cjs` extensions.
- Incremental: files are hashed; unchanged files are skipped on re-scan.
- Graph query: `get_dependency_graph(db, project_id)` returns `{nodes, edges}`.

### FM-182 — Impact Analysis

Given a set of changed files, returns all transitively affected downstream files.

**Key service:** `code_graph_service.analyze_impact(db, project_id, changed_files)`

- Uses BFS over the dependency graph.
- Returns affected files with distance from change origin.

### FM-183 — Test Coverage Mapping

Links source files to their test files via `coverage_maps` records.

- `record_coverage(db, project_id, source_file, test_file, …)`
- `get_coverage_gaps(db, project_id)` — finds source files with no linked tests.
- `ingest_coverage_report(db, project_id, report)` — bulk import from CI coverage JSON.

### FM-184 — Pattern Detection & Debt Tracking

Configurable regex-based rules scan source code for anti-patterns (e.g. hardcoded secrets, TODO markers, God classes).

- Rules have `severity` (CRITICAL / WARNING / INFO) and `pattern_type` (ANTI / POSITIVE).
- `scan_file_for_patterns(db, project_id, file_path, source_code, rules)` records occurrences.
- CRITICAL and WARNING anti-pattern hits are **automatically promoted to Knowledge Base entries** (FM-185 integration).

### FM-185 — Knowledge Base Integration

Significant pattern detections (CRITICAL / WARNING, non-POSITIVE) are forwarded to the project Knowledge Base as `KnowledgeType.PATTERN` entries. Tags include `["pattern-detection", <severity>, <rule_name>]`.

### FM-186 — Technical Debt Scoring

Each file receives a debt score based on pattern occurrences, complexity metrics, and coverage gaps.

### FM-187 — Test Flakiness Tracker

Records test outcomes across runs and flags tests whose pass rate falls below a configurable threshold.

### FM-188 — Code Complexity Metrics

Computes cyclomatic complexity, lines of code, and maintainability index per file.

### FM-189 — Quarantine Monitor

Automatically quarantines flaky tests and tracks their recovery.

---

## Configuration

All code intelligence features are enabled by default per project. Pattern rules must be created explicitly via the API or service layer.

### Creating a Pattern Rule

```python
await pattern_debt_service.create_pattern_rule(
    db, name="hardcoded-secret",
    pattern_type=PatternType.ANTI,
    rule_definition=r"password\s*=\s*['\"]",
    severity=PatternSeverity.CRITICAL,
    description="Detects hardcoded passwords",
)
```

---

## Performance

- **Graph traversal:** <2 seconds for 10,000-file projects (benchmarked in `test_fm181_189_code_intelligence.py::TestGraphPerformance`).
- **Impact analysis:** <2 seconds for hub files with 200+ dependents.
- **Pattern scanning:** linear in file size; regex compilation is cached.

---

## Interpreting Results

| Metric                | Good             | Needs Attention      |
| --------------------- | ---------------- | -------------------- |
| Debt score            | <20              | >50                  |
| Cyclomatic complexity | <10 per function | >20                  |
| Test flakiness rate   | <5%              | >15%                 |
| Coverage gaps         | 0 files          | >10% of source files |

---

## API Endpoints

All under `/api/v1/code-intelligence/`:

| Method | Path                       | Description                             |
| ------ | -------------------------- | --------------------------------------- |
| POST   | `/scan`                    | Scan a file for dependencies + patterns |
| GET    | `/graph/{project_id}`      | Full dependency graph                   |
| POST   | `/impact`                  | Impact analysis for changed files       |
| GET    | `/coverage/{project_id}`   | Coverage summary                        |
| GET    | `/debt/{project_id}`       | Debt scores per file                    |
| GET    | `/flakiness/{project_id}`  | Flaky test report                       |
| GET    | `/complexity/{project_id}` | Complexity metrics                      |
| POST   | `/select-tests`            | FM-184: Intelligent test selection      |
| POST   | `/code-intelligence-context` | FM-189: Agent context bundle          |

---

## Intelligent Test Selection (FM-184)

Composes impact analysis (FM-182) and coverage mapping (FM-183) to select the minimal set of tests needed for a set of changed files.

```python
result = await code_graph_service.select_tests_for_changes(
    db, project_id, changed_files=["src/auth.py"], mode="standard",
)
# {"selected_tests": [...], "test_count": 5, "confidence": 0.85, ...}
```

**Modes:**
- `minimal` (depth 1) — only directly affected tests
- `standard` (depth 2) — includes 1-hop transitive dependencies
- `comprehensive` (depth 5) — full blast radius

**Confidence score:** `covered_sources / total_relevant_sources` — indicates how well the selected tests cover the blast radius.

---

## Agent Code Intelligence Context (FM-189)

Packages all code intelligence data into a single context for agent consumption:

```python
ctx = await code_graph_service.build_code_intelligence_context(
    db, project_id, changed_files=["src/main.py"],
)
prompt_text = code_graph_service.format_context_for_prompt(ctx)
```

Context includes: dependency graph summary, coverage metrics, coverage gaps, top 10 complexity hotspots, debt summary, flakiness data, and optional impact analysis for changed files.
