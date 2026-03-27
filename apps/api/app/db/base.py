"""Aggregator module — import Base + all models so Alembic metadata is complete.

- base_class.py: defines Base (no model imports, no circular risk)
- base.py (this file): re-exports Base AND imports every model

Alembic env.py and anything that needs "all tables registered" should import from here.
Models themselves import Base from base_class to avoid circular dependencies.
"""

from app.db.base_class import Base  # noqa: F401

# Import all models so their tables are registered on Base.metadata.
from app.models.user import User  # noqa: F401
from app.models.project import Project  # noqa: F401
from app.models.run import Run  # noqa: F401
from app.models.artifact import Artifact  # noqa: F401
from app.models.task import Task  # noqa: F401
from app.models.planner_result import PlannerResult  # noqa: F401
from app.models.agent import Agent  # noqa: F401
from app.models.approval_request import ApprovalRequest  # noqa: F401
from app.models.execution_event import ExecutionEvent  # noqa: F401
from app.models.connector import Connector  # noqa: F401
from app.models.project_connector_link import ProjectConnectorLink  # noqa: F401
from app.models.credential_vault import CredentialVault  # noqa: F401
from app.models.cost_record import CostRecord  # noqa: F401
from app.models.governance_policy import GovernancePolicy  # noqa: F401
from app.models.trust_score import TrustScore  # noqa: F401
from app.models.replay_snapshot import ReplaySnapshot  # noqa: F401
from app.models.council import CouncilSession, CouncilVote  # noqa: F401
from app.models.project_knowledge import ProjectKnowledge  # noqa: F401
from app.models.repo_connection import RepoConnection  # noqa: F401
