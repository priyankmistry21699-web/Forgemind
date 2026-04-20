/**
 * Direct tests for lib/artifacts.ts.
 */
import { describe, expect, it, vi, beforeEach } from "vitest";

const mocks = vi.hoisted(() => ({ apiFetch: vi.fn() }));
vi.mock("@/lib/api", () => ({
  apiFetch: mocks.apiFetch,
  ApiError: class ApiError extends Error {},
}));

import { fetchArtifacts, fetchArtifact } from "../artifacts";

beforeEach(() => {
  mocks.apiFetch.mockReset();
});

describe("artifacts client", () => {
  it("fetchArtifacts with no runId hits /projects/:id/artifacts", async () => {
    mocks.apiFetch.mockResolvedValue({ items: [], total: 0 });
    await fetchArtifacts("p-1");
    expect(mocks.apiFetch).toHaveBeenCalledWith("/projects/p-1/artifacts");
  });

  it("fetchArtifacts appends ?run_id when provided", async () => {
    mocks.apiFetch.mockResolvedValue({ items: [], total: 0 });
    await fetchArtifacts("p-1", "r-9");
    expect(mocks.apiFetch).toHaveBeenCalledWith(
      "/projects/p-1/artifacts?run_id=r-9",
    );
  });

  it("fetchArtifact hits /artifacts/:id", async () => {
    mocks.apiFetch.mockResolvedValue({ id: "a-1" });
    await fetchArtifact("a-1");
    expect(mocks.apiFetch).toHaveBeenCalledWith("/artifacts/a-1");
  });
});
