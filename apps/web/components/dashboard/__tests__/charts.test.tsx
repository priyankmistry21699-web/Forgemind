/**
 * FM-197 — Chart primitive smoke tests.
 *
 * These don't try to pixel-test SVG rendering; they verify the
 * empty-state branches and a couple of formatting invariants that would
 * silently regress under `next build` but impact what the operator sees.
 */

import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { LineChart } from "../charts/line-chart";
import { BarChart } from "../charts/bar-chart";
import { PieChart } from "../charts/pie-chart";
import { GaugeChart } from "../charts/gauge-chart";
import { StatNumber } from "../charts/stat-number";
import { DataTable } from "../charts/data-table";

describe("LineChart", () => {
  it("renders 'No data points' on empty series", () => {
    render(<LineChart data={[]} />);
    expect(screen.getByText(/no data points/i)).toBeInTheDocument();
  });

  it("renders a single-value degenerate display", () => {
    render(<LineChart data={[{ label: "t", value: 42.3 }]} unit="%" />);
    expect(screen.getByText(/42\.3%/)).toBeInTheDocument();
  });

  it("renders an SVG path when given ≥2 points", () => {
    const { container } = render(
      <LineChart
        data={[
          { label: "t1", value: 10 },
          { label: "t2", value: 20 },
          { label: "t3", value: 15 },
        ]}
      />,
    );
    expect(container.querySelector("svg")).not.toBeNull();
    expect(container.querySelectorAll("circle").length).toBe(3);
  });
});

describe("GaugeChart", () => {
  it("shows 'No reading available' when value is null", () => {
    render(<GaugeChart value={null} />);
    expect(screen.getByText(/no reading available/i)).toBeInTheDocument();
  });

  it("clamps values above max into the [min, max] window", () => {
    const { container } = render(
      <GaugeChart value={9999} min={0} max={100} unit="%" />,
    );
    const svg = container.querySelector("svg");
    expect(svg?.getAttribute("aria-label")).toContain("100.0%");
  });

  it("renders for NaN as the no-reading branch", () => {
    render(<GaugeChart value={Number.NaN} />);
    expect(screen.getByText(/no reading available/i)).toBeInTheDocument();
  });
});

describe("StatNumber", () => {
  it("renders 'No value' for null/NaN", () => {
    render(<StatNumber value={null} />);
    expect(screen.getByText(/no value/i)).toBeInTheDocument();
  });

  it("formats large numbers with locale grouping (system-independent)", () => {
    // Use a jsdom-stable locale so the test is deterministic across
    // developer machines that ship with different default locales
    // (e.g. en-US "1,234,567" vs en-IN "12,34,567").
    const orig = Number.prototype.toLocaleString;
    Number.prototype.toLocaleString = function (
      _locale?: string | string[],
      opts?: Intl.NumberFormatOptions,
    ) {
      return orig.call(this, "en-US", opts);
    };
    try {
      render(<StatNumber value={1234567} unit="$" />);
      expect(screen.getByText(/1,234,567/)).toBeInTheDocument();
    } finally {
      Number.prototype.toLocaleString = orig;
    }
  });

  it("formats integer-valued floats as integers", () => {
    render(<StatNumber value={42.0} />);
    expect(screen.getByText(/^42$/)).toBeInTheDocument();
  });
});

describe("BarChart / PieChart empty states", () => {
  it("BarChart handles empty data without crashing", () => {
    const { container } = render(<BarChart data={[]} />);
    expect(container).toBeTruthy();
  });

  it("PieChart handles empty data without crashing", () => {
    const { container } = render(<PieChart data={[]} />);
    expect(container).toBeTruthy();
  });
});

describe("DataTable", () => {
  it("renders headers and rows when data is present", () => {
    render(
      <DataTable
        columns={["Metric", "Value"]}
        rows={[
          ["Coverage", "88%"],
          ["Pass rate", "97%"],
        ]}
      />,
    );
    expect(screen.getByText("Metric")).toBeInTheDocument();
    expect(screen.getByText("Coverage")).toBeInTheDocument();
    expect(screen.getByText("97%")).toBeInTheDocument();
  });

  it("renders gracefully with empty rows", () => {
    const { container } = render(<DataTable columns={["A", "B"]} rows={[]} />);
    expect(container).toBeTruthy();
  });
});
