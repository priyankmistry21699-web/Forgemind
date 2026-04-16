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
