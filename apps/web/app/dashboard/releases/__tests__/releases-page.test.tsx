/**
 * FM-138 smoke tests for the Release Operations page.
 *
 * The page is gated by a manually-entered Project ID; fetches only fire
 * after the user types one in and clicks Load. We verify the four
 * observable branches: initial state, empty result, populated list,
 * and error.
 */

import { describe, expect, it, vi, beforeEach } from "vitest";
import { act, fireEvent, render, screen } from "@testing-library/react";

const mocks = vi.hoisted(() => ({
  fetchProjectReleasePackages: vi.fn(),
  evaluateGates: vi.fn(),
  fetchRollbackReadiness: vi.fn(),
}));

vi.mock("@/lib/release-ops", () => mocks);

import ReleasesPage from "../page";

beforeEach(() => {
  Object.values(mocks).forEach((m) => m.mockReset());
});

function enterProjectId(id: string) {
  const input = screen.getByPlaceholderText("Enter Project ID");
  fireEvent.change(input, { target: { value: id } });
}

describe("ReleasesPage (FM-138)", () => {
  it("renders the header and filter without firing any fetch until a project is entered", () => {
    render(<ReleasesPage />);

    expect(screen.getByText("Release Operations")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Enter Project ID")).toBeInTheDocument();
    expect(mocks.fetchProjectReleasePackages).not.toHaveBeenCalled();
  });

  it("loads and renders release packages after a project id is entered", async () => {
    mocks.fetchProjectReleasePackages.mockResolvedValue({
      items: [
        {
          id: "rel-1",
          version: "1.2.3",
          status: "ready",
          summary: "First release",
          created_at: new Date("2025-03-01").toISOString(),
        },
      ],
      total: 1,
    });

    render(<ReleasesPage />);

    await act(async () => {
      enterProjectId("proj-42");
    });

    expect(screen.getByText("v1.2.3")).toBeInTheDocument();
    expect(screen.getByText("ready")).toBeInTheDocument();
    expect(mocks.fetchProjectReleasePackages).toHaveBeenCalledWith("proj-42");
  });

  it("shows the empty-state message when no release packages are returned", async () => {
    mocks.fetchProjectReleasePackages.mockResolvedValue({
      items: [],
      total: 0,
    });

    render(<ReleasesPage />);

    await act(async () => {
      enterProjectId("proj-empty");
    });

    expect(screen.getByText("No release packages found.")).toBeInTheDocument();
  });

  it("surfaces the error banner when the fetch rejects", async () => {
    mocks.fetchProjectReleasePackages.mockRejectedValue(
      new Error("upstream unavailable"),
    );

    render(<ReleasesPage />);

    await act(async () => {
      enterProjectId("proj-bad");
    });

    expect(screen.getByText("upstream unavailable")).toBeInTheDocument();
  });
});
