"""
ForgeMind Execution Quality Eval Suite (FM-045)

Evaluates the quality of:
- Chat topic detection accuracy
- Connector recommendation accuracy
- Retry policy selection accuracy
- Chatbot stub response quality

Run with: python -m pytest evals/test_quality_evals.py -v
"""

import json
import uuid
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio

# Load eval benchmarks
EVAL_DATA_PATH = Path(__file__).parent / "datasets" / "eval_benchmarks.json"
with open(EVAL_DATA_PATH) as f:
    EVAL_DATA = json.load(f)


# =====================================================================
# Topic Detection Evals
# =====================================================================

class TestTopicDetectionEvals:
    """Verify that chat_service.detect_topics correctly identifies topics."""

    @pytest.mark.parametrize(
        "eval_case",
        EVAL_DATA["topic_detection_evals"],
        ids=[e["id"] for e in EVAL_DATA["topic_detection_evals"]],
    )
    def test_topic_detection(self, eval_case):
        from app.services.chat_service import detect_topics

        detected = detect_topics(eval_case["input"])
        expected = set(eval_case["expected_topics"])
        detected_set = set(detected)

        # All expected topics should be detected
        assert expected.issubset(detected_set), (
            f"Expected topics {expected} but detected {detected_set} "
            f"for input: '{eval_case['input']}'"
        )


# =====================================================================
# Connector Recommendation Evals
# =====================================================================

class TestConnectorRecommendationEvals:
    """Verify connector recommendations match expected outputs."""

    @pytest.mark.parametrize(
        "eval_case",
        EVAL_DATA["connector_evals"],
        ids=[e["id"] for e in EVAL_DATA["connector_evals"]],
    )
    def test_connector_recommendations(self, eval_case):
        from app.services.connector_service import recommend_connectors

        recs = recommend_connectors(
            eval_case["input"]["recommended_stack"],
            eval_case["input"]["project_description"],
        )

        rec_slugs = {r["slug"] for r in recs}
        rec_by_slug = {r["slug"]: r for r in recs}
        props = eval_case["expected_properties"]

        # Check required connectors are present
        for key, value in props.items():
            if key.startswith("includes_") and value is True:
                connector_name = key.replace("includes_", "")
                assert connector_name in rec_slugs or any(
                    connector_name in s for s in rec_slugs
                ), f"Expected connector '{connector_name}' in recommendations, got {rec_slugs}"

            if key.endswith("_priority"):
                connector_name = key.replace("_priority", "")
                matching = [r for r in recs if connector_name in r["slug"]]
                if matching:
                    assert matching[0]["priority"] == value, (
                        f"Expected {connector_name} priority '{value}' "
                        f"but got '{matching[0]['priority']}'"
                    )


# =====================================================================
# Retry Policy Evals
# =====================================================================

class TestRetryPolicyEvals:
    """Verify retry policy selection logic."""

    @pytest.mark.parametrize(
        "eval_case",
        [e for e in EVAL_DATA["retry_evals"] if e["category"] == "policy_selection"],
        ids=[e["id"] for e in EVAL_DATA["retry_evals"] if e["category"] == "policy_selection"],
    )
    def test_policy_selection(self, eval_case):
        from app.services.adaptive_retry_service import (
            get_policy_for_task,
            get_max_retries,
        )

        task_type = eval_case["input"]["task_type"]
        policy = get_policy_for_task(task_type)
        max_retries = get_max_retries(policy)
        props = eval_case["expected_properties"]

        assert policy == props["policy"], (
            f"Expected policy '{props['policy']}' for task type '{task_type}' "
            f"but got '{policy}'"
        )
        assert max_retries == props["max_retries"], (
            f"Expected max_retries {props['max_retries']} for policy '{policy}' "
            f"but got {max_retries}"
        )

    @pytest.mark.parametrize(
        "eval_case",
        [
            e
            for e in EVAL_DATA["retry_evals"]
            if e["category"] in ("exhaustion_handling", "no_retry_policy")
        ],
        ids=[
            e["id"]
            for e in EVAL_DATA["retry_evals"]
            if e["category"] in ("exhaustion_handling", "no_retry_policy")
        ],
    )
    @pytest.mark.asyncio
    async def test_retry_exhaustion(self, eval_case, db_session):
        from app.services.adaptive_retry_service import can_retry
        from app.models.task import Task, TaskStatus
        from app.models.run import Run
        from app.models.project import Project

        inp = eval_case["input"]
        props = eval_case["expected_properties"]

        # Create minimal project + run + task for the test
        project = Project(
            name="Eval Project", description="Eval", owner_id=uuid.UUID("00000000-0000-0000-0000-000000000001")
        )
        db_session.add(project)
        await db_session.flush()

        run = Run(run_number=1, project_id=project.id, trigger="eval")
        db_session.add(run)
        await db_session.flush()

        task = Task(
            title="Eval Task",
            task_type="generic",
            status=TaskStatus(inp["task_status"]),
            run_id=run.id,
            retry_count=inp["retry_count"],
            max_retries=inp["max_retries"],
            retry_policy=inp["retry_policy"],
        )
        db_session.add(task)
        await db_session.flush()

        result = await can_retry(db_session, task)

        assert result["can_retry"] == props["can_retry"], (
            f"Expected can_retry={props['can_retry']} but got {result['can_retry']}"
        )
        assert result["suggested_action"] == props["suggested_action"], (
            f"Expected suggested_action='{props['suggested_action']}' "
            f"but got '{result['suggested_action']}'"
        )


# =====================================================================
# Chatbot Stub Response Quality Evals
# =====================================================================

class TestChatbotStubEvals:
    """Verify chatbot stub responses contain expected information."""

    def test_blocker_stub_detects_blocked(self):
        from app.services.chat_service import _build_stub_response

        context = (
            "=== Tasks (5) ===\n"
            "  completed: 2\n  blocked: 2\n  running: 1\n"
            "  Progress: 40%\n\n"
            "[blocked] Deploy to staging\n"
            "[blocked] Run integration tests\n"
        )

        topics = ["blocker"]
        result = _build_stub_response(context, "What's blocking?", topics, [])
        assert "blocking" in result.lower() or "blocked" in result.lower()

    def test_failure_stub_shows_errors(self):
        from app.services.chat_service import _build_stub_response

        context = (
            "=== Failures (1) ===\n"
            "  - Implement API (implementation): ModuleNotFoundError\n"
        )

        topics = ["failure"]
        result = _build_stub_response(context, "Why did it fail?", topics, [])
        assert "failed" in result.lower() or "error" in result.lower() or "ModuleNotFoundError" in result

    def test_approval_stub_shows_pending(self):
        from app.services.chat_service import _build_stub_response

        context = (
            "=== Approvals (1) ===\n"
            "  pending: 1\n"
        )

        topics = ["approval"]
        result = _build_stub_response(context, "Any pending approvals?", topics, [])
        assert "pending" in result.lower()

    def test_connector_stub_uses_extra_sections(self):
        from app.services.chat_service import _build_stub_response

        extra = [
            "=== Connector Readiness (4) ===\n"
            "  Ready: 2 | Configured: 0 | Blocked: 1 | Missing: 1\n"
            "  [OK] GitHub (github) — required\n"
            "  [MISSING] Docker (docker) — required"
        ]

        topics = ["connector"]
        result = _build_stub_response("", "Are connectors ready?", topics, extra)
        assert "Connector Readiness" in result

    def test_retry_stub_uses_extra_sections(self):
        from app.services.chat_service import _build_stub_response

        extra = [
            "=== Retry Status ===\n"
            "  Failed: 2 | Retried: 1 | Exhausted: 1"
        ]

        topics = ["retry"]
        result = _build_stub_response("", "Can I retry?", topics, extra)
        assert "Retry Status" in result

    def test_next_step_stub(self):
        from app.services.chat_service import _build_stub_response

        extra = [
            "=== Suggested Next Steps ===\n"
            "  1. Review 1 pending approval(s)\n"
            "  2. 3 task(s) are READY"
        ]

        topics = ["next_step"]
        result = _build_stub_response("", "What should I do next?", topics, extra)
        assert "Suggested Next Steps" in result

    def test_general_fallback_shows_context(self):
        from app.services.chat_service import _build_stub_response

        context = "Run #1 — status: running"
        topics = ["general"]
        result = _build_stub_response(context, "Hello", topics, [])
        assert "Run #1" in result
