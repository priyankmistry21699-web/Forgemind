/**
 * Direct tests for lib/planner.ts.
 */
import { describe, expect, it, vi, beforeEach } from "vitest";

const mocks = vi.hoisted(() => ({ apiFetch: vi.fn() }));
vi.mock("@/lib/api", () => ({
  apiFetch: mocks.apiFetch,
  ApiError: class ApiError extends Error {},
}));

import { submitPromptIntake, fetchPlannerResult } from "../planner";

beforeEach(() => {
  mocks.apiFetch.mockReset();
});

describe("submitPromptIntake()", () => {
  it("POSTs /planner/intake with the full request body", async () => {
    mocks.apiFetch.mockResolvedValue({
      project_id: "p-1",
      run_id: "r-1",
      tasks_created: 3,
      message: "ok",
      created_at: new Date().toISOString(),
    });
    await submitPromptIntake({
      prompt: "Build a REST API for tasks",
      project_name: "Tasky",
    });
    expect(mocks.apiFetch).toHaveBeenCalledWith(
      "/planner/intake",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          prompt: "Build a REST API for tasks",
          project_name: "Tasky",
        }),
      }),
    );
  });

  it("propagates errors from apiFetch (no swallow)", async () => {
    mocks.apiFetch.mockRejectedValue(new Error("llm timeout"));
    await expect(
      submitPromptIntake({ prompt: "ten chars.", project_name: null }),
    ).rejects.toThrow("llm timeout");
  });
});

describe("fetchPlannerResult()", () => {
  it("targets /runs/:id/plan", async () => {
    mocks.apiFetch.mockResolvedValue({ run_id: "r-1" });
    await fetchPlannerResult("r-1");
    expect(mocks.apiFetch).toHaveBeenCalledWith("/runs/r-1/plan");
  });

  it("SWALLOWS errors and returns null rather than throwing", async () => {
    mocks.apiFetch.mockRejectedValue(new Error("404"));
    await expect(fetchPlannerResult("nope")).resolves.toBeNull();
  });
});
