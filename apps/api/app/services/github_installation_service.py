"""GitHub installation & repository link service.

FM-151: GitHub App & Repository Linking.
"""

import uuid

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.github_integration import GitHubInstallation, RepositoryLink


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
) -> list[GitHubInstallation]:
    result = await db.execute(
        select(GitHubInstallation)
        .where(GitHubInstallation.is_active.is_(True))
        .options(selectinload(GitHubInstallation.repos))
    )
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
