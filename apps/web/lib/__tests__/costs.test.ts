/**
 * Direct tests for lib/costs.ts.
 */
import { describe, expect, it, vi, beforeEach } from "vitest";

const mocks = vi.hoisted(() => ({ apiFetch: vi.fn() }));
vi.mock("@/lib/api", () => ({
  apiFetch: mocks.apiFetch,
  ApiError: class ApiError extends Error {},
}));

import {
  fetchCostRecords,
  fetchRunCostSummary,
  fetchProjectCostSummary,
  fetchCostBreakdown,
} from "../costs";

beforeEach(() => {
  mocks.apiFetch.mockReset();
});

describe("costs client", () => {
  it("fetchCostRecords uses defaults offset=0 limit=50", async () => {
    mocks.apiFetch.mockResolvedValue({ items: [], total: 0 });
    await fetchCostRecords();
    expect(mocks.apiFetch).toHaveBeenCalledWith("/costs?offset=0&limit=50");
  });

  it("fetchRunCostSummary hits /costs/runs/:id/summary", async () => {
    mocks.apiFetch.mockResolvedValue({ total_tokens: 0 });
    await fetchRunCostSummary("r-1");
    expect(mocks.apiFetch).toHaveBeenCalledWith("/costs/runs/r-1/summary");
  });

  it("fetchProjectCostSummary hits /costs/projects/:id/summary", async () => {
    mocks.apiFetch.mockResolvedValue({ total_tokens: 0 });
    await fetchProjectCostSummary("p-1");
    expect(mocks.apiFetch).toHaveBeenCalledWith("/costs/projects/p-1/summary");
  });

  it("fetchCostBreakdown hits /costs/breakdown", async () => {
    mocks.apiFetch.mockResolvedValue({ by_agent: {} });
    await fetchCostBreakdown();
    expect(mocks.apiFetch).toHaveBeenCalledWith("/costs/breakdown");
  });
});
