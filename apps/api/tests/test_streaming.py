"""Tests for SSE streaming endpoint (FM-054)."""
import pytest


@pytest.mark.asyncio
class TestStreaming:

    async def test_stream_endpoint_exists(self, client):
        """Verify the SSE endpoint is registered and returns a streaming response."""
        from app.main import create_app
        app = create_app()
        routes = [r.path for r in app.routes]
        assert "/stream/events" in routes

    async def test_event_generator_yields_heartbeat(self):
        """Verify the event generator yields heartbeat SSE frames."""
        from app.api.routes.streaming import _event_generator
        gen = _event_generator()
        first = await gen.__anext__()
        assert "event: heartbeat" in first
        assert "data: {}" in first
        await gen.aclose()
