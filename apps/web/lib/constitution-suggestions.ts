import { apiFetch } from "@/lib/api";
import type {
  ConstitutionSuggestion,
  ConstitutionSuggestionList,
  SuggestionStatus,
} from "@forgemind/types";

/** Generate new constitution suggestions for a project. */
export async function generateSuggestions(
  projectId: string,
): Promise<ConstitutionSuggestionList> {
  return apiFetch<ConstitutionSuggestionList>(
    `/projects/${projectId}/constitution-suggestions/generate`,
    { method: "POST" },
  );
}

/** Fetch existing constitution suggestions for a project. */
export async function fetchSuggestions(
  projectId: string,
  status?: SuggestionStatus,
): Promise<ConstitutionSuggestionList> {
  const qs = status ? `?status_filter=${status}` : "";
  return apiFetch<ConstitutionSuggestionList>(
    `/projects/${projectId}/constitution-suggestions${qs}`,
  );
}

/** Accept or reject a constitution suggestion. */
export async function resolveSuggestion(
  projectId: string,
  suggestionId: string,
  action: "accept" | "reject",
): Promise<ConstitutionSuggestion> {
  return apiFetch<ConstitutionSuggestion>(
    `/projects/${projectId}/constitution-suggestions/${suggestionId}/resolve`,
    { method: "POST", body: JSON.stringify({ action }) },
  );
}
