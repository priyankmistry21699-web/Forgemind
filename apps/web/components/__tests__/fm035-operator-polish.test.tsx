/**
 * FM-035 — operator polish assertions.
 *
 * ArtifactListSection and ApprovalListSection drive the artifact-count
 * heading, approval-count badge, and cross-link affordances on the project
 * detail / run detail pages.  These tests exercise them directly so the
 * polish specifics are not silently stubbed out by higher-level tests.
 */

import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import type { Artifact } from "@/types/artifact";
import type { Approval } from "@/types/approval";

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

import { ArtifactListSection } from "@/components/artifacts/artifact-list-section";
import { ApprovalListSection } from "@/components/approvals/approval-list-section";

function makeArtifact(overrides: Partial<Artifact> = {}): Artifact {
  return {
    id: "art-1",
    title: "Spec v1",
    artifact_type: "plan_summary",
    content: null,
    meta: null,
    version: 1,
    project_id: "proj-1",
    run_id: "run-1",
    task_id: null,
    created_by: "alice",
    spec_artifact_id: null,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    ...overrides,
  };
}

function makeApproval(overrides: Partial<Approval> = {}): Approval {
  return {
    id: "app-1",
    status: "pending",
    title: "Approve deploy",
    description: "Production push",
    project_id: "proj-1",
    run_id: "run-1",
    task_id: null,
    artifact_id: null,
    decided_by: null,
    decision_comment: null,
    decided_at: null,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    ...overrides,
  };
}

describe("ArtifactListSection (FM-035 polish)", () => {
  it("renders the dashed empty-state card when there are no artifacts", () => {
    render(<ArtifactListSection artifacts={[]} />);
    expect(
      screen.getByText("No artifacts produced yet"),
    ).toBeInTheDocument();
  });

  it("cross-links each artifact row to /dashboard/artifacts/:id", () => {
    render(
      <ArtifactListSection
        artifacts={[
          makeArtifact({ id: "art-1", title: "Spec v1" }),
          makeArtifact({
            id: "art-2",
            title: "Design doc",
            artifact_type: "architecture",
          }),
        ]}
      />,
    );
    const link1 = screen.getByRole("link", { name: /Spec v1/ });
    const link2 = screen.getByRole("link", { name: /Design doc/ });
    expect(link1).toHaveAttribute("href", "/dashboard/artifacts/art-1");
    expect(link2).toHaveAttribute("href", "/dashboard/artifacts/art-2");
    // badges reflect the (normalised) artifact_type label
    expect(screen.getByText("plan summary")).toBeInTheDocument();
    expect(screen.getByText("architecture")).toBeInTheDocument();
  });
});

describe("ApprovalListSection (FM-035 polish)", () => {
  it("renders the 'All caught up' empty-state when there are no approvals", () => {
    render(<ApprovalListSection approvals={[]} />);
    expect(screen.getByText("No approval requests")).toBeInTheDocument();
    expect(screen.getByText(/All caught up/i)).toBeInTheDocument();
  });

  it("renders a pending badge (dot + uppercase PENDING) for each pending approval", () => {
    render(
      <ApprovalListSection
        approvals={[
          makeApproval({ id: "a1", status: "pending", title: "Deploy v2" }),
          makeApproval({
            id: "a2",
            status: "approved",
            title: "Budget bump",
            decided_by: "bob",
            decided_at: new Date().toISOString(),
            decision_comment: "LGTM",
          }),
        ]}
      />,
    );
    expect(screen.getByText("Deploy v2")).toBeInTheDocument();
    expect(screen.getByText("Budget bump")).toBeInTheDocument();
    expect(screen.getByText("pending")).toBeInTheDocument();
    expect(screen.getByText("approved")).toBeInTheDocument();
    // decision comment surfaced for the approved row
    expect(screen.getByText("LGTM")).toBeInTheDocument();
  });
});
