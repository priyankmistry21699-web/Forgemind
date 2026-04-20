/**
 * Direct tests for lib/activity.ts.
 */
import { describe, expect, it, vi, beforeEach } from "vitest";

const mocks = vi.hoisted(() => ({ apiFetch: vi.fn() }));
vi.mock("@/lib/api", () => ({
  apiFetch: mocks.apiFetch,
  ApiError: class ApiError extends Error {},
}));

import {
  fetchActivity,
  fetchWorkspaceActivity,
  updatePresence,
  fetchPresences,
  fetchUserPresence,
  fetchUserContext,
} from "../activity";

beforeEach(() => {
  mocks.apiFetch.mockReset();
});

describe("activity client", () => {
  it("fetchActivity defaults offset=0 limit=50 and no workspace filter", async () => {
    mocks.apiFetch.mockResolvedValue({ items: [], total: 0 });
    await fetchActivity();
    expect(mocks.apiFetch).toHaveBeenCalledWith("/activity?offset=0&limit=50");
  });

  it("fetchActivity threads workspace_id when provided", async () => {
    mocks.apiFetch.mockResolvedValue({ items: [], total: 0 });
    await fetchActivity(5, 10, "w-1");
    const [url] = mocks.apiFetch.mock.calls[0];
    expect(String(url)).toContain("offset=5");
    expect(String(url)).toContain("limit=10");
    expect(String(url)).toContain("workspace_id=w-1");
  });

  it("fetchWorkspaceActivity hits /workspaces/:id/activity", async () => {
    mocks.apiFetch.mockResolvedValue({ items: [], total: 0 });
    await fetchWorkspaceActivity("w-1");
    expect(mocks.apiFetch).toHaveBeenCalledWith(
      "/workspaces/w-1/activity?offset=0&limit=50",
    );
  });

  it("updatePresence PUTs /presence with JSON body", async () => {
    mocks.apiFetch.mockResolvedValue({ status: "online" });
    await updatePresence({ status: "online" });
    expect(mocks.apiFetch).toHaveBeenCalledWith(
      "/presence",
      expect.objectContaining({
        method: "PUT",
        body: JSON.stringify({ status: "online" }),
      }),
    );
  });

  it("fetchPresences + fetchUserPresence + fetchUserContext hit expected URLs", async () => {
    mocks.apiFetch.mockResolvedValue({ items: [], total: 0 });
    await fetchPresences();
    expect(mocks.apiFetch).toHaveBeenCalledWith(
      "/presence?offset=0&limit=100",
    );

    mocks.apiFetch.mockResolvedValue({ status: "online" });
    await fetchUserPresence("u-1");
    expect(mocks.apiFetch).toHaveBeenCalledWith("/presence/u-1");

    mocks.apiFetch.mockResolvedValue({ assignments: [] });
    await fetchUserContext("u-1");
    expect(mocks.apiFetch).toHaveBeenCalledWith("/users/u-1/context");
  });
});
