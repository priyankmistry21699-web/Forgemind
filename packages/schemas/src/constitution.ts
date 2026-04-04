/** FM-102/103: Constitution types matching the backend ConstitutionRead schema. */

export interface Constitution {
  id: string;
  project_id: string;
  title: string | null;
  content: string;
  summary: string | null;
  version: number;
  created_at: string;
  updated_at: string;
}
