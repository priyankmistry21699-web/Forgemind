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
from app.models.project_constitution import ProjectConstitution  # noqa: F401
from app.models.repo_connection import RepoConnection  # noqa: F401
from app.models.workspace import Workspace  # noqa: F401
from app.models.membership import WorkspaceMember, ProjectMember  # noqa: F401
from app.models.notification import Notification, NotificationDeliveryConfig  # noqa: F401
from app.models.escalation import EscalationRule, EscalationEvent  # noqa: F401
from app.models.activity import ActivityFeedEntry, UserPresence  # noqa: F401
from app.models.code_ops import (  # noqa: F401
    CodeMapping,
    PatchProposal,
    ChangeReview,
    BranchStrategy,
    PRDraft,
    RepoActionApproval,
    SandboxExecution,
)
from app.models.architecture import (  # noqa: F401
    ArchitectureNode,
    ArchitectureEdge,
    ArchitectureSnapshot,
    ArchitectureDrift,
    ArchitectureRule,
    ArchitectureRuleResult,
    ChangeImpactAssessment,
)

# FM-111–120: Phase routing, templates, constitution suggestions
from app.models.phase_agent_profile import PhaseAgentProfile  # noqa: F401
from app.models.project_template import ProjectTemplate  # noqa: F401
from app.models.constitution_suggestion import ConstitutionSuggestion  # noqa: F401

# FM-121–130: Execution checkpoints, delivery, traceability
from app.models.execution_checkpoint import ExecutionCheckpoint  # noqa: F401

# FM-131–140: Release operations
from app.models.release_ops import (  # noqa: F401
    ReleasePackage,
    DeploymentEnvironment,
    ReleaseGateResult,
)

# FM-141–150: Collaboration, UX & Team Coordination
from app.models.comment import Comment  # noqa: F401
from app.models.saved_view import SavedView  # noqa: F401
from app.models.run_annotation import RunAnnotation  # noqa: F401
from app.models.approval_delegation import ApprovalDelegation  # noqa: F401

# FM-151–160: GitHub & CI Integration
from app.models.github_integration import (  # noqa: F401
    GitHubInstallation,
    RepositoryLink,
    ExternalEvent,
    PullRequestLink,
    CIPipelineRun,
    IssueLink,
    CodeOwnership,
)

# FM-161–170: Search, Knowledge & Organizational Memory
from app.models.search_knowledge import (  # noqa: F401
    SearchIndex,
    Convention,
    Recommendation,
)

# FM-171–180: Enterprise Governance, Permissions & Compliance
from app.models.enterprise_governance import (  # noqa: F401
    AuditLog,
    GovernancePolicyEvaluation,
    ComplianceReport,
    IpAllowlistEntry,
    RetentionPolicy,
)
from app.models.sso_configuration import SSOConfiguration  # noqa: F401
