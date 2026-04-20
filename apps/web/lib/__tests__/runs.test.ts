/**
 * Direct tests for lib/runs.ts.
 */
import { describe, expect, it, vi, beforeEach } from "vitest";

const mocks = vi.hoisted(() => ({ apiFetch: vi.fn() }));
vi.mock("@/lib/api", () => ({
  apiFetch: mocks.apiFetch,
  ApiError: class ApiError extends Error {},
}));

import { fetchRun, fetchRunsByProject } from "../runs";

beforeEach(() => {
  mocks.apiFetch.mockReset();
});

describe("runs client", () => {
  it("fetchRun hits /runs/:id", async () => {
    mocks.apiFetch.mockResolvedValue({ id: "r-1" });
    await fetchRun("r-1");
    expect(mocks.apiFetch).toHaveBeenCalledWith("/runs/r-1");
  });

  it("fetchRunsByProject uses default skip=0&limit=20", async () => {
    mocks.apiFetch.mockResolvedValue({ items: [], total: 0 });
    await fetchRunsByProject("p-1");
    expect(mocks.apiFetch).toHaveBeenCalledWith(
      "/projects/p-1/runs?skip=0&limit=20",
    );
  });

  it("fetchRunsByProject threads custom pagination", async () => {
    mocks.apiFetch.mockResolvedValue({ items: [], total: 0 });
    await fetchRunsByProject("p-1", 10, 5);
    expect(mocks.apiFetch).toHaveBeenCalledWith(
      "/projects/p-1/runs?skip=10&limit=5",
    );
  });
});
