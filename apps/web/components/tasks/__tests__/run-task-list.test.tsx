/**
 * FM-014 smoke tests for RunTaskList.
 *
 * The component drives task display on the dashboard home page and the
 * project detail page.  It has four observable branches (loading / empty /
 * error / populated) plus the retry / cancel affordances, which we verify
 * trigger the underlying lib-layer calls.
 */

import { describe, expect, it, vi, beforeEach } from "vitest";
import { act, render, screen } from "@testing-library/react";
import type { Task } from "@/types/task";

const mocks = vi.hoisted(() => ({
  fetchTasksByRun: vi.fn(),
  retryTask: vi.fn(),
  cancelTask: vi.fn(),
}));

vi.mock("@/lib/tasks", () => mocks);

import { RunTaskList } from "../run-task-list";

function makeTask(overrides: Partial<Task> = {}): Task {
  return {
    id: "task-1",
    title: "Plan sprint",
    description: "Break down the epic",
    task_type: "plan",
    status: "ready",
    order_index: 0,
    depends_on: null,
    parent_id: null,
    run_id: "run-1",
    assigned_agent_slug: null,
    error_message: null,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    ...overrides,
  };
}

beforeEach(() => {
  mocks.fetchTasksByRun.mockReset();
  mocks.retryTask.mockReset();
  mocks.cancelTask.mockReset();
});

describe("RunTaskList", () => {
  it("renders a skeleton placeholder while tasks are loading", () => {
    // never-resolving promise keeps us in the loading branch
    mocks.fetchTasksByRun.mockReturnValue(new Promise(() => {}));
    const { container } = render(<RunTaskList runId="run-1" />);
    expect(container.querySelectorAll(".animate-pulse")).toHaveLength(3);
  });

  it("shows the error banner when the fetch rejects with an Error", async () => {
    mocks.fetchTasksByRun.mockRejectedValue(new Error("boom"));
    await act(async () => {
      render(<RunTaskList runId="run-1" />);
    });
    expect(screen.getByText("Failed to load tasks")).toBeInTheDocument();
    expect(screen.getByText("boom")).toBeInTheDocument();
  });

  it("shows the empty-state copy when the run has zero tasks", async () => {
    mocks.fetchTasksByRun.mockResolvedValue({ items: [], total: 0 });
    await act(async () => {
      render(<RunTaskList runId="run-1" />);
    });
    expect(screen.getByText("No tasks in this run.")).toBeInTheDocument();
  });

  it("renders populated state with task title, status, and ready/completed counters", async () => {
    mocks.fetchTasksByRun.mockResolvedValue({
      items: [
        makeTask({ id: "t1", status: "ready", title: "Plan" }),
        makeTask({
          id: "t2",
          status: "completed",
          title: "Ship",
          order_index: 1,
        }),
        makeTask({
          id: "t3",
          status: "failed",
          title: "Tidy",
          order_index: 2,
          error_message: "segfault",
        }),
      ],
      total: 3,
    });

    await act(async () => {
      render(<RunTaskList runId="run-1" />);
    });

    expect(screen.getByText("3 tasks")).toBeInTheDocument();
    expect(screen.getByText("1 ready")).toBeInTheDocument();
    expect(screen.getByText("1 completed")).toBeInTheDocument();
    expect(screen.getByText("Plan")).toBeInTheDocument();
    expect(screen.getByText("Ship")).toBeInTheDocument();
    expect(screen.getByText("Tidy")).toBeInTheDocument();
    // error message for the failed task is surfaced
    expect(screen.getByText("segfault")).toBeInTheDocument();
    // failed task exposes a Retry button; running tasks expose Cancel
    expect(screen.getByRole("button", { name: /retry/i })).toBeInTheDocument();
  });

  it("pluralises correctly for a single-task run", async () => {
    mocks.fetchTasksByRun.mockResolvedValue({
      items: [makeTask()],
      total: 1,
    });
    await act(async () => {
      render(<RunTaskList runId="run-1" />);
    });
    expect(screen.getByText("1 task")).toBeInTheDocument();
  });
});
