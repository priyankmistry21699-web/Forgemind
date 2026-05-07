from fastapi import APIRouter, Depends

from app.api.routes.health import router as health_router
from app.api.routes.projects import router as projects_router
from app.api.routes.planner import router as planner_router
from app.api.routes.planner_results import router as planner_results_router
from app.api.routes.tasks import router as tasks_router
from app.api.routes.runs import router as runs_router
from app.api.routes.artifacts import router as artifacts_router
from app.api.routes.agents import router as agents_router
from app.api.routes.approvals import router as approvals_router
from app.api.routes.events import router as events_router
from app.api.routes.chat import router as chat_router
from app.api.routes.composition import router as composition_router
from app.api.routes.connectors import router as connectors_router
from app.api.routes.memory import router as memory_router
from app.api.routes.credential_vault import router as vault_router
from app.api.routes.retry import router as retry_router
from app.api.routes.run_lifecycle import router as lifecycle_router
from app.api.routes.costs import router as costs_router
from app.api.routes.governance import router as governance_router
from app.api.routes.audit import router as audit_router
from app.api.routes.trust import router as trust_router
from app.api.routes.replay import router as replay_router
from app.api.routes.council import router as council_router
from app.api.routes.knowledge import router as knowledge_router
from app.api.routes.repos import router as repos_router
from app.api.routes.workspaces import router as workspaces_router
from app.api.routes.members import router as members_router
from app.api.routes.streaming import router as streaming_router
from app.api.routes.notifications import router as notifications_router
from app.api.routes.escalation import router as escalation_router
from app.api.routes.activity import router as activity_router
from app.api.routes.code_ops import router as code_ops_router
from app.api.routes.auth import router as auth_router
from app.api.routes.metrics import router as metrics_router
from app.api.routes.architecture import router as architecture_router
from app.api.routes.constitution import router as constitution_router
from app.api.routes.phase_agent_profiles import router as phase_profiles_router
from app.api.routes.project_templates import router as templates_router
from app.api.routes.constitution_suggestions import router as suggestions_router
from app.api.routes.checkpoints import router as checkpoints_router
from app.api.routes.delivery import router as delivery_router
from app.api.routes.release_ops import router as release_ops_router
from app.api.routes.comments import router as comments_router
from app.api.routes.saved_views import router as saved_views_router
from app.api.routes.annotations import router as annotations_router
from app.api.routes.github_integration import router as github_router
from app.api.routes.search_knowledge import router as search_knowledge_router
from app.api.routes.enterprise_governance import router as enterprise_governance_router
from app.api.routes.collaboration import router as collaboration_router
from app.api.routes.code_intelligence import router as code_intelligence_router
from app.api.routes.analytics import router as analytics_router
from app.api.routes.api_ecosystem import router as api_ecosystem_router
from app.api.routes.admin import router as admin_router
from app.api.routes.agent_intelligence import router as agent_intelligence_router
from app.api.routes.scheduling import router as scheduling_router
from app.api.routes.platform_intelligence import router as platform_intelligence_router
from app.api.routes.platform_ops import router as platform_ops_router
from app.services import api_key_service

api_router = APIRouter()

# Health check — mounted at root level (no prefix)
api_router.include_router(health_router, tags=["health"])

# Project CRUD
api_router.include_router(projects_router, tags=["projects"])

# Prompt intake + planner
api_router.include_router(planner_router, tags=["planner"])

# Planner results
api_router.include_router(planner_results_router, tags=["planner"])

# Task DAG + orchestration
api_router.include_router(tasks_router, tags=["tasks"])

# Run listing
api_router.include_router(runs_router, tags=["runs"])

# Artifacts
api_router.include_router(artifacts_router, tags=["artifacts"])

# Agent registry
api_router.include_router(agents_router, tags=["agents"])

# Approval requests
api_router.include_router(approvals_router, tags=["approvals"])

# Execution events
api_router.include_router(events_router, tags=["events"])

# Execution chatbot
api_router.include_router(chat_router, tags=["chat"])

# Team composition
api_router.include_router(composition_router, tags=["composition"])

# Connectors
api_router.include_router(connectors_router, tags=["connectors"])

# Execution memory
api_router.include_router(memory_router, tags=["memory"])

# Credential vault
api_router.include_router(vault_router, tags=["vault"])

# Adaptive retry
api_router.include_router(retry_router, tags=["retry"])

# Run lifecycle & health (FM-046)
api_router.include_router(lifecycle_router, tags=["lifecycle"])

# Cost tracking (FM-047)
api_router.include_router(costs_router, tags=["costs"])

# Governance policies (FM-048)
api_router.include_router(governance_router, tags=["governance"])

# Audit trail export (FM-049)
api_router.include_router(audit_router, tags=["audit"])

# Trust scoring & risk (FM-050)
api_router.include_router(trust_router, tags=["trust"])

# Replay & trace inspection (FM-046)
api_router.include_router(replay_router, tags=["replay"])

# Council decision engine (FM-047A)
api_router.include_router(council_router, tags=["council"])

# Knowledge base (FM-048)
api_router.include_router(knowledge_router, tags=["knowledge"])

# Repo connections (FM-049)
api_router.include_router(repos_router, tags=["repos"])

# Workspaces (FM-051)
api_router.include_router(workspaces_router, tags=["workspaces"])

# Members (FM-052/053)
api_router.include_router(members_router, tags=["members"])

# SSE streaming (FM-054)
api_router.include_router(streaming_router, tags=["streaming"])

# Notifications (FM-055/056)
api_router.include_router(notifications_router, tags=["notifications"])

# Escalation (FM-057)
api_router.include_router(escalation_router, tags=["escalation"])

# Activity & Presence (FM-058/059)
api_router.include_router(activity_router, tags=["activity"])

# Code operations (FM-061–069)
api_router.include_router(code_ops_router, tags=["code-ops"])

# Authentication (FM-074)
api_router.include_router(auth_router, tags=["auth"])

# Metrics (FM-078)
api_router.include_router(metrics_router, tags=["metrics"])

# Architecture Intelligence (FM-081-090)
api_router.include_router(architecture_router, tags=["architecture"])

# Project Constitution (FM-102)
api_router.include_router(constitution_router, tags=["constitution"])

# Phase Agent Profiles (FM-111/113)
api_router.include_router(phase_profiles_router, tags=["phase-profiles"])

# Project Templates (FM-114/115)
api_router.include_router(templates_router, tags=["templates"])

# Constitution Suggestions (FM-117)
api_router.include_router(suggestions_router, tags=["suggestions"])

# Execution Checkpoints (FM-121)
api_router.include_router(checkpoints_router, tags=["checkpoints"])

# Delivery, Review, Traceability, Memory, Confidence (FM-124–128)
api_router.include_router(delivery_router, tags=["delivery"])

# Release Operations (FM-131–137)
api_router.include_router(release_ops_router, tags=["release-ops"])

# Threaded Comments (FM-141)
api_router.include_router(comments_router, tags=["comments"])
api_router.include_router(saved_views_router, tags=["saved-views"])
api_router.include_router(annotations_router, tags=["annotations"])
api_router.include_router(github_router, tags=["github"])

# Search, Knowledge & Organizational Memory (FM-161–170)
api_router.include_router(
    search_knowledge_router,
    tags=["search", "knowledge", "conventions", "recommendations"],
)

# Enterprise Governance, Permissions & Compliance (FM-171–180)
api_router.include_router(
    enterprise_governance_router, tags=["enterprise-governance", "audit", "compliance"]
)

# Task Assignment, Approval Delegation, Project Overview (FM-147/148/150)
api_router.include_router(
    collaboration_router, tags=["collaboration", "assignments", "delegations"]
)

# Code Intelligence: Dependency Graph, Impact, Coverage, Patterns, Debt, Flakiness, Complexity (FM-181–189)
api_router.include_router(
    code_intelligence_router,
    tags=["code-intelligence", "dependencies", "patterns", "debt", "complexity"],
)

# Analytics & Metrics: Execution, Health, Budget, Velocity, Quality, Portfolio, Dashboards, Alerts (FM-191–199)
api_router.include_router(
    analytics_router, tags=["analytics", "metrics", "health", "dashboards", "alerts"]
)

# ── FM-201 / FM-202: Versioned Public API with rate limiting ─────
# Mount ALL core endpoint groups under /api/v1/ with rate-limit headers.
_v1_rate_limit = Depends(api_key_service.require_rate_limit())

api_router.include_router(
    projects_router,
    prefix="/api/v1",
    tags=["api-v1", "projects"],
    dependencies=[_v1_rate_limit],
)
api_router.include_router(
    runs_router,
    prefix="/api/v1",
    tags=["api-v1", "runs"],
    dependencies=[_v1_rate_limit],
)
api_router.include_router(
    tasks_router,
    prefix="/api/v1",
    tags=["api-v1", "tasks"],
    dependencies=[_v1_rate_limit],
)
api_router.include_router(
    costs_router,
    prefix="/api/v1",
    tags=["api-v1", "costs"],
    dependencies=[_v1_rate_limit],
)
api_router.include_router(
    code_intelligence_router,
    prefix="/api/v1",
    tags=["api-v1", "code-intelligence"],
    dependencies=[_v1_rate_limit],
)
api_router.include_router(
    analytics_router,
    prefix="/api/v1",
    tags=["api-v1", "analytics"],
    dependencies=[_v1_rate_limit],
)
api_router.include_router(
    approvals_router,
    prefix="/api/v1",
    tags=["api-v1", "approvals"],
    dependencies=[_v1_rate_limit],
)
api_router.include_router(
    governance_router,
    prefix="/api/v1",
    tags=["api-v1", "governance"],
    dependencies=[_v1_rate_limit],
)

# API & Ecosystem: API Keys, Rate Limiting, Webhooks, Connectors (FM-201–208)
# (already has /api/v1/ecosystem prefix + rate limiting in its own router)
api_router.include_router(
    api_ecosystem_router, tags=["api-keys", "webhooks", "connectors", "ecosystem"]
)

# Admin operations (FM-215/216/217/221)
api_router.include_router(admin_router, tags=["admin"])

# Agent intelligence: memory, cost, stream, docs, security (FM-222–230)
api_router.include_router(agent_intelligence_router, tags=["agent-intelligence"])

# Scheduling & event-driven triggers (FM-231/232)
api_router.include_router(scheduling_router, tags=["scheduling"])

# Platform intelligence: perf, prompts, experiments, SLOs, anomalies (FM-233–240)
api_router.include_router(platform_intelligence_router, tags=["platform-intelligence"])

# Platform ops: quotas, audit export, PII, admin stats (FM-241–248)
api_router.include_router(platform_ops_router, tags=["platform-ops"])
