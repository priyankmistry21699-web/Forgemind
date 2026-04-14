"""Outbound GitHub API client — posts comments, status checks, and syncs data.

FM-154/157: First outbound GitHub integration — PR and issue comment posting.

Architecture:
- Uses httpx.AsyncClient for non-blocking HTTP calls to api.github.com.
- Authenticates via GitHub App installation access tokens OR personal tokens.
- All outbound calls go through `_github_request()` for consistent error handling.
- When credentials are unavailable, operations raise GitHubClientError so callers
  can handle gracefully (e.g. queue for retry).

Honest scoping:
- This client supports comment posting and commit status creation.
- Full GitHub App JWT → installation token exchange is architecture-ready
  but requires real credentials (GITHUB_APP_ID + GITHUB_PRIVATE_KEY).
"""

import logging
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)

GITHUB_API_BASE = "https://api.github.com"


class GitHubClientError(Exception):
    """Raised when a GitHub API call fails."""

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"GitHub API error {status_code}: {message}")


@dataclass
class GitHubComment:
    """Represents a comment posted to GitHub."""

    id: int
    html_url: str
    body: str


@dataclass
class CommitStatus:
    """Represents a commit status posted to GitHub."""

    id: int
    state: str
    target_url: str | None
    description: str
    context: str


async def _github_request(
    method: str,
    path: str,
    *,
    token: str,
    json_body: dict | None = None,
) -> dict:
    """Make an authenticated request to the GitHub API.

    Args:
        method: HTTP method (GET, POST, PATCH, etc.)
        path: API path (e.g. /repos/owner/repo/issues/1/comments)
        token: GitHub access token (installation or personal)
        json_body: Optional JSON payload for POST/PATCH

    Returns:
        Parsed JSON response dict.

    Raises:
        GitHubClientError: If the API returns a non-2xx status.
    """
    url = f"{GITHUB_API_BASE}{path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.request(
            method, url, headers=headers, json=json_body
        )

    if response.status_code >= 400:
        error_body = response.text[:500]
        logger.error(
            "github_api: %s %s → %d: %s",
            method, path, response.status_code, error_body,
        )
        raise GitHubClientError(response.status_code, error_body)

    if response.status_code == 204:
        return {}

    return response.json()


# ── Comment Operations ───────────────────────────────────────────


async def post_pr_comment(
    owner: str,
    repo: str,
    pr_number: int,
    body: str,
    token: str,
) -> GitHubComment:
    """Post a comment on a GitHub pull request (issue comment endpoint).

    This uses the issues API since PR comments are a subset of issue comments
    on GitHub. For review-specific (inline) comments, use the pulls review API.
    """
    data = await _github_request(
        "POST",
        f"/repos/{owner}/{repo}/issues/{pr_number}/comments",
        token=token,
        json_body={"body": body},
    )
    return GitHubComment(
        id=data["id"],
        html_url=data.get("html_url", ""),
        body=data.get("body", body),
    )


async def post_issue_comment(
    owner: str,
    repo: str,
    issue_number: int,
    body: str,
    token: str,
) -> GitHubComment:
    """Post a comment on a GitHub issue."""
    data = await _github_request(
        "POST",
        f"/repos/{owner}/{repo}/issues/{issue_number}/comments",
        token=token,
        json_body={"body": body},
    )
    return GitHubComment(
        id=data["id"],
        html_url=data.get("html_url", ""),
        body=data.get("body", body),
    )


# ── Commit Status Operations ────────────────────────────────────


async def create_commit_status(
    owner: str,
    repo: str,
    sha: str,
    *,
    state: str,
    description: str = "",
    target_url: str | None = None,
    context: str = "forgemind/ci",
    token: str,
) -> CommitStatus:
    """Create a commit status on GitHub (pending, success, failure, error).

    This is used by ForgeMind to report CI/analysis results back to GitHub PRs.
    """
    if state not in ("pending", "success", "failure", "error"):
        raise ValueError(f"Invalid commit status state: {state}")

    payload: dict = {
        "state": state,
        "description": description[:140],  # GitHub limit
        "context": context,
    }
    if target_url:
        payload["target_url"] = target_url

    data = await _github_request(
        "POST",
        f"/repos/{owner}/{repo}/statuses/{sha}",
        token=token,
        json_body=payload,
    )
    return CommitStatus(
        id=data.get("id", 0),
        state=data.get("state", state),
        target_url=data.get("target_url"),
        description=data.get("description", description),
        context=data.get("context", context),
    )


# ── Repository Metadata ─────────────────────────────────────────


async def get_repository(
    owner: str,
    repo: str,
    token: str,
) -> dict:
    """Fetch repository metadata from GitHub."""
    return await _github_request("GET", f"/repos/{owner}/{repo}", token=token)
