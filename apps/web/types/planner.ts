/** Planner types matching the backend PromptIntake schemas. */

export interface PromptIntakeRequest {
  prompt: string;
  project_name?: string | null;
}

export interface PromptIntakeResponse {
  project_id: string;
  run_id: string;
  tasks_created: number;
  message: string;
  created_at: string;
}

export interface PlannerResult {
  id: string;
  run_id: string;
  overview: string | null;
  architecture_summary: string | null;
  recommended_stack: Record<string, string> | null;
  assumptions: string[] | null;
  next_steps: string[] | null;
  created_at: string;
  updated_at: string;
}
