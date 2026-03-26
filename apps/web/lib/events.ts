import { apiFetch } from "@/lib/api";
import type { ExecutionEventList } from "@/types/execution-event";

/** Fetch execution events, optionally filtered by project/run. */
export async function fetchEvents(opts?: {
  projectId?: string;
  runId?: string;
  limit?: number;
}): Promise<ExecutionEventList> {
  const params = new URLSearchParams();
  if (opts?.projectId) params.set("project_id", opts.projectId);
  if (opts?.runId) params.set("run_id", opts.runId);
  if (opts?.limit) params.set("limit", String(opts.limit));
  const qs = params.toString();
  return apiFetch<ExecutionEventList>(`/events${qs ? `?${qs}` : ""}`);
}
