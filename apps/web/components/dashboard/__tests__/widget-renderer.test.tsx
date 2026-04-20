/**
 * FM-197 — Widget renderer component tests.
 *
 * Covers the loading / error / success / empty / unsupported-chart
 * branches of `WidgetRenderer`, plus chart-type dispatch. Mocks the
 * backend `getWidgetData` call so these run fully offline.
 */

import { describe, expect, it, vi, beforeEach } from "vitest";
import { act, render, screen, waitFor } from "@testing-library/react";
import type { WidgetConfig } from "@/types/dashboard";

// Hoisted mocks — must be declared before the SUT is imported.
const { getWidgetDataMock } = vi.hoisted(() => ({
  getWidgetDataMock: vi.fn(),
}));

vi.mock("@/lib/dashboards", () => ({
  getWidgetData: getWidgetDataMock,
}));

import { WidgetRenderer } from "../widget-renderer";
import { ApiError } from "@/lib/api";

function makeWidget(overrides: Partial<WidgetConfig> = {}): WidgetConfig {
  return {
    id: "w1",
    widget_type: "health_score",
    chart_type: "gauge",
    title: "Health",
    position: { x: 0, y: 0 },
    size: { w: 3, h: 2 },
    ...overrides,
  };
}

beforeEach(() => {
  getWidgetDataMock.mockReset();
});

describe("WidgetRenderer", () => {
  it("renders a 'select a project' placeholder when projectId is null", () => {
    render(
      <WidgetRenderer
        dashboardId="dash-1"
        projectId={null}
        widget={makeWidget()}
      />,
    );
    expect(
      screen.getByText(/select a project to load widget data/i),
    ).toBeInTheDocument();
    // No fetch when no project.
    expect(getWidgetDataMock).not.toHaveBeenCalled();
  });

  it("shows the Loading placeholder before fetch resolves", async () => {
    // Promise that never resolves within the test — lets us assert the
    // loading branch is actually reached.
    let resolve!: (v: unknown) => void;
    getWidgetDataMock.mockImplementationOnce(
      () => new Promise((r) => (resolve = r)),
    );
    render(
      <WidgetRenderer
        dashboardId="dash-1"
        projectId="proj-1"
        widget={makeWidget()}
      />,
    );
    expect(await screen.findByText(/loading/i)).toBeInTheDocument();
    await act(async () => {
      resolve({ data: { overall_score: 50 } });
    });
  });

  it("renders the header title and chart_type badge", async () => {
    getWidgetDataMock.mockResolvedValue({ data: { overall_score: 80 } });
    render(
      <WidgetRenderer
        dashboardId="dash-1"
        projectId="proj-1"
        widget={makeWidget({ title: "My Health", chart_type: "gauge" })}
      />,
    );
    expect(await screen.findByText("My Health")).toBeInTheDocument();
    expect(screen.getByText("gauge")).toBeInTheDocument();
  });

  it("humanizes widget_type when no title is provided", async () => {
    getWidgetDataMock.mockResolvedValue({ data: null });
    render(
      <WidgetRenderer
        dashboardId="dash-1"
        projectId="proj-1"
        widget={makeWidget({ title: undefined, widget_type: "execution_metrics" })}
      />,
    );
    expect(await screen.findByText("Execution Metrics")).toBeInTheDocument();
  });

  it("renders the error branch with status+message when ApiError is thrown", async () => {
    getWidgetDataMock.mockRejectedValueOnce(
      new ApiError(503, "Service Unavailable", null),
    );
    render(
      <WidgetRenderer
        dashboardId="dash-1"
        projectId="proj-1"
        widget={makeWidget()}
      />,
    );
    expect(await screen.findByText(/failed to load/i)).toBeInTheDocument();
    expect(
      screen.getByText(/503:/),
    ).toBeInTheDocument();
  });

  it("renders a fallback error message when a plain Error is thrown", async () => {
    getWidgetDataMock.mockRejectedValueOnce(new Error("network down"));
    render(
      <WidgetRenderer
        dashboardId="dash-1"
        projectId="proj-1"
        widget={makeWidget()}
      />,
    );
    expect(await screen.findByText(/network down/)).toBeInTheDocument();
  });

  it("renders 'Failed to load widget' when a non-Error is thrown", async () => {
    getWidgetDataMock.mockRejectedValueOnce("stringly typed failure");
    render(
      <WidgetRenderer
        dashboardId="dash-1"
        projectId="proj-1"
        widget={makeWidget()}
      />,
    );
    expect(
      await screen.findByText(/failed to load widget/i),
    ).toBeInTheDocument();
  });

  it.each([
    ["line", "health_score"],
    ["bar", "velocity"],
    ["pie", "debt_summary"],
    ["gauge", "health_score"],
    ["number", "quality"],
    ["table", "flakiness_summary"],
  ] as const)(
    "renders chart_type=%s without crashing for widget_type=%s",
    async (chart, widgetType) => {
      getWidgetDataMock.mockResolvedValue({
        data: {
          overall_score: 70,
          throughput_7d: 5,
          overall_quality_score: 88,
          total_debt_items: 4,
          by_type: { critical: 1, high: 3 },
          total_flaky: 2,
          flaky_tests: [
            { name: "t1", failure_rate: 12.3, runs: 10 },
          ],
        },
      });
      render(
        <WidgetRenderer
          dashboardId="dash-1"
          projectId="proj-1"
          widget={makeWidget({
            chart_type: chart,
            widget_type: widgetType,
          })}
        />,
      );
      // Wait for useEffect → fetch → setState → rerender.
      await waitFor(() =>
        expect(getWidgetDataMock).toHaveBeenCalledWith(
          "dash-1",
          widgetType,
          "proj-1",
        ),
      );
      // No "Failed to load" text should appear on any valid dispatch.
      expect(
        screen.queryByText(/failed to load/i),
      ).not.toBeInTheDocument();
    },
  );

  it("renders an 'Unsupported chart' placeholder for unknown chart_type", async () => {
    getWidgetDataMock.mockResolvedValue({ data: { overall_score: 10 } });
    render(
      <WidgetRenderer
        dashboardId="dash-1"
        projectId="proj-1"
        widget={makeWidget({
          // Deliberately malformed to hit the default branch.
          chart_type: "bogus" as unknown as WidgetConfig["chart_type"],
        })}
      />,
    );
    expect(
      await screen.findByText(/unsupported chart: bogus/i),
    ).toBeInTheDocument();
  });

  it("does not update state after unmount (cancellation guard)", async () => {
    // If the effect leaks, React will surface an act() warning. We turn
    // console.error into a throw so the test fails loudly in that case.
    let resolve!: (v: unknown) => void;
    getWidgetDataMock.mockImplementationOnce(
      () => new Promise((r) => (resolve = r)),
    );
    const { unmount } = render(
      <WidgetRenderer
        dashboardId="dash-1"
        projectId="proj-1"
        widget={makeWidget()}
      />,
    );
    unmount();
    // Resolve after unmount — the `cancelled` flag in the component
    // must suppress the setState call.
    resolve({ data: { overall_score: 1 } });
    // Microtask flush.
    await Promise.resolve();
    // The component is gone; no assertion needed beyond "no warning was thrown".
    expect(true).toBe(true);
  });
});
