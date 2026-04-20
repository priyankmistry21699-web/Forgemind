/**
 * FM-012 — ProjectCreateForm direct tests.
 *
 * Covers: initial render (with optional template dropdown), client-side
 * validation (empty name), loading-while-submitting, success path, failure
 * path, and cancel handler.
 */

import { describe, expect, it, vi, beforeEach } from "vitest";
import { act, fireEvent, render, screen } from "@testing-library/react";

const mocks = vi.hoisted(() => ({
  createProject: vi.fn(),
  fetchTemplates: vi.fn(),
}));

vi.mock("@/lib/projects", () => ({ createProject: mocks.createProject }));
vi.mock("@/lib/templates", () => ({ fetchTemplates: mocks.fetchTemplates }));

import { ProjectCreateForm } from "../project-create-form";

const onCreated = vi.fn();
const onCancel = vi.fn();

beforeEach(() => {
  mocks.createProject.mockReset();
  mocks.fetchTemplates.mockReset();
  onCreated.mockReset();
  onCancel.mockReset();
  // Default: no templates available
  mocks.fetchTemplates.mockResolvedValue({ items: [], total: 0 });
});

async function renderForm() {
  await act(async () => {
    render(<ProjectCreateForm onCreated={onCreated} onCancel={onCancel} />);
  });
}

describe("ProjectCreateForm (FM-012)", () => {
  it("renders the name + description inputs and action buttons", async () => {
    await renderForm();

    expect(screen.getByLabelText(/project name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/description/i)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /create project/i }),
    ).toBeDisabled(); // empty name keeps submit disabled
    expect(screen.getByRole("button", { name: /cancel/i })).toBeEnabled();
  });

  it("renders the template dropdown when fetchTemplates returns items", async () => {
    mocks.fetchTemplates.mockResolvedValue({
      items: [
        {
          id: "tpl-1",
          slug: "rest-api",
          name: "REST API",
          description: null,
          category: "backend",
          constitution_template: null,
          default_governance_config: null,
          default_phase_profiles: null,
          suggested_task_types: null,
          spec_defaults: null,
          plan_defaults: null,
          is_builtin: true,
          is_active: true,
          created_at: "",
          updated_at: "",
        },
      ],
      total: 1,
    });
    await renderForm();

    const select = screen.getByLabelText(/template/i) as HTMLSelectElement;
    expect(select).toBeInTheDocument();
    expect(
      screen.getByRole("option", { name: /REST API.*backend/ }),
    ).toBeInTheDocument();
    // default option "No template (blank project)"
    expect(
      screen.getByRole("option", { name: /No template/i }),
    ).toBeInTheDocument();
  });

  it("keeps submit disabled while the name is whitespace-only (validation)", async () => {
    await renderForm();

    fireEvent.change(screen.getByLabelText(/project name/i), {
      target: { value: "   " },
    });
    expect(
      screen.getByRole("button", { name: /create project/i }),
    ).toBeDisabled();
    // never called because form short-circuits on empty trimmed name
    expect(mocks.createProject).not.toHaveBeenCalled();
  });

  it("shows the 'Creating…' loading label while submission is pending and disables cancel", async () => {
    // Never-resolving promise keeps us in the loading branch.
    mocks.createProject.mockReturnValue(new Promise(() => {}));
    await renderForm();

    fireEvent.change(screen.getByLabelText(/project name/i), {
      target: { value: "Atlas" },
    });
    fireEvent.change(screen.getByLabelText(/description/i), {
      target: { value: "ops hub" },
    });

    await act(async () => {
      fireEvent.click(
        screen.getByRole("button", { name: /create project/i }),
      );
    });

    expect(
      screen.getByRole("button", { name: /creating/i }),
    ).toBeDisabled();
    expect(screen.getByRole("button", { name: /cancel/i })).toBeDisabled();
    expect(mocks.createProject).toHaveBeenCalledWith({
      name: "Atlas",
      description: "ops hub",
      template_id: null,
    });
  });

  it("invokes onCreated on successful submission", async () => {
    mocks.createProject.mockResolvedValue({ id: "p1" });
    await renderForm();

    fireEvent.change(screen.getByLabelText(/project name/i), {
      target: { value: "Atlas" },
    });

    await act(async () => {
      fireEvent.click(
        screen.getByRole("button", { name: /create project/i }),
      );
    });

    expect(onCreated).toHaveBeenCalledTimes(1);
    expect(onCancel).not.toHaveBeenCalled();
  });

  it("surfaces the error message when createProject rejects", async () => {
    mocks.createProject.mockRejectedValue(new Error("name conflict"));
    await renderForm();

    fireEvent.change(screen.getByLabelText(/project name/i), {
      target: { value: "Atlas" },
    });

    await act(async () => {
      fireEvent.click(
        screen.getByRole("button", { name: /create project/i }),
      );
    });

    expect(screen.getByText("name conflict")).toBeInTheDocument();
    expect(onCreated).not.toHaveBeenCalled();
    // submit button goes back to its idle state
    expect(
      screen.getByRole("button", { name: /create project/i }),
    ).toBeEnabled();
  });

  it("calls onCancel when the Cancel button is clicked", async () => {
    await renderForm();
    fireEvent.click(screen.getByRole("button", { name: /cancel/i }));
    expect(onCancel).toHaveBeenCalledTimes(1);
  });
});
