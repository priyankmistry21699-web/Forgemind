/**
 * FM-239/240: Tests for the SLOs & Anomalies page.
 */

import { render, screen, waitFor } from "@testing-library/react";
import { vi, describe, it, expect, beforeEach } from "vitest";

vi.mock("@/lib/slos", () => ({
  listSLOs: vi.fn().mockResolvedValue([
    {
      id: "slo-1",
      name: "Run success SLO",
      metric: "run_success_rate",
      threshold: 0.9,
      target_pct: 0.99,
      window_days: 30,
      latest_attainment_pct: 0.97,
      latest_met: true,
    },
  ]),
  listAnomalies: vi.fn().mockResolvedValue([
    {
      id: "a-1",
      type: "error_rate_jump",
      severity: "high",
      title: "High run error rate: 75%",
      metric_value: 0.75,
      deviation_pct: null,
      resolved: false,
      detected_at: "2026-05-07T08:00:00Z",
    },
  ]),
  computeSLO: vi.fn().mockResolvedValue({
    slo_id: "slo-1",
    attainment_pct: 0.97,
    met: true,
    total_events: 100,
    p50: 200,
    p95: 500,
    p99: 900,
  }),
  triggerAnomalyScan: vi.fn().mockResolvedValue({ detected: 0 }),
}));

import SLOsPage from "../page";

describe("SLOsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders heading", async () => {
    render(<SLOsPage />);
    await waitFor(() => {
      expect(screen.getByText("SLOs & Anomalies")).toBeInTheDocument();
    });
  });

  it("renders SLO row", async () => {
    render(<SLOsPage />);
    await waitFor(() => {
      expect(screen.getByText("Run success SLO")).toBeInTheDocument();
      expect(screen.getByText("run_success_rate")).toBeInTheDocument();
    });
  });

  it("renders attainment percentage", async () => {
    render(<SLOsPage />);
    await waitFor(() => {
      expect(screen.getByText("97.0%")).toBeInTheDocument();
    });
  });

  it("renders met badge", async () => {
    render(<SLOsPage />);
    await waitFor(() => {
      expect(screen.getByText("met")).toBeInTheDocument();
    });
  });

  it("renders anomaly entry", async () => {
    render(<SLOsPage />);
    await waitFor(() => {
      expect(screen.getByText("High run error rate: 75%")).toBeInTheDocument();
    });
  });

  it("renders Run Scan button", async () => {
    render(<SLOsPage />);
    await waitFor(() => {
      expect(screen.getByText("Run Scan")).toBeInTheDocument();
    });
  });
});
