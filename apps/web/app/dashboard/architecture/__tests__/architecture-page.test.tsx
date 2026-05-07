/**
 * FM-085 smoke tests for the architecture review dashboard.
 *
 * The page reads ?project=<id> from window.location on each render, so each
 * test only needs to update the URL before calling render().
 */

import { describe, expect, it, vi, beforeEach } from "vitest";
import { act, render, screen } from "@testing-library/react";
import type {
  ArchitectureGraph,
  ArchitectureDriftList,
  ArchitectureRuleList,
  ArchitectureRuleResultList,
  RefactorRecommendationList,
  StructuralHealthScore,
} from "@/types/architecture";

const mocks = vi.hoisted(() => ({
  fetchArchitectureGraph: vi.fn(),
  fetchDrifts: vi.fn(),
  fetchArchitectureRules: vi.fn(),
  fetchRuleResults: vi.fn(),
  fetchRecommendations: vi.fn(),
  fetchHealthScore: vi.fn(),
}));

vi.mock("@/lib/architecture", () => mocks);
vi.mock("next/link", () => ({
  __esModule: true,
  default: ({
    href,
    children,
  }: {
    href: string;
    children: React.ReactNode;
  }) => <a href={href}>{children}</a>,
}));

import Page from "../page";

function setUrl(search: string) {
  window.history.replaceState({}, "", `/dashboard/architecture${search}`);
}

async function loadPage() {
  return Page;
}

beforeEach(() => {
  Object.values(mocks).forEach((m) => m.mockReset());
});

describe("ArchitectureDashboard (FM-085)", () => {
  it("renders the 'no project selected' hint when ?project is missing", async () => {
    setUrl("");
    const Page = await loadPage();

    await act(async () => {
      render(<Page />);
    });

    expect(
      screen.getByText(/to view a project's architecture/i),
    ).toBeInTheDocument();
    // None of the fetches should have been dispatched.
    expect(mocks.fetchArchitectureGraph).not.toHaveBeenCalled();
    expect(mocks.fetchHealthScore).not.toHaveBeenCalled();
  });

  it("shows the loading message while the parallel fetch is in-flight", async () => {
    setUrl("?project=proj-42");
    Object.values(mocks).forEach((m) =>
      m.mockReturnValue(new Promise(() => {})),
    );

    const Page = await loadPage();
    render(<Page />);

    expect(screen.getByText("Loading...")).toBeInTheDocument();
  });

  it("renders the populated dashboard when every fetch resolves", async () => {
    setUrl("?project=proj-42");

    const graph: ArchitectureGraph = {
      project_id: "proj-42",
      nodes: [
        {
          id: "n1",
          workspace_id: null,
          project_id: "proj-42",
          repo_id: null,
          node_type: "service",
          key: "svc-a",
          name: "Svc A",
          path: null,
          language: null,
          metadata_: null,
          source_type: "declared",
          status: "active",
          created_at: "2025-01-01",
          updated_at: "2025-01-01",
        },
      ],
      edges: [],
      node_count: 1,
      edge_count: 0,
    };
    const drifts: ArchitectureDriftList = {
      items: [
        {
          id: "d1",
          project_id: "proj-42",
          drift_type: "layer_violation",
          severity: "high",
          title: "Layering breach",
          description: "",
          source_snapshot_id: null,
          comparison_target: null,
          status: "open",
          metadata_: null,
          detected_at: "2025-01-01",
          resolved_at: null,
        },
      ],
      total: 1,
    };
    const rules: ArchitectureRuleList = {
      items: [
        {
          id: "r1",
          project_id: "proj-42",
          name: "No cross-layer imports",
          description: null,
          category: "layer",
          rule_config: {},
          enabled: true,
          severity: "high",
          created_at: "2025-01-01",
          updated_at: "2025-01-01",
        },
      ],
      total: 1,
    };
    const results: ArchitectureRuleResultList = {
      items: [
        {
          id: "rr1",
          rule_id: "r1",
          project_id: "proj-42",
          status: "violation",
          message: "Layer X imports layer Y",
          details: null,
          violating_node_ids: null,
          violating_edge_ids: null,
          evaluated_at: "2025-01-01",
        },
      ],
      total: 1,
    };
    const recs: RefactorRecommendationList = {
      items: [
        {
          recommendation_type: "split_module",
          title: "Split auth service",
          description: "Extract token issuance",
          severity: "medium",
          confidence: 0.8,
          affected_nodes: ["n1"],
          rationale: "",
        },
      ],
      total: 1,
    };
    const health: StructuralHealthScore = {
      project_id: "proj-42",
      overall_score: 72,
      component_coverage: 80,
      drift_penalty: 8,
      rule_compliance: 90,
      isolation_ratio: 5,
      details: {
        total_nodes: 1,
        total_edges: 0,
        declared_nodes: 1,
        open_drifts: 1,
        total_rule_evaluations: 1,
        rule_violations: 1,
        isolated_nodes: 0,
      },
    };

    mocks.fetchArchitectureGraph.mockResolvedValue(graph);
    mocks.fetchDrifts.mockResolvedValue(drifts);
    mocks.fetchArchitectureRules.mockResolvedValue(rules);
    mocks.fetchRuleResults.mockResolvedValue(results);
    mocks.fetchRecommendations.mockResolvedValue(recs);
    mocks.fetchHealthScore.mockResolvedValue(health);

    const Page = await loadPage();
    await act(async () => {
      render(<Page />);
    });

    expect(
      screen.getByText("Architecture Review Workspace"),
    ).toBeInTheDocument();
    // Health score bubble
    expect(screen.getByText("72")).toBeInTheDocument();
    // Drift row
    expect(screen.getByText("Layering breach")).toBeInTheDocument();
    // Rule
    expect(screen.getByText("No cross-layer imports")).toBeInTheDocument();
    // Rule violation message
    expect(screen.getByText("Layer X imports layer Y")).toBeInTheDocument();
    // Recommendation
    expect(screen.getByText("Split auth service")).toBeInTheDocument();
    // All 6 fetches were invoked with the URL-scoped project id
    for (const m of Object.values(mocks)) {
      expect(m).toHaveBeenCalledWith("proj-42");
    }
  });

  it("surfaces an error banner when any fetch rejects", async () => {
    setUrl("?project=proj-42");
    mocks.fetchArchitectureGraph.mockRejectedValue(new Error("server down"));
    // The page uses Promise.all — one rejection fails the whole load.
    mocks.fetchDrifts.mockResolvedValue({ items: [], total: 0 });
    mocks.fetchArchitectureRules.mockResolvedValue({ items: [], total: 0 });
    mocks.fetchRuleResults.mockResolvedValue({ items: [], total: 0 });
    mocks.fetchRecommendations.mockResolvedValue({ items: [], total: 0 });
    mocks.fetchHealthScore.mockResolvedValue(null);

    const Page = await loadPage();
    await act(async () => {
      render(<Page />);
    });

    expect(screen.getByText("server down")).toBeInTheDocument();
  });
});
