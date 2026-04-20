/**
 * FM-003 / FM-012 smoke tests for the project-list primitive components.
 *
 * These components are the presentation layer used by the dashboard home page
 * (apps/web/app/dashboard/page.tsx) for the loading / empty / populated /
 * error branches of the project list.  The page itself pulls in too many
 * nested client components to render cheaply, so we exercise the primitives
 * directly here.
 */

import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import type { Project } from "@/types/project";

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

import {
  ProjectCard,
  ProjectListEmpty,
  ProjectListError,
  ProjectListSkeleton,
} from "../project-list";

function makeProject(overrides: Partial<Project> = {}): Project {
  return {
    id: "00000000-0000-0000-0000-000000000001",
    name: "Atlas",
    description: "Primary orchestration project",
    status: "active",
    owner_id: "owner-1",
    workspace_id: null,
    template_id: null,
    created_at: new Date(Date.now() - 90 * 60 * 1000).toISOString(), // 90 min ago
    updated_at: new Date().toISOString(),
    ...overrides,
  };
}

describe("ProjectCard", () => {
  it("links to the project detail route and renders name + status", () => {
    render(<ProjectCard project={makeProject()} />);

    const link = screen.getByRole("link");
    expect(link).toHaveAttribute(
      "href",
      "/dashboard/projects/00000000-0000-0000-0000-000000000001",
    );
    expect(screen.getByText("Atlas")).toBeInTheDocument();
    expect(screen.getByText("active")).toBeInTheDocument();
  });

  it("omits the description block when description is null", () => {
    render(<ProjectCard project={makeProject({ description: null })} />);
    expect(
      screen.queryByText("Primary orchestration project"),
    ).not.toBeInTheDocument();
  });

  it("computes a human-readable relative timestamp", () => {
    // created 90 minutes ago -> "1h ago"
    render(<ProjectCard project={makeProject()} />);
    expect(screen.getByText(/Created 1h ago/)).toBeInTheDocument();
  });

  it("falls back to the draft style for an unknown status value", () => {
    // exercise the STATUS_STYLES ?? fallback branch; TS is happy because we
    // cast through unknown since ProjectStatus is a closed union at compile
    // time but the runtime fallback must still hold for stale API data.
    render(
      <ProjectCard
        project={makeProject({
          status: "mystery" as unknown as Project["status"],
        })}
      />,
    );
    // Badge still renders, just with the raw unknown value.
    expect(screen.getByText("mystery")).toBeInTheDocument();
  });
});

describe("ProjectListEmpty", () => {
  it("renders the empty-state guidance copy", () => {
    render(<ProjectListEmpty />);
    expect(screen.getByText("No projects yet")).toBeInTheDocument();
    expect(
      screen.getByText(/Create your first project/i),
    ).toBeInTheDocument();
  });
});

describe("ProjectListSkeleton", () => {
  it("renders three animate-pulse placeholders", () => {
    const { container } = render(<ProjectListSkeleton />);
    expect(container.querySelectorAll(".animate-pulse")).toHaveLength(3);
  });
});

describe("ProjectListError", () => {
  it("surfaces the given error message alongside the headline", () => {
    render(<ProjectListError message="network down" />);
    expect(screen.getByText("Failed to load projects")).toBeInTheDocument();
    expect(screen.getByText("network down")).toBeInTheDocument();
  });
});
