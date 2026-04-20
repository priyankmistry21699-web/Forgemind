"""Outbound GitHub API client — creates PRs, posts comments, status checks.

FM-153: Outbound PR creation on GitHub.
FM-154/157: PR/issue comment posting, commit status, reviewer requests.

Architecture:
- Uses httpx.AsyncClient for non-blocking HTTP calls to api.github.com.
- Authenticates via GITHUB_API_TOKEN (personal access token or installation token).
- All outbound calls go through `_github_request()` for consistent error handling.
- When credentials are unavailable, operations raise GitHubClientError so callers
  can handle gracefully (e.g. queue for retry).
"""

import logging
import re as _re
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


@dataclass
class GitHubPullRequest:
    """Represents a pull request created on GitHub."""

    number: int
    html_url: str
    title: str
    head_ref: str
    base_ref: str
    state: str


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
        response = await client.request(method, url, headers=headers, json=json_body)

    if response.status_code >= 400:
        error_body = response.text[:500]
        logger.error(
            "github_api: %s %s → %d: %s",
            method,
            path,
            response.status_code,
            error_body,
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


# ── Pull Request Creation ────────────────────────────────────────


async def create_pull_request(
    owner: str,
    repo: str,
    *,
    title: str,
    head: str,
    base: str,
    body: str = "",
    draft: bool = False,
    token: str,
) -> GitHubPullRequest:
    """Create a pull request on GitHub.

    Args:
        owner: Repository owner (org or user).
        repo: Repository name.
        title: PR title.
        head: Branch containing the changes.
        base: Branch to merge into.
        body: PR description (markdown).
        draft: Whether to create as a draft PR.
        token: GitHub API token.

    Returns:
        GitHubPullRequest with number, URL, and branch info.
    """
    payload: dict = {
        "title": title,
        "head": head,
        "base": base,
        "body": body,
        "draft": draft,
    }
    data = await _github_request(
        "POST",
        f"/repos/{owner}/{repo}/pulls",
        token=token,
        json_body=payload,
    )
    return GitHubPullRequest(
        number=data["number"],
        html_url=data.get("html_url", ""),
        title=data.get("title", title),
        head_ref=data.get("head", {}).get("ref", head),
        base_ref=data.get("base", {}).get("ref", base),
        state=data.get("state", "open"),
    )


# ── Reviewer Requests ────────────────────────────────────────────


async def request_reviewers(
    owner: str,
    repo: str,
    pr_number: int,
    *,
    reviewers: list[str] | None = None,
    team_reviewers: list[str] | None = None,
    token: str,
) -> dict:
    """Request reviewers on a GitHub pull request.

    Uses POST /repos/{owner}/{repo}/pulls/{pull_number}/requested_reviewers.
    At least one of reviewers or team_reviewers must be provided.
    """
    payload: dict = {}
    if reviewers:
        payload["reviewers"] = reviewers
    if team_reviewers:
        payload["team_reviewers"] = team_reviewers
    if not payload:
        raise ValueError("At least one reviewer or team_reviewer must be specified")

    data = await _github_request(
        "POST",
        f"/repos/{owner}/{repo}/pulls/{pr_number}/requested_reviewers",
        token=token,
        json_body=payload,
    )
    return {
        "requested_reviewers": [
            u.get("login", "") for u in data.get("requested_reviewers", [])
        ],
        "requested_teams": [t.get("slug", "") for t in data.get("requested_teams", [])],
    }


# ── CI Pass Rate ─────────────────────────────────────────────────


async def get_ci_pass_rate(
    owner: str,
    repo: str,
    *,
    branch: str = "main",
    per_page: int = 20,
    token: str,
) -> dict:
    """Calculate CI pass rate from recent workflow runs on a branch.

    Fetches the last `per_page` completed workflow runs on the given branch
    and computes the success rate.
    """
    data = await _github_request(
        "GET",
        f"/repos/{owner}/{repo}/actions/runs?branch={branch}&status=completed&per_page={per_page}",
        token=token,
    )
    runs = data.get("workflow_runs", [])
    if not runs:
        return {"branch": branch, "total_runs": 0, "success_count": 0, "pass_rate": 0.0}

    success_count = sum(1 for r in runs if r.get("conclusion") == "success")
    return {
        "branch": branch,
        "total_runs": len(runs),
        "success_count": success_count,
        "pass_rate": round(success_count / len(runs) * 100, 1),
    }


# ── FM-156: Branch Management ───────────────────────────────────


async def create_branch(
    owner: str,
    repo: str,
    *,
    branch_name: str,
    base_branch: str = "main",
    token: str,
) -> dict:
    """Create a branch on a GitHub repository (FM-156).

    1. Resolves the SHA of the base branch head.
    2. Creates a new git ref for the branch.
    """
    # Get SHA of the base branch
    ref_data = await _github_request(
        "GET",
        f"/repos/{owner}/{repo}/git/ref/heads/{base_branch}",
        token=token,
    )
    sha = ref_data["object"]["sha"]

    # Create the new branch
    result = await _github_request(
        "POST",
        f"/repos/{owner}/{repo}/git/refs",
        token=token,
        json_body={
            "ref": f"refs/heads/{branch_name}",
            "sha": sha,
        },
    )
    return {
        "branch_name": branch_name,
        "base_branch": base_branch,
        "sha": sha,
        "ref": result.get("ref", f"refs/heads/{branch_name}"),
    }


def slugify_branch_name(task_title: str, task_id: str) -> str:
    """Generate a clean branch name from a task title (FM-156)."""
    slug = task_title.lower().strip()
    slug = _re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")[:50]
    short_id = task_id[:8]
    return f"task/{slug}-{short_id}"
