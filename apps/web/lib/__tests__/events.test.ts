/**
 * Direct tests for lib/events.ts.
 */
import { describe, expect, it, vi, beforeEach } from "vitest";

const mocks = vi.hoisted(() => ({ apiFetch: vi.fn() }));
vi.mock("@/lib/api", () => ({
  apiFetch: mocks.apiFetch,
  ApiError: class ApiError extends Error {},
}));

import { fetchEvents } from "../events";

beforeEach(() => {
  mocks.apiFetch.mockReset();
});

describe("fetchEvents()", () => {
  it("hits /events with no query when no filters are provided", async () => {
    mocks.apiFetch.mockResolvedValue({ items: [], total: 0 });
    await fetchEvents();
    expect(mocks.apiFetch).toHaveBeenCalledWith("/events");
  });

  it("threads project_id + run_id + limit into the query", async () => {
    mocks.apiFetch.mockResolvedValue({ items: [], total: 0 });
    await fetchEvents({ projectId: "p-1", runId: "r-1", limit: 25 });
    expect(mocks.apiFetch).toHaveBeenCalledWith(
      "/events?project_id=p-1&run_id=r-1&limit=25",
    );
  });

  it("omits missing filters and keeps query minimal", async () => {
    mocks.apiFetch.mockResolvedValue({ items: [], total: 0 });
    await fetchEvents({ projectId: "p-1" });
    expect(mocks.apiFetch).toHaveBeenCalledWith("/events?project_id=p-1");
  });
});
