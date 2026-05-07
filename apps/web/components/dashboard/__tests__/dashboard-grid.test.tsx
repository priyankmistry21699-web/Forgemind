/**
 * FM-197 — Dashboard grid layout tests.
 *
 * Verifies that layout metadata from the backend (columns, row_height,
 * per-widget position/size) is faithfully translated to CSS Grid
 * placement, and that the empty-state branch renders correctly.
 */

import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import type { DashboardLayout } from "@/types/dashboard";

// Stub the widget renderer so this test is truly a layout test, not a
// data-fetch test. We render a minimal marker that records the widget id.
vi.mock("../widget-renderer", () => ({
  WidgetRenderer: ({ widget }: { widget: { id: string; title?: string } }) => (
    <div data-testid={`widget-${widget.id}`}>{widget.title ?? widget.id}</div>
  ),
}));

import { DashboardGrid } from "../dashboard-grid";

describe("DashboardGrid", () => {
  it("renders the empty-state when layout has no widgets", () => {
    const layout: DashboardLayout = { widgets: [] };
    render(<DashboardGrid dashboardId="d1" projectId="p1" layout={layout} />);
    expect(
      screen.getByText(/this dashboard has no widgets yet/i),
    ).toBeInTheDocument();
  });

  it("treats missing widgets array as empty", () => {
    // widgets is explicitly missing to exercise the `?? []` branch.
    const layout = {} as DashboardLayout;
    render(<DashboardGrid dashboardId="d1" projectId="p1" layout={layout} />);
    expect(
      screen.getByText(/this dashboard has no widgets yet/i),
    ).toBeInTheDocument();
  });

  it("maps position+size to gridColumn / gridRow spans", () => {
    const layout: DashboardLayout = {
      columns: 12,
      row_height: 80,
      widgets: [
        {
          id: "a",
          widget_type: "health_score",
          chart_type: "gauge",
          position: { x: 0, y: 0 },
          size: { w: 6, h: 2 },
        },
        {
          id: "b",
          widget_type: "velocity",
          chart_type: "number",
          position: { x: 6, y: 0 },
          size: { w: 6, h: 2 },
        },
        {
          id: "c",
          widget_type: "quality",
          chart_type: "line",
          position: { x: 0, y: 2 },
          size: { w: 12, h: 3 },
        },
      ],
    };
    render(<DashboardGrid dashboardId="d1" projectId="p1" layout={layout} />);

    const a = screen.getByTestId("widget-a").parentElement as HTMLElement;
    const b = screen.getByTestId("widget-b").parentElement as HTMLElement;
    const c = screen.getByTestId("widget-c").parentElement as HTMLElement;

    // Grid uses 1-based indexing, so x=0 → colStart=1.
    expect(a.style.gridColumn).toBe("1 / span 6");
    expect(a.style.gridRow).toBe("1 / span 2");
    expect(b.style.gridColumn).toBe("7 / span 6");
    expect(b.style.gridRow).toBe("1 / span 2");
    expect(c.style.gridColumn).toBe("1 / span 12");
    expect(c.style.gridRow).toBe("3 / span 3");
  });

  it("clamps negative/missing span values to the minimum of 1", () => {
    const layout: DashboardLayout = {
      widgets: [
        {
          id: "broken",
          widget_type: "health_score",
          chart_type: "gauge",
          // Intentionally invalid — the grid engine should clamp.
          position: { x: -5, y: -3 },
          size: { w: 0, h: 0 },
        },
      ],
    };
    render(<DashboardGrid dashboardId="d1" projectId="p1" layout={layout} />);
    const el = screen.getByTestId("widget-broken").parentElement as HTMLElement;
    expect(el.style.gridColumn).toBe("1 / span 1");
    expect(el.style.gridRow).toBe("1 / span 1");
  });

  it("applies column and row-height overrides from the layout", () => {
    const layout: DashboardLayout = {
      columns: 4,
      row_height: 120,
      widgets: [
        {
          id: "x",
          widget_type: "quality",
          chart_type: "bar",
          position: { x: 0, y: 0 },
          size: { w: 4, h: 1 },
        },
      ],
    };
    const { container } = render(
      <DashboardGrid dashboardId="d1" projectId="p1" layout={layout} />,
    );
    const grid = container.firstElementChild as HTMLElement;
    expect(grid.style.gridTemplateColumns).toBe("repeat(4, minmax(0, 1fr))");
    expect(grid.style.gridAutoRows).toBe("120px");
  });
});
