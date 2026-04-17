# Analytics & Portfolio Operations — Admin Guide (FM-191 → FM-200)

## Overview

ForgeMind's Analytics layer provides **execution metrics**, **health scoring**, **velocity & quality tracking**, **portfolio dashboards**, **scheduled reports**, **metric alerts**, and **executive summaries** with natural-language narratives.

---

## Features

### FM-191 — Execution Metrics

Every task and run status transition automatically records an `ExecutionMetric` via lifecycle hooks in `task_service` and `run_lifecycle_service`.

- Metric types: `LLM_CALL_DURATION`, `TOOL_CALL_DURATION`, `QUEUE_TIME`, `TOTAL_RUN_TIME`, `TOKEN_USAGE`.
- Auto-capture: wired into `update_task_status()` and `transition_run()` — no manual instrumentation needed.

### FM-192 — Health Scoring

Composite health score (0–100) with letter grade (A–F) computed from weighted dimensions: velocity, quality, cost efficiency, reliability.

### FM-193 — Cost Budget Enforcement

Per-project cost budgets with automatic alerts when spending exceeds configurable thresholds.

### FM-194 — Velocity Metrics

Tracks completed runs, runs per day, average completion time, and trend direction.

### FM-195 — Quality Metrics

Test pass rate, defect density, code review coverage, and quality gate enforcement.

### FM-196 — Portfolio Overview

Multi-project dashboard aggregating health, velocity, cost, and quality across an organization.

- `get_portfolio_summary(db, project_ids, sort_by, sort_order, filter_min_runs)`
- Supports sorting by health, cost, velocity, last activity.
- Performance: <1 second for 50 projects (benchmarked).

### FM-197 — Custom Dashboards & Widgets

Widget data resolution for 7+ chart types (velocity, quality, cost, health, etc.).

- **Widget config validation:** `validate_widget_config()` / `validate_dashboard_layout()` validates widget_type, chart_type (line, bar, pie, table, number, gauge), position, and size before persistence.
- **Data source resolution:** `resolve_widget_data()` dispatches to the correct service and returns chart-ready JSON.
- **Layout persistence:** `layout_json` stored on Dashboard model.
- **Note:** Visual widget rendering is a frontend concern (React components). Backend provides all data/validation infrastructure.

### FM-198 — Scheduled Reports

Background cron-based scheduler generates reports on user-defined schedules.

- Cron expressions: standard 5-field format (`minute hour dom month dow`).
- Supported syntax: `*`, literals, comma lists, ranges (`1-5`), steps (`*/10`).
- Scheduler runs every 60 seconds in the FastAPI lifespan background loop.

### FM-199 — Executive Summary with Narrative

`generate_executive_summary()` returns structured JSON **plus** a `narrative` field containing a human-readable, non-technical paragraph summarizing:

- Health grade and score with strong/weak dimensions
- Velocity: completed runs and throughput
- Quality: pass rate categorization and defect density warnings

### FM-200 — Hardening

Performance benchmarks verify:

- Metric queries respond in <500ms for 90-day windows with 500+ records.
- Health computation completes in <500ms.
- Portfolio summary for 50 projects returns in <1 second.

---

## Metric Definitions

| Metric            | Unit         | Source                                     |
| ----------------- | ------------ | ------------------------------------------ |
| LLM Call Duration | ms           | Auto-captured per LLM invocation           |
| Queue Time        | ms           | Time from task creation to execution start |
| Total Run Time    | ms           | End-to-end run duration                    |
| Token Usage       | tokens       | Cumulative tokens per run                  |
| Test Pass Rate    | ratio (0–1)  | Passed tests / total tests                 |
| Defect Density    | defects/KLOC | Defects found / thousands of lines         |

---

## Dashboard Setup

1. **Create a dashboard:** POST to `/dashboards` with name, project_id, visibility.
2. **Add widgets:** Each widget references a `widget_type` (velocity, quality, cost, health, etc.).
3. **Resolve data:** GET `/dashboards/{id}/widgets/{widget_id}/data` returns chart-ready JSON.

---

## Alert Configuration

Alerts trigger when a metric crosses a threshold:

```python
await dashboard_alert_service.create_alert_rule(
    db, project_id=project_id,
    metric_type=ExecutionMetricType.LLM_CALL_DURATION,
    condition_op=AlertConditionOp.GREATER_THAN,
    threshold=5000.0,  # 5 seconds
    cooldown_minutes=60,
)
```

Alerts respect cooldown periods to avoid notification storms.

---

## Scheduled Report Setup

```python
await dashboard_alert_service.create_scheduled_report(
    db, project_id=project_id,
    report_type="executive_summary",
    cron_expression="0 9 * * 1",  # Every Monday at 9 AM UTC
)
```

The background scheduler (`scheduled_report_loop`) checks every 60 seconds and executes matching reports.
