/**
 * FM-013 — PromptIntakeForm direct tests.
 *
 * Covers: render, minLength=10 validation, loading branch, success path,
 * error path, character counter, and cancel handler.
 */

import { describe, expect, it, vi, beforeEach } from "vitest";
import { act, fireEvent, render, screen } from "@testing-library/react";

const mocks = vi.hoisted(() => ({
  submitPromptIntake: vi.fn(),
}));

vi.mock("@/lib/planner", () => ({
  submitPromptIntake: mocks.submitPromptIntake,
}));

import { PromptIntakeForm } from "../prompt-intake-form";

const onPlanned = vi.fn();
const onCancel = vi.fn();

beforeEach(() => {
  mocks.submitPromptIntake.mockReset();
  onPlanned.mockReset();
  onCancel.mockReset();
});

function renderForm() {
  render(<PromptIntakeForm onPlanned={onPlanned} onCancel={onCancel} />);
}

describe("PromptIntakeForm (FM-013)", () => {
  it("renders prompt + optional project name inputs and a disabled submit", () => {
    renderForm();
    expect(
      screen.getByLabelText(/what do you want to build/i),
    ).toBeInTheDocument();
    expect(screen.getByLabelText(/project name/i)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /plan project/i }),
    ).toBeDisabled();
    expect(screen.getByText(/0\/5000/)).toBeInTheDocument();
  });

  it("keeps submit disabled until the prompt hits the 10-char minimum", () => {
    renderForm();
    const ta = screen.getByLabelText(/what do you want to build/i);

    fireEvent.change(ta, { target: { value: "short" } });
    expect(
      screen.getByRole("button", { name: /plan project/i }),
    ).toBeDisabled();

    fireEvent.change(ta, { target: { value: "10chars!!!" } });
    expect(screen.getByRole("button", { name: /plan project/i })).toBeEnabled();

    // character counter updates as we type
    expect(screen.getByText(/10\/5000/)).toBeInTheDocument();
  });

  it("shows the 'Planning…' label while the submission is pending", async () => {
    mocks.submitPromptIntake.mockReturnValue(new Promise(() => {}));
    renderForm();

    fireEvent.change(screen.getByLabelText(/what do you want to build/i), {
      target: { value: "Build a task board API" },
    });
    fireEvent.change(screen.getByLabelText(/project name/i), {
      target: { value: "Tasky" },
    });

    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /plan project/i }));
    });

    expect(screen.getByRole("button", { name: /planning/i })).toBeDisabled();
    expect(screen.getByRole("button", { name: /cancel/i })).toBeDisabled();
    expect(mocks.submitPromptIntake).toHaveBeenCalledWith({
      prompt: "Build a task board API",
      project_name: "Tasky",
    });
  });

  it("invokes onPlanned with the response on success", async () => {
    const response = {
      project_id: "proj-1",
      run_id: "run-1",
      tasks_created: 5,
      message: "ok",
      created_at: new Date().toISOString(),
    };
    mocks.submitPromptIntake.mockResolvedValue(response);
    renderForm();

    fireEvent.change(screen.getByLabelText(/what do you want to build/i), {
      target: { value: "Build a task board API" },
    });

    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /plan project/i }));
    });

    expect(onPlanned).toHaveBeenCalledWith(response);
    expect(mocks.submitPromptIntake).toHaveBeenCalledWith({
      prompt: "Build a task board API",
      project_name: null, // blank project name is coerced to null
    });
  });

  it("surfaces the error message when submitPromptIntake rejects", async () => {
    mocks.submitPromptIntake.mockRejectedValue(new Error("llm timeout"));
    renderForm();

    fireEvent.change(screen.getByLabelText(/what do you want to build/i), {
      target: { value: "Build a task board API" },
    });

    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /plan project/i }));
    });

    expect(screen.getByText("llm timeout")).toBeInTheDocument();
    expect(onPlanned).not.toHaveBeenCalled();
  });

  it("calls onCancel when the Cancel button is clicked", () => {
    renderForm();
    fireEvent.click(screen.getByRole("button", { name: /cancel/i }));
    expect(onCancel).toHaveBeenCalledTimes(1);
  });

  it("keeps submit disabled when the prompt is only whitespace padded to 10+ chars", () => {
    renderForm();
    // 12 whitespace chars — button's disabled attr uses prompt.trim().length < 10.
    fireEvent.change(screen.getByLabelText(/what do you want to build/i), {
      target: { value: "            " },
    });
    expect(
      screen.getByRole("button", { name: /plan project/i }),
    ).toBeDisabled();
  });

  it("short-circuits submission when trimmed prompt is shorter than 10 chars (handleSubmit guard)", async () => {
    renderForm();

    const ta = screen.getByLabelText(
      /what do you want to build/i,
    ) as HTMLTextAreaElement;
    // "  hi there  " → trims to 8 chars, below the gate.
    fireEvent.change(ta, { target: { value: "  hi there  " } });

    // Force a submit event directly so we bypass the disabled-button UI.
    await act(async () => {
      fireEvent.submit(ta.closest("form")!);
    });
    expect(mocks.submitPromptIntake).not.toHaveBeenCalled();
    expect(onPlanned).not.toHaveBeenCalled();
  });
});
