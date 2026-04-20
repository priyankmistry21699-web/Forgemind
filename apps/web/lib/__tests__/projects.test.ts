/**
 * Direct tests for lib/projects.ts — verifies URL/method/body shape
 * by mocking the shared apiFetch wrapper.
 */
import { describe, expect, it, vi, beforeEach } from "vitest";

const mocks = vi.hoisted(() => ({ apiFetch: vi.fn() }));
vi.mock("@/lib/api", () => ({
  apiFetch: mocks.apiFetch,
  ApiError: class ApiError extends Error {},
}));

import {
  fetchProjects,
  fetchProject,
  fetchLatestRun,
  createProject,
} from "../projects";

beforeEach(() => {
  mocks.apiFetch.mockReset();
});

describe("fetchProjects()", () => {
  it("hits /projects with default skip + limit", async () => {
    mocks.apiFetch.mockResolvedValue({ items: [], total: 0 });
    await fetchProjects();
    expect(mocks.apiFetch).toHaveBeenCalledWith("/projects?skip=0&limit=20");
  });

  it("threads skip + limit into the query string", async () => {
    mocks.apiFetch.mockResolvedValue({ items: [], total: 0 });
    await fetchProjects(40, 5);
    expect(mocks.apiFetch).toHaveBeenCalledWith("/projects?skip=40&limit=5");
  });

  it("propagates the parsed project list back to the caller", async () => {
    const payload = { items: [{ id: "p1" }], total: 1 };
    mocks.apiFetch.mockResolvedValue(payload);
    await expect(fetchProjects()).resolves.toEqual(payload);
  });
});

describe("fetchProject()", () => {
  it("targets /projects/:id", async () => {
    mocks.apiFetch.mockResolvedValue({ id: "p1", name: "Atlas" });
    await fetchProject("p1");
    expect(mocks.apiFetch).toHaveBeenCalledWith("/projects/p1");
  });
});

describe("fetchLatestRun()", () => {
  it("targets /projects/:id/runs/latest", async () => {
    mocks.apiFetch.mockResolvedValue({ id: "r1" });
    const r = await fetchLatestRun("p1");
    expect(mocks.apiFetch).toHaveBeenCalledWith("/projects/p1/runs/latest");
    expect(r).toEqual({ id: "r1" });
  });

  it("SWALLOWS errors and returns null rather than throwing", async () => {
    mocks.apiFetch.mockRejectedValue(new Error("404"));
    await expect(fetchLatestRun("p1")).resolves.toBeNull();
  });
});

describe("createProject()", () => {
  it("POSTs to /projects with the JSON-stringified payload", async () => {
    mocks.apiFetch.mockResolvedValue({ id: "p42" });
    await createProject({
      name: "Atlas",
      description: "ops hub",
      template_id: "tpl-1",
    });

    expect(mocks.apiFetch).toHaveBeenCalledWith(
      "/projects",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          name: "Atlas",
          description: "ops hub",
          template_id: "tpl-1",
        }),
      }),
    );
  });

  it("passes null description + null template_id through untouched", async () => {
    mocks.apiFetch.mockResolvedValue({ id: "p0" });
    await createProject({ name: "Bare", description: null, template_id: null });

    const [, init] = mocks.apiFetch.mock.calls[0];
    expect(JSON.parse(init.body as string)).toEqual({
      name: "Bare",
      description: null,
      template_id: null,
    });
  });
});
