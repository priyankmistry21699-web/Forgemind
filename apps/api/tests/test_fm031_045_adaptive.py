"""
FM-031 → FM-045 — Adaptive orchestration, memory, vault, chat,
connectors milestone smoke tests (tightening FM-041 → FM-045 in
particular).

Covers the gap where this range was mostly tested indirectly:
  - FM-031..034 chat + execution memory + retry scaffolding
  - FM-035..040 connectors, artifact detail, dashboards UX
  - FM-041..045 adaptive orchestrator + retry + credential vault +
    council + knowledge base (explicit)
"""


# ── FM-031/032: Chat service + route ──────────────────────────────
class TestFM031Chat:
    def test_chat_service_importable(self):
        import app.services.chat_service as mod

        assert mod is not None

    def test_chat_route_registered(self):
        from app.main import create_app

        app = create_app()
        paths = [getattr(r, "path", "") for r in app.routes]
        assert any("/chat" in p for p in paths)


# ── FM-033: Run memory service ────────────────────────────────────
class TestFM033RunMemory:
    def test_run_memory_service_importable(self):
        import app.services.run_memory_service as mod

        assert mod is not None


# ── FM-034: Adaptive retry scaffolding ────────────────────────────
class TestFM034AdaptiveRetry:
    def test_adaptive_retry_service_importable(self):
        import app.services.adaptive_retry_service as mod

        assert mod is not None

    def test_retry_route_registered(self):
        from app.main import create_app

        app = create_app()
        paths = [getattr(r, "path", "") for r in app.routes]
        assert any("/retry" in p for p in paths)


# ── FM-035: Operator polish — artifact + approval surfaces ────────
class TestFM035ArtifactPolish:
    def test_artifact_list_route_registered(self):
        from app.main import create_app

        app = create_app()
        paths = [getattr(r, "path", "") for r in app.routes]
        assert any("/artifacts" in p for p in paths)


# ── FM-036..039: Connectors service + route ───────────────────────
class TestFM036Connectors:
    def test_connector_service_importable(self):
        import app.services.connector_service as mod

        assert mod is not None

    def test_connectors_route_registered(self):
        from app.main import create_app

        app = create_app()
        paths = [getattr(r, "path", "") for r in app.routes]
        assert any("/connectors" in p for p in paths)


# ── FM-040: Costs service + route ─────────────────────────────────
class TestFM040Costs:
    def test_cost_tracking_service_importable(self):
        import app.services.cost_tracking_service as mod

        assert mod is not None

    def test_costs_route_registered(self):
        from app.main import create_app

        app = create_app()
        paths = [getattr(r, "path", "") for r in app.routes]
        assert any("/costs" in p for p in paths)


# ══════════════════════════════════════════════════════════════════
# TIGHTEN: FM-041..045 (adaptive + memory + vault + council + KB)
# ══════════════════════════════════════════════════════════════════


# ── FM-041: Adaptive orchestrator ─────────────────────────────────
class TestFM041AdaptiveOrchestrator:
    def test_adaptive_orchestrator_module_importable(self):
        import app.services.adaptive_orchestrator as mod

        assert mod is not None


# ── FM-042: Credential vault ──────────────────────────────────────
class TestFM042CredentialVault:
    def test_credential_vault_service_importable(self):
        import app.services.credential_vault_service as mod

        assert mod is not None

    def test_vault_route_registered(self):
        from app.main import create_app

        app = create_app()
        paths = [getattr(r, "path", "") for r in app.routes]
        assert any("/vault" in p for p in paths)


# ── FM-043: Council decision engine ───────────────────────────────
class TestFM043Council:
    def test_council_service_importable(self):
        import app.services.council_service as mod

        assert mod is not None

    def test_council_route_registered(self):
        from app.main import create_app

        app = create_app()
        paths = [getattr(r, "path", "") for r in app.routes]
        assert any("/council" in p for p in paths)


# ── FM-044: Knowledge base ────────────────────────────────────────
class TestFM044KnowledgeBase:
    def test_knowledge_service_importable(self):
        import app.services.knowledge_service as mod

        assert mod is not None

    def test_knowledge_route_registered(self):
        from app.main import create_app

        app = create_app()
        paths = [getattr(r, "path", "") for r in app.routes]
        assert any("/knowledge" in p for p in paths)


# ── FM-045: Governance policies ───────────────────────────────────
class TestFM045Governance:
    def test_governance_engine_service_importable(self):
        import app.services.governance_engine_service as mod

        assert mod is not None

    def test_governance_policy_model_importable(self):
        from app.models.governance_policy import PolicyAction, PolicyTrigger

        assert PolicyAction is not None and PolicyTrigger is not None

    def test_governance_route_registered(self):
        from app.main import create_app

        app = create_app()
        paths = [getattr(r, "path", "") for r in app.routes]
        assert any("/governance" in p for p in paths)
