"""Tests for health endpoints — liveness and readiness checks."""

import pytest


class TestHealthEndpoints:
    """Test /health and /health/ready."""

    async def test_health_check(self, client):
        """GET /health returns healthy status."""
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["service"] == "forgemind-api"

    async def test_readiness_check(self, client):
        """GET /health/ready returns ready status with DB connected."""
        resp = await client.get("/health/ready")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ready"
        assert data["database"] == "connected"
