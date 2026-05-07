/**
 * FM-231/232: Tests for the Schedules & Triggers page.
 */

import { render, screen, waitFor } from "@testing-library/react";
import { vi, describe, it, expect, beforeEach } from "vitest";

vi.mock("@/lib/schedules", () => ({
  listSchedules: vi.fn().mockResolvedValue([
    {
      id: "sch-1",
      name: "Nightly build",
      cron_expression: "0 2 * * *",
      status: "active",
      fire_count: 14,
      last_fired_at: "2026-05-06T02:00:00Z",
      created_at: "2026-04-01T00:00:00Z",
    },
  ]),
  listTriggerRules: vi.fn().mockResolvedValue([
    {
      id: "rule-1",
      name: "PR auto-review",
      event_type: "pr_opened",
      enabled: true,
      fire_count: 5,
      conditions: { branch: "main" },
    },
  ]),
  pauseSchedule: vi.fn().mockResolvedValue(undefined),
  resumeSchedule: vi.fn().mockResolvedValue(undefined),
}));

import SchedulesPage from "../page";

describe("SchedulesPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders heading", async () => {
    render(<SchedulesPage />);
    await waitFor(() => {
      expect(screen.getByText("Schedules & Triggers")).toBeInTheDocument();
    });
  });

  it("renders cron schedule row", async () => {
    render(<SchedulesPage />);
    await waitFor(() => {
      expect(screen.getByText("Nightly build")).toBeInTheDocument();
      expect(screen.getByText("0 2 * * *")).toBeInTheDocument();
    });
  });

  it("renders trigger rule row", async () => {
    render(<SchedulesPage />);
    await waitFor(() => {
      expect(screen.getByText("PR auto-review")).toBeInTheDocument();
      expect(screen.getByText("pr_opened")).toBeInTheDocument();
    });
  });

  it("shows fire count for schedule", async () => {
    render(<SchedulesPage />);
    await waitFor(() => {
      expect(screen.getByText("14")).toBeInTheDocument();
    });
  });

  it("shows active badge", async () => {
    render(<SchedulesPage />);
    await waitFor(() => {
      expect(screen.getByText("active")).toBeInTheDocument();
    });
  });
});
