/**
 * FM-236/237: Tests for the Cost Analysis page.
 */

import { render, screen, waitFor } from "@testing-library/react";
import { vi, describe, it, expect, beforeEach } from "vitest";

vi.mock("@/lib/cost-attribution", () => ({
  getCostForecast: vi.fn().mockResolvedValue({
    project_id: "00000000-0000-0000-0000-000000000001",
    forecast_month: "2026-05",
    actual_spend_usd: 12.34,
    forecasted_spend_usd: 25.00,
    budget_usd: 50.0,
    burn_rate_usd_per_day: 0.82,
    days_remaining: 24,
    will_exceed_budget: false,
    confidence: 0.7,
    breakdown_by_agent: {
      codegen: 8.0,
      review: 4.34,
    },
  }),
  getRunCostAttribution: vi.fn().mockResolvedValue({
    run_id: "run-1",
    total_cost_usd: 0.12,
    by_agent: [],
  }),
}));

import CostAnalysisPage from "../page";

describe("CostAnalysisPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders heading", async () => {
    render(<CostAnalysisPage />);
    await waitFor(() => {
      expect(screen.getByText("Cost Analysis")).toBeInTheDocument();
    });
  });

  it("renders actual spend stat card", async () => {
    render(<CostAnalysisPage />);
    await waitFor(() => {
      expect(screen.getByText("$12.34")).toBeInTheDocument();
    });
  });

  it("renders forecast month", async () => {
    render(<CostAnalysisPage />);
    await waitFor(() => {
      expect(screen.getByText("2026-05")).toBeInTheDocument();
    });
  });

  it("renders burn rate", async () => {
    render(<CostAnalysisPage />);
    await waitFor(() => {
      expect(screen.getByText("$0.82/day")).toBeInTheDocument();
    });
  });

  it("renders agent breakdown table", async () => {
    render(<CostAnalysisPage />);
    await waitFor(() => {
      expect(screen.getByText("codegen")).toBeInTheDocument();
      expect(screen.getByText("review")).toBeInTheDocument();
    });
  });

  it("renders days remaining", async () => {
    render(<CostAnalysisPage />);
    await waitFor(() => {
      expect(screen.getByText("24")).toBeInTheDocument();
    });
  });
});
