/** Council types matching the backend schemas (FM-047A). */

export type CouncilStatus = "convened" | "deliberating" | "decided" | "deadlocked" | "escalated";
export type DecisionMethod = "consensus" | "majority" | "supermajority" | "weighted";
export type VoteDecision = "approve" | "reject" | "abstain" | "modify";

export interface CouncilVote {
  id: string;
  session_id: string;
  agent_slug: string;
  decision: VoteDecision;
  reasoning: string | null;
  confidence: number;
  weight: number;
  suggested_modifications: Record<string, unknown> | null;
  created_at: string;
}

export interface CouncilSession {
  id: string;
  project_id: string;
  run_id: string | null;
  task_id: string | null;
  topic: string;
  description: string | null;
  context: Record<string, unknown> | null;
  status: CouncilStatus;
  decision_method: DecisionMethod;
  final_decision: string | null;
  decision_rationale: string | null;
  decision_metadata: Record<string, unknown> | null;
  convened_at: string;
  decided_at: string | null;
  votes: CouncilVote[];
  created_at: string;
  updated_at: string;
}

export interface CouncilSessionList {
  items: CouncilSession[];
  total: number;
}
