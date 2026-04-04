"use client";

import { useState, useEffect, useCallback } from "react";
import {
  fetchConstitution,
  saveConstitution,
  deleteConstitution,
} from "@/lib/constitution";
import type { Constitution } from "@/types/constitution";

interface ConstitutionEditorProps {
  projectId: string;
}

export function ConstitutionEditor({ projectId }: ConstitutionEditorProps) {
  const [constitution, setConstitution] = useState<Constitution | null>(null);
  const [content, setContent] = useState("");
  const [title, setTitle] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchConstitution(projectId);
      setConstitution(data);
      setContent(data?.content ?? "");
      setTitle(data?.title ?? "");
    } catch {
      setError("Failed to load constitution");
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleSave() {
    if (!content.trim()) {
      setError("Constitution content cannot be empty");
      return;
    }
    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      const saved = await saveConstitution(projectId, {
        content: content.trim(),
        title: title.trim() || undefined,
      });
      setConstitution(saved);
      setSuccess(`Constitution saved (v${saved.version})`);
    } catch {
      setError("Failed to save constitution");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    if (!constitution) return;
    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      await deleteConstitution(projectId);
      setConstitution(null);
      setContent("");
      setTitle("");
      setSuccess("Constitution deleted");
    } catch {
      setError("Failed to delete constitution");
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="rounded-lg border border-[var(--color-border)] p-6">
        <p className="text-sm text-[var(--color-text-muted)]">
          Loading constitution…
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-card)] p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Project Constitution</h3>
        {constitution && (
          <span className="text-xs text-[var(--color-text-muted)]">
            v{constitution.version}
          </span>
        )}
      </div>

      <p className="text-sm text-[var(--color-text-muted)]">
        Define rules and constraints that shape how AI agents behave in this
        project. The constitution is automatically injected into all agent
        prompts.
      </p>

      {error && (
        <div className="rounded bg-red-50 border border-red-200 p-3 text-sm text-red-700">
          {error}
        </div>
      )}
      {success && (
        <div className="rounded bg-green-50 border border-green-200 p-3 text-sm text-green-700">
          {success}
        </div>
      )}

      <input
        type="text"
        placeholder="Constitution title (optional)"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        className="w-full rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 text-sm"
      />

      <textarea
        placeholder="Enter constitution rules and constraints…"
        value={content}
        onChange={(e) => setContent(e.target.value)}
        rows={12}
        className="w-full rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 text-sm font-mono"
      />

      <div className="flex gap-2">
        <button
          onClick={handleSave}
          disabled={saving || !content.trim()}
          className="rounded bg-[var(--color-accent)] px-4 py-2 text-sm font-medium text-white hover:opacity-90 disabled:opacity-50 transition-opacity"
        >
          {saving ? "Saving…" : "Save Constitution"}
        </button>
        {constitution && (
          <button
            onClick={handleDelete}
            disabled={saving}
            className="rounded border border-red-300 px-4 py-2 text-sm font-medium text-red-600 hover:bg-red-50 disabled:opacity-50 transition-colors"
          >
            Delete
          </button>
        )}
      </div>
    </div>
  );
}
