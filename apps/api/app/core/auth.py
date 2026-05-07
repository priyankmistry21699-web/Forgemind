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
    from jose import jwt  # noqa: F811

    _jose_available = True
except ImportError:
    pass

# ── Configuration ────────────────────────────────────────────────

_STUB_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
_JWT_ALGORITHM = "HS256"
_TOKEN_EXPIRE_HOURS = 1  # L-23: reduced from 24h to limit stolen-token exposure window
_AUTH_ERROR_MSG = "Could not validate credentials"  # L-24: single message prevents token-state probing

_security = HTTPBearer(auto_error=False)


def _get_jwt_secret() -> str | None:
    """Get JWT secret from settings (lazy import to avoid circular)."""
    from app.core.config import settings

    return settings.secret_key


def _is_dev_mode() -> bool:
    """Return True only when the app is explicitly running in local development.

    VULN-10 fix: restrict the no-token stub fallback to APP_ENV == 'development'
    only. Previously this accepted any non-'production' env, which meant that
    staging deployments with the default secret became fully public.
    Staging/test/CI environments are internet-accessible in many setups and
    must require real tokens.
    """
    from app.core.config import settings

    is_default_secret = settings.secret_key == "change-me-to-a-random-secret"
    is_local_dev = settings.app_env == "development"

    if is_default_secret and not is_local_dev:
        # Should never reach here — config.py refuses to start with the default
        # secret in staging/test/production — but log loudly just in case.
        logger.error(
            "SECURITY: default SECRET_KEY detected in APP_ENV=%s. "
            "Authentication will NOT be bypassed outside 'development'.",
            settings.app_env,
        )

    return is_default_secret and is_local_dev


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
        except (ValueError, KeyError) as exc:
            # L-24: log the specific failure internally but return a uniform
            # message so callers cannot distinguish token states.
            logger.debug("JWT validation failed (ValueError/KeyError): %s", exc)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=_AUTH_ERROR_MSG,
                headers={"WWW-Authenticate": "Bearer"},
            )
        except Exception as exc:
            logger.debug("JWT validation failed (unexpected): %s", exc)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=_AUTH_ERROR_MSG,
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
