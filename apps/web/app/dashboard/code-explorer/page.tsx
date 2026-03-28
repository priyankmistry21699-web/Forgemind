"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface FileTreeEntry {
  name: string;
  path: string;
  type: "file" | "directory";
  size: number | null;
  language: string | null;
}

interface FileContent {
  path: string;
  content: string;
  language: string | null;
  size: number;
}

interface RepoConnection {
  id: string;
  name: string;
  repo_url: string;
  last_sync_status: string | null;
}

export default function CodeExplorerPage() {
  const [repos, setRepos] = useState<RepoConnection[]>([]);
  const [selectedRepo, setSelectedRepo] = useState<string | null>(null);
  const [currentPath, setCurrentPath] = useState("");
  const [entries, setEntries] = useState<FileTreeEntry[]>([]);
  const [fileContent, setFileContent] = useState<FileContent | null>(null);
  const [loading, setLoading] = useState(true);
  const [treeLoading, setTreeLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load repo connections
  const loadRepos = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/repos`);
      if (!res.ok) throw new Error("Failed to load repositories");
      const data = await res.json();
      setRepos(data.items || []);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadRepos();
  }, [loadRepos]);

  // Load file tree
  const loadTree = useCallback(
    async (repoId: string, path: string) => {
      setTreeLoading(true);
      setFileContent(null);
      setError(null);
      try {
        const params = new URLSearchParams();
        if (path) params.set("path", path);
        const res = await fetch(
          `${API_BASE}/repos/${repoId}/tree?${params.toString()}`
        );
        if (!res.ok) throw new Error("Failed to load tree");
        const data = await res.json();
        setEntries(data.entries || []);
        setCurrentPath(path);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Failed to load tree");
      } finally {
        setTreeLoading(false);
      }
    },
    []
  );

  // Load file content
  const loadFile = useCallback(
    async (repoId: string, path: string) => {
      setTreeLoading(true);
      setError(null);
      try {
        const params = new URLSearchParams({ path });
        const res = await fetch(
          `${API_BASE}/repos/${repoId}/file?${params.toString()}`
        );
        if (!res.ok) throw new Error("Failed to load file");
        const data = await res.json();
        setFileContent(data);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Failed to load file");
      } finally {
        setTreeLoading(false);
      }
    },
    []
  );

  const handleSelectRepo = (repoId: string) => {
    setSelectedRepo(repoId);
    setCurrentPath("");
    setFileContent(null);
    loadTree(repoId, "");
  };

  const handleEntryClick = (entry: FileTreeEntry) => {
    if (!selectedRepo) return;
    if (entry.type === "directory") {
      loadTree(selectedRepo, entry.path);
    } else {
      loadFile(selectedRepo, entry.path);
    }
  };

  const navigateUp = () => {
    if (!selectedRepo || !currentPath) return;
    const parts = currentPath.split("/").filter(Boolean);
    parts.pop();
    loadTree(selectedRepo, parts.join("/"));
  };

  const breadcrumbs = currentPath
    ? currentPath.split("/").filter(Boolean)
    : [];

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="animate-spin w-6 h-6 border-2 border-[var(--color-accent)] border-t-transparent rounded-full" />
      </div>
    );
  }

  return (
    <div className="space-y-4 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-xs text-[var(--color-text-muted)]">
          <Link
            href="/dashboard"
            className="hover:text-[var(--color-text)] transition-colors"
          >
            Dashboard
          </Link>
          <span>/</span>
          <span className="text-[var(--color-text)]">Code Explorer</span>
        </div>
      </div>

      {/* Repo selector */}
      <div className="flex items-center gap-3">
        <label className="text-sm text-[var(--color-text-muted)]">
          Repository:
        </label>
        <select
          className="rounded border border-[var(--color-border)] bg-[var(--color-surface)] text-sm text-[var(--color-text)] px-3 py-1.5"
          value={selectedRepo || ""}
          onChange={(e) => handleSelectRepo(e.target.value)}
        >
          <option value="">Select a repository</option>
          {repos.map((r) => (
            <option key={r.id} value={r.id}>
              {r.name}
            </option>
          ))}
        </select>
        {selectedRepo && (
          <span className="text-xs text-[var(--color-text-muted)]">
            {repos.find((r) => r.id === selectedRepo)?.repo_url}
          </span>
        )}
      </div>

      {error && (
        <div className="text-sm text-red-400 bg-red-500/10 border border-red-500/20 rounded px-3 py-2">
          {error}
        </div>
      )}

      {selectedRepo && (
        <div className="grid grid-cols-[320px_1fr] gap-4">
          {/* File tree panel */}
          <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] overflow-hidden">
            {/* Breadcrumb path */}
            <div className="px-3 py-2 border-b border-[var(--color-border)] flex items-center gap-1 text-xs text-[var(--color-text-muted)] overflow-x-auto">
              <button
                onClick={() => loadTree(selectedRepo, "")}
                className="hover:text-[var(--color-accent)] transition-colors"
              >
                /
              </button>
              {breadcrumbs.map((part, i) => {
                const path = breadcrumbs.slice(0, i + 1).join("/");
                return (
                  <span key={path} className="flex items-center gap-1">
                    <span>/</span>
                    <button
                      onClick={() => loadTree(selectedRepo, path)}
                      className="hover:text-[var(--color-accent)] transition-colors"
                    >
                      {part}
                    </button>
                  </span>
                );
              })}
            </div>

            {/* Entries */}
            <div className="max-h-[600px] overflow-y-auto">
              {treeLoading ? (
                <div className="flex justify-center py-8">
                  <div className="animate-spin w-4 h-4 border-2 border-[var(--color-accent)] border-t-transparent rounded-full" />
                </div>
              ) : (
                <>
                  {currentPath && (
                    <button
                      onClick={navigateUp}
                      className="w-full text-left px-3 py-1.5 text-sm hover:bg-[var(--color-bg)] transition-colors text-[var(--color-text-muted)] flex items-center gap-2"
                    >
                      <span>📁</span>
                      <span>..</span>
                    </button>
                  )}
                  {entries.map((entry) => (
                    <button
                      key={entry.path}
                      onClick={() => handleEntryClick(entry)}
                      className="w-full text-left px-3 py-1.5 text-sm hover:bg-[var(--color-bg)] transition-colors flex items-center gap-2"
                    >
                      <span>
                        {entry.type === "directory" ? "📁" : "📄"}
                      </span>
                      <span className="text-[var(--color-text)] truncate">
                        {entry.name}
                      </span>
                      {entry.language && (
                        <span className="ml-auto text-xs text-[var(--color-text-muted)]">
                          {entry.language}
                        </span>
                      )}
                    </button>
                  ))}
                  {entries.length === 0 && !treeLoading && (
                    <p className="p-3 text-xs text-[var(--color-text-muted)]">
                      Empty directory
                    </p>
                  )}
                </>
              )}
            </div>
          </div>

          {/* Content panel */}
          <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] overflow-hidden">
            {fileContent ? (
              <>
                <div className="px-4 py-2 border-b border-[var(--color-border)] flex items-center justify-between">
                  <span className="text-sm font-mono text-[var(--color-text)]">
                    {fileContent.path}
                  </span>
                  <span className="text-xs text-[var(--color-text-muted)]">
                    {fileContent.language || "text"} · {fileContent.size} bytes
                  </span>
                </div>
                <pre className="p-4 text-xs font-mono text-[var(--color-text-muted)] overflow-auto max-h-[600px] whitespace-pre">
                  {fileContent.content}
                </pre>
              </>
            ) : (
              <div className="flex items-center justify-center h-64 text-sm text-[var(--color-text-muted)]">
                Select a file to view its content
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
