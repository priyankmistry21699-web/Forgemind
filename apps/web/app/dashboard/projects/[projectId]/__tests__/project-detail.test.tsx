/**
 * FM-016 / FM-035 smoke tests for the project detail page.
 *
 * The page composes a lot of sub-components (RunTaskList, PlannerResultView,
 * ArtifactListSection, ApprovalListSection, ConstitutionEditor,
 * PhaseProfileEditor, ConstitutionSuggestions).  We mock them out so the
 * tests stay focused on the page's own branches: loading, error / missing
 * project, and populated-with-latest-run.
 */

import { describe, expect, it, vi, beforeEach } from "vitest";
import { act, render, screen } from "@testing-library/react";
import type { Project } from "@/types/project";
import type { Run } from "@/types/run";

const mocks = vi.hoisted(() => ({
  useParams: vi.fn(),
  fetchProject: vi.fn(),
  fetchLatestRun: vi.fn(),
  fetchArtifacts: vi.fn(),
  fetchApprovals: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  useParams: mocks.useParams,
}));
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
vi.mock("@/lib/projects", () => ({
  fetchProject: mocks.fetchProject,
  fetchLatestRun: mocks.fetchLatestRun,
}));
vi.mock("@/lib/artifacts", () => ({
  fetchArtifacts: mocks.fetchArtifacts,
}));
vi.mock("@/lib/approvals", () => ({
  fetchApprovals: mocks.fetchApprovals,
}));

// Silence / stub heavy sub-components.
vi.mock("@/components/tasks/run-task-list", () => ({
  RunTaskList: ({ runId }: { runId: string }) => (
    <div data-testid="run-task-list">{runId}</div>
  ),
}));
vi.mock("@/components/planner/planner-result-view", () => ({
  PlannerResultView: ({ runId }: { runId: string }) => (
    <div data-testid="planner-result-view">{runId}</div>
  ),
}));
vi.mock("@/components/artifacts/artifact-list-section", () => ({
  ArtifactListSection: () => <div data-testid="artifact-list-section" />,
}));
vi.mock("@/components/approvals/approval-list-section", () => ({
  ApprovalListSection: () => <div data-testid="approval-list-section" />,
}));
vi.mock("@/components/projects/constitution-editor", () => ({
  ConstitutionEditor: () => <div data-testid="constitution-editor" />,
}));
vi.mock("@/components/projects/phase-profile-editor", () => ({
  PhaseProfileEditor: () => <div data-testid="phase-profile-editor" />,
}));
vi.mock("@/components/projects/constitution-suggestions", () => ({
  ConstitutionSuggestions: () => (
    <div data-testid="constitution-suggestions" />
  ),
}));

import ProjectDetailPage from "../page";

function makeProject(overrides: Partial<Project> = {}): Project {
  return {
    id: "proj-1",
    name: "Helios",
    description: "Sun-chasing mission",
    status: "active",
    owner_id: "owner-1",
    workspace_id: null,
    template_id: null,
    created_at: new Date("2025-01-01").toISOString(),
    updated_at: new Date("2025-01-02").toISOString(),
    ...overrides,
  };
}

function makeRun(overrides: Partial<Run> = {}): Run {
  return {
    id: "run-1",
    run_number: 7,
    status: "running",
    trigger: "manual",
    project_id: "proj-1",
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    ...overrides,
  };
}

beforeEach(() => {
  mocks.useParams.mockReset();
  mocks.fetchProject.mockReset();
  mocks.fetchLatestRun.mockReset();
  mocks.fetchArtifacts.mockReset();
  mocks.fetchApprovals.mockReset();
  mocks.useParams.mockReturnValue({ projectId: "proj-1" });
});

describe("ProjectDetailPage (FM-016 / FM-035)", () => {
  it("renders the loading skeleton before the fetches resolve", () => {
    mocks.fetchProject.mockReturnValue(new Promise(() => {}));
    mocks.fetchLatestRun.mockReturnValue(new Promise(() => {}));

    const { container } = render(<ProjectDetailPage />);
    expect(container.querySelectorAll(".animate-pulse").length).toBeGreaterThan(
      0,
    );
  });

  it("renders the error card when fetchProject rejects", async () => {
    mocks.fetchProject.mockRejectedValue(new Error("404 not found"));
    mocks.fetchLatestRun.mockResolvedValue(null);

    await act(async () => {
      render(<ProjectDetailPage />);
    });

    expect(screen.getByText("Failed to load project")).toBeInTheDocument();
    expect(screen.getByText("404 not found")).toBeInTheDocument();
  });

  it("renders no-runs empty-state when fetchLatestRun returns null", async () => {
    mocks.fetchProject.mockResolvedValue(makeProject());
    mocks.fetchLatestRun.mockResolvedValue(null);

    await act(async () => {
      render(<ProjectDetailPage />);
    });

    // Name appears in both breadcrumb and H1 header
    expect(screen.getAllByText("Helios").length).toBeGreaterThanOrEqual(1);
    expect(
      screen.getByRole("heading", { name: "Helios", level: 1 }),
    ).toBeInTheDocument();
    expect(screen.getByText("Sun-chasing mission")).toBeInTheDocument();
    expect(screen.getByText("No runs yet")).toBeInTheDocument();
    // no run means we should NOT have made the secondary artifact / approval calls
    expect(mocks.fetchArtifacts).not.toHaveBeenCalled();
    expect(mocks.fetchApprovals).not.toHaveBeenCalled();
  });

  it("renders run metadata + task list once project and latest run resolve", async () => {
    mocks.fetchProject.mockResolvedValue(makeProject());
    mocks.fetchLatestRun.mockResolvedValue(makeRun());
    mocks.fetchArtifacts.mockResolvedValue({ items: [], total: 0 });
    mocks.fetchApprovals.mockResolvedValue({ items: [], total: 0 });

    await act(async () => {
      render(<ProjectDetailPage />);
    });

    expect(screen.getByText("Run #7")).toBeInTheDocument();
    expect(screen.getByText(/Triggered by manual/)).toBeInTheDocument();
    // RunTaskList is mounted with the right runId via the stubbed component
    expect(screen.getByTestId("run-task-list")).toHaveTextContent("run-1");
    expect(screen.getByTestId("planner-result-view")).toHaveTextContent(
      "run-1",
    );
    // secondary fetches happen once a run is present
    expect(mocks.fetchArtifacts).toHaveBeenCalledWith("proj-1", "run-1");
    expect(mocks.fetchApprovals).toHaveBeenCalledWith({ runId: "run-1" });
  });
});
