/** Constitution Suggestion types matching backend schemas. */

export type SuggestionStatus = "pending" | "accepted" | "rejected" | "expired";

export interface ConstitutionSuggestion {
  id: string;
  project_id: string;
  title: string;
  rationale: string | null;
  suggested_text: string;
  category: string | null;
  status: SuggestionStatus;
  source_metadata: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface ConstitutionSuggestionList {
  items: ConstitutionSuggestion[];
  total: number;
}

export interface ConstitutionSuggestionResolve {
  action: "accept" | "reject";
}
