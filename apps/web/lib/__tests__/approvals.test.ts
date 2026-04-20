/**
 * Direct tests for lib/approvals.ts.
 */
import { describe, expect, it, vi, beforeEach } from "vitest";

const mocks = vi.hoisted(() => ({ apiFetch: vi.fn() }));
vi.mock("@/lib/api", () => ({
  apiFetch: mocks.apiFetch,
  ApiError: class ApiError extends Error {},
}));

import { fetchApprovals, decideApproval } from "../approvals";

beforeEach(() => {
  mocks.apiFetch.mockReset();
});

describe("fetchApprovals()", () => {
  it("hits /approvals with no query when called with no filters", async () => {
    mocks.apiFetch.mockResolvedValue({ items: [], total: 0 });
    await fetchApprovals();
    expect(mocks.apiFetch).toHaveBeenCalledWith("/approvals");
  });

  it("builds the project_id + run_id + status query params in order", async () => {
    mocks.apiFetch.mockResolvedValue({ items: [], total: 0 });
    await fetchApprovals({
      projectId: "p1",
      runId: "r1",
      status: "pending",
    });
    expect(mocks.apiFetch).toHaveBeenCalledWith(
      "/approvals?project_id=p1&run_id=r1&status=pending",
    );
  });

  it("only includes status when that's the only filter set", async () => {
    mocks.apiFetch.mockResolvedValue({ items: [], total: 0 });
    await fetchApprovals({ status: "pending" });
    expect(mocks.apiFetch).toHaveBeenCalledWith("/approvals?status=pending");
  });

  it("URL-encodes filter values with special chars", async () => {
    mocks.apiFetch.mockResolvedValue({ items: [], total: 0 });
    await fetchApprovals({ status: "a b&c" });
    const [url] = mocks.apiFetch.mock.calls[0];
    expect(String(url)).toContain("status=a+b%26c");
  });
});

describe("decideApproval()", () => {
  it("POSTs /approvals/:id/decide with the decision body", async () => {
    mocks.apiFetch.mockResolvedValue({ id: "a1", status: "approved" });
    await decideApproval("a1", {
      status: "approved",
      decided_by: "alice",
      decision_comment: "LGTM",
    });

    expect(mocks.apiFetch).toHaveBeenCalledWith(
      "/approvals/a1/decide",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          status: "approved",
          decided_by: "alice",
          decision_comment: "LGTM",
        }),
      }),
    );
  });

  it("lets rejections through with the same signature", async () => {
    mocks.apiFetch.mockResolvedValue({ id: "a1", status: "rejected" });
    await decideApproval("a1", { status: "rejected" });
    const [, init] = mocks.apiFetch.mock.calls[0];
    expect(JSON.parse(init.body as string)).toEqual({ status: "rejected" });
  });
});
