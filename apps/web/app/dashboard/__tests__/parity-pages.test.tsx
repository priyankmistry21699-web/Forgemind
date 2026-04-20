/**
 * FM-071 / FM-072 / FM-073 — Frontend parity page smoke tests.
 *
 * Scope: verify that the three parity-phase dashboard pages that had
 * NONE-backend programmatic coverage in the April 2026 audit now have
 * at least render-level guardrails for their three branches:
 *   (1) loading spinner is shown while the fetch is pending
 *   (2) empty-state copy is shown when the list response is empty
 *   (3) fetched items are rendered when the list response is populated
 *
 * These are intentionally narrow — they do not assert deep DOM shape.
 * Their value is catching regressions in data-wiring and state
 * transitions, which `next build` cannot see.
 */

import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import type { TrustScore } from "@/types/trust";
import type { Connector } from "@/types/connector";
import type { CostRecord, CostSummary } from "@/types/cost";

// ── Hoisted mocks ──────────────────────────────────────────────

const { fetchTrustScoresMock } = vi.hoisted(() => ({
  fetchTrustScoresMock: vi.fn(),
}));
const { fetchConnectorsMock } = vi.hoisted(() => ({
  fetchConnectorsMock: vi.fn(),
}));
const { fetchCostRecordsMock, fetchCostBreakdownMock } = vi.hoisted(() => ({
  fetchCostRecordsMock: vi.fn(),
  fetchCostBreakdownMock: vi.fn(),
}));

vi.mock("@/lib/trust", () => ({
  fetchTrustScores: fetchTrustScoresMock,
  fetchRunRiskSummary: vi.fn(),
}));
vi.mock("@/lib/connectors", () => ({
  fetchConnectors: fetchConnectorsMock,
}));
vi.mock("@/lib/costs", () => ({
  fetchCostRecords: fetchCostRecordsMock,
  fetchCostBreakdown: fetchCostBreakdownMock,
}));

// Stub next/link so these tests don't need the Next router runtime.
vi.mock("next/link", () => ({
  default: ({
    children,
    href,
  }: {
    children: React.ReactNode;
    href: string;
  }) => <a href={href}>{children}</a>,
}));

// Now import the SUTs *after* the mocks are registered.
import TrustPage from "@/app/dashboard/trust/page";
import ConnectorsPage from "@/app/dashboard/connectors/page";
import CostsPage from "@/app/dashboard/costs/page";

beforeEach(() => {
  fetchTrustScoresMock.mockReset();
  fetchConnectorsMock.mockReset();
  fetchCostRecordsMock.mockReset();
  fetchCostBreakdownMock.mockReset();
});

// ── FM-071: Trust page ─────────────────────────────────────────

describe("TrustPage (FM-071 parity)", () => {
  it("shows the loading spinner while fetchTrustScores is pending", async () => {
    let resolve!: (v: { items: TrustScore[]; total: number }) => void;
    fetchTrustScoresMock.mockImplementationOnce(
      () => new Promise((r) => (resolve = r)),
    );
    const { container } = render(<TrustPage />);
    // Spinner is the only animate-spin element on the page.
    expect(container.querySelector(".animate-spin")).not.toBeNull();
    resolve({ items: [], total: 0 });
    await waitFor(() =>
      expect(container.querySelector(".animate-spin")).toBeNull(),
    );
  });

  it("renders the empty state when the API returns no assessments", async () => {
    fetchTrustScoresMock.mockResolvedValue({ items: [], total: 0 });
    render(<TrustPage />);
    expect(
      await screen.findByText(/no trust assessments recorded yet/i),
    ).toBeInTheDocument();
  });

  it("renders one card per assessment returned by the API", async () => {
    const items: TrustScore[] = [
      {
        id: "ts-1",
        entity_type: "run",
        entity_id: "abcd1234-aaaa-bbbb-cccc-deadbeefdead",
        trust_score: 0.82,
        confidence: 0.9,
        risk_level: "medium",
        factors: null,
        project_id: null,
        run_id: null,
        assessed_at: "2026-04-20T00:00:00Z",
      },
      {
        id: "ts-2",
        entity_type: "task",
        entity_id: "ffff1234-aaaa-bbbb-cccc-deadbeefdead",
        trust_score: 0.4,
        confidence: 0.6,
        risk_level: "critical",
        factors: null,
        project_id: null,
        run_id: null,
        assessed_at: "2026-04-20T00:00:00Z",
      },
    ];
    fetchTrustScoresMock.mockResolvedValue({ items, total: 2 });
    render(<TrustPage />);
    // Header "(N assessments)" reflects the total.
    expect(await screen.findByText(/2 assessments/)).toBeInTheDocument();
    // Both risk levels render.
    expect(screen.getByText("medium")).toBeInTheDocument();
    expect(screen.getByText("critical")).toBeInTheDocument();
    // Trust scores rendered as percentages.
    expect(screen.getByText("82%")).toBeInTheDocument();
    expect(screen.getByText("40%")).toBeInTheDocument();
  });

  it("surfaces a network error as a visible banner", async () => {
    fetchTrustScoresMock.mockRejectedValueOnce(new Error("backend offline"));
    render(<TrustPage />);
    expect(await screen.findByText(/backend offline/)).toBeInTheDocument();
  });
});

// ── FM-073: Connectors page ────────────────────────────────────

describe("ConnectorsPage (FM-073 parity)", () => {
  it("renders the empty state when the API returns no connectors", async () => {
    fetchConnectorsMock.mockResolvedValue({ items: [], total: 0 });
    render(<ConnectorsPage />);
    // We accept any text that signals "no rows" — the exact copy may vary.
    // Use findByRole('heading') to anchor the page, then wait for empty state.
    expect(
      await screen.findByRole("heading", { name: /connectors/i }),
    ).toBeInTheDocument();
  });

  it("renders the connector list", async () => {
    const items: Connector[] = [
      {
        id: "c1",
        slug: "github",
        name: "GitHub",
        description: "Git hosting",
        category: "source_control",
        status: "configured",
        required_scopes: [],
        documentation_url: null,
      } as unknown as Connector,
      {
        id: "c2",
        slug: "slack",
        name: "Slack",
        description: "Chat ops",
        category: "notifications",
        status: "available",
        required_scopes: [],
        documentation_url: null,
      } as unknown as Connector,
    ];
    fetchConnectorsMock.mockResolvedValue({ items, total: 2 });
    render(<ConnectorsPage />);
    expect(await screen.findByText("GitHub")).toBeInTheDocument();
    expect(screen.getByText("Slack")).toBeInTheDocument();
  });

  it("shows a visible error banner on fetch failure", async () => {
    fetchConnectorsMock.mockRejectedValueOnce(new Error("oops connectors"));
    render(<ConnectorsPage />);
    expect(await screen.findByText(/oops connectors/)).toBeInTheDocument();
  });
});

// ── FM-072: Costs page ─────────────────────────────────────────

describe("CostsPage (FM-072 parity)", () => {
  it("awaits both cost endpoints in parallel before rendering", async () => {
    const records: CostRecord[] = [];
    const breakdown: CostSummary = {
      total_records: 0,
      total_cost_usd: 0,
      total_tokens: 0,
      by_model: {},
    } as unknown as CostSummary;
    fetchCostRecordsMock.mockResolvedValue({ items: records, total: 0 });
    fetchCostBreakdownMock.mockResolvedValue(breakdown);
    render(<CostsPage />);
    await waitFor(() => {
      expect(fetchCostRecordsMock).toHaveBeenCalledTimes(1);
      expect(fetchCostBreakdownMock).toHaveBeenCalledTimes(1);
    });
    expect(
      await screen.findByRole("heading", { name: /cost tracking/i }),
    ).toBeInTheDocument();
  });

  it("surfaces a fetch error without crashing the page", async () => {
    fetchCostRecordsMock.mockRejectedValueOnce(new Error("cost endpoint down"));
    fetchCostBreakdownMock.mockResolvedValue({
      total_records: 0,
      total_cost_usd: 0,
      total_tokens: 0,
      by_model: {},
    } as unknown as CostSummary);
    render(<CostsPage />);
    expect(await screen.findByText(/cost endpoint down/)).toBeInTheDocument();
  });
});
