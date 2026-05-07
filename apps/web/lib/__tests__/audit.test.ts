/**
 * Direct tests for lib/audit.ts.
 */
import { describe, expect, it, vi, beforeEach } from "vitest";

const mocks = vi.hoisted(() => ({ apiFetch: vi.fn() }));
vi.mock("@/lib/api", () => ({
  apiFetch: mocks.apiFetch,
  ApiError: class ApiError extends Error {},
}));

import { fetchAuditSummary, exportAuditJson, exportAuditCsv } from "../audit";

beforeEach(() => {
  mocks.apiFetch.mockReset();
});

describe("audit client", () => {
  it("fetchAuditSummary with no params hits /audit/summary", async () => {
    mocks.apiFetch.mockResolvedValue({ totals: {} });
    await fetchAuditSummary();
    expect(mocks.apiFetch).toHaveBeenCalledWith("/audit/summary");
  });

  it("fetchAuditSummary threads each filter into the query string", async () => {
    mocks.apiFetch.mockResolvedValue({ totals: {} });
    await fetchAuditSummary({
      project_id: "p-1",
      run_id: "r-1",
      event_type: "task_completed" as never,
      start_date: "2025-01-01",
      end_date: "2025-01-31",
    });
    const [url] = mocks.apiFetch.mock.calls[0];
    const s = String(url);
    expect(s.startsWith("/audit/summary?")).toBe(true);
    expect(s).toContain("project_id=p-1");
    expect(s).toContain("run_id=r-1");
    expect(s).toContain("event_type=task_completed");
    expect(s).toContain("start_date=2025-01-01");
    expect(s).toContain("end_date=2025-01-31");
  });

  it("exportAuditJson targets /audit/export/json", async () => {
    mocks.apiFetch.mockResolvedValue({ items: [] });
    await exportAuditJson({ project_id: "p-1" });
    expect(mocks.apiFetch).toHaveBeenCalledWith(
      "/audit/export/json?project_id=p-1",
    );
  });

  it("exportAuditCsv targets /audit/export/csv", async () => {
    mocks.apiFetch.mockResolvedValue("ts,type\n...");
    await exportAuditCsv();
    expect(mocks.apiFetch).toHaveBeenCalledWith("/audit/export/csv");
  });
});
