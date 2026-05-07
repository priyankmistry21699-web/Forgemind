/**
 * FM-220: Tests for the Ops Dashboard page.
 */

import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { vi, describe, it, expect, beforeEach } from "vitest";

// Mock the ops lib
vi.mock("@/lib/ops", () => ({
  fetchQueryStats: vi.fn().mockResolvedValue([
    { query: "SELECT * FROM runs", duration_ms: 650, timestamp: "2026-05-06T10:00:00Z" },
  ]),
  fetchCacheStats: vi.fn().mockResolvedValue({
    local_size: 42,
    local_max_size: 512,
    hits: 1000,
    misses: 200,
    hit_rate: 0.833,
  }),
  fetchJobs: vi.fn().mockResolvedValue([
    { name: "send_notification", last_run_at: null, status: "ok" },
  ]),
  fetchModelRouterStatus: vi.fn().mockResolvedValue({
    models: {
      "gpt-4o": { healthy: true, error_count: 0, last_error_at: null },
      "gpt-4o-mini": { healthy: false, error_count: 3, last_error_at: "2026-05-06T09:00:00Z" },
    },
    config_source: "default",
  }),
  flushCache: vi.fn().mockResolvedValue(undefined),
  triggerJob: vi.fn().mockResolvedValue(undefined),
}));

import OpsPage from "../page";

describe("OpsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders heading", async () => {
    render(<OpsPage />);
    await waitFor(() => {
      expect(screen.getByText("Ops Dashboard")).toBeInTheDocument();
    });
  });

  it("renders cache stats", async () => {
    render(<OpsPage />);
    await waitFor(() => {
      expect(screen.getByText("Hit Rate")).toBeInTheDocument();
      expect(screen.getByText("83.3%")).toBeInTheDocument();
    });
  });

  it("renders background jobs", async () => {
    render(<OpsPage />);
    await waitFor(() => {
      expect(screen.getByText("send_notification")).toBeInTheDocument();
    });
  });

  it("renders slow queries", async () => {
    render(<OpsPage />);
    await waitFor(() => {
      expect(screen.getByText("650ms")).toBeInTheDocument();
    });
  });

  it("renders model router with healthy status", async () => {
    render(<OpsPage />);
    await waitFor(() => {
      expect(screen.getByText("gpt-4o")).toBeInTheDocument();
      expect(screen.getAllByText("healthy").length).toBeGreaterThanOrEqual(1);
    });
  });

  it("shows flush cache button", async () => {
    render(<OpsPage />);
    await waitFor(() => {
      expect(screen.getByText("Flush Cache")).toBeInTheDocument();
    });
  });
});
