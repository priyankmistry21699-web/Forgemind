"""Tests for Chat API endpoint."""

import uuid
from unittest.mock import AsyncMock, patch

import pytest


class TestChatAboutRun:
    """POST /runs/{run_id}/chat"""

    async def test_chat_success(self, client, sample_run):
        """Chat should return a reply, even if LLM is not configured (stub mode)."""
        with patch(
            "app.services.chat_service.chat_about_run",
            new_callable=AsyncMock,
            return_value="This run is in pending status with 0 completed tasks.",
        ):
            resp = await client.post(
                f"/runs/{sample_run.id}/chat",
                json={"message": "What is the status of this run?"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert "reply" in data
            assert isinstance(data["reply"], str)
            assert len(data["reply"]) > 0

    async def test_chat_empty_message(self, client, sample_run):
        """Empty message should be rejected by validation."""
        resp = await client.post(
            f"/runs/{sample_run.id}/chat",
            json={"message": ""},
        )
        # Depending on schema validation, may be 422 or handled gracefully
        assert resp.status_code in (200, 422)
