"""JWT token creation and verification.

Provides stateless JWT helpers decoupled from FastAPI,
so they can be reused across services.
"""

import uuid
import logging
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Any

logger = logging.getLogger(__name__)

_jose_available = False
try:
    from jose import jwt, JWTError  # noqa: F401

    _jose_available = True
except ImportError:
    pass

_DEFAULT_ALGORITHM = "HS256"
_DEFAULT_EXPIRE_HOURS = 24


@dataclass
class JWTConfig:
    """Configuration for JWT token operations."""

    secret: str
    algorithm: str = _DEFAULT_ALGORITHM
    expire_hours: int = _DEFAULT_EXPIRE_HOURS


def create_token(
    user_id: uuid.UUID,
    config: JWTConfig,
    *,
    expires_delta: timedelta | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """Create a JWT access token."""
    if not _jose_available:
        raise ValueError("python-jose is not installed")

    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(hours=config.expire_hours))

    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": expire,
        **(extra_claims or {}),
    }
    return jwt.encode(payload, config.secret, algorithm=config.algorithm)


def decode_token(token: str, config: JWTConfig) -> dict[str, Any]:
    """Decode and verify a JWT token."""
    if not _jose_available:
        raise ValueError("python-jose is not installed")

    return jwt.decode(token, config.secret, algorithms=[config.algorithm])
