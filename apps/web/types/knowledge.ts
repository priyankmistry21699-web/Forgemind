/** Project knowledge types matching the backend schemas (FM-048). */

export type KnowledgeType =
  | "pattern"
  | "decision"
  | "lesson_learned"
  | "dependency"
  | "best_practice"
  | "architecture"
  | "constraint";

export interface ProjectKnowledge {
  id: string;
  project_id: string;
  source_run_id: string | null;
  source_task_id: string | null;
  knowledge_type: KnowledgeType;
  title: string;
  content: string;
  tags: string[] | null;
  metadata_: Record<string, unknown> | null;
  relevance_score: number;
  usage_count: number;
  created_at: string;
  updated_at: string;
}

export interface ProjectKnowledgeList {
  items: ProjectKnowledge[];
  total: number;
}
