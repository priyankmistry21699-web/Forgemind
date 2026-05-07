import { apiFetch } from "./api";

export interface CronTrigger {
  id: string;
  name: string;
  cron_expression: string;
  status: "active" | "paused" | "disabled";
  fire_count: number;
  last_fired_at: string | null;
  created_at: string;
}

export interface TriggerRule {
  id: string;
  name: string;
  event_type: string;
  enabled: boolean;
  fire_count: number;
  conditions: Record<string, unknown> | null;
}

export async function listSchedules(projectId: string): Promise<CronTrigger[]> {
  const data = await apiFetch(`/projects/${projectId}/schedules`);
  return data.items ?? [];
}

export async function createSchedule(
  projectId: string,
  body: { name: string; cron_expression: string; prompt?: string }
): Promise<CronTrigger> {
  return apiFetch(`/projects/${projectId}/schedules`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function pauseSchedule(projectId: string, triggerId: string): Promise<void> {
  await apiFetch(`/projects/${projectId}/schedules/${triggerId}/pause`, { method: "PATCH" });
}

export async function resumeSchedule(projectId: string, triggerId: string): Promise<void> {
  await apiFetch(`/projects/${projectId}/schedules/${triggerId}/resume`, { method: "PATCH" });
}

export async function listTriggerRules(projectId: string): Promise<TriggerRule[]> {
  const data = await apiFetch(`/projects/${projectId}/trigger-rules`);
  return data.items ?? [];
}
