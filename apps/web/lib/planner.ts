import { apiFetch } from "@/lib/api";
import type {
  PromptIntakeRequest,
  PromptIntakeResponse,
  PlannerResult,
} from "@/types/planner";

/** Submit a natural-language prompt to the planner. */
export async function submitPromptIntake(
  data: PromptIntakeRequest,
): Promise<PromptIntakeResponse> {
  return apiFetch<PromptIntakeResponse>("/planner/intake", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/** Fetch the planner result for a run. Returns null if none exists. */
export async function fetchPlannerResult(
  runId: string,
): Promise<PlannerResult | null> {
  try {
    return await apiFetch<PlannerResult>(`/runs/${runId}/plan`);
  } catch {
    return null;
  }
}
