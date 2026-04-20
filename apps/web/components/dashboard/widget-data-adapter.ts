/**
 * Widget data adapter.
 *
 * Normalizes the backend `WidgetDataEnvelope.data` payload — whose shape
 * differs per `widget_type` — into canonical primitives consumed by the
 * chart components: a primary scalar, a labeled series, and tabular rows.
 *
 * Defensive-by-design: never throws on unknown/missing fields. Any value
 * it cannot interpret is dropped and the caller renders an empty state.
 */

import type { WidgetType } from "@/types/dashboard";

export interface SeriesPoint {
  label: string;
  value: number;
}

export interface NormalizedWidget {
  /** Primary KPI (e.g. overall score). `null` if the payload has no clear scalar. */
  scalar: number | null;
  /** Optional secondary label to display next to the scalar. */
  scalarLabel?: string;
  /** Optional unit suffix (e.g. "%", "ms"). */
  unit?: string;
  /** Suggested [min, max] bounds (used by gauges). */
  bounds?: [number, number];
  /** Labeled categorical series — feeds bar/pie. */
  series: SeriesPoint[];
  /** Time-ordered numeric series — feeds line charts. */
  trend: SeriesPoint[];
  /** Generic table rows. */
  table: {
    columns: string[];
    rows: (string | number)[][];
  };
}

const EMPTY: NormalizedWidget = {
  scalar: null,
  series: [],
  trend: [],
  table: { columns: [], rows: [] },
};

function isRecord(v: unknown): v is Record<string, unknown> {
  return typeof v === "object" && v !== null && !Array.isArray(v);
}

function toNumber(v: unknown): number | null {
  if (typeof v === "number" && Number.isFinite(v)) return v;
  if (typeof v === "string") {
    const n = Number(v);
    return Number.isFinite(n) ? n : null;
  }
  return null;
}

function humanize(key: string): string {
  return key
    .replace(/[_-]+/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase())
    .replace(/\bPct\b/g, "%");
}

/** Extract a labeled series from any record whose values are numeric. */
function numericFieldsAsSeries(
  rec: Record<string, unknown>,
  include?: string[],
  exclude: string[] = [],
): SeriesPoint[] {
  const out: SeriesPoint[] = [];
  const keys = include ?? Object.keys(rec);
  for (const k of keys) {
    if (exclude.includes(k)) continue;
    const n = toNumber(rec[k]);
    if (n !== null) out.push({ label: humanize(k), value: n });
  }
  return out;
}

// ─── per-widget-type adapters ────────────────────────────────────────────

function adaptHealthScore(data: Record<string, unknown>): NormalizedWidget {
  const scalar = toNumber(data.overall_score);
  const componentKeys = [
    "exec_health_score",
    "quality_score",
    "velocity_score",
    "cost_score",
    "complexity_score",
    "reliability_score",
  ];
  const series = numericFieldsAsSeries(data, componentKeys);
  const grade = typeof data.grade === "string" ? data.grade : undefined;
  return {
    scalar,
    scalarLabel: grade ? `Grade ${grade}` : "Overall",
    unit: "",
    bounds: [0, 100],
    series,
    trend: series,
    table: {
      columns: ["Component", "Score"],
      rows: series.map((s) => [s.label, s.value.toFixed(1)]),
    },
  };
}

function adaptVelocity(data: Record<string, unknown>): NormalizedWidget {
  const scalar =
    toNumber(data.throughput_7d) ??
    toNumber(data.runs_completed) ??
    toNumber(data.velocity_score);
  const series = numericFieldsAsSeries(
    data,
    [
      "throughput_1d",
      "throughput_7d",
      "throughput_30d",
      "runs_completed",
      "runs_failed",
      "approvals_completed",
    ],
  );
  return {
    scalar,
    scalarLabel: "Throughput (7d)",
    unit: "",
    bounds: undefined,
    series,
    trend: series,
    table: {
      columns: ["Metric", "Value"],
      rows: series.map((s) => [s.label, s.value]),
    },
  };
}

function adaptQuality(data: Record<string, unknown>): NormalizedWidget {
  const scalar =
    toNumber(data.overall_quality_score) ??
    toNumber(data.quality_score) ??
    toNumber(data.pass_rate);
  const series = numericFieldsAsSeries(data, [
    "coverage_pct",
    "pass_rate",
    "flakiness_score",
    "review_approval_rate",
  ]);
  return {
    scalar,
    scalarLabel: "Quality",
    unit: "%",
    bounds: [0, 100],
    series,
    trend: series,
    table: {
      columns: ["Metric", "Value"],
      rows: series.map((s) => [s.label, s.value.toFixed(2)]),
    },
  };
}

function adaptExecution(data: Record<string, unknown>): NormalizedWidget {
  const scalar =
    toNumber(data.total_runs) ??
    toNumber(data.avg_duration_ms) ??
    toNumber(data.success_rate);
  const series = numericFieldsAsSeries(data, [
    "total_runs",
    "successful_runs",
    "failed_runs",
    "in_progress_runs",
  ]);
  const timingKeys = ["avg_duration_ms", "p50_duration_ms", "p95_duration_ms"];
  const trend = numericFieldsAsSeries(data, timingKeys);
  return {
    scalar,
    scalarLabel: "Total runs",
    series,
    trend: trend.length > 0 ? trend : series,
    table: {
      columns: ["Metric", "Value"],
      rows: [...series, ...trend].map((s) => [s.label, s.value]),
    },
  };
}

function adaptDebt(data: Record<string, unknown>): NormalizedWidget {
  const scalar =
    toNumber(data.total_debt_items) ??
    toNumber(data.total_debt) ??
    toNumber(data.debt_score);
  let series: SeriesPoint[] = [];
  const byType = data.by_type ?? data.by_category;
  if (isRecord(byType)) {
    series = numericFieldsAsSeries(byType);
  } else {
    series = numericFieldsAsSeries(data, [
      "critical",
      "high",
      "medium",
      "low",
      "info",
    ]);
  }
  return {
    scalar,
    scalarLabel: "Debt items",
    series,
    trend: series,
    table: {
      columns: ["Category", "Count"],
      rows: series.map((s) => [s.label, s.value]),
    },
  };
}

function adaptComplexity(data: Record<string, unknown>): NormalizedWidget {
  const scalar =
    toNumber(data.avg_cyclomatic_complexity) ??
    toNumber(data.avg_cyclomatic) ??
    toNumber(data.complexity_score);
  const series = numericFieldsAsSeries(data, [
    "avg_cyclomatic_complexity",
    "avg_cognitive_complexity",
    "max_cyclomatic_complexity",
    "files_analyzed",
  ]);
  // hotspots: list of { path, complexity } → table + bar
  let hotspots: SeriesPoint[] = [];
  let table: NormalizedWidget["table"] = {
    columns: ["Metric", "Value"],
    rows: series.map((s) => [s.label, s.value.toFixed(2)]),
  };
  const rawHot = data.hotspots ?? data.top_complex_files;
  if (Array.isArray(rawHot)) {
    hotspots = rawHot
      .slice(0, 10)
      .map((item) => {
        if (!isRecord(item)) return null;
        const label =
          (typeof item.path === "string" && item.path) ||
          (typeof item.file === "string" && item.file) ||
          (typeof item.name === "string" && item.name) ||
          "unknown";
        const value =
          toNumber(item.complexity) ??
          toNumber(item.cyclomatic) ??
          toNumber(item.score);
        if (value === null) return null;
        return { label, value };
      })
      .filter((v): v is SeriesPoint => v !== null);
    if (hotspots.length > 0) {
      table = {
        columns: ["File", "Complexity"],
        rows: hotspots.map((h) => [h.label, h.value]),
      };
    }
  }
  return {
    scalar,
    scalarLabel: "Avg complexity",
    series: hotspots.length > 0 ? hotspots : series,
    trend: series,
    table,
  };
}

function adaptFlakiness(data: Record<string, unknown>): NormalizedWidget {
  const scalar =
    toNumber(data.total_flaky) ??
    toNumber(data.flaky_count) ??
    toNumber(data.flakiness_score);
  const rawList = data.flaky_tests ?? data.tests ?? data.items;
  let rows: (string | number)[][] = [];
  let series: SeriesPoint[] = [];
  if (Array.isArray(rawList)) {
    rows = rawList
      .slice(0, 20)
      .map((item) => {
        if (!isRecord(item)) return null;
        const name =
          (typeof item.test_name === "string" && item.test_name) ||
          (typeof item.name === "string" && item.name) ||
          "unknown";
        const rate = toNumber(item.failure_rate) ?? toNumber(item.flake_rate);
        const runs = toNumber(item.runs) ?? toNumber(item.total_runs);
        return [name, rate !== null ? `${rate.toFixed(1)}%` : "—", runs ?? "—"];
      })
      .filter((r): r is (string | number)[] => r !== null);
    series = rawList
      .slice(0, 10)
      .map((item) => {
        if (!isRecord(item)) return null;
        const label =
          (typeof item.test_name === "string" && item.test_name) ||
          (typeof item.name === "string" && item.name) ||
          "unknown";
        const value = toNumber(item.failure_rate) ?? toNumber(item.flake_rate);
        if (value === null) return null;
        return { label, value };
      })
      .filter((v): v is SeriesPoint => v !== null);
  }
  if (series.length === 0) {
    series = numericFieldsAsSeries(data, [
      "total_flaky",
      "new_flaky",
      "resolved_flaky",
    ]);
  }
  return {
    scalar,
    scalarLabel: "Flaky tests",
    series,
    trend: series,
    table: {
      columns: ["Test", "Failure rate", "Runs"],
      rows,
    },
  };
}

const ADAPTERS: Record<
  WidgetType,
  (data: Record<string, unknown>) => NormalizedWidget
> = {
  health_score: adaptHealthScore,
  velocity: adaptVelocity,
  quality: adaptQuality,
  execution_metrics: adaptExecution,
  debt_summary: adaptDebt,
  complexity_summary: adaptComplexity,
  flakiness_summary: adaptFlakiness,
};

export function normalizeWidgetData(
  widgetType: WidgetType,
  data: Record<string, unknown> | null | undefined,
): NormalizedWidget {
  if (!data || !isRecord(data)) return EMPTY;
  const adapter = ADAPTERS[widgetType];
  if (!adapter) return EMPTY;
  try {
    return adapter(data);
  } catch {
    return EMPTY;
  }
}
