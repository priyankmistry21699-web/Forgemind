"""API Key & Rate Limiting services — FM-201/202.

FM-201: API key issuance, validation, revocation with scoped permissions.
FM-202: Rate limiting with sliding window per key/IP.
"""

import hashlib
import logging
import secrets
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.api_ecosystem import APIKey

logger = logging.getLogger(__name__)


# ── FM-201: API Key Management ───────────────────────────────────

API_KEY_PREFIX_LEN = 8
API_KEY_SECRET_LEN = 32


def _generate_api_key() -> tuple[str, str, str]:
    """Generate raw key, prefix, and hash.

    Returns (raw_key, prefix, key_hash).
    Raw key format: fm_<prefix>_<secret>
    """
    prefix = secrets.token_hex(API_KEY_PREFIX_LEN // 2)
    secret = secrets.token_hex(API_KEY_SECRET_LEN)
    raw_key = f"fm_{prefix}_{secret}"
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    return raw_key, prefix, key_hash


def hash_api_key(raw_key: str) -> str:
    """Hash a raw API key for lookup."""
    return hashlib.sha256(raw_key.encode()).hexdigest()


async def create_api_key(
    db: AsyncSession,
    *,
    creator_id: uuid.UUID,
    name: str,
    scopes: list[str] | None = None,
    org_id: uuid.UUID | None = None,
    expires_at: datetime | None = None,
) -> tuple[APIKey, str]:
    """Create a new API key. Returns (key_record, raw_key).

    The raw_key is returned ONLY at creation time — it is not stored.
    """
    raw_key, prefix, key_hash = _generate_api_key()

    key = APIKey(
        creator_id=creator_id,
        name=name,
        key_prefix=prefix,
        key_hash=key_hash,
        scopes=scopes or ["read"],
        org_id=org_id,
        expires_at=expires_at,
    )
    db.add(key)
    await db.flush()
    return key, raw_key


async def validate_api_key(
    db: AsyncSession,
    raw_key: str,
) -> APIKey:
    """Validate a raw API key. Returns the key record or raises 401."""
    key_hash = hash_api_key(raw_key)
    result = await db.execute(
        select(APIKey).where(
            APIKey.key_hash == key_hash,
            APIKey.revoked.is_(False),
        )
    )
    key = result.scalar_one_or_none()
    if key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or revoked API key",
        )

    # Check expiration
    if key.expires_at and key.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key has expired",
        )

    # Update last_used_at
    key.last_used_at = datetime.now(timezone.utc)
    await db.flush()
    return key


async def validate_api_key_with_scopes(
    db: AsyncSession,
    raw_key: str,
    *,
    required_scopes: list[str] | None = None,
) -> APIKey:
    """Validate API key and check that it has the required scopes.

    Raises 401 for invalid key, 403 for missing scopes.
    """
    key = await validate_api_key(db, raw_key)

    if required_scopes:
        key_scopes = set(key.scopes or [])
        # Wildcard scope grants everything
        if "*" not in key_scopes:
            missing = set(required_scopes) - key_scopes
            if missing:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"API key missing required scopes: {', '.join(sorted(missing))}",
                )
    return key


def require_scope(*scopes: str):
    """Create a FastAPI dependency that enforces API key scopes.

    Usage:
        @router.get("/protected", dependencies=[Depends(require_scope("read"))])
        async def protected_endpoint(): ...
    """
    required = list(scopes)

    async def _dependency(
        db: AsyncSession,
        api_key: str,
    ) -> APIKey:
        return await validate_api_key_with_scopes(
            db, api_key, required_scopes=required,
        )

    return _dependency


async def revoke_api_key(
    db: AsyncSession,
    key_id: uuid.UUID,
    creator_id: uuid.UUID,
) -> APIKey:
    """Revoke an API key (soft delete)."""
    result = await db.execute(
        select(APIKey).where(APIKey.id == key_id)
    )
    key = result.scalar_one_or_none()
    if key is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )
    if key.creator_id != creator_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to revoke this key",
        )
    key.revoked = True
    await db.flush()
    return key


async def list_api_keys(
    db: AsyncSession,
    creator_id: uuid.UUID,
    *,
    include_revoked: bool = False,
) -> list[APIKey]:
    """List API keys for a user."""
    query = select(APIKey).where(APIKey.creator_id == creator_id)
    if not include_revoked:
        query = query.where(APIKey.revoked.is_(False))
    result = await db.execute(query.order_by(APIKey.created_at.desc()))
    return list(result.scalars().all())


# ── FM-202: Rate Limiting ────────────────────────────────────────

# In-memory sliding window rate limiter (per-process).
# Production: swap for Redis-backed implementation.

import time
from collections import defaultdict

_rate_limits: dict[str, list[float]] = defaultdict(list)

DEFAULT_RATE_LIMIT = 100  # requests per window
DEFAULT_WINDOW_SECONDS = 60


def check_rate_limit(
    identifier: str,
    *,
    max_requests: int = DEFAULT_RATE_LIMIT,
    window_seconds: int = DEFAULT_WINDOW_SECONDS,
) -> dict[str, Any]:
    """Check and enforce sliding-window rate limit.

    Returns dict with allowed, remaining, reset_at fields.
    Raises HTTP 429 if limit exceeded.
    """
    now = time.time()
    cutoff = now - window_seconds

    # Prune old entries
    timestamps = _rate_limits[identifier]
    _rate_limits[identifier] = [t for t in timestamps if t > cutoff]
    timestamps = _rate_limits[identifier]

    remaining = max_requests - len(timestamps)
    reset_at = cutoff + window_seconds

    if remaining <= 0:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={
                "X-RateLimit-Limit": str(max_requests),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(reset_at)),
                "Retry-After": str(window_seconds),
            },
        )

    # Record this request
    _rate_limits[identifier].append(now)

    return {
        "allowed": True,
        "remaining": remaining - 1,
        "limit": max_requests,
        "reset_at": int(reset_at),
    }


def reset_rate_limit(identifier: str) -> None:
    """Reset rate limit for a given identifier (testing/admin)."""
    _rate_limits.pop(identifier, None)
