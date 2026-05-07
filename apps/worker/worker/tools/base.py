"""FM-225: Abstract base + registry for agent tools.

Every tool:
- Declares a name and JSON schema for its parameters
- Implements async execute(**kwargs) → dict
- Returns a dict with at minimum {"success": bool, "output": str|dict}

All invocations are logged as AuditLogEntry records (fire-and-forget).
"""

from __future__ import annotations

import abc
import logging
from typing import Any

logger = logging.getLogger("forgemind.worker.tools")

# Registry: name → tool class
_REGISTRY: dict[str, "AgentTool"] = {}


class AgentTool(abc.ABC):
    """Abstract base for all agent tools."""

    name: str = ""
    description: str = ""
    parameters_schema: dict[str, Any] = {}

    @abc.abstractmethod
    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        """Run the tool and return {"success": bool, "output": ...}."""

    async def __call__(self, **kwargs: Any) -> dict[str, Any]:
        logger.debug("tool[%s] called with %s", self.name, list(kwargs.keys()))
        try:
            result = await self.execute(**kwargs)
        except Exception as exc:
            logger.exception("tool[%s] raised: %s", self.name, exc)
            result = {"success": False, "output": str(exc)}
        await _audit(self.name, kwargs, result)
        return result


async def _audit(tool_name: str, inputs: dict, result: dict) -> None:
    """Fire-and-forget audit log entry for every tool invocation."""
    try:
        from app.db.session import async_session_factory
        from app.services.audit_log_service import log_event  # type: ignore[import]

        async with async_session_factory() as db:
            await log_event(
                db,
                action=f"agent_tool:{tool_name}",
                resource_type="tool",
                details={
                    "inputs": {k: str(v)[:200] for k, v in inputs.items()},
                    "success": result.get("success", False),
                },
            )
            await db.commit()
    except Exception:
        pass  # audit failures must never break tool execution


class ToolRegistry:
    """Simple name → instance registry."""

    def __init__(self) -> None:
        self._tools: dict[str, AgentTool] = {}

    def register(self, tool: AgentTool) -> None:
        self._tools[tool.name] = tool
        logger.debug("tool_registry: registered '%s'", tool.name)

    def get(self, name: str) -> AgentTool | None:
        return self._tools.get(name)

    def list_tools(self) -> list[dict[str, Any]]:
        return [
            {"name": t.name, "description": t.description, "schema": t.parameters_schema}
            for t in self._tools.values()
        ]


# Global registry instance
registry = ToolRegistry()
