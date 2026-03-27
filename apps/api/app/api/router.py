from fastapi import APIRouter

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
