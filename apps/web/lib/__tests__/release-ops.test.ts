/**
 * Direct tests for lib/release-ops.ts.
 */
import { describe, expect, it, vi, beforeEach } from "vitest";

const mocks = vi.hoisted(() => ({ apiFetch: vi.fn() }));
vi.mock("@/lib/api", () => ({
  apiFetch: mocks.apiFetch,
  ApiError: class ApiError extends Error {},
}));

import {
  fetchRunReleasePackages,
  fetchProjectReleasePackages,
  fetchReleasePackage,
  generateReleasePackage,
  fetchEnvironments,
  fetchEnvironment,
  evaluateReadiness,
  evaluateGates,
  fetchGateResults,
  fetchRollbackReadiness,
  fetchPostReleaseReport,
} from "../release-ops";

beforeEach(() => {
  mocks.apiFetch.mockReset();
});

describe("release-ops client", () => {
  it("fetchRunReleasePackages hits /runs/:id/release-packages", async () => {
    mocks.apiFetch.mockResolvedValue({ items: [], total: 0 });
    await fetchRunReleasePackages("r-1");
    expect(mocks.apiFetch).toHaveBeenCalledWith("/runs/r-1/release-packages");
  });

  it("fetchProjectReleasePackages hits /projects/:id/release-packages", async () => {
    mocks.apiFetch.mockResolvedValue({ items: [], total: 0 });
    await fetchProjectReleasePackages("p-1");
    expect(mocks.apiFetch).toHaveBeenCalledWith(
      "/projects/p-1/release-packages",
    );
  });

  it("fetchReleasePackage hits /release-packages/:id", async () => {
    mocks.apiFetch.mockResolvedValue({ id: "pkg-1" });
    await fetchReleasePackage("pkg-1");
    expect(mocks.apiFetch).toHaveBeenCalledWith("/release-packages/pkg-1");
  });

  it("generateReleasePackage POSTs with no query when version is omitted", async () => {
    mocks.apiFetch.mockResolvedValue({ id: "pkg-1" });
    await generateReleasePackage("r-1");
    expect(mocks.apiFetch).toHaveBeenCalledWith(
      "/runs/r-1/release-packages/generate",
      { method: "POST" },
    );
  });

  it("generateReleasePackage URL-encodes the version param", async () => {
    mocks.apiFetch.mockResolvedValue({ id: "pkg-1" });
    await generateReleasePackage("r-1", "1.0 RC");
    expect(mocks.apiFetch).toHaveBeenCalledWith(
      "/runs/r-1/release-packages/generate?version=1.0%20RC",
      { method: "POST" },
    );
  });

  it("fetchEnvironments + fetchEnvironment hit expected URLs", async () => {
    mocks.apiFetch.mockResolvedValue({ items: [], total: 0 });
    await fetchEnvironments("p-1");
    expect(mocks.apiFetch).toHaveBeenCalledWith("/projects/p-1/environments");
    mocks.apiFetch.mockResolvedValue({ id: "env-1" });
    await fetchEnvironment("env-1");
    expect(mocks.apiFetch).toHaveBeenCalledWith("/environments/env-1");
  });

  it("evaluateReadiness hits readiness/:env URL", async () => {
    mocks.apiFetch.mockResolvedValue({ ready: true });
    await evaluateReadiness("pkg-1", "env-1");
    expect(mocks.apiFetch).toHaveBeenCalledWith(
      "/release-packages/pkg-1/readiness/env-1",
    );
  });

  it("evaluateGates POSTs /release-packages/:id/gates/evaluate", async () => {
    mocks.apiFetch.mockResolvedValue({ result: "pass" });
    await evaluateGates("pkg-1");
    expect(mocks.apiFetch).toHaveBeenCalledWith(
      "/release-packages/pkg-1/gates/evaluate",
      { method: "POST" },
    );
  });

  it("evaluateGates appends environment_id when provided", async () => {
    mocks.apiFetch.mockResolvedValue({ result: "pass" });
    await evaluateGates("pkg-1", "env-9");
    expect(mocks.apiFetch).toHaveBeenCalledWith(
      "/release-packages/pkg-1/gates/evaluate?environment_id=env-9",
      { method: "POST" },
    );
  });

  it("fetchGateResults + fetchRollbackReadiness + fetchPostReleaseReport URLs", async () => {
    mocks.apiFetch.mockResolvedValue({ items: [] });
    await fetchGateResults("pkg-1");
    expect(mocks.apiFetch).toHaveBeenCalledWith(
      "/release-packages/pkg-1/gates",
    );

    mocks.apiFetch.mockResolvedValue({ can_rollback: true });
    await fetchRollbackReadiness("pkg-1");
    expect(mocks.apiFetch).toHaveBeenCalledWith(
      "/release-packages/pkg-1/rollback-readiness",
    );

    mocks.apiFetch.mockResolvedValue({});
    await fetchPostReleaseReport("pkg-1");
    expect(mocks.apiFetch).toHaveBeenCalledWith(
      "/release-packages/pkg-1/report",
    );
  });
});
