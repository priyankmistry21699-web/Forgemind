/**
 * Direct tests for lib/agents.ts.
 */
import { describe, expect, it, vi, beforeEach } from "vitest";

const mocks = vi.hoisted(() => ({ apiFetch: vi.fn() }));
vi.mock("@/lib/api", () => ({
  apiFetch: mocks.apiFetch,
  ApiError: class ApiError extends Error {},
}));

import { fetchAgents, fetchAgent } from "../agents";

beforeEach(() => {
  mocks.apiFetch.mockReset();
});

describe("agents client", () => {
  it("fetchAgents hits /agents", async () => {
    mocks.apiFetch.mockResolvedValue({ items: [], total: 0 });
    await fetchAgents();
    expect(mocks.apiFetch).toHaveBeenCalledWith("/agents");
  });

  it("fetchAgent hits /agents/:id", async () => {
    mocks.apiFetch.mockResolvedValue({ id: "a-1" });
    await fetchAgent("a-1");
    expect(mocks.apiFetch).toHaveBeenCalledWith("/agents/a-1");
  });
});
