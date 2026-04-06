/** Project Template types matching backend schemas. */

export interface ProjectTemplate {
  id: string;
  slug: string;
  name: string;
  description: string | null;
  category: string;
  constitution_template: string | null;
  default_governance_config: Record<string, unknown> | null;
  default_phase_profiles: Record<string, unknown>[] | null;
  suggested_task_types: string[] | null;
  spec_defaults: Record<string, unknown> | null;
  plan_defaults: Record<string, unknown> | null;
  is_builtin: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ProjectTemplateList {
  items: ProjectTemplate[];
  total: number;
}
