"""Webhook receiver — ingests and processes GitHub webhook events.

FM-152: Webhook Receiver & Event Ingestion.
"""

import uuid
import hashlib
import hmac

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.github_integration import (
    ExternalEvent,
    ExternalEventSource,
    RepositoryLink,
    PullRequestLink,
    PRStatus,
    CIPipelineRun,
    CIPipelineStatus,
    IssueLink,
    IssueLinkStatus,
)


def verify_github_signature(payload_body: bytes, signature: str, secret: str) -> bool:
    """Verify GitHub HMAC-SHA256 webhook signature."""
    if not signature.startswith("sha256="):
        return False
    expected = hmac.new(
        secret.encode(), payload_body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)


async def ingest_event(
    db: AsyncSession,
    event_type: str,
    delivery_id: str | None,
    payload: dict,
) -> ExternalEvent:
    """Store raw webhook event for processing."""
    # Find the matching repo link by repo full_name
    repo_fullname = payload.get("repository", {}).get("full_name")
    repo_link_id = None
    if repo_fullname:
        result = await db.execute(
            select(RepositoryLink.id).where(
                RepositoryLink.full_name == repo_fullname,
                RepositoryLink.is_active.is_(True),
            )
        )
        row = result.scalar_one_or_none()
        if row:
            repo_link_id = row

    event = ExternalEvent(
        source=ExternalEventSource.GITHUB,
        event_type=event_type,
        delivery_id=delivery_id,
        repository_link_id=repo_link_id,
        payload=payload,
        processed=False,
    )
    db.add(event)
    await db.flush()
    await db.refresh(event)
    return event


async def process_pr_event(
    db: AsyncSession,
    event: ExternalEvent,
) -> PullRequestLink | None:
    """Process a pull_request webhook event into a PullRequestLink."""
    pr_data = event.payload.get("pull_request", {})
    if not pr_data:
        return None

    action = event.payload.get("action", "")
    pr_number = pr_data.get("number")

    # Check if PR link already exists
    existing = await db.execute(
        select(PullRequestLink).where(
            PullRequestLink.repository_link_id == event.repository_link_id,
            PullRequestLink.pr_number == pr_number,
        )
    )
    pr_link = existing.scalar_one_or_none()

    status_map = {"open": PRStatus.OPEN, "closed": PRStatus.CLOSED}
    gh_status = pr_data.get("state", "open")
    if pr_data.get("merged"):
        pr_status = PRStatus.MERGED
    else:
        pr_status = status_map.get(gh_status, PRStatus.OPEN)

    if pr_link:
        pr_link.status = pr_status
        pr_link.pr_title = pr_data.get("title", pr_link.pr_title)
        if pr_data.get("merged_at"):
            from datetime import datetime

            pr_link.merged_at = datetime.fromisoformat(
                pr_data["merged_at"].replace("Z", "+00:00")
            )
    else:
        pr_link = PullRequestLink(
            repository_link_id=event.repository_link_id,
            pr_number=pr_number,
            pr_title=pr_data.get("title", ""),
            pr_url=pr_data.get("html_url", ""),
            head_branch=pr_data.get("head", {}).get("ref", ""),
            base_branch=pr_data.get("base", {}).get("ref", ""),
            status=pr_status,
        )
        db.add(pr_link)

    event.processed = True
    await db.flush()
    if pr_link.id is None:
        await db.refresh(pr_link)
    return pr_link


async def process_workflow_run_event(
    db: AsyncSession,
    event: ExternalEvent,
) -> CIPipelineRun | None:
    """Process a workflow_run event into a CIPipelineRun."""
    wr = event.payload.get("workflow_run", {})
    if not wr:
        return None

    status_map = {
        "queued": CIPipelineStatus.QUEUED,
        "in_progress": CIPipelineStatus.IN_PROGRESS,
        "completed": CIPipelineStatus.SUCCESS,
    }
    conclusion = wr.get("conclusion")
    if conclusion == "failure":
        ci_status = CIPipelineStatus.FAILURE
    elif conclusion == "cancelled":
        ci_status = CIPipelineStatus.CANCELLED
    else:
        ci_status = status_map.get(wr.get("status", "queued"), CIPipelineStatus.QUEUED)

    pipeline = CIPipelineRun(
        repository_link_id=event.repository_link_id,
        external_run_id=wr.get("id", 0),
        workflow_name=wr.get("name", "unknown"),
        head_sha=wr.get("head_sha", ""),
        branch=wr.get("head_branch", ""),
        status=ci_status,
        conclusion=conclusion,
    )
    db.add(pipeline)
    event.processed = True
    await db.flush()
    await db.refresh(pipeline)
    return pipeline


async def process_issues_event(
    db: AsyncSession,
    event: ExternalEvent,
) -> IssueLink | None:
    """Process an issues webhook event into an IssueLink."""
    issue_data = event.payload.get("issue", {})
    if not issue_data:
        return None

    issue_number = issue_data.get("number")

    # Find the project via repo link
    repo_link = None
    if event.repository_link_id:
        repo_link = await db.get(RepositoryLink, event.repository_link_id)

    if repo_link is None:
        return None

    existing = await db.execute(
        select(IssueLink).where(
            IssueLink.repository_link_id == event.repository_link_id,
            IssueLink.issue_number == issue_number,
        )
    )
    issue_link = existing.scalar_one_or_none()

    gh_state = issue_data.get("state", "open")
    status = IssueLinkStatus.CLOSED if gh_state == "closed" else IssueLinkStatus.OPEN
    labels = [l.get("name") for l in issue_data.get("labels", [])]

    if issue_link:
        issue_link.status = status
        issue_link.title = issue_data.get("title", issue_link.title)
        issue_link.labels = labels
    else:
        issue_link = IssueLink(
            repository_link_id=event.repository_link_id,
            project_id=repo_link.project_id,
            issue_number=issue_number,
            title=issue_data.get("title", ""),
            issue_url=issue_data.get("html_url", ""),
            status=status,
            labels=labels,
        )
        db.add(issue_link)

    event.processed = True
    await db.flush()
    if issue_link.id is None:
        await db.refresh(issue_link)
    return issue_link
