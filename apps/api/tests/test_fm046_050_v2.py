"""Tests for FM-046 through FM-050 NEW features.

FM-046: Run Replay and Execution Trace Inspection
FM-047A: Multi-Agent Council Decision Engine
FM-047: Policy-Based Approval Rules (enhanced)
FM-048: Multi-Run Memory and Project Knowledge Base
FM-049: External Repo / Workspace Execution Integration
FM-050: Production Readiness and Platform Hardening
"""

import uuid
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.run import Run, RunStatus
from app.models.task import Task, TaskStatus
from app.models.project import Project


# ══════════════════════════════════════════════════════════════════
# FM-046: Run Replay and Execution Trace Inspection
# ══════════════════════════════════════════════════════════════════


class TestReplaySnapshot:
    """Test replay snapshot capture and trace inspection."""

    @pytest.mark.asyncio
    async def test_capture_snapshot(self, db_session: AsyncSession, sample_project, sample_run, sample_task):
        from app.services import replay_service

        snapshot = await replay_service.capture_snapshot(
            db_session,
            task_id=sample_task.id,
            run_id=sample_run.id,
            project_id=sample_project.id,
            agent_slug="coder",
            input_snapshot={"prompt": "Write a function"},
            prompt_snapshot="You are a coder...",
            model_used="gpt-4o",
            temperature=0.3,
            output_snapshot={"code": "def hello(): pass"},
            tokens_used=100,
            duration_ms=500,
            cost_usd=0.01,
        )
        assert snapshot.id is not None
        assert snapshot.agent_slug == "coder"
        assert snapshot.replay_hash is not None
        assert snapshot.sequence_number == 0
        assert snapshot.is_replay is False

    @pytest.mark.asyncio
    async def test_execution_trace(self, db_session: AsyncSession, sample_project, sample_run, sample_task):
        from app.services import replay_service

        # Create 3 snapshots
        for i in range(3):
            await replay_service.capture_snapshot(
                db_session,
                task_id=sample_task.id,
                run_id=sample_run.id,
                project_id=sample_project.id,
                agent_slug="coder",
                input_snapshot={"step": i},
                output_snapshot={"result": f"step_{i}"},
                tokens_used=50,
                duration_ms=200,
                cost_usd=0.005,
            )

        trace = await replay_service.get_execution_trace(db_session, sample_run.id)
        assert trace["total_steps"] == 3
        assert trace["total_tokens"] == 150
        assert len(trace["snapshots"]) == 3

    @pytest.mark.asyncio
    async def test_replay_snapshot(self, db_session: AsyncSession, sample_project, sample_run, sample_task):
        from app.services import replay_service

        original = await replay_service.capture_snapshot(
            db_session,
            task_id=sample_task.id,
            run_id=sample_run.id,
            project_id=sample_project.id,
            agent_slug="coder",
            input_snapshot={"prompt": "test"},
            output_snapshot={"result": "ok"},
        )

        result = await replay_service.replay_snapshot(db_session, original.id)
        assert "error" not in result
        assert result["output_match"] is True
        assert result["original_id"] == str(original.id)

    @pytest.mark.asyncio
    async def test_compare_snapshots(self, db_session: AsyncSession, sample_project, sample_run, sample_task):
        from app.services import replay_service

        s1 = await replay_service.capture_snapshot(
            db_session,
            task_id=sample_task.id,
            run_id=sample_run.id,
            project_id=sample_project.id,
            agent_slug="coder",
            output_snapshot={"result": "hello"},
        )
        s2 = await replay_service.capture_snapshot(
            db_session,
            task_id=sample_task.id,
            run_id=sample_run.id,
            project_id=sample_project.id,
            agent_slug="coder",
            output_snapshot={"result": "world"},
        )

        result = await replay_service.compare_snapshots(db_session, s1.id, s2.id)
        assert result["output_match"] is False
        assert result["diff_summary"] is not None

    @pytest.mark.asyncio
    async def test_replay_hash_deterministic(self, db_session: AsyncSession, sample_project, sample_run, sample_task):
        from app.services import replay_service

        s1 = await replay_service.capture_snapshot(
            db_session,
            task_id=sample_task.id,
            run_id=sample_run.id,
            project_id=sample_project.id,
            agent_slug="coder",
            input_snapshot={"x": 1},
            prompt_snapshot="test",
            model_used="gpt-4o",
            temperature=0.3,
        )
        s2 = await replay_service.capture_snapshot(
            db_session,
            task_id=sample_task.id,
            run_id=sample_run.id,
            project_id=sample_project.id,
            agent_slug="coder",
            input_snapshot={"x": 1},
            prompt_snapshot="test",
            model_used="gpt-4o",
            temperature=0.3,
        )
        assert s1.replay_hash == s2.replay_hash

    @pytest.mark.asyncio
    async def test_list_snapshots_filters(self, db_session: AsyncSession, sample_project, sample_run, sample_task):
        from app.services import replay_service

        await replay_service.capture_snapshot(
            db_session,
            task_id=sample_task.id,
            run_id=sample_run.id,
            project_id=sample_project.id,
            agent_slug="coder",
        )

        snapshots, total = await replay_service.list_snapshots(
            db_session, run_id=sample_run.id
        )
        assert total >= 1


# ══════════════════════════════════════════════════════════════════
# FM-047A: Multi-Agent Council Decision Engine
# ══════════════════════════════════════════════════════════════════


class TestCouncilDecision:
    """Test council session management and decision resolution."""

    @pytest.mark.asyncio
    async def test_convene_council(self, db_session: AsyncSession, sample_project):
        from app.services import council_service
        from app.models.council import DecisionMethod

        session = await council_service.convene_council(
            db_session,
            project_id=sample_project.id,
            topic="Should we use microservices?",
            description="Architecture decision for the project",
            decision_method=DecisionMethod.MAJORITY,
        )
        assert session.id is not None
        assert session.status.value == "convened"
        assert session.topic == "Should we use microservices?"

    @pytest.mark.asyncio
    async def test_cast_vote(self, db_session: AsyncSession, sample_project):
        from app.services import council_service
        from app.models.council import DecisionMethod, VoteDecision

        session = await council_service.convene_council(
            db_session,
            project_id=sample_project.id,
            topic="Test decision",
            decision_method=DecisionMethod.MAJORITY,
        )

        vote = await council_service.cast_vote(
            db_session,
            session.id,
            agent_slug="architect",
            decision=VoteDecision.APPROVE,
            reasoning="Looks good",
            confidence=0.9,
        )
        assert vote.agent_slug == "architect"
        assert vote.decision == VoteDecision.APPROVE

    @pytest.mark.asyncio
    async def test_majority_decision(self, db_session: AsyncSession, sample_project):
        from app.services import council_service
        from app.models.council import DecisionMethod, VoteDecision

        session = await council_service.convene_council(
            db_session,
            project_id=sample_project.id,
            topic="Majority test",
            decision_method=DecisionMethod.MAJORITY,
        )

        # 2 approve, 1 reject = majority approve
        await council_service.cast_vote(db_session, session.id, agent_slug="architect", decision=VoteDecision.APPROVE, confidence=0.8)
        await council_service.cast_vote(db_session, session.id, agent_slug="coder", decision=VoteDecision.APPROVE, confidence=0.7)
        await council_service.cast_vote(db_session, session.id, agent_slug="reviewer", decision=VoteDecision.REJECT, confidence=0.6)

        db_session.expunge_all()
        result = await council_service.resolve_council(db_session, session.id)
        assert result["final_decision"] == "approve"
        assert result["status"] == "decided"

    @pytest.mark.asyncio
    async def test_consensus_decision_fails_split(self, db_session: AsyncSession, sample_project):
        from app.services import council_service
        from app.models.council import DecisionMethod, VoteDecision

        session = await council_service.convene_council(
            db_session,
            project_id=sample_project.id,
            topic="Consensus test",
            decision_method=DecisionMethod.CONSENSUS,
        )

        await council_service.cast_vote(db_session, session.id, agent_slug="architect", decision=VoteDecision.APPROVE)
        await council_service.cast_vote(db_session, session.id, agent_slug="reviewer", decision=VoteDecision.REJECT)

        result = await council_service.resolve_council(db_session, session.id)
        assert result["final_decision"] is None
        assert result["status"] == "deadlocked"

    @pytest.mark.asyncio
    async def test_consensus_decision_unanimous(self, db_session: AsyncSession, sample_project):
        from app.services import council_service
        from app.models.council import DecisionMethod, VoteDecision

        session = await council_service.convene_council(
            db_session,
            project_id=sample_project.id,
            topic="Unanimous test",
            decision_method=DecisionMethod.CONSENSUS,
        )

        await council_service.cast_vote(db_session, session.id, agent_slug="architect", decision=VoteDecision.APPROVE)
        await council_service.cast_vote(db_session, session.id, agent_slug="coder", decision=VoteDecision.APPROVE)

        db_session.expunge_all()
        result = await council_service.resolve_council(db_session, session.id)
        assert result["final_decision"] == "approve"
        assert result["status"] == "decided"

    @pytest.mark.asyncio
    async def test_escalate_deadlocked(self, db_session: AsyncSession, sample_project):
        from app.services import council_service
        from app.models.council import DecisionMethod, VoteDecision

        session = await council_service.convene_council(
            db_session,
            project_id=sample_project.id,
            topic="Escalation test",
            decision_method=DecisionMethod.CONSENSUS,
        )

        await council_service.cast_vote(db_session, session.id, agent_slug="architect", decision=VoteDecision.APPROVE)
        await council_service.cast_vote(db_session, session.id, agent_slug="reviewer", decision=VoteDecision.REJECT)

        # Resolve → deadlocked
        await council_service.resolve_council(db_session, session.id)

        # Escalate
        result = await council_service.escalate_council(db_session, session.id)
        assert result["status"] == "escalated"

    @pytest.mark.asyncio
    async def test_weighted_decision(self, db_session: AsyncSession, sample_project):
        from app.services import council_service
        from app.models.council import DecisionMethod, VoteDecision

        session = await council_service.convene_council(
            db_session,
            project_id=sample_project.id,
            topic="Weighted test",
            decision_method=DecisionMethod.WEIGHTED,
        )

        # Architect with high weight/confidence approves
        await council_service.cast_vote(db_session, session.id, agent_slug="architect", decision=VoteDecision.APPROVE, confidence=0.95, weight=2.0)
        # Reviewer with low weight rejects
        await council_service.cast_vote(db_session, session.id, agent_slug="reviewer", decision=VoteDecision.REJECT, confidence=0.5, weight=1.0)

        db_session.expunge_all()
        result = await council_service.resolve_council(db_session, session.id)
        assert result["final_decision"] == "approve"


# ══════════════════════════════════════════════════════════════════
# FM-047: Policy-Based Approval Rules (Enhanced)
# ══════════════════════════════════════════════════════════════════


class TestEnhancedPolicyApproval:
    """Test enhanced policy evaluation with multiple triggers."""

    @pytest.mark.asyncio
    async def test_cost_threshold_policy(self, db_session: AsyncSession, sample_project):
        from app.services import governance_service
        from app.models.governance_policy import PolicyTrigger, PolicyAction

        await governance_service.create_policy(
            db_session,
            name="High cost approval",
            trigger=PolicyTrigger.COST_THRESHOLD,
            action=PolicyAction.REQUIRE_APPROVAL,
            rules={"threshold_usd": 1.0},
            project_id=sample_project.id,
        )

        action = await governance_service.evaluate_task_approval(
            db_session,
            task_type="codegen",
            project_id=sample_project.id,
            cost_usd=2.0,
        )
        assert action == PolicyAction.REQUIRE_APPROVAL

    @pytest.mark.asyncio
    async def test_cost_threshold_below(self, db_session: AsyncSession, sample_project):
        from app.services import governance_service
        from app.models.governance_policy import PolicyTrigger, PolicyAction

        await governance_service.create_policy(
            db_session,
            name="High cost",
            trigger=PolicyTrigger.COST_THRESHOLD,
            action=PolicyAction.REQUIRE_APPROVAL,
            rules={"threshold_usd": 5.0},
            project_id=sample_project.id,
        )

        action = await governance_service.evaluate_task_approval(
            db_session,
            task_type="codegen",
            project_id=sample_project.id,
            cost_usd=1.0,
        )
        assert action == PolicyAction.AUTO_APPROVE

    @pytest.mark.asyncio
    async def test_agent_action_policy(self, db_session: AsyncSession, sample_project):
        from app.services import governance_service
        from app.models.governance_policy import PolicyTrigger, PolicyAction

        await governance_service.create_policy(
            db_session,
            name="Block coder",
            trigger=PolicyTrigger.AGENT_ACTION,
            action=PolicyAction.BLOCK,
            rules={"agent_slugs": ["coder"]},
            project_id=sample_project.id,
        )

        action = await governance_service.evaluate_task_approval(
            db_session,
            task_type="codegen",
            project_id=sample_project.id,
            agent_slug="coder",
        )
        assert action == PolicyAction.BLOCK

    @pytest.mark.asyncio
    async def test_custom_rule_and_logic(self, db_session: AsyncSession, sample_project):
        from app.services import governance_service
        from app.models.governance_policy import PolicyTrigger, PolicyAction

        await governance_service.create_policy(
            db_session,
            name="Custom combo",
            trigger=PolicyTrigger.CUSTOM,
            action=PolicyAction.REQUIRE_APPROVAL,
            rules={
                "conditions": [
                    {"field": "task_type", "op": "in", "value": ["architecture"]},
                    {"field": "cost_usd", "op": "gt", "value": 0.5},
                ],
                "logic": "and",
            },
            project_id=sample_project.id,
        )

        # Both conditions met
        action = await governance_service.evaluate_task_approval(
            db_session,
            task_type="architecture",
            project_id=sample_project.id,
            cost_usd=1.0,
        )
        assert action == PolicyAction.REQUIRE_APPROVAL

        # One condition fails
        action2 = await governance_service.evaluate_task_approval(
            db_session,
            task_type="codegen",
            project_id=sample_project.id,
            cost_usd=1.0,
        )
        assert action2 == PolicyAction.AUTO_APPROVE

    @pytest.mark.asyncio
    async def test_evaluate_with_council(self, db_session: AsyncSession, sample_project):
        from app.services import governance_service
        from app.models.governance_policy import PolicyTrigger, PolicyAction

        await governance_service.create_policy(
            db_session,
            name="Architecture review",
            trigger=PolicyTrigger.TASK_TYPE,
            action=PolicyAction.REQUIRE_APPROVAL,
            rules={"task_types": ["architecture"]},
            project_id=sample_project.id,
        )

        result = await governance_service.evaluate_approval_with_council(
            db_session,
            task_type="architecture",
            project_id=sample_project.id,
            cost_usd=1.0,
        )
        assert result["action"] == "require_approval"
        assert result["needs_council"] is True


# ══════════════════════════════════════════════════════════════════
# FM-048: Multi-Run Memory and Project Knowledge Base
# ══════════════════════════════════════════════════════════════════


class TestProjectKnowledge:
    """Test project knowledge base operations."""

    @pytest.mark.asyncio
    async def test_create_knowledge(self, db_session: AsyncSession, sample_project):
        from app.services import knowledge_service
        from app.models.project_knowledge import KnowledgeType

        entry = await knowledge_service.create_knowledge(
            db_session,
            project_id=sample_project.id,
            knowledge_type=KnowledgeType.PATTERN,
            title="Use dependency injection",
            content="DI pattern works well for testability",
            tags=["pattern", "architecture"],
        )
        assert entry.id is not None
        assert entry.knowledge_type == KnowledgeType.PATTERN
        assert entry.relevance_score == 1.0

    @pytest.mark.asyncio
    async def test_list_knowledge(self, db_session: AsyncSession, sample_project):
        from app.services import knowledge_service
        from app.models.project_knowledge import KnowledgeType

        await knowledge_service.create_knowledge(
            db_session,
            project_id=sample_project.id,
            knowledge_type=KnowledgeType.PATTERN,
            title="Pattern 1",
            content="Content 1",
        )
        await knowledge_service.create_knowledge(
            db_session,
            project_id=sample_project.id,
            knowledge_type=KnowledgeType.LESSON_LEARNED,
            title="Lesson 1",
            content="Content 2",
        )

        entries, total = await knowledge_service.list_knowledge(
            db_session, sample_project.id
        )
        assert total == 2

        # Filter by type
        filtered, ftotal = await knowledge_service.list_knowledge(
            db_session, sample_project.id,
            knowledge_type=KnowledgeType.PATTERN,
        )
        assert ftotal == 1

    @pytest.mark.asyncio
    async def test_extract_knowledge_from_run(self, db_session: AsyncSession, sample_project, sample_run, sample_task):
        from app.services import knowledge_service

        # Complete the task first
        sample_task.status = TaskStatus.COMPLETED
        sample_task.assigned_agent_slug = "architect"
        await db_session.flush()

        entries = await knowledge_service.extract_knowledge_from_run(
            db_session, sample_run.id
        )
        assert len(entries) >= 1

    @pytest.mark.asyncio
    async def test_knowledge_context(self, db_session: AsyncSession, sample_project):
        from app.services import knowledge_service
        from app.models.project_knowledge import KnowledgeType

        await knowledge_service.create_knowledge(
            db_session,
            project_id=sample_project.id,
            knowledge_type=KnowledgeType.ARCHITECTURE,
            title="Use microservices",
            content="Split into 3 services",
        )

        ctx = await knowledge_service.get_knowledge_context(
            db_session, sample_project.id
        )
        assert ctx["total_entries"] == 1
        assert "microservices" in ctx["context_text"]

    @pytest.mark.asyncio
    async def test_delete_knowledge(self, db_session: AsyncSession, sample_project):
        from app.services import knowledge_service
        from app.models.project_knowledge import KnowledgeType

        entry = await knowledge_service.create_knowledge(
            db_session,
            project_id=sample_project.id,
            knowledge_type=KnowledgeType.CONSTRAINT,
            title="Max 100 entities",
            content="DB constraint",
        )

        deleted = await knowledge_service.delete_knowledge(db_session, entry.id)
        assert deleted is True

        deleted2 = await knowledge_service.delete_knowledge(db_session, uuid.uuid4())
        assert deleted2 is False


# ══════════════════════════════════════════════════════════════════
# FM-049: External Repo / Workspace Integration
# ══════════════════════════════════════════════════════════════════


class TestRepoConnection:
    """Test repository connection operations."""

    @pytest.mark.asyncio
    async def test_create_connection(self, db_session: AsyncSession, sample_project):
        from app.services import repo_service
        from app.models.repo_connection import RepoProvider

        conn = await repo_service.create_connection(
            db_session,
            project_id=sample_project.id,
            provider=RepoProvider.GITHUB,
            repo_url="https://github.com/test/repo",
            repo_name="test/repo",
            default_branch="main",
        )
        assert conn.id is not None
        assert conn.provider.value == "github"
        assert conn.status.value == "pending"

    @pytest.mark.asyncio
    async def test_list_connections(self, db_session: AsyncSession, sample_project):
        from app.services import repo_service
        from app.models.repo_connection import RepoProvider

        await repo_service.create_connection(
            db_session,
            project_id=sample_project.id,
            provider=RepoProvider.GITHUB,
            repo_url="https://github.com/test/repo1",
            repo_name="test/repo1",
        )
        await repo_service.create_connection(
            db_session,
            project_id=sample_project.id,
            provider=RepoProvider.LOCAL,
            repo_url="/tmp/local-repo",
            repo_name="local-repo",
            workspace_path="/tmp/local-repo",
        )

        connections, total = await repo_service.list_connections(
            db_session, sample_project.id
        )
        assert total == 2

    @pytest.mark.asyncio
    async def test_update_connection(self, db_session: AsyncSession, sample_project):
        from app.services import repo_service
        from app.models.repo_connection import RepoProvider

        conn = await repo_service.create_connection(
            db_session,
            project_id=sample_project.id,
            provider=RepoProvider.GITHUB,
            repo_url="https://github.com/test/repo",
            repo_name="test/repo",
        )

        updated = await repo_service.update_connection(
            db_session, conn.id,
            default_branch="develop",
        )
        assert updated is not None
        assert updated.default_branch == "develop"

    @pytest.mark.asyncio
    async def test_delete_connection(self, db_session: AsyncSession, sample_project):
        from app.services import repo_service
        from app.models.repo_connection import RepoProvider

        conn = await repo_service.create_connection(
            db_session,
            project_id=sample_project.id,
            provider=RepoProvider.GITHUB,
            repo_url="https://github.com/test/repo",
            repo_name="test/repo",
        )

        deleted = await repo_service.delete_connection(db_session, conn.id)
        assert deleted is True

    @pytest.mark.asyncio
    async def test_health_check_no_cred(self, db_session: AsyncSession, sample_project):
        from app.services import repo_service
        from app.models.repo_connection import RepoProvider

        conn = await repo_service.create_connection(
            db_session,
            project_id=sample_project.id,
            provider=RepoProvider.GITHUB,
            repo_url="https://github.com/test/repo",
            repo_name="test/repo",
        )

        health = await repo_service.check_connection_health(db_session, conn.id)
        assert health["healthy"] is False
        assert len(health["issues"]) > 0


# ══════════════════════════════════════════════════════════════════
# FM-050: Production Hardening
# ══════════════════════════════════════════════════════════════════


class TestProductionHardening:
    """Test production hardening features."""

    def test_rate_limit_bucket(self):
        from app.core.rate_limit import _TokenBucket

        bucket = _TokenBucket(capacity=3, refill_rate=1.0)
        assert bucket.consume() is True
        assert bucket.consume() is True
        assert bucket.consume() is True
        assert bucket.consume() is False  # Exhausted

    def test_auth_stub_fallback(self):
        """In dev mode (no JWT secret), auth falls back to stub user."""
        from app.core.auth import _get_jwt_secret, _STUB_USER_ID
        # Default secret is "change-me-to-a-random-secret" → returns None
        assert _get_jwt_secret() is None

    def test_custom_rules_evaluation(self):
        """Test custom rule evaluation logic."""
        from app.services.governance_service import _evaluate_custom_rules

        rules = {
            "conditions": [
                {"field": "task_type", "op": "in", "value": ["architecture"]},
                {"field": "cost_usd", "op": "gt", "value": 0.5},
            ],
            "logic": "and",
        }

        assert _evaluate_custom_rules(rules, task_type="architecture", cost_usd=1.0) is True
        assert _evaluate_custom_rules(rules, task_type="codegen", cost_usd=1.0) is False
        assert _evaluate_custom_rules(rules, task_type="architecture", cost_usd=0.1) is False

    def test_custom_rules_or_logic(self):
        from app.services.governance_service import _evaluate_custom_rules

        rules = {
            "conditions": [
                {"field": "task_type", "op": "eq", "value": "architecture"},
                {"field": "cost_usd", "op": "gt", "value": 10.0},
            ],
            "logic": "or",
        }

        assert _evaluate_custom_rules(rules, task_type="architecture", cost_usd=0.1) is True
        assert _evaluate_custom_rules(rules, task_type="codegen", cost_usd=20.0) is True
        assert _evaluate_custom_rules(rules, task_type="codegen", cost_usd=0.1) is False

    def test_council_decision_resolution(self):
        """Test decision resolution logic directly."""
        from app.services.council_service import _resolve_decision
        from app.models.council import DecisionMethod, VoteDecision
        from types import SimpleNamespace

        # Create lightweight mock votes (avoid SQLAlchemy instrumentation)
        votes = []
        for slug, dec, conf in [("a", VoteDecision.APPROVE, 0.9), ("b", VoteDecision.APPROVE, 0.8), ("c", VoteDecision.REJECT, 0.5)]:
            v = SimpleNamespace(agent_slug=slug, decision=dec, confidence=conf, weight=1.0)
            votes.append(v)

        decision, rationale, summary = _resolve_decision(votes, DecisionMethod.MAJORITY)
        assert decision == "approve"
        assert summary["total_votes"] == 3

    def test_replay_hash_computation(self):
        from app.services.replay_service import _compute_replay_hash

        h1 = _compute_replay_hash("coder", {"x": 1}, "prompt", "gpt-4o", 0.3)
        h2 = _compute_replay_hash("coder", {"x": 1}, "prompt", "gpt-4o", 0.3)
        h3 = _compute_replay_hash("coder", {"x": 2}, "prompt", "gpt-4o", 0.3)

        assert h1 == h2
        assert h1 != h3
        assert len(h1) == 64  # SHA256 hex digest
