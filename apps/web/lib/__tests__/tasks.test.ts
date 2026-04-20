/**
 * Direct tests for lib/tasks.ts.
 */
import { describe, expect, it, vi, beforeEach } from "vitest";

const mocks = vi.hoisted(() => ({ apiFetch: vi.fn() }));
vi.mock("@/lib/api", () => ({
  apiFetch: mocks.apiFetch,
  ApiError: class ApiError extends Error {},
}));

import { fetchTasksByRun, retryTask, cancelTask } from "../tasks";

beforeEach(() => {
  mocks.apiFetch.mockReset();
});

describe("tasks client", () => {
  it("fetchTasksByRun hits /runs/:runId/tasks", async () => {
    mocks.apiFetch.mockResolvedValue({ items: [], total: 0 });
    await fetchTasksByRun("r-1");
    expect(mocks.apiFetch).toHaveBeenCalledWith("/runs/r-1/tasks");
  });

  it("retryTask POSTs /tasks/:id/retry with no body", async () => {
    mocks.apiFetch.mockResolvedValue({ id: "t-1", status: "ready" });
    await retryTask("t-1");
    expect(mocks.apiFetch).toHaveBeenCalledWith("/tasks/t-1/retry", {
      method: "POST",
    });
  });

  it("cancelTask POSTs /tasks/:id/cancel with no body", async () => {
    mocks.apiFetch.mockResolvedValue({ id: "t-1", status: "skipped" });
    await cancelTask("t-1");
    expect(mocks.apiFetch).toHaveBeenCalledWith("/tasks/t-1/cancel", {
      method: "POST",
    });
  });

  it("propagates errors from apiFetch", async () => {
    mocks.apiFetch.mockRejectedValue(new Error("409 conflict"));
    await expect(retryTask("t-1")).rejects.toThrow("409 conflict");
  });
});
