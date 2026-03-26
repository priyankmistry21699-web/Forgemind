"use client";

import { useState } from "react";
import { submitPromptIntake } from "@/lib/planner";
import type { PromptIntakeResponse } from "@/types/planner";

interface PromptIntakeFormProps {
  onPlanned: (result: PromptIntakeResponse) => void;
  onCancel: () => void;
}

export function PromptIntakeForm({
  onPlanned,
  onCancel,
}: PromptIntakeFormProps) {
  const [prompt, setPrompt] = useState("");
  const [projectName, setProjectName] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmedPrompt = prompt.trim();
    if (trimmedPrompt.length < 10) return;

    setSubmitting(true);
    setError(null);

    try {
      const result = await submitPromptIntake({
        prompt: trimmedPrompt,
        project_name: projectName.trim() || null,
      });
      onPlanned(result);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to plan project");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-card)] p-6">
      <h3 className="mb-1 text-sm font-semibold">Plan from Prompt</h3>
      <p className="mb-4 text-xs text-[var(--color-text-muted)]">
        Describe what you want to build and the planner will create a project
        with tasks.
      </p>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label
            htmlFor="prompt-text"
            className="mb-1 block text-xs font-medium text-[var(--color-text-muted)]"
          >
            What do you want to build? <span className="text-red-400">*</span>
          </label>
          <textarea
            id="prompt-text"
            rows={4}
            required
            minLength={10}
            maxLength={5000}
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="e.g. Build a REST API for managing a task board with user authentication, PostgreSQL storage, and email notifications..."
            className="w-full resize-none rounded-md border border-[var(--color-border)] bg-[var(--color-bg-secondary)] px-3 py-2 text-sm text-[var(--color-text)] placeholder:text-[var(--color-text-muted)]/50 focus:border-[var(--color-accent)] focus:outline-none"
          />
          <p className="mt-1 text-[11px] text-[var(--color-text-muted)]">
            {prompt.length}/5000 — minimum 10 characters
          </p>
        </div>

        <div>
          <label
            htmlFor="prompt-project-name"
            className="mb-1 block text-xs font-medium text-[var(--color-text-muted)]"
          >
            Project Name (optional)
          </label>
          <input
            id="prompt-project-name"
            type="text"
            maxLength={255}
            value={projectName}
            onChange={(e) => setProjectName(e.target.value)}
            placeholder="Leave blank to auto-generate"
            className="w-full rounded-md border border-[var(--color-border)] bg-[var(--color-bg-secondary)] px-3 py-2 text-sm text-[var(--color-text)] placeholder:text-[var(--color-text-muted)]/50 focus:border-[var(--color-accent)] focus:outline-none"
          />
        </div>

        {error && <p className="text-xs text-red-400">{error}</p>}

        <div className="flex items-center gap-3">
          <button
            type="submit"
            disabled={submitting || prompt.trim().length < 10}
            className="rounded-md bg-[var(--color-accent)] px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-[var(--color-accent-hover)] disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {submitting ? "Planning…" : "Plan Project"}
          </button>
          <button
            type="button"
            onClick={onCancel}
            disabled={submitting}
            className="rounded-md border border-[var(--color-border)] px-4 py-2 text-sm text-[var(--color-text-muted)] transition-colors hover:border-[var(--color-text-muted)] disabled:opacity-50"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}
