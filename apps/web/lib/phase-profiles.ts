import { apiFetch } from "@/lib/api";
import type {
  PhaseAgentProfile,
  PhaseAgentProfileCreate,
  PhaseAgentProfileList,
  WorkflowPhase,
} from "@forgemind/types";

/** Fetch all phase-agent profiles for a project. */
export async function fetchPhaseProfiles(
  projectId: string,
): Promise<PhaseAgentProfileList> {
  return apiFetch<PhaseAgentProfileList>(
    `/projects/${projectId}/phase-agent-profiles`,
  );
}

/** Create or update a phase-agent profile. */
export async function upsertPhaseProfile(
  projectId: string,
  phase: WorkflowPhase,
  data: PhaseAgentProfileCreate,
): Promise<PhaseAgentProfile> {
  return apiFetch<PhaseAgentProfile>(
    `/projects/${projectId}/phase-agent-profiles/${phase}`,
    { method: "PUT", body: JSON.stringify(data) },
  );
}

/** Remove a phase-agent profile. */
export async function deletePhaseProfile(
  projectId: string,
  phase: WorkflowPhase,
): Promise<void> {
  await apiFetch(`/projects/${projectId}/phase-agent-profiles/${phase}`, {
    method: "DELETE",
  });
}
