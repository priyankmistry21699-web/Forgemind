"""GitHub installation & repository link service.

FM-151: GitHub App & Repository Linking with token encryption and refresh.
"""

import uuid
import logging
from datetime import datetime, timezone, timedelta

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.github_integration import GitHubInstallation, RepositoryLink

logger = logging.getLogger(__name__)


async def create_installation(
    db: AsyncSession,
    installation_id: int,
    account_login: str,
    account_type: str,
    connected_by: uuid.UUID,
    permissions: dict | None = None,
) -> GitHubInstallation:
    inst = GitHubInstallation(
        installation_id=installation_id,
        account_login=account_login,
        account_type=account_type,
        connected_by=connected_by,
        permissions=permissions,
    )
    db.add(inst)
    await db.flush()
    await db.refresh(inst)
    return inst


async def get_installation_by_gh_id(
    db: AsyncSession,
    installation_id: int,
) -> GitHubInstallation | None:
    result = await db.execute(
        select(GitHubInstallation).where(
            GitHubInstallation.installation_id == installation_id
        )
    )
    return result.scalar_one_or_none()


async def list_installations(
    db: AsyncSession,
    *,
    connected_by: uuid.UUID | None = None,
) -> list[GitHubInstallation]:
    query = (
        select(GitHubInstallation)
        .where(GitHubInstallation.is_active.is_(True))
        .options(selectinload(GitHubInstallation.repos))
    )
    if connected_by is not None:
        query = query.where(GitHubInstallation.connected_by == connected_by)
    result = await db.execute(query)
    return list(result.scalars().all())


async def link_repository(
    db: AsyncSession,
    installation_id: uuid.UUID,
    project_id: uuid.UUID,
    github_repo_id: int,
    full_name: str,
    default_branch: str = "main",
) -> RepositoryLink:
    link = RepositoryLink(
        installation_id=installation_id,
        project_id=project_id,
        github_repo_id=github_repo_id,
        full_name=full_name,
        default_branch=default_branch,
    )
    db.add(link)
    await db.flush()
    await db.refresh(link)
    return link


async def list_repos_for_project(
    db: AsyncSession,
    project_id: uuid.UUID,
) -> list[RepositoryLink]:
    result = await db.execute(
        select(RepositoryLink).where(
            RepositoryLink.project_id == project_id,
            RepositoryLink.is_active.is_(True),
        )
    )
    return list(result.scalars().all())


async def unlink_repository(
    db: AsyncSession,
    link_id: uuid.UUID,
) -> None:
    link = await db.get(RepositoryLink, link_id)
    if link is None:
        raise HTTPException(status_code=404, detail="Repository link not found")
    link.is_active = False
    await db.flush()


# ---------------------------------------------------------------------------
# FM-151: Token encryption + refresh
# ---------------------------------------------------------------------------


async def store_installation_token(
    db: AsyncSession,
    installation_pk: uuid.UUID,
    access_token: str,
    expires_at: datetime | None = None,
) -> GitHubInstallation:
    """Encrypt and store an installation access token (FM-151)."""
    inst = await db.get(GitHubInstallation, installation_pk)
    if inst is None:
        raise HTTPException(status_code=404, detail="Installation not found")
    from app.services.encryption_service import encrypt

    inst.access_token_encrypted = encrypt(access_token)
    inst.token_expires_at = expires_at or (
        datetime.now(timezone.utc) + timedelta(hours=1)
    )
    await db.flush()
    await db.refresh(inst)
    return inst


async def get_installation_token(
    db: AsyncSession,
    installation_pk: uuid.UUID,
) -> str | None:
    """Decrypt and return the current installation access token.

    Returns None if no token is stored or token has expired.
    """
    inst = await db.get(GitHubInstallation, installation_pk)
    if inst is None or inst.access_token_encrypted is None:
        return None
    if inst.token_expires_at:
        expires_at = inst.token_expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < datetime.now(timezone.utc):
            logger.info("Token expired for installation %s", installation_pk)
            return None
    from app.services.encryption_service import decrypt

    try:
        return decrypt(inst.access_token_encrypted)
    except Exception:
        logger.warning("Failed to decrypt token for installation %s", installation_pk)
        return None


async def refresh_installation_token(
    db: AsyncSession,
    installation_pk: uuid.UUID,
    *,
    github_client: object | None = None,
) -> str | None:
    """Refresh an installation access token via GitHub API (FM-151).

    If github_client is None, uses the internal mock/stub path.
    Returns the new token string or None if refresh failed.
    """
    inst = await db.get(GitHubInstallation, installation_pk)
    if inst is None:
        return None

    # In production, this calls GitHub's POST /app/installations/{id}/access_tokens
    if github_client is not None:
        try:
            resp = await github_client.create_installation_token(inst.installation_id)
            token = resp["token"]
            expires_str = resp.get("expires_at")
            expires = None
            if expires_str:
                expires = datetime.fromisoformat(expires_str.replace("Z", "+00:00"))
            await store_installation_token(db, installation_pk, token, expires)
            return token
        except Exception as exc:
            logger.error("GitHub token refresh failed: %s", exc)
            return None

    # No client provided — cannot refresh
    return None


async def handle_oauth_callback(
    db: AsyncSession,
    installation_id_gh: int,
    access_token: str,
    expires_at: datetime | None = None,
) -> GitHubInstallation:
    """Handle OAuth/App installation callback — store token (FM-151)."""
    inst = await get_installation_by_gh_id(db, installation_id_gh)
    if inst is None:
        raise HTTPException(status_code=404, detail="Unknown installation")
    from app.services.encryption_service import encrypt

    inst.access_token_encrypted = encrypt(access_token)
    inst.token_expires_at = expires_at or (
        datetime.now(timezone.utc) + timedelta(hours=1)
    )
    await db.flush()
    await db.refresh(inst)
    return inst


# ---------------------------------------------------------------------------
# FM-151: Installation validation & lifecycle
# ---------------------------------------------------------------------------


async def validate_installation(
    db: AsyncSession,
    installation_pk: uuid.UUID,
) -> dict:
    """Check health of a GitHub installation (FM-151).

    Returns a status dict with: active, has_token, token_expired,
    expires_in_minutes, and an overall 'healthy' flag.
    """
    inst = await db.get(GitHubInstallation, installation_pk)
    if inst is None:
        raise HTTPException(status_code=404, detail="Installation not found")

    has_token = inst.access_token_encrypted is not None
    token_expired = False
    expires_in_minutes: float | None = None

    if has_token and inst.token_expires_at:
        exp = inst.token_expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        token_expired = exp < now
        if not token_expired:
            expires_in_minutes = round((exp - now).total_seconds() / 60, 1)

    healthy = inst.is_active and has_token and not token_expired

    return {
        "installation_id": inst.installation_id,
        "account_login": inst.account_login,
        "active": inst.is_active,
        "has_token": has_token,
        "token_expired": token_expired,
        "expires_in_minutes": expires_in_minutes,
        "healthy": healthy,
    }


async def get_or_refresh_token(
    db: AsyncSession,
    installation_pk: uuid.UUID,
    *,
    github_client: object | None = None,
) -> str | None:
    """Get the current token, refreshing if expired (FM-151).

    Chains: get_installation_token → if None and client available → refresh.
    Returns plaintext token or None.
    """
    token = await get_installation_token(db, installation_pk)
    if token is not None:
        return token

    # Token missing or expired — try refresh
    if github_client is not None:
        return await refresh_installation_token(
            db,
            installation_pk,
            github_client=github_client,
        )

    return None


async def list_installations_needing_refresh(
    db: AsyncSession,
    *,
    expiry_window_minutes: int = 10,
) -> list[GitHubInstallation]:
    """Find active installations with tokens expiring within the given window.

    Useful for proactive token refresh before expiry.
    """
    cutoff = datetime.now(timezone.utc) + timedelta(minutes=expiry_window_minutes)
    result = await db.execute(
        select(GitHubInstallation).where(
            GitHubInstallation.is_active.is_(True),
            GitHubInstallation.access_token_encrypted.isnot(None),
            GitHubInstallation.token_expires_at.isnot(None),
            GitHubInstallation.token_expires_at <= cutoff,
        )
    )
    return list(result.scalars().all())


async def deactivate_installation(
    db: AsyncSession,
    installation_pk: uuid.UUID,
) -> GitHubInstallation:
    """Soft-deactivate a GitHub installation (FM-151)."""
    inst = await db.get(GitHubInstallation, installation_pk)
    if inst is None:
        raise HTTPException(status_code=404, detail="Installation not found")
    inst.is_active = False
    await db.flush()
    await db.refresh(inst)
    return inst
