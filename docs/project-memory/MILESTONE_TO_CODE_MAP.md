# 8 · Milestone → Code Map

> Major delivered milestones mapped to the concrete services, routes, models, and UI folders that implement them. Groupings follow the wave structure in [`../MILESTONE_SUMMARY.md`](../MILESTONE_SUMMARY.md).

## Legend

- **R** = routes (`apps/api/app/api/routes/`)
- **S** = services (`apps/api/app/services/`)
- **M** = models (`apps/api/app/models/`)
- **UI** = frontend (`apps/web/app/dashboard/`, `apps/web/lib/`, `apps/web/components/`)

---

## V1 — Foundation (FM-001 → FM-035)

Core engine (planner + orchestrator + execution + events + approvals + costs).

| Milestone group | Code anchors |
| :-- | :-- |
| Planning | R `planner.py`, `planner_results.py` · S `planner_service`, `spec_service`, `spec_plan_validation_service`, `plan_artifact_service` · M `planner_result`, `artifact` · UI `dashboard/runs/`, `components/planner/` |
| Execution & events | R `runs.py`, `tasks.py`, `events.py`, `streaming.py` · S `execution_service`, `run_lifecycle_service`, `event_service`, `stream_service` · M `run`, `task`, `execution_event` · UI `dashboard/runs/`, `lib/runs.ts`, `lib/stream.ts` |
| Approvals & costs | R `approvals.py`, `costs.py` · S `approval_service`, `cost_tracking_service` · M `approval_request`, `cost_record` · UI `dashboard/approvals/`, `dashboard/costs/` |

## V2 — Governance (FM-036 → FM-080)

Constitution, trust, council, architecture approvals, enhanced approvals.

| Area | Code anchors |
| :-- | :-- |
| Constitution | R `constitution.py`, `constitution_suggestions.py` · S `constitution_service`, `constitution_suggestion_service` · M `project_constitution`, `constitution_suggestion` · UI `dashboard/governance/` |
| Trust scoring | R `trust.py` · S `trust_scoring_service` · M `trust_score` · UI `dashboard/trust/` |
| Council | R `council.py` · S `council_service` · M `council` · UI `dashboard/council/` |
| Architecture approvals | R `architecture.py` · S `architecture_approval_service` · M `architecture`, `approval_request` · UI `dashboard/architecture/` |
| Approval enhancements | S `approval_enhanced_service`, `spec_plan_approval_service` · M `approval_delegation` |

## V3 — Collaboration & replay (FM-081 → FM-140)

Workspaces, RBAC, comments, mentions, saved views, activity, replay, local CLI.

| Area | Code anchors |
| :-- | :-- |
| Workspaces + RBAC | R `workspaces.py`, `members.py` · S `workspace_service`, `membership_service`, `authz_service` · M `workspace`, `membership`, `user` · UI `dashboard/workspaces/`, `dashboard/settings/` |
| Comments + mentions | R `comments.py`, `collaboration.py` · S `comment_service`, `mention_service` · M `comment` · UI `components/chat/`, `dashboard/approvals/`, `dashboard/runs/` |
| Saved views | R `saved_views.py` · S `saved_view_service` · M `saved_view` · UI throughout list pages |
| Activity feed | R `activity.py` · S `activity_service`, `unified_activity_service`, `user_activity_service` · M `activity` · UI `dashboard/activity/`, `lib/activity.ts` |
| Replay | R `replay.py`, `checkpoints.py` · S `replay_service`, `execution_checkpoint_service` · M `replay_snapshot`, `execution_checkpoint` · UI `dashboard/replay/` |
| Local CLI (FM-091 → FM-100) | [`apps/local/forgemind_local/`](../../apps/local/forgemind_local/) — `cli.py`, `repo_index.py`, `local_chat.py`, `local_exec.py`, `local_patch.py`, `local_pr.py`, `local_handoff.py`, `local_state.py`, `ide_integration.py`, `config.py` |

## V4 Wave 10 — Collaboration hardening (FM-141 → FM-150)

| Item | Code |
| :-- | :-- |
| Threaded comments & mentions polish | `comment_service`, `mention_service`, `components/chat/` |
| Notifications v2 + inbox | R `notifications.py` · S `notification_service`, `notification_delivery_service`, `notification_digest_service` · M `notification` · UI `dashboard/notifications/`, `lib/notifications.ts` |
| Escalation | R `escalation.py` · S `escalation_service` · M `escalation` · UI `dashboard/escalations/` (scheduler loop in `background_scheduler.py`) |
| Workspace RBAC polish | S `authz_service`, `membership_service` · `core/authz_deps.py` |

## V4 Wave 11 — GitHub integration (FM-151 → FM-160)

| Item | Code |
| :-- | :-- |
| App install + repo sync | R `github_integration.py`, `repos.py` · S `github_installation_service`, `github_client`, `github_rate_limiter`, `repo_service` · M `github_integration`, `repo_connection` · UI `dashboard/connectors/` |
| Webhook ingestion | S `webhook_service` (`process_pr_event`, `process_workflow_run_event`, `process_issues_event`, `process_push_event`, `process_release_event`, `process_check_run_event`) |
| PR / review / merge | S `pr_service`, `code_review_service`, `merge_readiness_service`, `diff_intelligence_service` · UI `dashboard/reviews/`, `dashboard/code-explorer/` |
| CI pipeline view | S `ci_pipeline_service` · UI `dashboard/runs/`, `dashboard/releases/` |

## V4 Wave 12 — Cross-project search & memory (FM-161 → FM-170)

Alembic head reflects this wave: `fm161_170_search_knowledge`.

| Item | Code |
| :-- | :-- |
| Knowledge & memory | R `knowledge.py`, `memory.py`, `search_knowledge.py` · S `knowledge_service`, `search_service`, `embedding_service`, `run_memory_service`, `run_memory_enrichment_service` · M `project_knowledge`, `search_knowledge` · UI `dashboard/knowledge/`, `lib/knowledge.ts` |

## V4 Wave 13 — Enterprise governance (FM-171 → FM-180)

| Item | Code |
| :-- | :-- |
| SSO | S `sso_configuration_service` · M `sso_configuration` |
| IP allowlist | `core/ip_allowlist_middleware.py` + S `ip_allowlist_service` |
| Compliance reports | S `compliance_report_service` · R `enterprise_governance.py` |
| Retention policies | S `retention_policy_service` (driven by `background_scheduler`) · M `enterprise_governance` |
| Audit export | R `audit.py` · S `audit_log_service`, `audit_export_service` · UI `dashboard/audit/` |

## V4 Wave 14 — Code intelligence (FM-181 → FM-190)

See [`../code-intelligence.md`](../code-intelligence.md).

| Item | Code |
| :-- | :-- |
| Code graph | S `code_graph_service` · M `code_intelligence` · R `code_intelligence.py`, `architecture.py` |
| Pattern / debt | S `pattern_debt_service` |
| Flakiness / complexity | S `flakiness_complexity_service` |
| Refactor recommendations | S `refactor_recommendation_service` |
| Convention detection | S `convention_service` |
| Architecture topology / drift / rules / impact | S `topology_mapper_service`, `drift_detection_service`, `architecture_rule_service`, `impact_analysis_service` · R `architecture.py` · UI `dashboard/architecture/`, `dashboard/code-explorer/` |

## V4 Wave 15 — Analytics & portfolio (FM-191 → FM-200)

See [`../analytics-portfolio.md`](../analytics-portfolio.md).

| Item | Code |
| :-- | :-- |
| Composite health scores | S `execution_health_service`, `structural_health_service` · M `analytics_metrics` |
| Velocity & quality | S `velocity_quality_service` |
| Portfolio / project overview | S `project_overview_service` · R `analytics.py` |
| Budgets + alerts | S `cost_tracking_service`, `dashboard_alert_service` |
| Scheduled reports | S `background_scheduler` (`scheduled_report_loop`) + `notification_delivery_service` |
| Dashboard widgets / charts | UI `components/dashboard/` (`dashboard-grid.tsx`, `widget-renderer.tsx`, `widget-data-adapter.ts`, `charts/`) · `lib/dashboards.ts` |
| Release ops | R `delivery.py`, `release_ops.py` · S `release_gate_service`, `release_confidence_service`, `release_package_service`, `post_release_service`, `operational_timeline_service`, `rollback_readiness_service`, `deployment_readiness_service` · M `release_ops` · UI `dashboard/releases/` |

## V4 Wave 16 — Public API, SDKs, connectors (FM-201 → FM-210)

See [`../api-ecosystem.md`](../api-ecosystem.md).

| Item | Code |
| :-- | :-- |
| Versioning / OpenAPI | `apps/api/app/main.py` include_router · `/docs`, `/redoc`, `/openapi.json` |
| API keys + scopes | R `api_ecosystem.py` · S `api_key_service` · M `api_ecosystem` · `core/authz_deps.py` |
| Rate limiting | `core/rate_limit.py` |
| SDKs | `apps/api/app/sdk/python_client.py`, `typescript_client.ts`, `openapi-generator-config.yaml`, `pyproject.toml`, `package.json` |
| Webhooks | R `connectors.py` · S `webhook_connector_service`, `connector_service` · M `connector`, `project_connector_link` |
| Connector types (Slack / email / PagerDuty / generic) | S `webhook_connector_service` (dispatch branches) · `email_service` · `notification_delivery_service` |
| Credential vault | R `credential_vault.py` · S `credential_vault_service`, `encryption_service` · M `credential_vault` · UI `dashboard/vault/` |

---

## Cross-cutting concerns (not wave-specific)

| Concern | Where |
| :-- | :-- |
| Auth | `core/auth.py`, `core/authz_deps.py`, `routes/auth.py` |
| Middleware stack | `main.py` (order matters) + all of `core/` |
| Background scheduler | `services/background_scheduler.py` |
| SSE streaming | `services/stream_service.py` + `routes/streaming.py` + `lib/stream.ts` |
| LLM + cost | `core/llm.py` → `services/cost_tracking_service.py` |
| Audit | `services/audit_log_service.py`, `services/audit_export_service.py`, `routes/audit.py` |
| Retry / adaptive orchestration | `services/adaptive_orchestrator.py`, `services/adaptive_retry_service.py`, `routes/retry.py`, `routes/composition.py` |
