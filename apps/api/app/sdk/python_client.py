"""ForgeMind Python SDK — FM-209.

Async Python client for the ForgeMind API.
Auto-generated from OpenAPI spec with ergonomic improvements.
"""

from __future__ import annotations

import os
from typing import Any

import httpx


class ForgeMindError(Exception):
    """Base exception for ForgeMind SDK."""

    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"HTTP {status_code}: {detail}")


class ForgeMindClient:
    """Async Python SDK client for the ForgeMind API.

    Usage::

        async with ForgeMindClient(base_url="http://localhost:8000", api_key="fm_...") as client:
            projects = await client.list_projects()
    """

    def __init__(
        self,
        base_url: str = "",
        api_key: str = "",
        timeout: float = 30.0,
    ):
        self.base_url = (
            base_url.rstrip("/")
            or os.environ.get("FORGEMIND_BASE_URL", "http://localhost:8000")
        )
        self.api_key = api_key or os.environ.get("FORGEMIND_API_KEY", "")
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout,
            headers=self._auth_headers(),
        )

    def _auth_headers(self) -> dict[str, str]:
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        return headers

    async def __aenter__(self) -> ForgeMindClient:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    async def close(self) -> None:
        await self._client.aclose()

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        resp = await self._client.request(
            method, path, json=json, params=params,
        )
        if resp.status_code >= 400:
            try:
                detail = resp.json().get("detail", resp.text)
            except Exception:
                detail = resp.text
            raise ForgeMindError(resp.status_code, str(detail))
        return resp.json()

    # ── Projects ──────────────────────────────────────────────

    async def list_projects(self, **params: Any) -> dict[str, Any]:
        return await self._request("GET", "/api/v1/projects", params=params)

    async def get_project(self, project_id: str) -> dict[str, Any]:
        return await self._request("GET", f"/api/v1/projects/{project_id}")

    async def create_project(self, data: dict[str, Any]) -> dict[str, Any]:
        return await self._request("POST", "/api/v1/projects", json=data)

    # ── Tasks ─────────────────────────────────────────────────

    async def list_tasks(
        self, project_id: str, **params: Any,
    ) -> dict[str, Any]:
        return await self._request(
            "GET", f"/api/v1/projects/{project_id}/tasks", params=params,
        )

    async def create_task(
        self, project_id: str, data: dict[str, Any],
    ) -> dict[str, Any]:
        return await self._request(
            "POST", f"/api/v1/projects/{project_id}/tasks", json=data,
        )

    # ── Code Intelligence ─────────────────────────────────────

    async def get_dependency_graph(
        self, project_id: str,
    ) -> dict[str, Any]:
        return await self._request(
            "GET", f"/api/v1/projects/{project_id}/dependencies/graph",
        )

    async def analyze_impact(
        self, project_id: str, changed_files: list[str],
    ) -> dict[str, Any]:
        return await self._request(
            "POST",
            f"/api/v1/projects/{project_id}/dependencies/impact",
            json={"changed_files": changed_files},
        )

    async def select_tests(
        self, project_id: str, changed_files: list[str], mode: str = "standard",
    ) -> dict[str, Any]:
        return await self._request(
            "POST",
            f"/api/v1/projects/{project_id}/select-tests",
            json={"changed_files": changed_files, "mode": mode},
        )

    async def get_code_intelligence_context(
        self, project_id: str, changed_files: list[str] | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {}
        if changed_files:
            body["changed_files"] = changed_files
        return await self._request(
            "POST",
            f"/api/v1/projects/{project_id}/code-intelligence-context",
            json=body,
        )

    # ── Analytics ─────────────────────────────────────────────

    async def get_cycle_time(
        self, project_id: str, **params: Any,
    ) -> dict[str, Any]:
        return await self._request(
            "GET", f"/api/v1/projects/{project_id}/cycle-time", params=params,
        )

    async def get_quality_score(
        self, project_id: str,
    ) -> dict[str, Any]:
        return await self._request(
            "GET", f"/api/v1/projects/{project_id}/quality-score",
        )

    # ── Webhooks ──────────────────────────────────────────────

    async def fire_webhook(
        self, event_type: str, payload: dict[str, Any],
    ) -> dict[str, Any]:
        return await self._request(
            "POST", "/api/v1/webhooks/fire",
            json={"event_type": event_type, "payload": payload},
        )

    # ── API Keys ──────────────────────────────────────────────

    async def list_api_keys(self) -> dict[str, Any]:
        return await self._request("GET", "/api/v1/api-keys")

    async def create_api_key(
        self, name: str, scopes: list[str] | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {"name": name}
        if scopes:
            body["scopes"] = scopes
        return await self._request("POST", "/api/v1/api-keys", json=body)
