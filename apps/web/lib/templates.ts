import { apiFetch } from "@/lib/api";
import type { ProjectTemplate, ProjectTemplateList } from "@forgemind/types";

/** Fetch available project templates, optionally filtered by category. */
export async function fetchTemplates(
  category?: string,
): Promise<ProjectTemplateList> {
  const qs = category ? `?category=${encodeURIComponent(category)}` : "";
  return apiFetch<ProjectTemplateList>(`/templates${qs}`);
}

/** Fetch a single template by ID. */
export async function fetchTemplate(
  templateId: string,
): Promise<ProjectTemplate> {
  return apiFetch<ProjectTemplate>(`/templates/${templateId}`);
}
