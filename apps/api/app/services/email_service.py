"""Email notification channel — FM-207.

Provides transactional email sending, HTML template rendering, and
digest aggregation. Uses SMTP or configurable provider (SendGrid, SES).
Falls back to logging in development when no SMTP is configured.
"""

import logging
import smtplib
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

logger = logging.getLogger(__name__)


# ── Configuration ────────────────────────────────────────────────

# In production these come from environment or settings.
_smtp_config: dict[str, Any] = {
    "host": "",
    "port": 587,
    "username": "",
    "password": "",
    "from_address": "noreply@forgemind.dev",
    "use_tls": True,
}


def configure_smtp(
    host: str,
    port: int = 587,
    username: str = "",
    password: str = "",
    from_address: str = "noreply@forgemind.dev",
    use_tls: bool = True,
) -> None:
    """Set SMTP configuration at runtime."""
    _smtp_config.update(
        host=host,
        port=port,
        username=username,
        password=password,
        from_address=from_address,
        use_tls=use_tls,
    )


def is_smtp_configured() -> bool:
    """Return True if SMTP host is configured (not empty)."""
    return bool(_smtp_config.get("host"))


# ── Templates ────────────────────────────────────────────────────

_TEMPLATES: dict[str, dict[str, str]] = {
    "notification": {
        "subject": "[ForgeMind] {title}",
        "html": (
            "<html><body>"
            "<h2 style='color:#2563eb'>{title}</h2>"
            "<p>{body}</p>"
            "<hr><p style='color:#6b7280;font-size:12px'>"
            "ForgeMind — {timestamp}</p>"
            "</body></html>"
        ),
        "text": "{title}\n\n{body}\n\n-- ForgeMind ({timestamp})",
    },
    "alert": {
        "subject": "[ForgeMind Alert] {title}",
        "html": (
            "<html><body>"
            "<h2 style='color:#dc2626'>⚠ {title}</h2>"
            "<p>{body}</p>"
            "<p><strong>Metric:</strong> {metric_type} = {current_value} "
            "(threshold: {threshold})</p>"
            "<hr><p style='color:#6b7280;font-size:12px'>"
            "ForgeMind Alert — {timestamp}</p>"
            "</body></html>"
        ),
        "text": "⚠ {title}\n\n{body}\n\nMetric: {metric_type} = {current_value} "
        "(threshold: {threshold})\n\n-- ForgeMind Alert ({timestamp})",
    },
    "digest": {
        "subject": "[ForgeMind] Daily Digest — {date}",
        "html": (
            "<html><body>"
            "<h2 style='color:#2563eb'>Daily Digest — {date}</h2>"
            "{items_html}"
            "<hr><p style='color:#6b7280;font-size:12px'>"
            "ForgeMind — You can adjust email preferences in Settings.</p>"
            "</body></html>"
        ),
        "text": "Daily Digest — {date}\n\n{items_text}\n\n"
        "-- ForgeMind (adjust preferences in Settings)",
    },
}


def render_template(
    template_name: str,
    context: dict[str, Any],
) -> dict[str, str]:
    """Render an email template with the given context.

    Returns dict with 'subject', 'html', 'text' keys.
    """
    template = _TEMPLATES.get(template_name)
    if not template:
        raise ValueError(f"Unknown email template: {template_name}")

    # Provide defaults
    ctx = {"timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")}
    ctx.update(context)

    return {
        "subject": template["subject"].format_map(ctx),
        "html": template["html"].format_map(ctx),
        "text": template["text"].format_map(ctx),
    }


# ── Digest Aggregation ───────────────────────────────────────────

_pending_digest: dict[str, list[dict[str, Any]]] = {}


def add_to_digest(email: str, notification: dict[str, Any]) -> None:
    """Queue a notification for digest delivery."""
    _pending_digest.setdefault(email, []).append(notification)


def flush_digest(email: str) -> dict[str, str] | None:
    """Build and return a digest email for a given address, clearing the queue.

    Returns None if no pending notifications.
    """
    items = _pending_digest.pop(email, [])
    if not items:
        return None

    items_html = "".join(
        f"<div style='margin-bottom:12px'><strong>{it.get('title', '')}</strong>"
        f"<br>{it.get('body', '')}</div>"
        for it in items
    )
    items_text = "\n".join(
        f"- {it.get('title', '')}: {it.get('body', '')}" for it in items
    )
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    return render_template(
        "digest",
        {
            "date": date,
            "items_html": items_html,
            "items_text": items_text,
        },
    )


def get_pending_digest_count(email: str) -> int:
    """Return the number of pending digest items for an email."""
    return len(_pending_digest.get(email, []))


# ── Sending ──────────────────────────────────────────────────────


def send_email(
    to: str,
    subject: str,
    html_body: str,
    text_body: str | None = None,
) -> dict[str, Any]:
    """Send a single email.

    If SMTP is not configured, logs the email (development mode).
    Returns a result dict with status.
    """
    if not is_smtp_configured():
        logger.info(
            "Email (dev-mode, not sent): to=%s subject=%s",
            to,
            subject,
        )
        return {"status": "logged", "to": to, "subject": subject}

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = _smtp_config["from_address"]
    msg["To"] = to

    if text_body:
        msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(_smtp_config["host"], _smtp_config["port"]) as server:
            if _smtp_config["use_tls"]:
                server.starttls()
            if _smtp_config["username"]:
                server.login(_smtp_config["username"], _smtp_config["password"])
            server.sendmail(_smtp_config["from_address"], [to], msg.as_string())

        logger.info("Email sent: to=%s subject=%s", to, subject)
        return {"status": "sent", "to": to, "subject": subject}
    except Exception as exc:
        logger.error("Email send failed: to=%s error=%s", to, exc)
        return {"status": "failed", "to": to, "error": str(exc)}


def send_notification_email(
    to: str,
    title: str,
    body: str,
) -> dict[str, Any]:
    """Send a transactional notification email using the 'notification' template."""
    rendered = render_template("notification", {"title": title, "body": body})
    return send_email(to, rendered["subject"], rendered["html"], rendered["text"])


def send_alert_email(
    to: str,
    title: str,
    body: str,
    metric_type: str = "",
    current_value: str = "",
    threshold: str = "",
) -> dict[str, Any]:
    """Send an alert email using the 'alert' template."""
    rendered = render_template(
        "alert",
        {
            "title": title,
            "body": body,
            "metric_type": metric_type,
            "current_value": current_value,
            "threshold": threshold,
        },
    )
    return send_email(to, rendered["subject"], rendered["html"], rendered["text"])


# ── Preference Management ────────────────────────────────────────

# In-memory preference store.  Production would use DB.
_email_preferences: dict[str, dict[str, bool]] = {}

NOTIFICATION_CATEGORIES = (
    "alerts",
    "reports",
    "mentions",
    "approvals",
    "digest",
)


def set_email_preference(email: str, category: str, enabled: bool) -> None:
    """Set email preference for a category."""
    _email_preferences.setdefault(email, {})
    _email_preferences[email][category] = enabled


def get_email_preferences(email: str) -> dict[str, bool]:
    """Get email preferences for a user.  Defaults to all enabled."""
    prefs = _email_preferences.get(email, {})
    return {cat: prefs.get(cat, True) for cat in NOTIFICATION_CATEGORIES}


def is_category_enabled(email: str, category: str) -> bool:
    """Check if a specific category is enabled for the email."""
    prefs = get_email_preferences(email)
    return prefs.get(category, True)


def unsubscribe(email: str, category: str) -> None:
    """Unsubscribe an email from a notification category."""
    set_email_preference(email, category, False)


# ── FM-219: Jinja2 HTML templates + async DB-aware sender ────────

import os as _os
from pathlib import Path as _Path

_JINJA_TEMPLATE_DIR = _Path(__file__).parent.parent / "templates" / "email"
_jinja2_env = None


def _get_jinja2_env():
    global _jinja2_env
    if _jinja2_env is not None:
        return _jinja2_env
    try:
        from jinja2 import Environment, FileSystemLoader, select_autoescape

        _jinja2_env = Environment(
            loader=FileSystemLoader(str(_JINJA_TEMPLATE_DIR)),
            autoescape=select_autoescape(["html"]),
        )
    except ImportError:
        pass
    return _jinja2_env


def render_jinja_template(template_name: str, context: dict) -> str:
    """Render a Jinja2 HTML email template.  Falls back to plain text."""
    env = _get_jinja2_env()
    if env is None:
        return f"{context.get('title', '')}\n\n{context.get('description', '')}"
    try:
        return env.get_template(template_name).render(**context)
    except Exception as exc:
        logger.warning("render_jinja_template failed (%s)", exc)
        return str(context)


_APP_BASE_URL = _os.getenv("APP_BASE_URL", "http://localhost:3000")


async def send_notification_email_async(db: object, notif: object) -> bool:
    """FM-219: Async email sender driven by a Notification ORM object.

    Looks up the recipient User, picks the right Jinja2 template, renders
    it, and delivers via send_email (or logs in dev mode).
    """
    from app.models.user import User
    from app.models.notification import NotificationType

    user = await db.get(User, notif.user_id)  # type: ignore[union-attr]
    if user is None or not getattr(user, "email", None):
        return False

    ntype_val = (
        notif.notification_type.value  # type: ignore[union-attr]
        if hasattr(notif.notification_type, "value")
        else str(notif.notification_type)
    )

    template_map = {
        NotificationType.APPROVAL_REQUIRED.value: "approval_required.html",
        NotificationType.RUN_COMPLETED.value: "run_completed.html",
        NotificationType.RUN_FAILED.value: "run_completed.html",
        NotificationType.ESCALATION.value: "escalation.html",
    }
    template_name = template_map.get(ntype_val, "base.html")

    ctx = {
        "subject": notif.title,  # type: ignore[union-attr]
        "title": notif.title,  # type: ignore[union-attr]
        "description": notif.body or "",  # type: ignore[union-attr]
        "action_url": f"{_APP_BASE_URL}/dashboard",
        "project_name": "ForgeMind",
        "status": "completed",
        "run_number": "—",
        "hours_overdue": 0,
    }
    html = render_jinja_template(template_name, ctx)
    result = send_email(user.email, notif.title, html)  # type: ignore[union-attr]
    return result.get("status") in ("sent", "logged")
