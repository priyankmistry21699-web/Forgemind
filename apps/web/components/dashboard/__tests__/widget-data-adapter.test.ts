/**
 * FM-197 — Widget data adapter unit tests.
 *
 * These tests pin the contract between the FastAPI
 * `WidgetDataEnvelope.data` payload shapes (per widget_type) and the
 * canonical `NormalizedWidget` primitives consumed by the chart
 * components. They protect against silent backend-schema drift that
 * `next build` alone cannot catch.
 */

import { describe, expect, it } from "vitest";
import { normalizeWidgetData } from "../widget-data-adapter";
import type { WidgetType } from "@/types/dashboard";

describe("normalizeWidgetData — boundary inputs", () => {
  const EVERY_WIDGET: WidgetType[] = [
    "health_score",
    "velocity",
    "quality",
    "execution_metrics",
    "debt_summary",
    "complexity_summary",
    "flakiness_summary",
  ];

  it("returns the EMPTY shape for null data on every widget type", () => {
    for (const t of EVERY_WIDGET) {
      const out = normalizeWidgetData(t, null);
      expect(out.scalar).toBeNull();
      expect(out.series).toEqual([]);
      expect(out.trend).toEqual([]);
      expect(out.table.rows).toEqual([]);
    }
  });

  it("returns the EMPTY shape for undefined data", () => {
    for (const t of EVERY_WIDGET) {
      const out = normalizeWidgetData(t, undefined);
      expect(out.scalar).toBeNull();
    }
  });

  it("returns the EMPTY shape when given non-object data (number, string, array)", () => {
    for (const t of EVERY_WIDGET) {
      // @ts-expect-error deliberately exercising the runtime guard
      expect(normalizeWidgetData(t, 42).scalar).toBeNull();
      // @ts-expect-error deliberately exercising the runtime guard
      expect(normalizeWidgetData(t, "oops").scalar).toBeNull();
      // @ts-expect-error deliberately exercising the runtime guard
      expect(normalizeWidgetData(t, [1, 2, 3]).scalar).toBeNull();
    }
  });

  it("returns EMPTY for an unknown widget_type (forward-compat guard)", () => {
    const out = normalizeWidgetData("not_a_real_widget" as WidgetType, {
      foo: 1,
    });
    expect(out).toEqual({
      scalar: null,
      series: [],
      trend: [],
      table: { columns: [], rows: [] },
    });
  });
});

describe("normalizeWidgetData — health_score", () => {
  it("maps overall_score → scalar and components → series", () => {
    const out = normalizeWidgetData("health_score", {
      overall_score: 87.3,
      grade: "B",
      exec_health_score: 90,
      quality_score: 85,
      velocity_score: 80,
    });
    expect(out.scalar).toBe(87.3);
    expect(out.scalarLabel).toBe("Grade B");
    expect(out.bounds).toEqual([0, 100]);
    expect(out.series).toEqual([
      { label: "Exec Health Score", value: 90 },
      { label: "Quality Score", value: 85 },
      { label: "Velocity Score", value: 80 },
    ]);
    expect(out.table.columns).toEqual(["Component", "Score"]);
    expect(out.table.rows[0]).toEqual(["Exec Health Score", "90.0"]);
  });

  it("uses 'Overall' label when grade is missing", () => {
    const out = normalizeWidgetData("health_score", { overall_score: 50 });
    expect(out.scalarLabel).toBe("Overall");
  });

  it("coerces stringified numeric scores", () => {
    const out = normalizeWidgetData("health_score", {
      overall_score: "72.5",
    });
    expect(out.scalar).toBe(72.5);
  });

  it("drops non-numeric component values silently", () => {
    const out = normalizeWidgetData("health_score", {
      overall_score: 60,
      quality_score: "not-a-number",
      velocity_score: 55,
    });
    const labels = out.series.map((s) => s.label);
    expect(labels).not.toContain("Quality Score");
    expect(labels).toContain("Velocity Score");
  });
});

describe("normalizeWidgetData — velocity", () => {
  it("prefers throughput_7d as the scalar", () => {
    const out = normalizeWidgetData("velocity", {
      throughput_1d: 3,
      throughput_7d: 21,
      throughput_30d: 80,
    });
    expect(out.scalar).toBe(21);
    expect(out.scalarLabel).toBe("Throughput (7d)");
  });

  it("falls back through scalar candidates", () => {
    const out = normalizeWidgetData("velocity", {
      runs_completed: 11,
    });
    expect(out.scalar).toBe(11);
  });
});

describe("normalizeWidgetData — quality", () => {
  it("maps overall_quality_score with % unit and [0,100] bounds", () => {
    const out = normalizeWidgetData("quality", {
      overall_quality_score: 92.4,
      coverage_pct: 88,
      pass_rate: 97,
      flakiness_score: 2,
    });
    expect(out.scalar).toBe(92.4);
    expect(out.unit).toBe("%");
    expect(out.bounds).toEqual([0, 100]);
    expect(out.series.map((s) => s.label)).toEqual([
      "Coverage %",
      "Pass Rate",
      "Flakiness Score",
    ]);
  });
});

describe("normalizeWidgetData — execution_metrics", () => {
  it("pulls total_runs as scalar and splits series/trend", () => {
    const out = normalizeWidgetData("execution_metrics", {
      total_runs: 120,
      successful_runs: 100,
      failed_runs: 15,
      in_progress_runs: 5,
      avg_duration_ms: 1200,
      p50_duration_ms: 900,
      p95_duration_ms: 2800,
    });
    expect(out.scalar).toBe(120);
    expect(out.series.map((s) => s.label)).toEqual([
      "Total Runs",
      "Successful Runs",
      "Failed Runs",
      "In Progress Runs",
    ]);
    expect(out.trend.map((s) => s.label)).toEqual([
      "Avg Duration Ms",
      "P50 Duration Ms",
      "P95 Duration Ms",
    ]);
  });

  it("falls back trend → series when timing keys missing", () => {
    const out = normalizeWidgetData("execution_metrics", {
      total_runs: 3,
      successful_runs: 3,
    });
    expect(out.trend.length).toBeGreaterThan(0);
    expect(out.trend).toEqual(out.series);
  });
});

describe("normalizeWidgetData — debt_summary", () => {
  it("uses by_type when present", () => {
    const out = normalizeWidgetData("debt_summary", {
      total_debt_items: 42,
      by_type: { critical: 3, high: 9, medium: 20, low: 10 },
    });
    expect(out.scalar).toBe(42);
    const kv = Object.fromEntries(out.series.map((s) => [s.label, s.value]));
    expect(kv.Critical).toBe(3);
    expect(kv.Low).toBe(10);
  });

  it("falls back to flat severity fields when by_type is absent", () => {
    const out = normalizeWidgetData("debt_summary", {
      total_debt_items: 7,
      critical: 1,
      high: 2,
      medium: 3,
      low: 1,
    });
    expect(out.series).toHaveLength(4);
  });
});

describe("normalizeWidgetData — complexity_summary", () => {
  it("prefers hotspots over generic series when available", () => {
    const out = normalizeWidgetData("complexity_summary", {
      avg_cyclomatic_complexity: 6.2,
      files_analyzed: 200,
      hotspots: [
        { path: "a.py", complexity: 35 },
        { path: "b.py", complexity: 28 },
      ],
    });
    expect(out.scalar).toBe(6.2);
    expect(out.series.map((s) => s.label)).toEqual(["a.py", "b.py"]);
    expect(out.table.columns).toEqual(["File", "Complexity"]);
    expect(out.table.rows).toEqual([
      ["a.py", 35],
      ["b.py", 28],
    ]);
  });

  it("drops non-object / value-less hotspot entries defensively", () => {
    const out = normalizeWidgetData("complexity_summary", {
      avg_cyclomatic_complexity: 5,
      hotspots: [
        { path: "ok.py", complexity: 10 },
        "not-an-object",
        { path: "no-complexity.py" /* value missing → dropped */ },
        // An entry with no name but a valid numeric complexity is kept
        // by design — the adapter labels it "unknown" rather than losing
        // a signal. Verify that behavior explicitly here.
        { complexity: 5 },
      ],
    });
    // Exactly the two entries with numeric complexity survive.
    expect(out.series).toHaveLength(2);
    expect(out.series[0].label).toBe("ok.py");
    expect(out.series[1].label).toBe("unknown");
  });

  it("falls back to metric series when hotspots are missing", () => {
    const out = normalizeWidgetData("complexity_summary", {
      avg_cyclomatic_complexity: 4.1,
      avg_cognitive_complexity: 3.7,
      max_cyclomatic_complexity: 19,
    });
    expect(out.series.length).toBeGreaterThan(0);
    expect(out.series[0].label).toBe("Avg Cyclomatic Complexity");
  });
});

describe("normalizeWidgetData — flakiness_summary", () => {
  it("builds a row-oriented table from the flaky_tests list", () => {
    const out = normalizeWidgetData("flakiness_summary", {
      total_flaky: 3,
      flaky_tests: [
        { test_name: "test_a", failure_rate: 22.5, runs: 100 },
        { name: "test_b", flake_rate: 10.0, total_runs: 50 },
        { name: "test_c" /* no rate */ },
      ],
    });
    expect(out.scalar).toBe(3);
    expect(out.table.columns).toEqual(["Test", "Failure rate", "Runs"]);
    expect(out.table.rows[0]).toEqual(["test_a", "22.5%", 100]);
    expect(out.table.rows[1]).toEqual(["test_b", "10.0%", 50]);
    // Third row kept but with em-dash placeholders
    expect(out.table.rows[2][1]).toBe("—");
    expect(out.table.rows[2][2]).toBe("—");
  });

  it("aggregates a numeric series when no flaky list is provided", () => {
    const out = normalizeWidgetData("flakiness_summary", {
      total_flaky: 5,
      new_flaky: 2,
      resolved_flaky: 1,
    });
    expect(out.series.length).toBeGreaterThan(0);
  });
});

describe("normalizeWidgetData — adapter exception safety", () => {
  it("returns EMPTY rather than throwing on adversarial shapes", () => {
    // Provide a data object whose by_type is a function — would crash an
    // unguarded adapter. The adapter should swallow this and return EMPTY.
    const adversarial = Object.create(null);
    Object.defineProperty(adversarial, "total_debt_items", {
      get() {
        throw new Error("boom");
      },
      enumerable: true,
    });
    const out = normalizeWidgetData("debt_summary", adversarial);
    expect(out.scalar).toBeNull();
  });
});
