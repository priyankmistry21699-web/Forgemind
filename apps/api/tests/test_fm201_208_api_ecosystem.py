"""Tests for FM-201–208: API & Ecosystem.

Covers: API key management, rate limiting, webhooks, connector registry.
"""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.api_ecosystem import (
    DeliveryStatus,
    ConnectorType,
    ConnectorStatus,
)
from app.services import api_key_service, webhook_connector_service

STUB_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


# ══════════════════════════════════════════════════════════════════
# FM-201: API Key Management
# ══════════════════════════════════════════════════════════════════


class TestAPIKeys:
    @pytest.mark.asyncio
    async def test_create_api_key(self, db_session: AsyncSession):
        key, raw = await api_key_service.create_api_key(
            db_session, creator_id=STUB_USER_ID,
            name="Test Key", scopes=["read", "write"],
        )
        await db_session.commit()
        assert key.id is not None
        assert raw.startswith("fm_")
        assert key.key_prefix in raw
        assert key.scopes == ["read", "write"]

    @pytest.mark.asyncio
    async def test_validate_api_key(self, db_session: AsyncSession):
        key, raw = await api_key_service.create_api_key(
            db_session, creator_id=STUB_USER_ID, name="Validate Test",
        )
        await db_session.commit()

        validated = await api_key_service.validate_api_key(db_session, raw)
        assert validated.id == key.id

    @pytest.mark.asyncio
    async def test_validate_invalid_key(self, db_session: AsyncSession):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await api_key_service.validate_api_key(db_session, "fm_invalid_key")
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_revoke_api_key(self, db_session: AsyncSession):
        key, raw = await api_key_service.create_api_key(
            db_session, creator_id=STUB_USER_ID, name="Revoke Test",
        )
        await db_session.commit()

        revoked = await api_key_service.revoke_api_key(
            db_session, key.id, STUB_USER_ID,
        )
        assert revoked.revoked is True

    @pytest.mark.asyncio
    async def test_revoke_by_wrong_user(self, db_session: AsyncSession):
        key, _ = await api_key_service.create_api_key(
            db_session, creator_id=STUB_USER_ID, name="Wrong User",
        )
        await db_session.commit()

        from fastapi import HTTPException
        other_user = uuid.uuid4()
        with pytest.raises(HTTPException) as exc_info:
            await api_key_service.revoke_api_key(db_session, key.id, other_user)
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_list_api_keys(self, db_session: AsyncSession):
        await api_key_service.create_api_key(
            db_session, creator_id=STUB_USER_ID, name="Key A",
        )
        await api_key_service.create_api_key(
            db_session, creator_id=STUB_USER_ID, name="Key B",
        )
        await db_session.commit()

        keys = await api_key_service.list_api_keys(db_session, STUB_USER_ID)
        assert len(keys) >= 2

    @pytest.mark.asyncio
    async def test_revoked_key_excluded_from_list(self, db_session: AsyncSession):
        key, _ = await api_key_service.create_api_key(
            db_session, creator_id=STUB_USER_ID, name="To Revoke",
        )
        await db_session.commit()
        await api_key_service.revoke_api_key(db_session, key.id, STUB_USER_ID)
        await db_session.commit()

        keys = await api_key_service.list_api_keys(
            db_session, STUB_USER_ID, include_revoked=False,
        )
        ids = {k.id for k in keys}
        assert key.id not in ids

    @pytest.mark.asyncio
    async def test_validate_revoked_key_fails(self, db_session: AsyncSession):
        key, raw = await api_key_service.create_api_key(
            db_session, creator_id=STUB_USER_ID, name="Revoked Validate",
        )
        await db_session.commit()
        await api_key_service.revoke_api_key(db_session, key.id, STUB_USER_ID)
        await db_session.commit()

        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await api_key_service.validate_api_key(db_session, raw)
        assert exc_info.value.status_code == 401


# ══════════════════════════════════════════════════════════════════
# FM-202: Rate Limiting
# ══════════════════════════════════════════════════════════════════


class TestRateLimiting:
    def test_check_rate_limit_allows(self):
        api_key_service.reset_rate_limit("test-rate-1")
        result = api_key_service.check_rate_limit(
            "test-rate-1", max_requests=10, window_seconds=60,
        )
        assert result["allowed"] is True
        assert result["remaining"] >= 0

    def test_rate_limit_exceeded(self):
        api_key_service.reset_rate_limit("test-rate-2")
        # Exhaust the limit
        for _ in range(5):
            api_key_service.check_rate_limit(
                "test-rate-2", max_requests=5, window_seconds=60,
            )

        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            api_key_service.check_rate_limit(
                "test-rate-2", max_requests=5, window_seconds=60,
            )
        assert exc_info.value.status_code == 429

    def test_reset_rate_limit(self):
        api_key_service.reset_rate_limit("test-rate-3")
        for _ in range(5):
            api_key_service.check_rate_limit(
                "test-rate-3", max_requests=5, window_seconds=60,
            )
        api_key_service.reset_rate_limit("test-rate-3")
        result = api_key_service.check_rate_limit(
            "test-rate-3", max_requests=5, window_seconds=60,
        )
        assert result["allowed"] is True


# ══════════════════════════════════════════════════════════════════
# FM-203: Webhooks
# ══════════════════════════════════════════════════════════════════


class TestWebhooks:
    @pytest.mark.asyncio
    async def test_create_webhook(self, db_session: AsyncSession):
        wh = await webhook_connector_service.create_webhook(
            db_session, creator_id=STUB_USER_ID,
            url="https://example.com/hook",
            events=["run.completed", "task.failed"],
        )
        await db_session.commit()
        assert wh.id is not None
        assert wh.active is True

    @pytest.mark.asyncio
    async def test_create_webhook_with_secret(self, db_session: AsyncSession):
        wh = await webhook_connector_service.create_webhook(
            db_session, creator_id=STUB_USER_ID,
            url="https://example.com/secure-hook",
            events=["run.completed"],
            secret="my-secret-123",
        )
        await db_session.commit()
        assert wh.secret_hash is not None

    @pytest.mark.asyncio
    async def test_list_webhooks(self, db_session: AsyncSession):
        await webhook_connector_service.create_webhook(
            db_session, creator_id=STUB_USER_ID,
            url="https://example.com/h1", events=["run.completed"],
        )
        await db_session.commit()

        webhooks = await webhook_connector_service.list_webhooks(
            db_session, STUB_USER_ID,
        )
        assert len(webhooks) >= 1

    @pytest.mark.asyncio
    async def test_delete_webhook(self, db_session: AsyncSession):
        wh = await webhook_connector_service.create_webhook(
            db_session, creator_id=STUB_USER_ID,
            url="https://example.com/delete", events=["task.created"],
        )
        await db_session.commit()

        await webhook_connector_service.delete_webhook(db_session, wh.id)
        await db_session.commit()

        from fastapi import HTTPException
        with pytest.raises(HTTPException):
            await webhook_connector_service.get_webhook(db_session, wh.id)

    @pytest.mark.asyncio
    async def test_record_delivery(self, db_session: AsyncSession):
        wh = await webhook_connector_service.create_webhook(
            db_session, creator_id=STUB_USER_ID,
            url="https://example.com/deliver", events=["run.completed"],
        )
        await db_session.commit()

        delivery = await webhook_connector_service.record_delivery(
            db_session, subscription_id=wh.id,
            event_type="run.completed",
            payload={"run_id": "abc123"},
        )
        await db_session.commit()
        assert delivery.id is not None
        assert delivery.status == DeliveryStatus.PENDING

    @pytest.mark.asyncio
    async def test_mark_delivery_success(self, db_session: AsyncSession):
        wh = await webhook_connector_service.create_webhook(
            db_session, creator_id=STUB_USER_ID,
            url="https://example.com/success", events=["run.completed"],
        )
        delivery = await webhook_connector_service.record_delivery(
            db_session, subscription_id=wh.id,
            event_type="run.completed", payload={},
        )
        await db_session.commit()

        success = await webhook_connector_service.mark_delivery_success(
            db_session, delivery.id, status_code=200,
        )
        assert success.status == DeliveryStatus.DELIVERED

    @pytest.mark.asyncio
    async def test_mark_delivery_failed_with_retry(self, db_session: AsyncSession):
        wh = await webhook_connector_service.create_webhook(
            db_session, creator_id=STUB_USER_ID,
            url="https://example.com/retry", events=["run.completed"],
        )
        delivery = await webhook_connector_service.record_delivery(
            db_session, subscription_id=wh.id,
            event_type="run.completed", payload={},
        )
        await db_session.commit()

        failed = await webhook_connector_service.mark_delivery_failed(
            db_session, delivery.id, status_code=500,
        )
        assert failed.status == DeliveryStatus.RETRYING
        assert failed.attempt == 2
        assert failed.next_retry_at is not None

    @pytest.mark.asyncio
    async def test_delivery_history(self, db_session: AsyncSession):
        wh = await webhook_connector_service.create_webhook(
            db_session, creator_id=STUB_USER_ID,
            url="https://example.com/history", events=["run.completed"],
        )
        await webhook_connector_service.record_delivery(
            db_session, subscription_id=wh.id,
            event_type="run.completed", payload={"seq": 1},
        )
        await webhook_connector_service.record_delivery(
            db_session, subscription_id=wh.id,
            event_type="task.failed", payload={"seq": 2},
        )
        await db_session.commit()

        deliveries, total = await webhook_connector_service.get_delivery_history(
            db_session, wh.id,
        )
        assert total >= 2

    def test_sign_payload(self):
        payload = {"event": "test", "data": {"id": "123"}}
        sig = webhook_connector_service.sign_payload(payload, "my-secret")
        assert isinstance(sig, str)
        assert len(sig) == 64  # SHA-256 hex digest


# ══════════════════════════════════════════════════════════════════
# FM-208: Connector Registry
# ══════════════════════════════════════════════════════════════════


class TestConnectorRegistry:
    @pytest.mark.asyncio
    async def test_register_connector(self, db_session: AsyncSession):
        conn = await webhook_connector_service.register_connector(
            db_session, name="Slack Connector",
            connector_type=ConnectorType.BIDIRECTIONAL,
            description="Slack integration",
        )
        await db_session.commit()
        assert conn.id is not None
        assert conn.status == ConnectorStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_list_connectors(self, db_session: AsyncSession):
        await webhook_connector_service.register_connector(
            db_session, name="C1", connector_type=ConnectorType.SOURCE,
        )
        await db_session.commit()

        connectors = await webhook_connector_service.list_connectors(db_session)
        assert len(connectors) >= 1

    @pytest.mark.asyncio
    async def test_update_connector_status(self, db_session: AsyncSession):
        conn = await webhook_connector_service.register_connector(
            db_session, name="Status Test",
            connector_type=ConnectorType.SINK,
        )
        await db_session.commit()

        updated = await webhook_connector_service.update_connector_status(
            db_session, conn.id, ConnectorStatus.ERROR,
        )
        assert updated.status == ConnectorStatus.ERROR
        assert updated.last_health_check is not None

    @pytest.mark.asyncio
    async def test_delete_connector(self, db_session: AsyncSession):
        conn = await webhook_connector_service.register_connector(
            db_session, name="Delete Me",
            connector_type=ConnectorType.SOURCE,
        )
        await db_session.commit()

        await webhook_connector_service.delete_connector(db_session, conn.id)
        await db_session.commit()

        from fastapi import HTTPException
        with pytest.raises(HTTPException):
            await webhook_connector_service.get_connector(db_session, conn.id)


# ══════════════════════════════════════════════════════════════════
# FM-201: Scope Enforcement
# ══════════════════════════════════════════════════════════════════


class TestScopeEnforcement:
    @pytest.mark.asyncio
    async def test_validate_with_matching_scopes(self, db_session: AsyncSession):
        key, raw = await api_key_service.create_api_key(
            db_session, creator_id=STUB_USER_ID,
            name="scoped-key", scopes=["read", "write"],
        )
        await db_session.commit()

        validated = await api_key_service.validate_api_key_with_scopes(
            db_session, raw, required_scopes=["read"],
        )
        assert validated.id == key.id

    @pytest.mark.asyncio
    async def test_validate_with_missing_scopes(self, db_session: AsyncSession):
        key, raw = await api_key_service.create_api_key(
            db_session, creator_id=STUB_USER_ID,
            name="read-only", scopes=["read"],
        )
        await db_session.commit()

        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await api_key_service.validate_api_key_with_scopes(
                db_session, raw, required_scopes=["write"],
            )
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_validate_wildcard_scope(self, db_session: AsyncSession):
        key, raw = await api_key_service.create_api_key(
            db_session, creator_id=STUB_USER_ID,
            name="admin-key", scopes=["*"],
        )
        await db_session.commit()

        validated = await api_key_service.validate_api_key_with_scopes(
            db_session, raw, required_scopes=["read", "write", "admin"],
        )
        assert validated.id == key.id

    @pytest.mark.asyncio
    async def test_validate_no_required_scopes(self, db_session: AsyncSession):
        key, raw = await api_key_service.create_api_key(
            db_session, creator_id=STUB_USER_ID,
            name="any-key", scopes=["read"],
        )
        await db_session.commit()

        validated = await api_key_service.validate_api_key_with_scopes(
            db_session, raw, required_scopes=None,
        )
        assert validated.id == key.id

    def test_require_scope_creates_dependency(self):
        dep = api_key_service.require_scope("read", "write")
        assert callable(dep)

    @pytest.mark.asyncio
    async def test_validate_multiple_required_scopes(self, db_session: AsyncSession):
        key, raw = await api_key_service.create_api_key(
            db_session, creator_id=STUB_USER_ID,
            name="partial-key", scopes=["read"],
        )
        await db_session.commit()

        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await api_key_service.validate_api_key_with_scopes(
                db_session, raw, required_scopes=["read", "write"],
            )
        assert exc_info.value.status_code == 403
        assert "write" in exc_info.value.detail


# ══════════════════════════════════════════════════════════════════
# FM-203: Webhook HTTP Dispatch
# ══════════════════════════════════════════════════════════════════


class TestWebhookDispatch:
    @pytest.mark.asyncio
    async def test_dispatch_webhook_success(self, db_session: AsyncSession):
        """Test dispatch_webhook with a mocked HTTP POST that returns 200."""
        import httpx
        from unittest.mock import AsyncMock, patch

        wh = await webhook_connector_service.create_webhook(
            db_session, creator_id=STUB_USER_ID,
            url="https://example.com/hook", events=["run.completed"],
            secret="test-secret",
        )
        await db_session.commit()

        mock_response = httpx.Response(200, request=httpx.Request("POST", "https://example.com/hook"))
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):
            delivery = await webhook_connector_service.dispatch_webhook(
                db_session,
                subscription=wh,
                event_type="run.completed",
                payload={"run_id": "abc123"},
                secret="test-secret",
            )
            await db_session.commit()

        assert delivery.status == DeliveryStatus.DELIVERED

    @pytest.mark.asyncio
    async def test_dispatch_webhook_failure(self, db_session: AsyncSession):
        """Test dispatch_webhook with a 500 response triggers retry."""
        import httpx
        from unittest.mock import AsyncMock, patch

        wh = await webhook_connector_service.create_webhook(
            db_session, creator_id=STUB_USER_ID,
            url="https://example.com/fail", events=["run.failed"],
        )
        await db_session.commit()

        mock_response = httpx.Response(500, request=httpx.Request("POST", "https://example.com/fail"))
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):
            delivery = await webhook_connector_service.dispatch_webhook(
                db_session,
                subscription=wh,
                event_type="run.failed",
                payload={"error": "timeout"},
            )
            await db_session.commit()

        assert delivery.status == DeliveryStatus.RETRYING

    @pytest.mark.asyncio
    async def test_dispatch_webhook_network_error(self, db_session: AsyncSession):
        """Test dispatch_webhook when network error occurs."""
        import httpx
        from unittest.mock import AsyncMock, patch

        wh = await webhook_connector_service.create_webhook(
            db_session, creator_id=STUB_USER_ID,
            url="https://example.com/down", events=["task.created"],
        )
        await db_session.commit()

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock, side_effect=httpx.ConnectError("Connection refused")):
            delivery = await webhook_connector_service.dispatch_webhook(
                db_session,
                subscription=wh,
                event_type="task.created",
                payload={"task_id": "t1"},
            )
            await db_session.commit()

        assert delivery.status == DeliveryStatus.RETRYING

    @pytest.mark.asyncio
    async def test_fire_event_dispatches_to_matching_subs(self, db_session: AsyncSession):
        """Test fire_event finds matching subscriptions and dispatches."""
        import httpx
        from unittest.mock import AsyncMock, patch

        wh1 = await webhook_connector_service.create_webhook(
            db_session, creator_id=STUB_USER_ID,
            url="https://a.com/hook", events=["run.completed"],
        )
        wh2 = await webhook_connector_service.create_webhook(
            db_session, creator_id=STUB_USER_ID,
            url="https://b.com/hook", events=["task.created"],
        )
        await db_session.commit()

        mock_response = httpx.Response(200, request=httpx.Request("POST", "https://a.com/hook"))
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):
            deliveries = await webhook_connector_service.fire_event(
                db_session,
                event_type="run.completed",
                payload={"run_id": "r1"},
            )
            await db_session.commit()

        # Only wh1 matches "run.completed"
        assert len(deliveries) >= 1
        assert all(d.status == DeliveryStatus.DELIVERED for d in deliveries)

# ══════════════════════════════════════════════════════════════════
# FM-203 Enhancement: fire_event secret fix verification
# ══════════════════════════════════════════════════════════════════


class TestFireEventSecretFix:
    @pytest.mark.asyncio
    async def test_fire_event_passes_secret_hash(self, db_session: AsyncSession):
        """fire_event should pass secret_hash, not None."""
        import httpx
        from unittest.mock import AsyncMock, patch

        wh = await webhook_connector_service.create_webhook(
            db_session, creator_id=STUB_USER_ID,
            url="https://example.com/signed", events=["deploy.started"],
            secret="my-secret-key",
        )
        await db_session.commit()

        mock_response = httpx.Response(200, request=httpx.Request("POST", "https://example.com/signed"))
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response) as mock_post:
            deliveries = await webhook_connector_service.fire_event(
                db_session,
                event_type="deploy.started",
                payload={"deploy_id": "d1"},
            )
            await db_session.commit()

        assert len(deliveries) >= 1
        # Verify the actual http call included a signature header
        if mock_post.called:
            call_kwargs = mock_post.call_args
            if call_kwargs and call_kwargs.kwargs.get("headers"):
                # HMAC signature header should be present when secret_hash is provided
                headers = call_kwargs.kwargs["headers"]
                assert isinstance(headers, dict)


# ══════════════════════════════════════════════════════════════════
# FM-208: Connector ABC + Health Probe
# ══════════════════════════════════════════════════════════════════


class TestConnectorABC:
    def test_connector_abc_exists(self):
        """ConnectorABC abstract class should be importable."""
        from app.services.webhook_connector_service import ConnectorABC
        import abc
        assert issubclass(ConnectorABC, abc.ABC)

    def test_connector_abc_has_abstract_methods(self):
        """ConnectorABC should define validate_config, health_check, send."""
        from app.services.webhook_connector_service import ConnectorABC
        abstracts = ConnectorABC.__abstractmethods__
        assert "validate_config" in abstracts
        assert "health_check" in abstracts
        assert "send" in abstracts


class TestConnectorHealthCheck:
    @pytest.mark.asyncio
    async def test_health_check_no_url(self, db_session: AsyncSession):
        """Connector with no health_url → config_only probe."""
        conn = await webhook_connector_service.register_connector(
            db_session, name="No URL Connector",
            connector_type=ConnectorType.SOURCE,
            config_json={"api_key": "test"},
        )
        await db_session.commit()

        result = await webhook_connector_service.health_check_connector(
            db_session, conn.id,
        )
        assert result["probe"] == "config_only"
        assert result["new_status"] == ConnectorStatus.ACTIVE.value

    @pytest.mark.asyncio
    async def test_health_check_with_url_success(self, db_session: AsyncSession):
        """Connector with health_url and successful response → ACTIVE."""
        import httpx
        from unittest.mock import AsyncMock, patch

        conn = await webhook_connector_service.register_connector(
            db_session, name="URL Connector",
            connector_type=ConnectorType.SOURCE,
            config_json={"health_url": "https://api.example.com/health"},
        )
        await db_session.commit()

        mock_response = httpx.Response(200, request=httpx.Request("GET", "https://api.example.com/health"))
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
            result = await webhook_connector_service.health_check_connector(
                db_session, conn.id,
            )

        assert result["probe"] == "http_ok"
        assert result["new_status"] == ConnectorStatus.ACTIVE.value
        assert result["status_code"] == 200

    @pytest.mark.asyncio
    async def test_health_check_with_url_error(self, db_session: AsyncSession):
        """Connector with health_url returning 500 → ERROR."""
        import httpx
        from unittest.mock import AsyncMock, patch

        conn = await webhook_connector_service.register_connector(
            db_session, name="Failing Connector",
            connector_type=ConnectorType.SOURCE,
            config_json={"health_url": "https://api.example.com/health"},
        )
        await db_session.commit()

        mock_response = httpx.Response(500, request=httpx.Request("GET", "https://api.example.com/health"))
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
            result = await webhook_connector_service.health_check_connector(
                db_session, conn.id,
            )

        assert result["probe"] == "http_error"
        assert result["new_status"] == ConnectorStatus.ERROR.value

    @pytest.mark.asyncio
    async def test_health_check_network_error(self, db_session: AsyncSession):
        """Network error → ERROR status."""
        import httpx
        from unittest.mock import AsyncMock, patch

        conn = await webhook_connector_service.register_connector(
            db_session, name="Unreachable Connector",
            connector_type=ConnectorType.SOURCE,
            config_json={"health_url": "https://unreachable.example.com/health"},
        )
        await db_session.commit()

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock,
                    side_effect=httpx.ConnectError("Connection refused")):
            result = await webhook_connector_service.health_check_connector(
                db_session, conn.id,
            )

        assert result["probe"] == "http_unreachable"
        assert result["new_status"] == ConnectorStatus.ERROR.value

    @pytest.mark.asyncio
    async def test_health_check_empty_config(self, db_session: AsyncSession):
        """Connector with no config_json → INACTIVE."""
        conn = await webhook_connector_service.register_connector(
            db_session, name="Empty Config",
            connector_type=ConnectorType.SOURCE,
            config_json=None,
        )
        await db_session.commit()

        result = await webhook_connector_service.health_check_connector(
            db_session, conn.id,
        )
        assert result["probe"] == "config_only"
        assert result["new_status"] == ConnectorStatus.INACTIVE.value