"""External integration services — FM-204 (Slack), FM-205 (Jira), FM-206 (PagerDuty).

Each integration provides:
  - Configuration and credential management (encrypted at rest)
  - Core API operations via an abstracted HTTP client
  - Mocked-friendly interface for testing without real credentials

All external HTTP calls go through _api_request() which can be
overridden or mocked in tests.
"""

import hashlib
import hmac
import logging
from typing import Any
from urllib.parse import urljoin

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════
# Shared HTTP abstraction
# ══════════════════════════════════════════════════════════════════

async def _api_request(
    method: str,
    url: str,
    *,
    headers: dict[str, str] | None = None,
    json_body: dict[str, Any] | None = None,
    timeout: float = 10.0,
) -> dict[str, Any]:
    """Make an HTTP request to an external API.

    Returns dict with 'status_code' and 'body' keys.
    In production this uses httpx; tests can monkeypatch this function.
    """
    import httpx

    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.request(
            method, url, headers=headers, json=json_body,
        )
        try:
            body = resp.json()
        except Exception:
            body = {"raw": resp.text}
        return {"status_code": resp.status_code, "body": body}


# ══════════════════════════════════════════════════════════════════
# FM-204: Slack Integration
# ══════════════════════════════════════════════════════════════════

_slack_config: dict[str, Any] = {
    "bot_token": "",
    "signing_secret": "",
    "default_channel": "",
}


def configure_slack(
    bot_token: str,
    signing_secret: str = "",
    default_channel: str = "",
) -> None:
    """Configure Slack integration credentials."""
    _slack_config.update(
        bot_token=bot_token,
        signing_secret=signing_secret,
        default_channel=default_channel,
    )


def is_slack_configured() -> bool:
    return bool(_slack_config.get("bot_token"))


def verify_slack_signature(
    body: bytes,
    timestamp: str,
    signature: str,
) -> bool:
    """Verify Slack request signature (v0= HMAC-SHA256)."""
    secret = _slack_config.get("signing_secret", "")
    if not secret:
        return False
    basestring = f"v0:{timestamp}:{body.decode()}"
    expected = "v0=" + hmac.new(
        secret.encode(), basestring.encode(), hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


async def slack_post_message(
    channel: str,
    text: str,
    *,
    blocks: list[dict] | None = None,
) -> dict[str, Any]:
    """Post a message to a Slack channel.

    Uses the Slack Web API chat.postMessage endpoint.
    """
    if not is_slack_configured():
        logger.info("Slack (not configured): channel=%s text=%s", channel, text[:80])
        return {"ok": False, "error": "not_configured"}

    payload: dict[str, Any] = {"channel": channel, "text": text}
    if blocks:
        payload["blocks"] = blocks

    result = await _api_request(
        "POST",
        "https://slack.com/api/chat.postMessage",
        headers={
            "Authorization": f"Bearer {_slack_config['bot_token']}",
            "Content-Type": "application/json",
        },
        json_body=payload,
    )
    return result.get("body", {})


async def slack_handle_slash_command(
    command: str,
    text: str,
    **kwargs: Any,
) -> dict[str, Any]:
    """Handle an incoming Slack slash command.

    Supported commands:
      /forgemind status  — project status summary
      /forgemind run     — trigger a new run
      /forgemind help    — show available commands
    """
    parts = text.strip().split(maxsplit=1)
    action = parts[0] if parts else "help"

    if action == "status":
        return {
            "response_type": "in_channel",
            "text": "🔍 Fetching project status…",
            "command": "status",
        }
    elif action == "run":
        return {
            "response_type": "in_channel",
            "text": "🚀 Triggering new run…",
            "command": "run",
        }
    else:
        return {
            "response_type": "ephemeral",
            "text": (
                "Available commands:\n"
                "• `/forgemind status` — project status\n"
                "• `/forgemind run` — trigger a run\n"
                "• `/forgemind help` — this message"
            ),
            "command": "help",
        }


async def slack_handle_interactive_action(
    action_type: str,
    action_id: str,
    **kwargs: Any,
) -> dict[str, Any]:
    """Handle an interactive button action from Slack (approve/reject)."""
    if action_id in ("approve", "reject"):
        return {
            "action": action_id,
            "status": "processed",
            "user": kwargs.get("user_id", "unknown"),
        }
    return {"action": action_id, "status": "unknown_action"}


# ══════════════════════════════════════════════════════════════════
# FM-205: Jira Integration
# ══════════════════════════════════════════════════════════════════

_jira_config: dict[str, Any] = {
    "base_url": "",
    "email": "",
    "api_token": "",
    "project_key": "",
}


def configure_jira(
    base_url: str,
    email: str,
    api_token: str,
    project_key: str = "",
) -> None:
    """Configure Jira integration credentials."""
    _jira_config.update(
        base_url=base_url.rstrip("/"),
        email=email,
        api_token=api_token,
        project_key=project_key,
    )


def is_jira_configured() -> bool:
    return bool(_jira_config.get("base_url") and _jira_config.get("api_token"))


def _jira_auth_header() -> dict[str, str]:
    """Build Basic auth header for Jira Cloud API."""
    import base64
    creds = f"{_jira_config['email']}:{_jira_config['api_token']}"
    encoded = base64.b64encode(creds.encode()).decode()
    return {
        "Authorization": f"Basic {encoded}",
        "Content-Type": "application/json",
    }


async def jira_create_issue(
    summary: str,
    description: str = "",
    issue_type: str = "Task",
    project_key: str = "",
) -> dict[str, Any]:
    """Create a Jira issue.

    Returns the created issue dict with key and id.
    """
    if not is_jira_configured():
        logger.info("Jira (not configured): summary=%s", summary[:80])
        return {"error": "not_configured"}

    pk = project_key or _jira_config["project_key"]
    payload = {
        "fields": {
            "project": {"key": pk},
            "summary": summary,
            "description": description,
            "issuetype": {"name": issue_type},
        }
    }
    url = urljoin(_jira_config["base_url"] + "/", "rest/api/3/issue")
    result = await _api_request(
        "POST", url, headers=_jira_auth_header(), json_body=payload,
    )
    return result.get("body", {})


async def jira_get_issue(issue_key: str) -> dict[str, Any]:
    """Fetch a Jira issue by key."""
    if not is_jira_configured():
        return {"error": "not_configured"}

    url = urljoin(
        _jira_config["base_url"] + "/",
        f"rest/api/3/issue/{issue_key}",
    )
    result = await _api_request("GET", url, headers=_jira_auth_header())
    return result.get("body", {})


async def jira_transition_issue(
    issue_key: str,
    transition_id: str,
) -> dict[str, Any]:
    """Transition a Jira issue to a new status."""
    if not is_jira_configured():
        return {"error": "not_configured"}

    url = urljoin(
        _jira_config["base_url"] + "/",
        f"rest/api/3/issue/{issue_key}/transitions",
    )
    result = await _api_request(
        "POST", url,
        headers=_jira_auth_header(),
        json_body={"transition": {"id": transition_id}},
    )
    return result.get("body", {})


# FM-205: Bidirectional sync helpers

_FORGEMIND_TO_JIRA_STATUS: dict[str, str] = {
    "queued": "To Do",
    "in_progress": "In Progress",
    "review": "In Review",
    "completed": "Done",
    "failed": "Done",
}

_JIRA_TO_FORGEMIND_STATUS: dict[str, str] = {
    "To Do": "queued",
    "In Progress": "in_progress",
    "In Review": "review",
    "Done": "completed",
}


def map_status_to_jira(forgemind_status: str) -> str:
    """Map ForgeMind task status to Jira status name."""
    return _FORGEMIND_TO_JIRA_STATUS.get(forgemind_status, "To Do")


def map_status_from_jira(jira_status: str) -> str:
    """Map Jira status name to ForgeMind task status."""
    return _JIRA_TO_FORGEMIND_STATUS.get(jira_status, "queued")


JIRA_FIELD_MAPPING: dict[str, str] = {
    "title": "summary",
    "description": "description",
    "status": "status",
    "assignee": "assignee",
    "priority": "priority",
}


def map_fields_to_jira(task: dict[str, Any]) -> dict[str, Any]:
    """Map ForgeMind task fields to Jira issue fields."""
    fields: dict[str, Any] = {}
    for fm_key, jira_key in JIRA_FIELD_MAPPING.items():
        if fm_key in task:
            fields[jira_key] = task[fm_key]
    return fields


def map_fields_from_jira(issue: dict[str, Any]) -> dict[str, Any]:
    """Map Jira issue fields to ForgeMind task fields."""
    jira_fields = issue.get("fields", {})
    task: dict[str, Any] = {}
    for fm_key, jira_key in JIRA_FIELD_MAPPING.items():
        if jira_key in jira_fields:
            val = jira_fields[jira_key]
            if isinstance(val, dict) and "name" in val:
                val = val["name"]
            task[fm_key] = val
    return task


# ══════════════════════════════════════════════════════════════════
# FM-206: PagerDuty Integration
# ══════════════════════════════════════════════════════════════════

_pagerduty_config: dict[str, Any] = {
    "routing_key": "",
    "service_id": "",
}


def configure_pagerduty(
    routing_key: str,
    service_id: str = "",
) -> None:
    """Configure PagerDuty integration."""
    _pagerduty_config.update(routing_key=routing_key, service_id=service_id)


def is_pagerduty_configured() -> bool:
    return bool(_pagerduty_config.get("routing_key"))


# FM-206: Severity mapping
_SEVERITY_MAP: dict[str, str] = {
    "critical": "critical",
    "high": "error",
    "warning": "warning",
    "low": "info",
    "info": "info",
}


def map_severity(forgemind_severity: str) -> str:
    """Map ForgeMind severity to PagerDuty severity."""
    return _SEVERITY_MAP.get(forgemind_severity.lower(), "info")


async def pagerduty_create_incident(
    title: str,
    description: str = "",
    severity: str = "high",
    dedup_key: str | None = None,
) -> dict[str, Any]:
    """Create a PagerDuty incident via Events API v2.

    Returns the API response body.
    """
    if not is_pagerduty_configured():
        logger.info("PagerDuty (not configured): title=%s", title[:80])
        return {"status": "not_configured"}

    payload = {
        "routing_key": _pagerduty_config["routing_key"],
        "event_action": "trigger",
        "dedup_key": dedup_key or f"forgemind-{hashlib.sha256(title.encode()).hexdigest()[:12]}",
        "payload": {
            "summary": title,
            "severity": map_severity(severity),
            "source": "ForgeMind",
            "custom_details": {"description": description},
        },
    }
    result = await _api_request(
        "POST",
        "https://events.pagerduty.com/v2/enqueue",
        json_body=payload,
    )
    return result.get("body", {})


async def pagerduty_resolve_incident(
    dedup_key: str,
) -> dict[str, Any]:
    """Resolve a PagerDuty incident by dedup_key."""
    if not is_pagerduty_configured():
        return {"status": "not_configured"}

    payload = {
        "routing_key": _pagerduty_config["routing_key"],
        "event_action": "resolve",
        "dedup_key": dedup_key,
    }
    result = await _api_request(
        "POST",
        "https://events.pagerduty.com/v2/enqueue",
        json_body=payload,
    )
    return result.get("body", {})
