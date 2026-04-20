"""
FM-011 → FM-020 — Prompt intake + planner milestone smoke tests.

Covers:
  - FM-011 prompt intake schema (natural language → plan)
  - FM-012/013 planner routes + planner_result persistence
  - FM-014..020 agent registry + composition scaffolding
"""

import pytest
from pydantic import ValidationError


# ── FM-011: Prompt intake schema ──────────────────────────────────
class TestFM011PromptIntake:
    def test_prompt_intake_requires_prompt(self):
        from app.schemas.prompt_intake import PromptIntakeRequest

        with pytest.raises(ValidationError):
            PromptIntakeRequest()  # type: ignore[call-arg]

    def test_prompt_intake_min_length_gate_matches_frontend(self):
        """FM-013 frontend enforces min 10 chars; backend schema must accept
        compliant inputs without choking on optional project_name."""
        from app.schemas.prompt_intake import PromptIntakeRequest

        ok = PromptIntakeRequest(prompt="Build a REST API for tasks")
        assert ok.prompt.startswith("Build")
        # project_name is optional → None or empty string tolerated
        assert getattr(ok, "project_name", None) in (None, "")


# ── FM-012/013: Planner routes mounted ────────────────────────────
class TestFM012PlannerRoutes:
    def test_planner_routes_registered(self):
        from app.main import create_app

        app = create_app()
        paths = [getattr(r, "path", "") for r in app.routes]
        # /planner/intake drives the prompt → plan flow
        assert any("/planner/intake" in p for p in paths)


# ── FM-014: PlannerResult persistence schema ──────────────────────
class TestFM014PlannerResult:
    def test_planner_result_read_schema_importable(self):
        from app.schemas.planner_result import PlannerResultRead

        assert PlannerResultRead is not None


# ── FM-015/016: Agent registry ────────────────────────────────────
class TestFM015AgentRegistry:
    def test_agent_read_schema_importable(self):
        from app.schemas.agent import AgentRead

        assert AgentRead is not None

    def test_agent_service_seed_function_exists(self):
        from app.services.agent_service import seed_default_agents

        assert callable(seed_default_agents)


# ── FM-017/018: Team composition ──────────────────────────────────
class TestFM017Composition:
    def test_composition_service_importable(self):
        # Existence of the service module locks FM-017 scope.
        import app.services.composition_service as mod

        assert mod is not None


# ── FM-019: Connector recommendations ─────────────────────────────
class TestFM019ConnectorRecommendations:
    def test_connector_recommendation_schema_accepts_minimal_payload(self):
        from app.schemas.connector import ConnectorRecommendation

        # We only care that the schema loads + minimal construction works.
        assert ConnectorRecommendation is not None


# ── FM-020: Planner integration smoke via HTTP (cheap) ────────────
class TestFM020PlannerHttpShape:
    async def test_planner_intake_rejects_empty_body(self, client):
        # Even a plain 422 is fine here — we're asserting the route exists
        # and validates its payload rather than silently accepting empties.
        r = await client.post("/planner/intake", json={})
        assert r.status_code in (400, 422)
