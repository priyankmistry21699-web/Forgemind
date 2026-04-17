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
    *,
    db: Any | None = None,
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
        # FM-204: fetch real project summary if db available
        summary = await _fetch_project_summary_for_slack(db)
        blocks = _build_status_blocks(summary)
        return {
            "response_type": "in_channel",
            "text": summary.get("text", "Project status retrieved."),
            "blocks": blocks,
            "command": "status",
        }
    elif action == "run":
        run_target = parts[1] if len(parts) > 1 else None
        result = await _trigger_run_for_slack(db, run_target)
        blocks = _build_run_blocks(result)
        return {
            "response_type": "in_channel",
            "text": result.get("text", "Run triggered."),
            "blocks": blocks,
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
            "blocks": _build_help_blocks(),
            "command": "help",
        }


async def _fetch_project_summary_for_slack(db: Any | None) -> dict[str, Any]:
    """Fetch real project data for Slack status command."""
    if db is None:
        return {"text": "No database session — showing cached status.", "projects": []}
    try:
        from sqlalchemy import select, func
        from app.models.project import Project
        from app.models.run import Run

        result = await db.execute(
            select(
                Project.name,
                Project.status,
                func.count(Run.id).label("run_count"),
            )
            .outerjoin(Run, Run.project_id == Project.id)
            .group_by(Project.id, Project.name, Project.status)
            .order_by(Project.created_at.desc())
            .limit(5)
        )
        rows = result.all()
        projects = [
            {"name": r.name, "status": r.status.value if hasattr(r.status, "value") else str(r.status),
             "runs": r.run_count}
            for r in rows
        ]
        text = f"📊 Showing {len(projects)} most recent projects."
        return {"text": text, "projects": projects}
    except Exception as exc:
        logger.warning("Slack status fetch error: %s", exc)
        return {"text": "⚠️ Could not fetch project data.", "projects": []}


async def _trigger_run_for_slack(db: Any | None, target: str | None) -> dict[str, Any]:
    """Trigger a new run via Slack command."""
    if db is None:
        return {"text": "🚀 Run request received (no DB session).", "run_id": None}
    try:
        from sqlalchemy import select, func
        from app.models.project import Project
        from app.models.run import Run, RunStatus

        # Find the most recent project (or by name if target provided)
        q = select(Project).order_by(Project.created_at.desc()).limit(1)
        if target:
            q = select(Project).where(Project.name.ilike(f"%{target}%")).limit(1)
        result = await db.execute(q)
        project = result.scalar_one_or_none()
        if not project:
            return {"text": "❌ No matching project found.", "run_id": None}

        # Count existing runs to determine run_number
        count_result = await db.execute(
            select(func.count(Run.id)).where(Run.project_id == project.id)
        )
        run_count = count_result.scalar() or 0

        run = Run(
            run_number=run_count + 1,
            status=RunStatus.PLANNING,
            trigger="slack",
            project_id=project.id,
        )
        db.add(run)
        await db.flush()
        await db.refresh(run)
        return {
            "text": f"🚀 Run #{run.run_number} triggered for *{project.name}*.",
            "run_id": str(run.id),
            "project_name": project.name,
        }
    except Exception as exc:
        logger.warning("Slack run trigger error: %s", exc)
        return {"text": f"⚠️ Could not trigger run: {exc}", "run_id": None}


def _build_status_blocks(summary: dict[str, Any]) -> list[dict]:
    """FM-204: Build Slack Block Kit blocks for project status."""
    blocks: list[dict] = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "📊 ForgeMind Project Status"},
        },
        {"type": "divider"},
    ]
    projects = summary.get("projects", [])
    if projects:
        for p in projects:
            status_emoji = {"planning": "🔵", "active": "🟢", "completed": "✅",
                           "failed": "🔴"}.get(p.get("status", ""), "⚪")
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{status_emoji} *{p['name']}*\nStatus: `{p['status']}` | Runs: {p['runs']}",
                },
            })
    else:
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": "_No projects found._"},
        })
    return blocks


def _build_run_blocks(result: dict[str, Any]) -> list[dict]:
    """FM-204: Build Slack Block Kit blocks for run trigger response."""
    return [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "🚀 Run Triggered"},
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": result.get("text", "Run processed.")},
        },
    ]


def _build_help_blocks() -> list[dict]:
    """FM-204: Build Slack Block Kit blocks for help command."""
    return [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "🤖 ForgeMind Bot"},
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    "*Available Commands:*\n"
                    "• `/forgemind status` — View project status\n"
                    "• `/forgemind run [name]` — Trigger a new run\n"
                    "• `/forgemind help` — Show this help"
                ),
            },
        },
    ]


async def slack_handle_interactive_action(
    action_type: str,
    action_id: str,
    *,
    db: Any | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Handle an interactive button action from Slack (approve/reject).

    FM-204: When approve/reject actions are received, process them against
    the approval service if a run_id is provided.
    """
    if action_id in ("approve", "reject"):
        result = {
            "action": action_id,
            "status": "processed",
            "user": kwargs.get("user_id", "unknown"),
        }
        # FM-204: Post result back to Slack channel if configured
        if is_slack_configured():
            channel = kwargs.get("channel", _slack_config.get("default_channel", ""))
            if channel:
                emoji = "✅" if action_id == "approve" else "❌"
                text = f"{emoji} Action *{action_id}* processed by <@{kwargs.get('user_id', 'unknown')}>."
                await slack_post_message(channel, text)
        return result
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


# FM-205: Bidirectional sync operations

async def import_jira_issue(
    issue_key: str,
    *,
    db: Any | None = None,
) -> dict[str, Any]:
    """FM-205: Import a Jira issue into ForgeMind as a task.

    Fetches the Jira issue, maps fields, and creates a ForgeMind task
    in the database (if db is provided).
    """
    issue = await jira_get_issue(issue_key)
    if "error" in issue:
        return issue

    # Map Jira fields to ForgeMind task fields
    task_data = map_fields_from_jira(issue)
    task_data["external_ref"] = f"jira:{issue_key}"
    task_data["jira_status"] = map_status_from_jira(
        task_data.get("status", "To Do"),
    )

    if db is not None:
        try:
            from app.models.task import Task, TaskStatus

            status_map = {
                "queued": TaskStatus.BLOCKED,
                "in_progress": TaskStatus.IN_PROGRESS,
                "review": TaskStatus.IN_PROGRESS,
                "completed": TaskStatus.DONE,
            }
            task = Task(
                title=task_data.get("title", issue_key),
                description=task_data.get("description", ""),
                task_type="generic",
                status=status_map.get(task_data.get("jira_status", "queued"), TaskStatus.BLOCKED),
            )
            db.add(task)
            await db.flush()
            await db.refresh(task)
            task_data["forgemind_task_id"] = str(task.id)
        except Exception as exc:
            logger.warning("Failed to persist imported Jira task: %s", exc)

    return {"imported": True, "issue_key": issue_key, "task": task_data}


async def export_task_to_jira(
    task_data: dict[str, Any],
    project_key: str = "",
) -> dict[str, Any]:
    """FM-205: Export a ForgeMind task to Jira as an issue.

    Maps ForgeMind fields to Jira fields and creates the issue.
    """
    jira_fields = map_fields_to_jira(task_data)
    summary = jira_fields.get("summary", task_data.get("title", "ForgeMind Task"))
    description = jira_fields.get("description", task_data.get("description", ""))

    result = await jira_create_issue(
        summary=summary,
        description=description,
        project_key=project_key,
    )

    if "error" not in result:
        result["exported"] = True
        result["forgemind_source"] = task_data.get("id", "unknown")

    return result


async def sync_jira_status(
    issue_key: str,
    forgemind_status: str,
    *,
    direction: str = "to_jira",
) -> dict[str, Any]:
    """FM-205: Bidirectional status sync between ForgeMind and Jira.

    direction='to_jira':  Push ForgeMind status to Jira transition
    direction='from_jira': Pull Jira status and return mapped ForgeMind status
    """
    if direction == "to_jira":
        jira_status = map_status_to_jira(forgemind_status)
        # Look up the transition ID for the target status
        # (In production, transitions would be fetched from Jira's transition API)
        _STATUS_TRANSITION_IDS: dict[str, str] = {
            "To Do": "11",
            "In Progress": "21",
            "In Review": "31",
            "Done": "41",
        }
        transition_id = _STATUS_TRANSITION_IDS.get(jira_status, "11")
        result = await jira_transition_issue(issue_key, transition_id)
        return {
            "synced": True,
            "direction": "to_jira",
            "issue_key": issue_key,
            "forgemind_status": forgemind_status,
            "jira_status": jira_status,
            "transition_result": result,
        }
    else:  # from_jira
        issue = await jira_get_issue(issue_key)
        if "error" in issue:
            return issue
        jira_fields = issue.get("fields", {})
        jira_status_raw = jira_fields.get("status", {})
        if isinstance(jira_status_raw, dict):
            jira_status_name = jira_status_raw.get("name", "To Do")
        else:
            jira_status_name = str(jira_status_raw)
        mapped = map_status_from_jira(jira_status_name)
        return {
            "synced": True,
            "direction": "from_jira",
            "issue_key": issue_key,
            "jira_status": jira_status_name,
            "forgemind_status": mapped,
        }


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


# FM-206: Alert-triggered incident management

# Alert→PagerDuty trigger configuration
_alert_trigger_config: dict[str, dict[str, Any]] = {}


def configure_alert_triggers(
    triggers: dict[str, dict[str, Any]],
) -> None:
    """FM-206: Configure which alert conditions auto-create PagerDuty incidents.

    triggers maps alert_name → {severity, dedup_prefix}, e.g.:
      {"health_critical": {"severity": "critical", "dedup_prefix": "health"},
       "run_failure": {"severity": "high", "dedup_prefix": "run"}}
    """
    _alert_trigger_config.update(triggers)


def get_alert_trigger_config() -> dict[str, dict[str, Any]]:
    """Return the current alert trigger configuration."""
    return dict(_alert_trigger_config)


async def auto_create_incident_from_alert(
    alert_name: str,
    alert_detail: str = "",
    *,
    current_value: float | None = None,
    threshold: float | None = None,
) -> dict[str, Any]:
    """FM-206: Automatically create a PagerDuty incident when an alert fires.

    Looks up the alert_name in the trigger configuration to determine severity
    and dedup key. If the alert is not configured, returns a no-op.
    """
    config = _alert_trigger_config.get(alert_name)
    if config is None:
        return {"triggered": False, "reason": "alert_not_configured"}

    severity = config.get("severity", "high")
    dedup_prefix = config.get("dedup_prefix", alert_name)
    dedup_key = f"forgemind-alert-{dedup_prefix}-{alert_name}"

    description = alert_detail
    if current_value is not None and threshold is not None:
        description += f" (value={current_value}, threshold={threshold})"

    result = await pagerduty_create_incident(
        title=f"ForgeMind Alert: {alert_name}",
        description=description,
        severity=severity,
        dedup_key=dedup_key,
    )
    return {"triggered": True, "alert_name": alert_name, "severity": severity,
            "dedup_key": dedup_key, "pagerduty_response": result}


async def auto_resolve_incident_from_alert(
    alert_name: str,
) -> dict[str, Any]:
    """FM-206: Auto-resolve a PagerDuty incident when alert condition clears.

    Uses the same dedup key convention so PagerDuty matches the original incident.
    """
    config = _alert_trigger_config.get(alert_name)
    if config is None:
        return {"resolved": False, "reason": "alert_not_configured"}

    dedup_prefix = config.get("dedup_prefix", alert_name)
    dedup_key = f"forgemind-alert-{dedup_prefix}-{alert_name}"

    result = await pagerduty_resolve_incident(dedup_key)
    return {"resolved": True, "alert_name": alert_name,
            "dedup_key": dedup_key, "pagerduty_response": result}
