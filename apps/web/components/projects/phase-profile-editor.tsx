"use client";

import { useCallback, useEffect, useState } from "react";
import {
  fetchPhaseProfiles,
  upsertPhaseProfile,
  deletePhaseProfile,
} from "@/lib/phase-profiles";
import type {
  PhaseAgentProfile,
  WorkflowPhase,
} from "@forgemind/types";
import type { Agent } from "@forgemind/types";
import { apiFetch } from "@/lib/api";

const PHASES: WorkflowPhase[] = [
  "specify",
  "plan",
  "tasks",
  "implement",
  "review",
  "validate",
];

interface PhaseProfileEditorProps {
  projectId: string;
}

export function PhaseProfileEditor({ projectId }: PhaseProfileEditorProps) {
  const [profiles, setProfiles] = useState<PhaseAgentProfile[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [saving, setSaving] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    const [profileRes, agentRes] = await Promise.all([
      fetchPhaseProfiles(projectId),
      apiFetch<{ items: Agent[] }>("/agents"),
    ]);
    setProfiles(profileRes.items);
    setAgents(agentRes.items);
  }, [projectId]);

  useEffect(() => {
    load().catch(() => {});
  }, [load]);

  async function handleChange(phase: WorkflowPhase, agentId: string) {
    setError(null);
    setSaving(phase);
    try {
      if (!agentId) {
        await deletePhaseProfile(projectId, phase);
        setProfiles((prev) => prev.filter((p) => p.phase !== phase));
      } else {
        const updated = await upsertPhaseProfile(projectId, phase, {
          phase,
          agent_id: agentId,
        });
        setProfiles((prev) => {
          const rest = prev.filter((p) => p.phase !== phase);
          return [...rest, updated];
        });
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to update");
    } finally {
      setSaving(null);
    }
  }

  function getAgentForPhase(phase: WorkflowPhase): string {
    return profiles.find((p) => p.phase === phase)?.agent_id ?? "";
  }

  return (
    <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-bg-card)] p-4">
      <h4 className="mb-3 text-sm font-semibold text-[var(--color-text)]">
        Phase Agent Routing
      </h4>
      <p className="mb-4 text-xs text-[var(--color-text-muted)]">
        Assign a preferred agent for each workflow phase.
      </p>

      {error && <p className="mb-3 text-xs text-red-400">{error}</p>}

      <div className="space-y-2">
        {PHASES.map((phase) => (
          <div
            key={phase}
            className="flex items-center gap-3 rounded-lg bg-[var(--color-bg-secondary)] px-3 py-2"
          >
            <span className="w-24 text-xs font-medium capitalize text-[var(--color-text)]">
              {phase}
            </span>
            <select
              value={getAgentForPhase(phase)}
              onChange={(e) => handleChange(phase, e.target.value)}
              disabled={saving === phase}
              className="flex-1 rounded border border-[var(--color-border)] bg-[var(--color-bg-card)] px-2 py-1.5 text-xs text-[var(--color-text)] focus:border-[var(--color-accent)] focus:outline-none disabled:opacity-50"
            >
              <option value="">Auto (capability-based)</option>
              {agents.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.name}
                </option>
              ))}
            </select>
            {saving === phase && (
              <span className="text-xs text-[var(--color-text-muted)]">
                Saving…
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
