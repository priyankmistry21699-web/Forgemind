/**
 * Direct tests for lib/connectors.ts.
 */
import { describe, expect, it, vi, beforeEach } from "vitest";

const mocks = vi.hoisted(() => ({ apiFetch: vi.fn() }));
vi.mock("@/lib/api", () => ({
  apiFetch: mocks.apiFetch,
  ApiError: class ApiError extends Error {},
}));

import { fetchConnectors, fetchProjectReadiness } from "../connectors";

beforeEach(() => {
  mocks.apiFetch.mockReset();
});

describe("connectors client", () => {
  it("fetchConnectors hits /connectors", async () => {
    mocks.apiFetch.mockResolvedValue({ items: [], total: 0 });
    await fetchConnectors();
    expect(mocks.apiFetch).toHaveBeenCalledWith("/connectors");
  });

  it("fetchProjectReadiness hits /projects/:id/connectors/readiness", async () => {
    mocks.apiFetch.mockResolvedValue({ ready: true, gaps: [] });
    await fetchProjectReadiness("p-1");
    expect(mocks.apiFetch).toHaveBeenCalledWith(
      "/projects/p-1/connectors/readiness",
    );
  });
});
