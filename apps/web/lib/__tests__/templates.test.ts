/**
 * Direct tests for lib/templates.ts.
 */
import { describe, expect, it, vi, beforeEach } from "vitest";

const mocks = vi.hoisted(() => ({ apiFetch: vi.fn() }));
vi.mock("@/lib/api", () => ({
  apiFetch: mocks.apiFetch,
  ApiError: class ApiError extends Error {},
}));

import { fetchTemplates, fetchTemplate } from "../templates";

beforeEach(() => {
  mocks.apiFetch.mockReset();
});

describe("templates client", () => {
  it("fetchTemplates with no category hits /templates (no query)", async () => {
    mocks.apiFetch.mockResolvedValue({ items: [], total: 0 });
    await fetchTemplates();
    expect(mocks.apiFetch).toHaveBeenCalledWith("/templates");
  });

  it("fetchTemplates URL-encodes the category filter", async () => {
    mocks.apiFetch.mockResolvedValue({ items: [], total: 0 });
    await fetchTemplates("back end/api");
    expect(mocks.apiFetch).toHaveBeenCalledWith(
      "/templates?category=back%20end%2Fapi",
    );
  });

  it("fetchTemplate hits /templates/:id", async () => {
    mocks.apiFetch.mockResolvedValue({ id: "tpl-1" });
    await fetchTemplate("tpl-1");
    expect(mocks.apiFetch).toHaveBeenCalledWith("/templates/tpl-1");
  });
});
