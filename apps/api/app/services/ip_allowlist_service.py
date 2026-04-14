"""IP allowlist service — CIDR-based access control per workspace.

FM-178: Manages IP allowlist entries and validates client IPs.
"""

import ipaddress
import logging
import uuid

from sqlalchemy import select, func as sa_func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enterprise_governance import IpAllowlistEntry

logger = logging.getLogger(__name__)


def is_valid_cidr(cidr: str) -> bool:
    """Validate a CIDR notation string."""
    try:
        ipaddress.ip_network(cidr, strict=False)
        return True
    except ValueError:
        return False


def check_ip_against_allowlist(
    client_ip: str,
    entries: list[IpAllowlistEntry],
) -> bool:
    """Check if a client IP is within any active allowlist entry.

    Returns True if the IP is allowed (matches at least one entry),
    or if the allowlist is empty (no restrictions).
    """
    active_entries = [e for e in entries if e.is_active]

    if not active_entries:
        return True  # No allowlist = no restrictions

    try:
        addr = ipaddress.ip_address(client_ip)
    except ValueError:
        logger.warning("ip_allowlist: invalid client IP: %s", client_ip)
        return False

    for entry in active_entries:
        try:
            network = ipaddress.ip_network(entry.cidr, strict=False)
            if addr in network:
                return True
        except ValueError:
            continue

    return False


async def get_workspace_allowlist(
    db: AsyncSession,
    workspace_id: uuid.UUID,
) -> list[IpAllowlistEntry]:
    """Get all IP allowlist entries for a workspace."""
    q = (
        select(IpAllowlistEntry)
        .where(IpAllowlistEntry.workspace_id == workspace_id)
        .order_by(IpAllowlistEntry.created_at.desc())
    )
    rows = (await db.execute(q)).scalars().all()
    return list(rows)


async def list_allowlist_entries(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    *,
    active_only: bool = False,
    offset: int = 0,
    limit: int = 50,
) -> tuple[list[IpAllowlistEntry], int]:
    """List IP allowlist entries with pagination."""
    conditions = [IpAllowlistEntry.workspace_id == workspace_id]
    if active_only:
        conditions.append(IpAllowlistEntry.is_active == True)  # noqa: E712

    where_clause = and_(*conditions)

    count_q = (
        select(sa_func.count())
        .select_from(IpAllowlistEntry)
        .where(where_clause)
    )
    total = (await db.execute(count_q)).scalar() or 0

    items_q = (
        select(IpAllowlistEntry)
        .where(where_clause)
        .order_by(IpAllowlistEntry.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    rows = (await db.execute(items_q)).scalars().all()

    return list(rows), total


async def add_allowlist_entry(
    db: AsyncSession,
    *,
    workspace_id: uuid.UUID,
    cidr: str,
    description: str | None = None,
    is_active: bool = True,
    created_by: uuid.UUID,
) -> IpAllowlistEntry:
    """Add an IP allowlist entry."""
    if not is_valid_cidr(cidr):
        raise ValueError(f"Invalid CIDR notation: {cidr}")

    entry = IpAllowlistEntry(
        workspace_id=workspace_id,
        cidr=cidr,
        description=description,
        is_active=is_active,
        created_by=created_by,
    )
    db.add(entry)
    await db.flush()

    logger.info(
        "ip_allowlist: added %s to workspace %s by %s",
        cidr,
        workspace_id,
        created_by,
    )
    return entry


async def remove_allowlist_entry(
    db: AsyncSession,
    entry_id: uuid.UUID,
) -> bool:
    """Remove an IP allowlist entry. Returns True if deleted."""
    entry = await db.get(IpAllowlistEntry, entry_id)
    if entry is None:
        return False
    await db.delete(entry)
    await db.flush()
    return True


async def toggle_allowlist_entry(
    db: AsyncSession,
    entry_id: uuid.UUID,
    is_active: bool,
) -> IpAllowlistEntry | None:
    """Activate or deactivate an IP allowlist entry."""
    entry = await db.get(IpAllowlistEntry, entry_id)
    if entry is None:
        return None
    entry.is_active = is_active
    await db.flush()
    return entry
