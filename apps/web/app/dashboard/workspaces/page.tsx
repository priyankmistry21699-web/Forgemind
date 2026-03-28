"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { fetchWorkspaces, createWorkspace } from "@/lib/workspaces";
import type { Workspace } from "@/types/workspace";

export default function WorkspacesPage() {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState("");
  const [newSlug, setNewSlug] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchWorkspaces();
      setWorkspaces(data.items);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load workspaces");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const handleCreate = async () => {
    if (!newName.trim() || !newSlug.trim()) return;
    try {
      await createWorkspace({ name: newName, slug: newSlug });
      setNewName("");
      setNewSlug("");
      setShowCreate(false);
      load();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to create workspace");
    }
  };

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-xs text-[var(--color-text-muted)]">
        <Link href="/dashboard" className="hover:text-[var(--color-text)] transition-colors">
          Dashboard
        </Link>
        <span>/</span>
        <span className="text-[var(--color-text)]">Workspaces</span>
      </div>

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Workspaces</h1>
          <p className="mt-1 text-sm text-[var(--color-text-muted)]">
            Manage team workspaces and organization structure
          </p>
        </div>
        <button
          onClick={() => setShowCreate(!showCreate)}
          className="rounded-lg bg-[var(--color-accent)] px-4 py-2 text-xs font-medium text-white transition-colors hover:bg-[var(--color-accent-hover)]"
        >
          New Workspace
        </button>
      </div>

      {/* Create form */}
      {showCreate && (
        <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-bg-card)] p-4 space-y-3">
          <input
            type="text"
            placeholder="Workspace name"
            value={newName}
            onChange={(e) => {
              setNewName(e.target.value);
              setNewSlug(e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, "-"));
            }}
            className="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-secondary)] px-3 py-2 text-sm text-[var(--color-text)] placeholder:text-[var(--color-text-dim)]"
          />
          <input
            type="text"
            placeholder="slug"
            value={newSlug}
            onChange={(e) => setNewSlug(e.target.value)}
            className="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-secondary)] px-3 py-2 text-sm text-[var(--color-text)] placeholder:text-[var(--color-text-dim)]"
          />
          <div className="flex gap-2">
            <button
              onClick={handleCreate}
              className="rounded-lg bg-[var(--color-accent)] px-4 py-2 text-xs font-medium text-white hover:bg-[var(--color-accent-hover)]"
            >
              Create
            </button>
            <button
              onClick={() => setShowCreate(false)}
              className="rounded-lg border border-[var(--color-border)] px-4 py-2 text-xs font-medium text-[var(--color-text-muted)] hover:bg-[var(--color-bg-secondary)]"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-400">
          {error}
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-[var(--color-accent)] border-t-transparent" />
        </div>
      )}

      {/* Workspace list */}
      {!loading && workspaces.length === 0 && (
        <div className="rounded-xl border border-dashed border-[var(--color-border)] p-12 text-center">
          <p className="text-sm text-[var(--color-text-muted)]">No workspaces yet. Create one to get started.</p>
        </div>
      )}

      {!loading && workspaces.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {workspaces.map((ws) => (
            <div
              key={ws.id}
              className="rounded-xl border border-[var(--color-border)] bg-[var(--color-bg-card)] p-5 transition-all hover:border-[var(--color-accent)]/30"
            >
              <h3 className="font-semibold text-[var(--color-text)]">{ws.name}</h3>
              <p className="mt-1 text-xs text-[var(--color-text-dim)]">/{ws.slug}</p>
              {ws.description && (
                <p className="mt-2 text-sm text-[var(--color-text-muted)] line-clamp-2">
                  {ws.description}
                </p>
              )}
              <p className="mt-3 text-[10px] text-[var(--color-text-dim)]">
                Created {new Date(ws.created_at).toLocaleDateString()}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
