/**
 * ForgeMind TypeScript SDK — FM-209.
 *
 * Async TypeScript client for the ForgeMind API.
 * Covers all v1 endpoints with correct types.
 */

// ── Types ────────────────────────────────────────────────────────

export interface ForgeMindConfig {
  baseUrl?: string;
  apiKey?: string;
  timeout?: number;
}

export interface Project {
  id: string;
  name: string;
  description?: string;
  status: string;
  created_at?: string;
}

export interface Task {
  id: string;
  title: string;
  description?: string;
  task_type: string;
  status: string;
  order_index?: number;
}

export interface Run {
  id: string;
  run_number: number;
  status: string;
  trigger?: string;
}

export interface DependencyGraph {
  node_count: number;
  edge_count: number;
  nodes: Record<string, string[]>;
}

export interface ImpactAnalysis {
  changed_files: string[];
  total_affected: number;
  risk_score: number;
  risk_level: string;
  affected_tests: string[];
}

export interface TestSelection {
  mode: string;
  selected_tests: string[];
  confidence: number;
}

export interface CodeIntelligenceContext {
  project_id: string;
  dependency_graph: { node_count: number; edge_count: number };
  coverage: { mapping_count: number; covered_files: number; avg_coverage: number; gap_count: number };
  complexity_hotspots: Array<{ file: string; function: string; metric_type: string; value: number }>;
  debt: Record<string, unknown>;
  flakiness: Record<string, unknown>;
  impact_analysis?: Record<string, unknown>;
}

export interface APIKey {
  id: string;
  name: string;
  key_prefix: string;
  key?: string;
  scopes: string[];
}

export interface Webhook {
  id: string;
  url: string;
  events: string[];
  active: boolean;
}

export interface PaginatedResponse<T> {
  items: T[];
  total?: number;
}

export interface CycleTime {
  avg_seconds: number;
  median_seconds: number;
  p95_seconds: number;
}

export interface QualityScore {
  test_pass_rate: number;
  defect_density: number;
  rollback_rate: number;
  review_coverage: number;
}

export class ForgeMindError extends Error {
  statusCode: number;
  detail: string;

  constructor(statusCode: number, detail: string) {
    super(`HTTP ${statusCode}: ${detail}`);
    this.statusCode = statusCode;
    this.detail = detail;
    this.name = "ForgeMindError";
  }
}

// ── Client ───────────────────────────────────────────────────────

export class ForgeMindClient {
  private baseUrl: string;
  private apiKey: string;
  private timeout: number;

  constructor(config: ForgeMindConfig = {}) {
    this.baseUrl = (config.baseUrl || process.env.FORGEMIND_BASE_URL || "http://localhost:8000").replace(/\/$/, "");
    this.apiKey = config.apiKey || process.env.FORGEMIND_API_KEY || "";
    this.timeout = config.timeout || 30000;
  }

  private headers(): Record<string, string> {
    const h: Record<string, string> = { "Content-Type": "application/json" };
    if (this.apiKey) {
      h["X-API-Key"] = this.apiKey;
    }
    return h;
  }

  private async request<T = Record<string, unknown>>(
    method: string,
    path: string,
    options?: { body?: unknown; params?: Record<string, string> },
  ): Promise<T> {
    let url = `${this.baseUrl}${path}`;
    if (options?.params) {
      const qs = new URLSearchParams(options.params).toString();
      url += `?${qs}`;
    }

    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), this.timeout);

    try {
      const resp = await fetch(url, {
        method,
        headers: this.headers(),
        body: options?.body ? JSON.stringify(options.body) : undefined,
        signal: controller.signal,
      });

      if (!resp.ok) {
        let detail: string;
        try {
          const errBody = await resp.json();
          detail = (errBody as Record<string, string>).detail || resp.statusText;
        } catch {
          detail = resp.statusText;
        }
        throw new ForgeMindError(resp.status, detail);
      }

      return (await resp.json()) as T;
    } finally {
      clearTimeout(timer);
    }
  }

  // ── Projects ──────────────────────────────────────────────

  async listProjects(params?: Record<string, string>): Promise<PaginatedResponse<Project>> {
    return this.request("GET", "/api/v1/projects", { params });
  }

  async getProject(projectId: string): Promise<Project> {
    return this.request("GET", `/api/v1/projects/${projectId}`);
  }

  async createProject(data: { name: string; description?: string }): Promise<Project> {
    return this.request("POST", "/api/v1/projects", { body: data });
  }

  // ── Tasks ─────────────────────────────────────────────────

  async listTasks(projectId: string, params?: Record<string, string>): Promise<PaginatedResponse<Task>> {
    return this.request("GET", `/api/v1/projects/${projectId}/tasks`, { params });
  }

  async createTask(projectId: string, data: { title: string; description?: string; task_type?: string }): Promise<Task> {
    return this.request("POST", `/api/v1/projects/${projectId}/tasks`, { body: data });
  }

  // ── Code Intelligence ─────────────────────────────────────

  async getDependencyGraph(projectId: string): Promise<DependencyGraph> {
    return this.request("GET", `/api/v1/projects/${projectId}/dependencies/graph`);
  }

  async analyzeImpact(projectId: string, changedFiles: string[]): Promise<ImpactAnalysis> {
    return this.request("POST", `/api/v1/projects/${projectId}/dependencies/impact`, {
      body: { changed_files: changedFiles },
    });
  }

  async selectTests(projectId: string, changedFiles: string[], mode: string = "standard"): Promise<TestSelection> {
    return this.request("POST", `/api/v1/projects/${projectId}/select-tests`, {
      body: { changed_files: changedFiles, mode },
    });
  }

  async getCodeIntelligenceContext(
    projectId: string,
    changedFiles?: string[],
  ): Promise<CodeIntelligenceContext> {
    const body: Record<string, unknown> = {};
    if (changedFiles) body.changed_files = changedFiles;
    return this.request("POST", `/api/v1/projects/${projectId}/code-intelligence-context`, { body });
  }

  // ── Analytics ─────────────────────────────────────────────

  async getCycleTime(projectId: string, params?: Record<string, string>): Promise<CycleTime> {
    return this.request("GET", `/api/v1/projects/${projectId}/cycle-time`, { params });
  }

  async getQualityScore(projectId: string): Promise<QualityScore> {
    return this.request("GET", `/api/v1/projects/${projectId}/quality-score`);
  }

  // ── Webhooks ──────────────────────────────────────────────

  async fireWebhook(eventType: string, payload: Record<string, unknown>): Promise<Record<string, unknown>> {
    return this.request("POST", "/api/v1/webhooks/fire", {
      body: { event_type: eventType, payload },
    });
  }

  async listWebhooks(): Promise<PaginatedResponse<Webhook>> {
    return this.request("GET", "/api/v1/ecosystem/webhooks");
  }

  // ── API Keys ──────────────────────────────────────────────

  async listApiKeys(): Promise<PaginatedResponse<APIKey>> {
    return this.request("GET", "/api/v1/ecosystem/api-keys");
  }

  async createApiKey(name: string, scopes?: string[]): Promise<APIKey> {
    const body: Record<string, unknown> = { name };
    if (scopes) body.scopes = scopes;
    return this.request("POST", "/api/v1/ecosystem/api-keys", { body });
  }

  async revokeApiKey(keyId: string): Promise<{ revoked: boolean }> {
    return this.request("DELETE", `/api/v1/ecosystem/api-keys/${keyId}`);
  }
}

export default ForgeMindClient;
