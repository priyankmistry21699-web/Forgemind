/**
 * FM-003 / FM-015 / FM-030 — dashboard home page orchestration tests.
 *
 * Covers the page-level behaviour of apps/web/app/dashboard/page.tsx:
 *   - initial loading (both fetchProjects + fetchApprovals in-flight)
 *   - empty state
 *   - populated state with stat-card counts
 *   - pending-approvals "Needs attention" vs. "All clear" copy
 *   - form mutual exclusivity (create ↔ prompt)
 *   - planning result → task list wiring
 *   - error branch
 */

import { describe, expect, it, vi, beforeEach } from "vitest";
import { act, fireEvent, render, screen } from "@testing-library/react";
import type { Project } from "@/types/project";

const mocks = vi.hoisted(() => ({
  fetchProjects: vi.fn(),
  fetchApprovals: vi.fn(),
}));

vi.mock("@/lib/projects", () => ({ fetchProjects: mocks.fetchProjects }));
vi.mock("@/lib/approvals", () => ({ fetchApprovals: mocks.fetchApprovals }));
vi.mock("next/link", () => ({
  __esModule: true,
  default: ({
    href,
    children,
    ...rest
  }: {
    href: string;
    children: React.ReactNode;
  } & React.AnchorHTMLAttributes<HTMLAnchorElement>) => (
    <a href={href} {...rest}>
      {children}
    </a>
  ),
}));

// Stub heavy child components so we can focus on page orchestration.
vi.mock("@/components/projects/project-create-form", () => ({
  ProjectCreateForm: ({
    onCreated,
    onCancel,
  }: {
    onCreated: () => void;
    onCancel: () => void;
  }) => (
    <div data-testid="project-create-form">
      <button onClick={onCreated}>created-trigger</button>
      <button onClick={onCancel}>cancel-trigger</button>
    </div>
  ),
}));
vi.mock("@/components/planner/prompt-intake-form", () => ({
  PromptIntakeForm: ({
    onPlanned,
    onCancel,
  }: {
    onPlanned: (r: { run_id: string }) => void;
    onCancel: () => void;
  }) => (
    <div data-testid="prompt-intake-form">
      <button
        onClick={() =>
          onPlanned({
            project_id: "p-1",
            run_id: "r-99",
            tasks_created: 3,
            message: "ok",
            created_at: new Date().toISOString(),
          } as never)
        }
      >
        planned-trigger
      </button>
      <button onClick={onCancel}>cancel-trigger</button>
    </div>
  ),
}));
vi.mock("@/components/planner/planning-result-card", () => ({
  PlanningResultCard: ({
    onDismiss,
  }: {
    onDismiss: () => void;
  }) => (
    <div data-testid="planning-result-card">
      <button onClick={onDismiss}>dismiss</button>
    </div>
  ),
}));
vi.mock("@/components/tasks/run-task-list", () => ({
  RunTaskList: ({ runId }: { runId: string }) => (
    <div data-testid="run-task-list">{runId}</div>
  ),
}));

import DashboardPage from "../page";

function makeProject(overrides: Partial<Project> = {}): Project {
  return {
    id: `proj-${Math.random().toString(36).slice(2, 8)}`,
    name: "Atlas",
    description: "Primary orchestration project",
    status: "active",
    owner_id: "owner-1",
    workspace_id: null,
    template_id: null,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    ...overrides,
  };
}

beforeEach(() => {
  mocks.fetchProjects.mockReset();
  mocks.fetchApprovals.mockReset();
  // Provide a stable scrollIntoView since the page calls it on form open
  (Element.prototype as unknown as { scrollIntoView: () => void }).scrollIntoView = () => {};
});

describe("DashboardPage (FM-003 / FM-015 / FM-030)", () => {
  it("renders the loading skeleton while projects + approvals resolve", () => {
    mocks.fetchProjects.mockReturnValue(new Promise(() => {}));
    mocks.fetchApprovals.mockReturnValue(new Promise(() => {}));

    const { container } = render(<DashboardPage />);
    // stat cards show "—" while loading
    expect(
      container.querySelectorAll(".animate-pulse").length,
    ).toBeGreaterThan(0);
    expect(screen.getAllByText("—").length).toBeGreaterThanOrEqual(2);
  });

  it("renders empty-state + 'All clear' approvals note when both fetches return nothing", async () => {
    mocks.fetchProjects.mockResolvedValue({ items: [], total: 0 });
    mocks.fetchApprovals.mockResolvedValue({ items: [], total: 0 });

    await act(async () => {
      render(<DashboardPage />);
    });

    expect(screen.getByText("No projects yet")).toBeInTheDocument();
    expect(screen.getByText("All clear")).toBeInTheDocument();
    expect(screen.getByText("Create your first project")).toBeInTheDocument();
    // both fetches were made, with fetchApprovals scoped to pending
    expect(mocks.fetchApprovals).toHaveBeenCalledWith({ status: "pending" });
  });

  it("renders populated projects grid + pending-approvals stat + 'Needs attention →' copy", async () => {
    mocks.fetchProjects.mockResolvedValue({
      items: [
        makeProject({ id: "p1", name: "Atlas" }),
        makeProject({ id: "p2", name: "Helios" }),
      ],
      total: 2,
    });
    mocks.fetchApprovals.mockResolvedValue({ items: [], total: 4 });

    await act(async () => {
      render(<DashboardPage />);
    });

    // projects grid
    expect(screen.getByText("Atlas")).toBeInTheDocument();
    expect(screen.getByText("Helios")).toBeInTheDocument();
    // projects count badge
    expect(screen.getByText("2 projects")).toBeInTheDocument();
    // pending approvals stat card shows the 4 + call-to-action; scope to the card
    const approvalsLabel = screen.getByText("Pending Approvals");
    const approvalsCard = approvalsLabel.closest("a");
    expect(approvalsCard).not.toBeNull();
    expect(approvalsCard?.textContent).toContain("4");
    expect(screen.getByText(/Needs attention/i)).toBeInTheDocument();
    expect(approvalsCard).toHaveAttribute("href", "/dashboard/approvals");
  });

  it("shows the error state when fetchProjects rejects (promise.all branch)", async () => {
    mocks.fetchProjects.mockRejectedValue(new Error("backend offline"));
    mocks.fetchApprovals.mockResolvedValue({ items: [], total: 0 });

    await act(async () => {
      render(<DashboardPage />);
    });

    expect(screen.getByText("Failed to load projects")).toBeInTheDocument();
    expect(screen.getByText("backend offline")).toBeInTheDocument();
  });

  it("toggles forms with mutual exclusivity via the header + quick actions buttons", async () => {
    mocks.fetchProjects.mockResolvedValue({ items: [], total: 0 });
    mocks.fetchApprovals.mockResolvedValue({ items: [], total: 0 });

    await act(async () => {
      render(<DashboardPage />);
    });

    // Neither form mounted initially.
    expect(screen.queryByTestId("project-create-form")).toBeNull();
    expect(screen.queryByTestId("prompt-intake-form")).toBeNull();

    // Click the header "New Project" button -> create form mounts.
    const newProjectButtons = screen.getAllByRole("button", {
      name: /new project/i,
    });
    await act(async () => {
      fireEvent.click(newProjectButtons[0]);
    });
    expect(screen.getByTestId("project-create-form")).toBeInTheDocument();
    expect(screen.queryByTestId("prompt-intake-form")).toBeNull();

    // Switch to prompt form via header "Plan from Prompt".
    const planButtons = screen.getAllByRole("button", {
      name: /plan from prompt/i,
    });
    await act(async () => {
      fireEvent.click(planButtons[0]);
    });
    expect(screen.queryByTestId("project-create-form")).toBeNull();
    expect(screen.getByTestId("prompt-intake-form")).toBeInTheDocument();

    // Toggling the same button again closes the active form (mutual exclusivity).
    await act(async () => {
      fireEvent.click(planButtons[0]);
    });
    expect(screen.queryByTestId("prompt-intake-form")).toBeNull();
  });

  it("surfaces planning-result + RunTaskList wired with the returned run_id after a plan", async () => {
    mocks.fetchProjects.mockResolvedValue({ items: [], total: 0 });
    mocks.fetchApprovals.mockResolvedValue({ items: [], total: 0 });

    await act(async () => {
      render(<DashboardPage />);
    });

    // Open prompt form, fire the planned callback.
    const planButtons = screen.getAllByRole("button", {
      name: /plan from prompt/i,
    });
    await act(async () => {
      fireEvent.click(planButtons[0]);
    });
    await act(async () => {
      fireEvent.click(screen.getByText("planned-trigger"));
    });

    expect(screen.getByTestId("planning-result-card")).toBeInTheDocument();
    expect(screen.getByTestId("run-task-list")).toHaveTextContent("r-99");
  });
});
