/**
 * Direct tests for lib/workspaces.ts.
 */
import { describe, expect, it, vi, beforeEach } from "vitest";

const mocks = vi.hoisted(() => ({ apiFetch: vi.fn() }));
vi.mock("@/lib/api", () => ({
  apiFetch: mocks.apiFetch,
  ApiError: class ApiError extends Error {},
}));

import {
  fetchWorkspaces,
  fetchWorkspace,
  createWorkspace,
  updateWorkspace,
  fetchWorkspaceMembers,
  addWorkspaceMember,
} from "../workspaces";

beforeEach(() => {
  mocks.apiFetch.mockReset();
});

describe("workspaces client", () => {
  it("fetchWorkspaces uses defaults offset=0 limit=50", async () => {
    mocks.apiFetch.mockResolvedValue({ items: [], total: 0 });
    await fetchWorkspaces();
    expect(mocks.apiFetch).toHaveBeenCalledWith(
      "/workspaces?offset=0&limit=50",
    );
  });

  it("fetchWorkspace hits /workspaces/:id", async () => {
    mocks.apiFetch.mockResolvedValue({ id: "w-1" });
    await fetchWorkspace("w-1");
    expect(mocks.apiFetch).toHaveBeenCalledWith("/workspaces/w-1");
  });

  it("createWorkspace POSTs /workspaces with JSON body", async () => {
    mocks.apiFetch.mockResolvedValue({ id: "w-9" });
    await createWorkspace({ name: "Acme", slug: "acme" });
    expect(mocks.apiFetch).toHaveBeenCalledWith(
      "/workspaces",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ name: "Acme", slug: "acme" }),
      }),
    );
  });

  it("updateWorkspace PATCHes /workspaces/:id", async () => {
    mocks.apiFetch.mockResolvedValue({ id: "w-1" });
    await updateWorkspace("w-1", { name: "Renamed" });
    expect(mocks.apiFetch).toHaveBeenCalledWith(
      "/workspaces/w-1",
      expect.objectContaining({
        method: "PATCH",
        body: JSON.stringify({ name: "Renamed" }),
      }),
    );
  });

  it("fetchWorkspaceMembers uses defaults offset=0 limit=50", async () => {
    mocks.apiFetch.mockResolvedValue({ items: [], total: 0 });
    await fetchWorkspaceMembers("w-1");
    expect(mocks.apiFetch).toHaveBeenCalledWith(
      "/workspaces/w-1/members?offset=0&limit=50",
    );
  });

  it("addWorkspaceMember POSTs /workspaces/:id/members", async () => {
    mocks.apiFetch.mockResolvedValue({});
    await addWorkspaceMember("w-1", { user_id: "u-1", role: "admin" });
    expect(mocks.apiFetch).toHaveBeenCalledWith(
      "/workspaces/w-1/members",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ user_id: "u-1", role: "admin" }),
      }),
    );
  });
});
