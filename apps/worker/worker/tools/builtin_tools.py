"""FM-225: Built-in agent tools — WebSearch, ReadFile, WriteFile, RunCommand.

All tools run within the sandbox boundary:
- ReadFile / WriteFile are bounded to SANDBOX_BASE_DIR
- RunCommand uses the existing SANDBOX_COMMAND_ALLOWLIST
- WebSearch uses DuckDuckGo's public instant-answer API (no key needed)
"""

from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path
from typing import Any

from worker.tools.base import AgentTool, registry

logger = logging.getLogger("forgemind.worker.tools.builtin")

_SANDBOX_BASE = Path(os.getenv("SANDBOX_BASE_DIR", "/tmp/forgemind_sandbox"))
_SANDBOX_BASE.mkdir(parents=True, exist_ok=True)

_COMMAND_ALLOWLIST = {
    "python", "python3", "pip", "pytest", "echo", "cat", "ls", "pwd",
    "node", "npm", "npx", "tsc", "eslint", "go", "cargo", "rustc",
    "git", "diff", "grep", "find", "wc", "head", "tail", "bandit",
}


def _safe_path(path_str: str) -> Path | None:
    """Resolve path and confirm it stays within the sandbox."""
    try:
        resolved = (_SANDBOX_BASE / path_str.lstrip("/")).resolve()
        if not str(resolved).startswith(str(_SANDBOX_BASE.resolve())):
            return None
        return resolved
    except Exception:
        return None


# ---------------------------------------------------------------------------
# WebSearch
# ---------------------------------------------------------------------------


class WebSearchTool(AgentTool):
    name = "web_search"
    description = "Search the web via DuckDuckGo instant-answer API."
    parameters_schema = {
        "type": "object",
        "properties": {"query": {"type": "string", "description": "Search query"}},
        "required": ["query"],
    }

    async def execute(self, query: str = "", **_) -> dict[str, Any]:
        if not query:
            return {"success": False, "output": "query is required"}
        try:
            import httpx

            url = "https://api.duckduckgo.com/"
            params = {"q": query, "format": "json", "no_html": "1", "skip_disambig": "1"}
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(url, params=params)
                data = resp.json()
            abstract = data.get("AbstractText") or data.get("Answer") or ""
            related = [r.get("Text", "") for r in data.get("RelatedTopics", [])[:3] if isinstance(r, dict)]
            output = abstract or " | ".join(related) or "No results found"
            return {"success": True, "output": output, "source": data.get("AbstractURL", "")}
        except ImportError:
            return {"success": False, "output": "httpx not installed"}
        except Exception as exc:
            return {"success": False, "output": str(exc)}


# ---------------------------------------------------------------------------
# ReadFile
# ---------------------------------------------------------------------------


class ReadFileTool(AgentTool):
    name = "read_file"
    description = "Read a file from the sandbox directory."
    parameters_schema = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Relative path within sandbox"},
            "max_chars": {"type": "integer", "default": 8000},
        },
        "required": ["path"],
    }

    async def execute(self, path: str = "", max_chars: int = 8000, **_) -> dict[str, Any]:
        p = _safe_path(path)
        if p is None:
            return {"success": False, "output": "Path outside sandbox boundary"}
        if not p.exists():
            return {"success": False, "output": f"File not found: {path}"}
        content = p.read_text(errors="replace")[:max_chars]
        return {"success": True, "output": content, "size": p.stat().st_size}


# ---------------------------------------------------------------------------
# WriteFile
# ---------------------------------------------------------------------------


class WriteFileTool(AgentTool):
    name = "write_file"
    description = "Write content to a file in the sandbox directory."
    parameters_schema = {
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "content": {"type": "string"},
        },
        "required": ["path", "content"],
    }

    async def execute(self, path: str = "", content: str = "", **_) -> dict[str, Any]:
        p = _safe_path(path)
        if p is None:
            return {"success": False, "output": "Path outside sandbox boundary"}
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
        return {"success": True, "output": f"Written {len(content)} chars to {path}", "bytes": len(content.encode())}


# ---------------------------------------------------------------------------
# RunCommand
# ---------------------------------------------------------------------------


class RunCommandTool(AgentTool):
    name = "run_command"
    description = "Execute an allowlisted command in the sandbox directory."
    parameters_schema = {
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "Full shell command"},
            "timeout": {"type": "integer", "default": 30},
        },
        "required": ["command"],
    }

    async def execute(self, command: str = "", timeout: int = 30, **_) -> dict[str, Any]:
        import shlex

        parts = shlex.split(command)
        if not parts:
            return {"success": False, "output": "Empty command"}
        base_cmd = os.path.basename(parts[0])
        if base_cmd not in _COMMAND_ALLOWLIST:
            return {"success": False, "output": f"Command '{base_cmd}' not in allowlist"}

        try:
            proc = await asyncio.create_subprocess_exec(
                *parts,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=str(_SANDBOX_BASE),
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            output = stdout.decode(errors="replace")[:4000]
            return {
                "success": proc.returncode == 0,
                "output": output,
                "exit_code": proc.returncode,
            }
        except asyncio.TimeoutError:
            return {"success": False, "output": f"Command timed out after {timeout}s"}
        except Exception as exc:
            return {"success": False, "output": str(exc)}


# ---------------------------------------------------------------------------
# Register all built-ins
# ---------------------------------------------------------------------------

registry.register(WebSearchTool())
registry.register(ReadFileTool())
registry.register(WriteFileTool())
registry.register(RunCommandTool())
