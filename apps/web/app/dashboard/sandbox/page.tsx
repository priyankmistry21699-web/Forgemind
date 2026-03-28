"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface SandboxExecution {
  id: string;
  project_id: string;
  command: string;
  status: string;
  exit_code: number | null;
  stdout: string | null;
  stderr: string | null;
  timeout_seconds: number;
  approval_id: string | null;
  allowed_commands: string[] | null;
  resource_limits: Record<string, unknown> | null;
  isolated: boolean;
  created_at: string;
  updated_at: string;
}

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    pending: "bg-gray-500/20 text-gray-400",
    running: "bg-blue-500/20 text-blue-400",
    success: "bg-green-500/20 text-green-400",
    failed: "bg-red-500/20 text-red-400",
    timeout: "bg-amber-500/20 text-amber-400",
    blocked: "bg-red-500/20 text-red-400",
  };
  return (
    <span
      className={`px-2 py-0.5 rounded text-xs font-medium ${colors[status] || "bg-gray-500/20 text-gray-400"}`}
    >
      {status}
    </span>
  );
}

export default function SandboxPage() {
  const [executions, setExecutions] = useState<SandboxExecution[]>([]);
  const [selected, setSelected] = useState<SandboxExecution | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [runCommand, setRunCommand] = useState("");
  const [runLoading, setRunLoading] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/sandbox`);
      if (!res.ok) throw new Error("Failed to load executions");
      const data = await res.json();
      setExecutions(data.items || []);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const handleRun = async () => {
    if (!runCommand.trim()) return;
    setRunLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/sandbox/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ command: runCommand }),
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Execution failed");
      }
      const data = await res.json();
      setSelected(data);
      setRunCommand("");
      load();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Execution failed");
    } finally {
      setRunLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="animate-spin w-6 h-6 border-2 border-[var(--color-accent)] border-t-transparent rounded-full" />
      </div>
    );
  }

  return (
    <div className="space-y-4 max-w-5xl mx-auto">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-xs text-[var(--color-text-muted)]">
        <Link
          href="/dashboard"
          className="hover:text-[var(--color-text)] transition-colors"
        >
          Dashboard
        </Link>
        <span>/</span>
        <span className="text-[var(--color-text)]">Sandbox</span>
      </div>

      <h1 className="text-xl font-semibold text-[var(--color-text)]">
        Code Execution Sandbox
      </h1>

      {/* Run command */}
      <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-4">
        <label className="text-sm font-medium text-[var(--color-text)] block mb-2">
          Run Command
        </label>
        <div className="flex gap-2">
          <input
            type="text"
            value={runCommand}
            onChange={(e) => setRunCommand(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleRun()}
            placeholder="python script.py"
            className="flex-1 rounded border border-[var(--color-border)] bg-[var(--color-bg)] text-sm text-[var(--color-text)] px-3 py-1.5 font-mono"
          />
          <button
            onClick={handleRun}
            disabled={runLoading || !runCommand.trim()}
            className="px-4 py-1.5 rounded bg-[var(--color-accent)] text-white text-sm font-medium disabled:opacity-50 hover:opacity-90 transition-opacity"
          >
            {runLoading ? "Running..." : "Run"}
          </button>
        </div>
        <p className="text-xs text-[var(--color-text-muted)] mt-1">
          Only allowlisted commands (python, pip, pytest, echo, cat, ls, etc.)
          are permitted.
        </p>
      </div>

      {error && (
        <div className="text-sm text-red-400 bg-red-500/10 border border-red-500/20 rounded px-3 py-2">
          {error}
        </div>
      )}

      <div className="grid grid-cols-[1fr_1fr] gap-4">
        {/* Execution list */}
        <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] overflow-hidden">
          <div className="px-4 py-2 border-b border-[var(--color-border)]">
            <h2 className="text-sm font-medium text-[var(--color-text)]">
              Executions ({executions.length})
            </h2>
          </div>
          <div className="max-h-[500px] overflow-y-auto divide-y divide-[var(--color-border)]">
            {executions.length === 0 ? (
              <p className="p-4 text-sm text-[var(--color-text-muted)]">
                No executions yet.
              </p>
            ) : (
              executions.map((exec) => (
                <button
                  key={exec.id}
                  onClick={() => setSelected(exec)}
                  className={`w-full text-left px-4 py-3 hover:bg-[var(--color-bg)] transition-colors ${selected?.id === exec.id ? "bg-[var(--color-bg)]" : ""}`}
                >
                  <div className="flex items-center justify-between">
                    <code className="text-xs font-mono text-[var(--color-text)] truncate max-w-[200px]">
                      {exec.command}
                    </code>
                    <StatusBadge status={exec.status} />
                  </div>
                  <div className="flex items-center gap-3 mt-1 text-xs text-[var(--color-text-muted)]">
                    {exec.exit_code !== null && (
                      <span>exit: {exec.exit_code}</span>
                    )}
                    <span>
                      {new Date(exec.created_at).toLocaleString()}
                    </span>
                  </div>
                </button>
              ))
            )}
          </div>
        </div>

        {/* Execution detail */}
        <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] overflow-hidden">
          {selected ? (
            <>
              <div className="px-4 py-2 border-b border-[var(--color-border)] flex items-center justify-between">
                <code className="text-sm font-mono text-[var(--color-text)]">
                  {selected.command}
                </code>
                <StatusBadge status={selected.status} />
              </div>
              <div className="p-4 space-y-3">
                <div className="flex flex-wrap gap-3 text-xs text-[var(--color-text-muted)]">
                  {selected.exit_code !== null && (
                    <span>Exit Code: {selected.exit_code}</span>
                  )}
                  <span>Timeout: {selected.timeout_seconds}s</span>
                  <span>Isolated: {selected.isolated ? "Yes" : "No"}</span>
                </div>

                {selected.stdout && (
                  <div>
                    <h3 className="text-xs font-medium text-[var(--color-text)] mb-1">
                      stdout
                    </h3>
                    <pre className="p-3 rounded bg-[var(--color-bg)] text-xs font-mono text-green-400 max-h-48 overflow-auto whitespace-pre">
                      {selected.stdout}
                    </pre>
                  </div>
                )}
                {selected.stderr && (
                  <div>
                    <h3 className="text-xs font-medium text-[var(--color-text)] mb-1">
                      stderr
                    </h3>
                    <pre className="p-3 rounded bg-[var(--color-bg)] text-xs font-mono text-red-400 max-h-48 overflow-auto whitespace-pre">
                      {selected.stderr}
                    </pre>
                  </div>
                )}
                {!selected.stdout && !selected.stderr && (
                  <p className="text-xs text-[var(--color-text-muted)]">
                    No output captured.
                  </p>
                )}
              </div>
            </>
          ) : (
            <div className="flex items-center justify-center h-64 text-sm text-[var(--color-text-muted)]">
              Select an execution to view details
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
