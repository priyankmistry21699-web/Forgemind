/**
 * Direct tests for lib/knowledge.ts.
 */
import { describe, expect, it, vi, beforeEach } from "vitest";

const mocks = vi.hoisted(() => ({ apiFetch: vi.fn() }));
vi.mock("@/lib/api", () => ({
  apiFetch: mocks.apiFetch,
  ApiError: class ApiError extends Error {},
}));

import { fetchProjectKnowledge, fetchKnowledgeEntry } from "../knowledge";

beforeEach(() => {
  mocks.apiFetch.mockReset();
});

describe("knowledge client", () => {
  it("fetchProjectKnowledge uses defaults offset=0 limit=50", async () => {
    mocks.apiFetch.mockResolvedValue({ items: [], total: 0 });
    await fetchProjectKnowledge("p-1");
    expect(mocks.apiFetch).toHaveBeenCalledWith(
      "/projects/p-1/knowledge?offset=0&limit=50",
    );
  });

  it("fetchProjectKnowledge threads custom pagination", async () => {
    mocks.apiFetch.mockResolvedValue({ items: [], total: 0 });
    await fetchProjectKnowledge("p-1", 10, 5);
    expect(mocks.apiFetch).toHaveBeenCalledWith(
      "/projects/p-1/knowledge?offset=10&limit=5",
    );
  });

  it("fetchKnowledgeEntry hits /knowledge/:id", async () => {
    mocks.apiFetch.mockResolvedValue({ id: "k-1" });
    await fetchKnowledgeEntry("k-1");
    expect(mocks.apiFetch).toHaveBeenCalledWith("/knowledge/k-1");
  });
});
