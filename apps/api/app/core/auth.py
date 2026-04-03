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
    return settings.secret_key


def _is_dev_mode() -> bool:
    """Check if running in dev mode (default/unchanged secret + non-production env).

    Both conditions must be true: SECRET_KEY must be the default AND
    APP_ENV must not be 'production'. This prevents accidental deployment
    with default config from bypassing authentication.
    """
    from app.core.config import settings
    return (
        settings.secret_key == "change-me-to-a-random-secret"
        and settings.app_env != "production"
    )


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

    if _is_dev_mode():
        logger.warning("Creating JWT with default dev secret — NOT safe for production")

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
    Development: returns stub user ID when no token is provided.
    """
    # If a token is provided, always verify it (even in dev mode)
    if credentials is not None:
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

    # No token provided — allow stub fallback only in dev mode
    if _is_dev_mode():
        return _STUB_USER_ID

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Bearer"},
    )
