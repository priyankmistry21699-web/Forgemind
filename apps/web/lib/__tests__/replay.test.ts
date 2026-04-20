/**
 * Direct tests for lib/replay.ts.
 */
import { describe, expect, it, vi, beforeEach } from "vitest";

const mocks = vi.hoisted(() => ({ apiFetch: vi.fn() }));
vi.mock("@/lib/api", () => ({
  apiFetch: mocks.apiFetch,
  ApiError: class ApiError extends Error {},
}));

import {
  fetchExecutionTrace,
  fetchTaskSnapshots,
  fetchSnapshot,
} from "../replay";

beforeEach(() => {
  mocks.apiFetch.mockReset();
});

describe("replay client", () => {
  it("fetchExecutionTrace hits /runs/:id/trace", async () => {
    mocks.apiFetch.mockResolvedValue({ events: [] });
    await fetchExecutionTrace("r-1");
    expect(mocks.apiFetch).toHaveBeenCalledWith("/runs/r-1/trace");
  });

  it("fetchTaskSnapshots uses defaults offset=0 limit=50", async () => {
    mocks.apiFetch.mockResolvedValue({ items: [], total: 0 });
    await fetchTaskSnapshots("t-1");
    expect(mocks.apiFetch).toHaveBeenCalledWith(
      "/tasks/t-1/snapshots?offset=0&limit=50",
    );
  });

  it("fetchSnapshot hits /replay/snapshots/:id", async () => {
    mocks.apiFetch.mockResolvedValue({ id: "s-1" });
    await fetchSnapshot("s-1");
    expect(mocks.apiFetch).toHaveBeenCalledWith("/replay/snapshots/s-1");
  });
});
