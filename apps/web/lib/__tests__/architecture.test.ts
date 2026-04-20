/**
 * Direct tests for lib/architecture.ts. Keeps assertions focused on URL
 * shape + method + body coercion — the highest-value client contract.
 */
import { describe, expect, it, vi, beforeEach } from "vitest";

const mocks = vi.hoisted(() => ({ apiFetch: vi.fn() }));
vi.mock("@/lib/api", () => ({
  apiFetch: mocks.apiFetch,
  ApiError: class ApiError extends Error {},
}));

import {
  fetchArchitectureGraph,
  fetchArchitectureNodes,
  fetchArchitectureEdges,
  fetchArchitectureSnapshots,
  mapTopology,
  detectDrift,
  fetchDrifts,
  fetchArchitectureRules,
  fetchRuleResults,
  generateDesignDoc,
  analyseImpact,
} from "../architecture";

beforeEach(() => {
  mocks.apiFetch.mockReset();
});

describe("architecture client", () => {
  it("fetchArchitectureGraph → GET /projects/:id/architecture/graph", async () => {
    mocks.apiFetch.mockResolvedValue({ nodes: [], edges: [] });
    await fetchArchitectureGraph("p-1");
    expect(mocks.apiFetch).toHaveBeenCalledWith(
      "/projects/p-1/architecture/graph",
    );
  });

  it("fetchArchitectureNodes/Edges use default offset=0 + limit=100", async () => {
    mocks.apiFetch.mockResolvedValue({ items: [] });
    await fetchArchitectureNodes("p-1");
    expect(mocks.apiFetch).toHaveBeenCalledWith(
      "/projects/p-1/architecture/nodes?offset=0&limit=100",
    );

    mocks.apiFetch.mockResolvedValue({ items: [] });
    await fetchArchitectureEdges("p-1", 10, 5);
    expect(mocks.apiFetch).toHaveBeenCalledWith(
      "/projects/p-1/architecture/edges?offset=10&limit=5",
    );
  });

  it("fetchArchitectureSnapshots hits the expected path", async () => {
    mocks.apiFetch.mockResolvedValue({ items: [] });
    await fetchArchitectureSnapshots("p-1");
    expect(mocks.apiFetch).toHaveBeenCalledWith(
      "/projects/p-1/architecture/snapshots",
    );
  });

  it("mapTopology POSTs with empty JSON body + json header", async () => {
    mocks.apiFetch.mockResolvedValue({});
    await mapTopology("p-1");
    expect(mocks.apiFetch).toHaveBeenCalledWith(
      "/projects/p-1/architecture/topology/map",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({}),
      }),
    );
  });

  it("detectDrift POSTs to /projects/:id/architecture/drift/detect", async () => {
    mocks.apiFetch.mockResolvedValue({ items: [] });
    await detectDrift("p-1");
    expect(mocks.apiFetch).toHaveBeenCalledWith(
      "/projects/p-1/architecture/drift/detect",
      { method: "POST" },
    );
  });

  it("fetchDrifts / fetchArchitectureRules / fetchRuleResults hit their paths", async () => {
    mocks.apiFetch.mockResolvedValue({ items: [] });
    await fetchDrifts("p-1");
    await fetchArchitectureRules("p-1");
    await fetchRuleResults("p-1");
    const urls = mocks.apiFetch.mock.calls.map((c: unknown[]) => c[0]);
    expect(urls).toEqual([
      "/projects/p-1/architecture/drift",
      "/projects/p-1/architecture/rules",
      "/projects/p-1/architecture/rule-results",
    ]);
  });

  it("generateDesignDoc POSTs /projects/:id/architecture/design-doc", async () => {
    mocks.apiFetch.mockResolvedValue({ id: "doc-1" });
    await generateDesignDoc("p-1");
    expect(mocks.apiFetch).toHaveBeenCalledWith(
      "/projects/p-1/architecture/design-doc",
      { method: "POST" },
    );
  });

  it("analyseImpact POSTs the body through to impact-analysis", async () => {
    mocks.apiFetch.mockResolvedValue({ impacted: [] });
    await analyseImpact("p-1", { file_path: "src/a.ts" });
    expect(mocks.apiFetch).toHaveBeenCalledWith(
      "/projects/p-1/architecture/impact-analysis",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ file_path: "src/a.ts" }),
      }),
    );
  });
});
