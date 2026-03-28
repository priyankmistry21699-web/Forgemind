"use client";

import { useCallback, useEffect, useState } from "react";
import { fetchProjectMembers, addProjectMember, removeProjectMember } from "@/lib/project-members";
import type { ProjectMember } from "@/types/project-member";

const ROLE_COLORS: Record<string, string> = {
  lead: "text-amber-400 bg-amber-500/10",
  contributor: "text-blue-400 bg-blue-500/10",
  reviewer: "text-purple-400 bg-purple-500/10",
  viewer: "text-[var(--color-text-dim)] bg-[var(--color-bg-secondary)]",
};

interface ProjectMembersPanelProps {
  projectId: string;
}

export function ProjectMembersPanel({ projectId }: ProjectMembersPanelProps) {
  const [members, setMembers] = useState<ProjectMember[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [newUserId, setNewUserId] = useState("");
  const [newRole, setNewRole] = useState("contributor");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchProjectMembers(projectId);
      setMembers(data.items);
    } catch {
      // silently handle
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    load();
  }, [load]);

  const handleAdd = async () => {
    if (!newUserId.trim()) return;
    try {
      await addProjectMember(projectId, { user_id: newUserId, role: newRole });
      setNewUserId("");
      setShowAdd(false);
      load();
    } catch {
      // handle error
    }
  };

  const handleRemove = async (memberId: string) => {
    try {
      await removeProjectMember(memberId);
      load();
    } catch {
      // handle error
    }
  };

  return (
    <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-bg-card)] p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-[var(--color-text)]">
          Team Members ({members.length})
        </h3>
        <button
          onClick={() => setShowAdd(!showAdd)}
          className="rounded-md bg-[var(--color-accent)] px-2 py-1 text-[10px] font-medium text-white hover:bg-[var(--color-accent-hover)]"
        >
          + Add
        </button>
      </div>

      {/* Add form */}
      {showAdd && (
        <div className="mb-3 space-y-2 rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-secondary)] p-3">
          <input
            type="text"
            placeholder="User ID"
            value={newUserId}
            onChange={(e) => setNewUserId(e.target.value)}
            className="w-full rounded-md border border-[var(--color-border)] bg-[var(--color-bg-card)] px-2 py-1.5 text-xs text-[var(--color-text)]"
          />
          <select
            value={newRole}
            onChange={(e) => setNewRole(e.target.value)}
            className="w-full rounded-md border border-[var(--color-border)] bg-[var(--color-bg-card)] px-2 py-1.5 text-xs text-[var(--color-text)]"
          >
            <option value="lead">Lead</option>
            <option value="contributor">Contributor</option>
            <option value="reviewer">Reviewer</option>
            <option value="viewer">Viewer</option>
          </select>
          <button
            onClick={handleAdd}
            className="w-full rounded-md bg-[var(--color-accent)] px-2 py-1.5 text-xs font-medium text-white hover:bg-[var(--color-accent-hover)]"
          >
            Add Member
          </button>
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="flex justify-center py-4">
          <div className="h-4 w-4 animate-spin rounded-full border-2 border-[var(--color-accent)] border-t-transparent" />
        </div>
      )}

      {/* Member list */}
      {!loading && members.length === 0 && (
        <p className="py-4 text-center text-xs text-[var(--color-text-dim)]">No members yet</p>
      )}

      {!loading && members.length > 0 && (
        <div className="space-y-2">
          {members.map((m) => (
            <div
              key={m.id}
              className="flex items-center justify-between rounded-lg px-3 py-2 hover:bg-[var(--color-bg-secondary)]"
            >
              <div className="flex items-center gap-2">
                <div className="flex h-6 w-6 items-center justify-center rounded-full bg-[var(--color-bg-secondary)] text-[10px] font-bold text-[var(--color-text-muted)]">
                  U
                </div>
                <span className="text-xs text-[var(--color-text)]">{m.user_id.slice(0, 8)}...</span>
              </div>
              <div className="flex items-center gap-2">
                <span className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${ROLE_COLORS[m.role] ?? ""}`}>
                  {m.role}
                </span>
                <button
                  onClick={() => handleRemove(m.id)}
                  className="text-[10px] text-[var(--color-text-dim)] hover:text-red-400"
                >
                  ×
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
