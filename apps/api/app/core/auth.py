"""JWT authentication — production auth with fallback to stub.

FM-050: Provides JWT token verification using python-jose.
Falls back to stub user if JWT_SECRET is not configured (dev mode).
"""

import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger(__name__)

# Lazy import jose — available when python-jose is installed
_jose_available = False
try:
    from jose import jwt, JWTError
    _jose_available = True
except ImportError:
    pass

# ── Configuration ────────────────────────────────────────────────

_STUB_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
_JWT_ALGORITHM = "HS256"
_TOKEN_EXPIRE_HOURS = 24

_security = HTTPBearer(auto_error=False)


def _get_jwt_secret() -> str | None:
    """Get JWT secret from settings (lazy import to avoid circular)."""
    from app.core.config import settings
    secret = settings.secret_key
    if secret == "change-me-to-a-random-secret":
        return None
    return secret


def create_access_token(
    user_id: uuid.UUID,
    *,
    expires_delta: timedelta | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """Create a JWT access token."""
    secret = _get_jwt_secret()
    if secret is None or not _jose_available:
        raise ValueError("JWT not configured — set SECRET_KEY and install python-jose")

    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(hours=_TOKEN_EXPIRE_HOURS))

    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": expire,
        **(extra_claims or {}),
    }
    return jwt.encode(payload, secret, algorithm=_JWT_ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """Decode and verify a JWT token."""
    secret = _get_jwt_secret()
    if secret is None or not _jose_available:
        raise ValueError("JWT not configured")

    return jwt.decode(token, secret, algorithms=[_JWT_ALGORITHM])


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(_security),
) -> uuid.UUID:
    """Extract user ID from JWT token, or fall back to stub in dev mode.

    Production: requires valid JWT Bearer token.
    Development: returns stub user ID when no JWT_SECRET is configured.
    """
    secret = _get_jwt_secret()

    # Dev mode — no JWT configured, return stub
    if secret is None or not _jose_available:
        return _STUB_USER_ID

    # Production mode — require valid token
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_token(credentials.credentials)
        user_id = uuid.UUID(payload["sub"])
        return user_id
    except (ValueError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
