/**
 * Direct tests for lib/trust.ts.
 */
import { describe, expect, it, vi, beforeEach } from "vitest";

const mocks = vi.hoisted(() => ({ apiFetch: vi.fn() }));
vi.mock("@/lib/api", () => ({
  apiFetch: mocks.apiFetch,
  ApiError: class ApiError extends Error {},
}));

import { fetchTrustScores, fetchRunRiskSummary } from "../trust";

beforeEach(() => {
  mocks.apiFetch.mockReset();
});

describe("trust client", () => {
  it("fetchTrustScores uses defaults offset=0 limit=50", async () => {
    mocks.apiFetch.mockResolvedValue({ items: [], total: 0 });
    await fetchTrustScores();
    expect(mocks.apiFetch).toHaveBeenCalledWith(
      "/trust/scores?offset=0&limit=50",
    );
  });

  it("fetchTrustScores threads custom pagination", async () => {
    mocks.apiFetch.mockResolvedValue({ items: [], total: 0 });
    await fetchTrustScores(20, 10);
    expect(mocks.apiFetch).toHaveBeenCalledWith(
      "/trust/scores?offset=20&limit=10",
    );
  });

  it("fetchRunRiskSummary hits /trust/runs/:id/risk-summary", async () => {
    mocks.apiFetch.mockResolvedValue({ risk_level: "low" });
    await fetchRunRiskSummary("r-1");
    expect(mocks.apiFetch).toHaveBeenCalledWith(
      "/trust/runs/r-1/risk-summary",
    );
  });
});
