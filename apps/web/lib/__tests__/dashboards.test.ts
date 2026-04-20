/**
 * Direct tests for lib/dashboards.ts — the analytics/dashboard API client.
 */
import { describe, expect, it, vi, beforeEach } from "vitest";

const mocks = vi.hoisted(() => ({ apiFetch: vi.fn() }));
vi.mock("@/lib/api", () => ({
  apiFetch: mocks.apiFetch,
  ApiError: class ApiError extends Error {},
}));

import {
  listDashboards,
  getDashboard,
  createDashboard,
  updateDashboard,
  deleteDashboard,
  getWidgetData,
} from "../dashboards";

beforeEach(() => {
  mocks.apiFetch.mockReset();
});

describe("dashboards client", () => {
  it("listDashboards uses default limit + offset and /analytics/dashboards", async () => {
    mocks.apiFetch.mockResolvedValue({ items: [], total: 0 });
    await listDashboards();
    expect(mocks.apiFetch).toHaveBeenCalledWith(
      "/analytics/dashboards?limit=50&offset=0",
    );
  });

  it("listDashboards threads custom offset/limit into the query", async () => {
    mocks.apiFetch.mockResolvedValue({ items: [], total: 0 });
    await listDashboards(10, 5);
    expect(mocks.apiFetch).toHaveBeenCalledWith(
      "/analytics/dashboards?limit=5&offset=10",
    );
  });

  it("getDashboard hits /analytics/dashboards/:id", async () => {
    mocks.apiFetch.mockResolvedValue({ id: "d-1" });
    await getDashboard("d-1");
    expect(mocks.apiFetch).toHaveBeenCalledWith("/analytics/dashboards/d-1");
  });

  it("createDashboard POSTs /analytics/dashboards with body", async () => {
    mocks.apiFetch.mockResolvedValue({ id: "d-99", name: "new" });
    await createDashboard({ name: "new" });
    expect(mocks.apiFetch).toHaveBeenCalledWith(
      "/analytics/dashboards",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ name: "new" }),
      }),
    );
  });

  it("updateDashboard PUTs /analytics/dashboards/:id with body", async () => {
    mocks.apiFetch.mockResolvedValue({ id: "d-1", name: "renamed" });
    await updateDashboard("d-1", { name: "renamed" });
    expect(mocks.apiFetch).toHaveBeenCalledWith(
      "/analytics/dashboards/d-1",
      expect.objectContaining({
        method: "PUT",
        body: JSON.stringify({ name: "renamed" }),
      }),
    );
  });

  it("deleteDashboard DELETEs /analytics/dashboards/:id and resolves undefined", async () => {
    mocks.apiFetch.mockResolvedValue({ deleted: true });
    await expect(deleteDashboard("d-1")).resolves.toBeUndefined();
    expect(mocks.apiFetch).toHaveBeenCalledWith("/analytics/dashboards/d-1", {
      method: "DELETE",
    });
  });

  it("getWidgetData builds the dashboard/widget/project URL + project_id query", async () => {
    mocks.apiFetch.mockResolvedValue({ data: [] });
    await getWidgetData("d-1", "velocity" as never, "p-1");
    expect(mocks.apiFetch).toHaveBeenCalledWith(
      "/analytics/dashboards/d-1/widgets/velocity?project_id=p-1",
    );
  });
});
