"""FM-200 aggregate — API ecosystem hardening smoke.

Aggregate audit evidence for FM-201 → FM-208: versioned public API, API keys,
rate limiting, webhooks, external connectors.
"""


class TestFM200EcosystemRoutes:
    def test_api_v1_and_ecosystem_routes_mounted(self):
        from app.main import create_app

        app = create_app()
        paths = [getattr(r, "path", "") for r in app.routes]
        # FM-201 versioned public API.
        assert any(p.startswith("/api/v1") for p in paths)
        # FM-203..208 ecosystem router exposes webhook/connector/key endpoints.
        assert any(
            ("webhook" in p) or ("api-key" in p) or ("connector" in p) for p in paths
        )


class TestFM200ApiKeyService:
    def test_api_key_service_surface(self):
        from app.services import api_key_service

        # Stable surface used by FM-201/202/203 route code + tests.
        for name in (
            "create_api_key",
            "validate_api_key",
            "revoke_api_key",
            "list_api_keys",
            "hash_api_key",
            "check_rate_limit",
            "require_rate_limit",
        ):
            assert hasattr(api_key_service, name), name


class TestFM200ApiKeyModel:
    def test_api_key_model_importable(self):
        from app.models.api_ecosystem import APIKey

        assert APIKey.__tablename__  # table name exists


class TestFM200WebhookAndConnectors:
    def test_webhook_and_connector_services_importable(self):
        from app.services import webhook_service, webhook_connector_service

        assert webhook_service is not None
        assert webhook_connector_service is not None
